"""Timer service to replace Tcl `after` callbacks with pygame-friendly scheduling."""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from .event_bus import EventBus, get_default_event_bus

logger = logging.getLogger(__name__)

TimerCallback = Callable[["TimerEvent"], Any]
_EPSILON_MS = 1e-6
_MANUAL_REASON = "manual"
_SIM_REASON = "simulation"


@dataclass(slots=True)
class TimerEvent:
    """Metadata passed to timer callbacks and optionally through the event bus."""

    timer_id: str
    metadata: Mapping[str, Any]
    tags: frozenset[str]
    run_count: int
    scheduled_for_ms: float
    fired_at_ms: float
    interval_ms: float | None
    repeating: bool
    simulation_bound: bool


@dataclass(slots=True)
class ScheduledTimer:
    timer_id: str
    callback: TimerCallback
    delay_ms: float
    interval_ms: float
    repeating: bool
    simulation_bound: bool
    tags: frozenset[str]
    metadata: dict[str, Any]
    next_fire_time_ms: float
    created_ms: float
    max_runs: int | None
    run_count: int = 0
    cancelled: bool = False
    paused_reasons: set[str] = field(default_factory=set)
    remaining_ms: float = 0.0

    @property
    def paused(self) -> bool:
        return bool(self.paused_reasons)


class TimerService:
    """Frame-driven timer scheduler for the pygame UI stack."""

    def __init__(
        self,
        *,
        clock: Callable[[], float] | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._clock = clock or time.monotonic
        self._event_bus = event_bus or get_default_event_bus()
        self._lock = threading.RLock()
        self._timers: dict[str, ScheduledTimer] = {}
        self._time_ms: float = 0.0
        self._last_clock_sample_ms: float | None = None
        self._simulation_paused = False

    # ------------------------------------------------------------------
    # Scheduling API
    # ------------------------------------------------------------------
    def schedule(
        self,
        delay_ms: float,
        callback: TimerCallback,
        *,
        repeating: bool = False,
        interval_ms: float | None = None,
        simulation_bound: bool = False,
        tags: Iterable[str] | None = None,
        metadata: Mapping[str, Any] | None = None,
        max_runs: int | None = None,
        timer_id: str | None = None,
    ) -> str:
        """Schedule ``callback`` after ``delay_ms`` milliseconds."""

        if delay_ms < 0:
            raise ValueError("delay_ms must be non-negative")
        if not callable(callback):
            raise ValueError("callback must be callable")
        resolved_interval = interval_ms if interval_ms is not None else delay_ms
        if repeating and resolved_interval <= 0:
            raise ValueError("interval_ms must be positive for repeating timers")
        timer_key = timer_id or uuid.uuid4().hex
        tags_set = frozenset(tags or ())
        metadata_dict = dict(metadata or {})
        with self._lock:
            next_fire = self._time_ms + delay_ms
            timer = ScheduledTimer(
                timer_id=timer_key,
                callback=callback,
                delay_ms=delay_ms,
                interval_ms=resolved_interval,
                repeating=repeating,
                simulation_bound=simulation_bound,
                tags=tags_set,
                metadata=metadata_dict,
                next_fire_time_ms=next_fire,
                created_ms=self._time_ms,
                max_runs=max_runs,
            )
            self._timers[timer_key] = timer
            if self._simulation_paused and simulation_bound:
                self._apply_pause(timer, _SIM_REASON)
        return timer_key

    def call_later(
        self,
        delay_ms: float,
        callback: TimerCallback,
        **kwargs: Any,
    ) -> str:
        return self.schedule(delay_ms, callback, repeating=False, **kwargs)

    def call_every(
        self,
        interval_ms: float,
        callback: TimerCallback,
        *,
        delay_ms: float | None = None,
        **kwargs: Any,
    ) -> str:
        start_after = interval_ms if delay_ms is None else delay_ms
        return self.schedule(
            start_after,
            callback,
            repeating=True,
            interval_ms=interval_ms,
            **kwargs,
        )

    def cancel(self, timer_id: str) -> bool:
        with self._lock:
            timer = self._timers.pop(timer_id, None)
            if timer is None:
                return False
            timer.cancelled = True
            return True

    def cancel_by_tag(self, tag: str) -> int:
        tag_lower = tag
        with self._lock:
            targets = [
                tid for tid, timer in self._timers.items() if tag_lower in timer.tags
            ]
            for tid in targets:
                self.cancel(tid)
        return len(targets)

    def pause_timer(self, timer_id: str) -> bool:
        with self._lock:
            timer = self._timers.get(timer_id)
            if timer is None:
                return False
            self._apply_pause(timer, _MANUAL_REASON)
            return True

    def resume_timer(self, timer_id: str) -> bool:
        with self._lock:
            timer = self._timers.get(timer_id)
            if timer is None:
                return False
            self._release_pause(timer, _MANUAL_REASON)
            return True

    def set_simulation_paused(self, paused: bool) -> None:
        with self._lock:
            if self._simulation_paused == paused:
                return
            self._simulation_paused = paused
            for timer in self._timers.values():
                if not timer.simulation_bound:
                    continue
                if paused:
                    self._apply_pause(timer, _SIM_REASON)
                else:
                    self._release_pause(timer, _SIM_REASON)

    # ------------------------------------------------------------------
    # Update loop integration
    # ------------------------------------------------------------------
    def tick(self, dt_ms: float | None = None) -> int:
        with self._lock:
            delta = self._resolve_delta(dt_ms)
            if delta:
                self._time_ms += delta
            return self._dispatch_due_locked()

    def run_pending(self) -> int:
        """Process timers without advancing virtual time."""

        return self.tick(0.0)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------
    @property
    def now_ms(self) -> float:
        with self._lock:
            return self._time_ms

    def active_count(self) -> int:
        with self._lock:
            return len(self._timers)

    def has_timer(self, timer_id: str) -> bool:
        with self._lock:
            return timer_id in self._timers

    def clear(self) -> None:
        with self._lock:
            self._timers.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _resolve_delta(self, dt_ms: float | None) -> float:
        if dt_ms is not None:
            return max(float(dt_ms), 0.0)
        sample_ms = self._clock() * 1000.0
        if self._last_clock_sample_ms is None:
            self._last_clock_sample_ms = sample_ms
            return 0.0
        delta = max(sample_ms - self._last_clock_sample_ms, 0.0)
        self._last_clock_sample_ms = sample_ms
        return delta

    def _dispatch_due_locked(self) -> int:
        callbacks_run = 0
        for timer in list(self._timers.values()):
            callbacks_run += self._fire_if_due(timer)
        return callbacks_run

    def _fire_if_due(self, timer: ScheduledTimer) -> int:
        if timer.cancelled or timer.paused:
            return 0
        fired = 0
        while (
            not timer.cancelled
            and not timer.paused
            and timer.next_fire_time_ms - self._time_ms <= _EPSILON_MS
        ):
            fired += 1
            timer.run_count += 1
            event = TimerEvent(
                timer_id=timer.timer_id,
                metadata=dict(timer.metadata),
                tags=timer.tags,
                run_count=timer.run_count,
                scheduled_for_ms=timer.next_fire_time_ms,
                fired_at_ms=self._time_ms,
                interval_ms=timer.interval_ms if timer.repeating else None,
                repeating=timer.repeating,
                simulation_bound=timer.simulation_bound,
            )
            try:
                timer.callback(event)
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.exception(
                    "Timer %s callback raised", timer.timer_id, exc_info=exc
                )
            self._publish_event(timer, event)
            if timer.repeating and not timer.cancelled:
                if timer.max_runs and timer.run_count >= timer.max_runs:
                    self.cancel(timer.timer_id)
                    break
                timer.next_fire_time_ms = self._time_ms + timer.interval_ms
            else:
                self.cancel(timer.timer_id)
                break
        return fired

    def _apply_pause(self, timer: ScheduledTimer, reason: str) -> None:
        if timer.cancelled or reason in timer.paused_reasons:
            return
        if not timer.paused_reasons:
            timer.remaining_ms = max(timer.next_fire_time_ms - self._time_ms, 0.0)
        timer.paused_reasons.add(reason)

    def _release_pause(self, timer: ScheduledTimer, reason: str) -> None:
        if timer.cancelled or reason not in timer.paused_reasons:
            return
        timer.paused_reasons.remove(reason)
        if not timer.paused_reasons:
            timer.next_fire_time_ms = self._time_ms + timer.remaining_ms
            timer.remaining_ms = 0.0

    def _publish_event(self, timer: ScheduledTimer, event: TimerEvent) -> None:
        if self._event_bus is None:
            return
        payload = {
            "timer_id": event.timer_id,
            "metadata": dict(event.metadata),
            "tags": event.tags,
            "run_count": event.run_count,
            "repeating": event.repeating,
            "interval_ms": event.interval_ms,
            "simulation_bound": event.simulation_bound,
            "fired_at_ms": event.fired_at_ms,
        }
        combined_tags = ("timer",) + tuple(event.tags)
        self._event_bus.publish(
            "timer.fired",
            payload,
            source="timer-service",
            tags=combined_tags,
            defer=True,
        )


_DEFAULT_TIMER_SERVICE = TimerService()


def get_default_timer_service() -> TimerService:
    return _DEFAULT_TIMER_SERVICE


def set_default_timer_service(service: TimerService) -> TimerService:
    global _DEFAULT_TIMER_SERVICE
    _DEFAULT_TIMER_SERVICE = service
    return _DEFAULT_TIMER_SERVICE


__all__ = [
    "TimerService",
    "TimerEvent",
    "get_default_timer_service",
    "set_default_timer_service",
]
