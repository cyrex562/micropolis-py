"""Publish/subscribe event bus for the pygame UI stack."""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable, Iterable, MutableMapping, Sequence
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

EventCallback = Callable[["BusEvent"], Any]
EventPredicate = Callable[["BusEvent"], bool]


@dataclass(slots=True)
class BusEvent:
    """Normalized event data dispatched through the :class:`EventBus`."""

    topic: str
    payload: Any = None
    source: str | None = None
    tags: frozenset[str] = field(default_factory=frozenset)
    timestamp: float = field(default_factory=time.monotonic)
    metadata: MutableMapping[str, Any] | None = field(default_factory=dict)


@dataclass(slots=True)
class EventSubscription:
    """Registration metadata for a subscriber callback."""

    subscription_id: str
    topic: str
    callback: EventCallback
    priority: int = 0
    once: bool = False
    predicate: EventPredicate | None = None

    def matches(self, event: BusEvent) -> bool:
        if self.predicate is None:
            return True
        try:
            return bool(self.predicate(event))
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.exception(
                "Event predicate failed for topic %s", self.topic, exc_info=exc
            )
            return False


class EventBus:
    """Thread-safe event bus with prioritized publish/subscribe semantics."""

    def __init__(self, *, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock or time.monotonic
        self._subscriptions: dict[str, EventSubscription] = {}
        self._topics: dict[str, list[EventSubscription]] = defaultdict(list)
        self._queue: deque[BusEvent] = deque()
        self._dispatching = False
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Subscription management
    # ------------------------------------------------------------------
    def subscribe(
        self,
        topic: str,
        callback: EventCallback,
        *,
        priority: int = 0,
        once: bool = False,
        predicate: EventPredicate | None = None,
    ) -> str:
        """Register a callback for ``topic`` and return a subscription id."""

        normalized = self._normalize_topic(topic)
        if not normalized:
            raise ValueError("topic must be a non-empty string")
        if not callable(callback):
            raise ValueError("callback must be callable")
        subscription_id = uuid.uuid4().hex
        subscription = EventSubscription(
            subscription_id=subscription_id,
            topic=normalized,
            callback=callback,
            priority=int(priority),
            once=once,
            predicate=predicate,
        )
        with self._lock:
            self._subscriptions[subscription_id] = subscription
            bucket = self._topics[normalized]
            bucket.append(subscription)
            bucket.sort(key=lambda sub: sub.priority, reverse=True)
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a previously registered callback."""

        with self._lock:
            subscription = self._subscriptions.pop(subscription_id, None)
            if not subscription:
                return False
            bucket = self._topics.get(subscription.topic)
            if bucket:
                self._topics[subscription.topic] = [
                    sub for sub in bucket if sub.subscription_id != subscription_id
                ]
                if not self._topics[subscription.topic]:
                    del self._topics[subscription.topic]
        return True

    def clear(self) -> None:
        """Remove all subscribers and pending events (testing helper)."""

        with self._lock:
            self._subscriptions.clear()
            self._topics.clear()
            self._queue.clear()
            self._dispatching = False

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------
    def publish(
        self,
        topic: str,
        payload: Any = None,
        *,
        source: str | None = None,
        tags: Iterable[str] | None = None,
        metadata: MutableMapping[str, Any] | None = None,
        defer: bool = False,
    ) -> int:
        """Publish an event to subscribers and return the number of callbacks run."""

        normalized = self._normalize_topic(topic)
        tags_set = frozenset(tags or ())
        event = BusEvent(
            topic=normalized,
            payload=payload,
            source=source,
            tags=tags_set,
            timestamp=self._clock(),
            metadata=metadata or {},
        )
        return self._enqueue_event(event, defer=defer)

    def publish_many(self, events: Sequence[tuple[str, Any]]) -> int:
        """Publish a batch of ``(topic, payload)`` events."""

        count = 0
        for topic, payload in events:
            self.publish(topic, payload, defer=True)
        count += self.flush()
        return count

    def flush(self) -> int:
        """Force dispatch of queued events and return callback count."""

        return self._drain_queue()

    # Convenience bridges -------------------------------------------------
    def publish_pygame_event(
        self, event: Any, *, tags: Iterable[str] | None = None
    ) -> None:
        """Publish a pygame event under ``pygame.event.*`` topics."""

        event_type = getattr(event, "type", "unknown")
        type_name = self._resolve_pygame_type(event_type)
        envelope = {
            "event": event,
            "type": event_type,
            "type_name": type_name,
        }
        combined_tags = tuple(set((tags or ())) | {"pygame"})
        self.publish(
            "pygame.event",
            envelope,
            source="pygame",
            tags=combined_tags,
        )
        self.publish(
            f"pygame.event.{type_name}",
            envelope,
            source="pygame",
            tags=combined_tags,
        )

    def publish_simulation_event(
        self,
        name: str,
        payload: Any | None = None,
        **fields: Any,
    ) -> None:
        """Publish under ``simulation.<name>`` for engine-side state changes."""

        data = payload if payload is not None else fields
        self.publish(
            f"simulation.{self._normalize_topic(name)}",
            data,
            source="simulation",
            tags=("simulation",),
        )

    def publish_sugar_message(
        self,
        command: str,
        payload: Any | None = None,
        **fields: Any,
    ) -> None:
        """Publish Sugar activity bridge messages under ``sugar.<command>``."""

        data = payload if payload is not None else fields
        self.publish(
            f"sugar.{self._normalize_topic(command)}",
            data,
            source="sugar",
            tags=("sugar",),
        )

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    def subscriber_count(self, topic: str | None = None) -> int:
        if topic is None:
            with self._lock:
                return len(self._subscriptions)
        normalized = self._normalize_topic(topic)
        with self._lock:
            return len(self._topics.get(normalized, ()))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _enqueue_event(self, event: BusEvent, *, defer: bool) -> int:
        with self._lock:
            self._queue.append(event)
            should_dispatch = not defer and not self._dispatching
        if should_dispatch:
            return self._drain_queue()
        return 0

    def _drain_queue(self) -> int:
        if self._dispatching:
            return 0
        self._dispatching = True
        callbacks_run = 0
        try:
            while True:
                with self._lock:
                    if not self._queue:
                        self._dispatching = False
                        return callbacks_run
                    event = self._queue.popleft()
                callbacks_run += self._deliver(event)
        finally:
            self._dispatching = False
        return callbacks_run

    def _deliver(self, event: BusEvent) -> int:
        subscribers = self._matching_subscribers(event.topic)
        callbacks_run = 0
        for subscription in subscribers:
            if subscription.subscription_id not in self._subscriptions:
                continue
            if not subscription.matches(event):
                continue
            try:
                # Conservative compatibility: some legacy callbacks expect
                # the raw payload (a dict) whereas newer consumers expect
                # the full BusEvent object. Use a small heuristic based on
                # the subscriber's first parameter name to decide which
                # form to deliver. This keeps behavior stable for both
                # styles while avoiding accidental TypeErrors.
                cb = subscription.callback
                delivered = False
                try:
                    import inspect

                    sig = inspect.signature(cb)
                    params = list(sig.parameters.values())
                    if params:
                        first_name = params[0].name.lower()
                        # Common names used by payload-only callbacks
                        if first_name in ("payload", "data", "msg", "message"):
                            cb(event.payload)
                            delivered = True
                except Exception:
                    # If inspection fails, fall back to BusEvent delivery
                    delivered = False

                if not delivered:
                    # Default: deliver the full BusEvent
                    cb(event)

                callbacks_run += 1
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.exception(
                    "Unhandled exception in subscriber %s for topic %s",
                    subscription.subscription_id,
                    event.topic,
                    exc_info=exc,
                )
            if subscription.once:
                self.unsubscribe(subscription.subscription_id)
        return callbacks_run

    # Backwards-compatible alias used by tests and some legacy code
    def emit(self, topic: str, payload: Any = None, **kwargs) -> int:
        """Compatibility wrapper naming: delegate to publish()."""
        return self.publish(topic, payload, **kwargs)

    def _matching_subscribers(self, topic: str) -> list[EventSubscription]:
        matches: list[EventSubscription] = []
        with self._lock:
            for pattern, bucket in self._topics.items():
                if self._topic_matches(pattern, topic):
                    matches.extend(bucket)
        return matches

    @staticmethod
    def _normalize_topic(topic: str) -> str:
        return topic.strip().lower()

    @staticmethod
    def _topic_matches(pattern: str, topic: str) -> bool:
        if pattern == "*" or pattern == topic:
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return topic == prefix or topic.startswith(prefix + ".")
        return False

    @staticmethod
    def _resolve_pygame_type(event_type: Any) -> str:
        if isinstance(event_type, str):
            return event_type.lower()
        try:
            import pygame  # type: ignore

            if hasattr(pygame, "event") and hasattr(pygame.event, "event_name"):
                name = pygame.event.event_name(event_type)
                if name:
                    return name.lower()
        except Exception:  # pragma: no cover - pygame optional dependency
            pass
        return str(event_type).lower()


_DEFAULT_EVENT_BUS = EventBus()


def get_default_event_bus() -> EventBus:
    """Return the lazily initialized default event bus instance."""

    return _DEFAULT_EVENT_BUS


def set_default_event_bus(bus: EventBus) -> EventBus:
    """Override the module-level default bus (primarily for testing)."""

    global _DEFAULT_EVENT_BUS
    _DEFAULT_EVENT_BUS = bus
    return _DEFAULT_EVENT_BUS


__all__ = [
    "BusEvent",
    "EventBus",
    "EventSubscription",
    "get_default_event_bus",
    "set_default_event_bus",
]
