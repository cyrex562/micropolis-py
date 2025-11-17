from __future__ import annotations

from typing import Any

import pytest

from micropolis.ui.event_bus import (
    BusEvent,
    EventBus,
    get_default_event_bus,
    set_default_event_bus,
)


class FakeEvent:
    def __init__(self, event_type: Any) -> None:
        self.type = event_type


@pytest.fixture
def bus() -> EventBus:
    bus = EventBus()
    yield bus


def test_priority_order_and_multiple_subscribers(bus: EventBus) -> None:
    order: list[str] = []

    def low(event: BusEvent) -> None:
        order.append(f"low:{event.topic}")

    def high(event: BusEvent) -> None:
        order.append(f"high:{event.topic}")

    bus.subscribe("funds.updated", low, priority=0)
    bus.subscribe("funds.updated", high, priority=10)

    callbacks = bus.publish("funds.updated", {"value": 123})

    assert callbacks == 2
    assert order == ["high:funds.updated", "low:funds.updated"]


def test_once_subscriptions_are_removed_after_delivery(bus: EventBus) -> None:
    calls: list[int] = []
    token = bus.subscribe("population.updated", lambda e: calls.append(1), once=True)

    bus.publish("population.updated", None)
    bus.publish("population.updated", None)

    assert calls == [1]
    assert bus.unsubscribe(token) is False


def test_wildcard_patterns_and_predicate_filter(bus: EventBus) -> None:
    payloads: list[Any] = []

    def predicate(event: BusEvent) -> bool:
        return bool(event.payload and event.payload.get("level") == "warning")

    bus.subscribe("sugar.*", lambda e: payloads.append(e.payload), predicate=predicate)

    bus.publish("sugar.buddy_joined", {"level": "info"})
    bus.publish("sugar.alert", {"level": "warning", "buddy": "Ada"})

    assert payloads == [{"level": "warning", "buddy": "Ada"}]


def test_reentrant_publish_is_queued(bus: EventBus) -> None:
    events: list[str] = []

    def handler(event: BusEvent) -> None:
        events.append(event.topic)
        if event.topic == "a" and len(events) == 1:
            bus.publish("b", None)

    bus.subscribe("a", handler)
    bus.subscribe("b", handler)

    bus.publish("a", None)

    assert events == ["a", "b"]


def test_publish_pygame_event_emits_general_and_specific_topics(bus: EventBus) -> None:
    received: list[str] = []
    bus.subscribe("pygame.event", lambda e: received.append(e.topic))
    bus.subscribe("pygame.event.keydown", lambda e: received.append(e.topic))

    bus.publish_pygame_event(FakeEvent("KEYDOWN"))

    assert received == ["pygame.event", "pygame.event.keydown"]


def test_simulation_and_sugar_helpers(bus: EventBus) -> None:
    payloads: dict[str, Any] = {}

    bus.subscribe(
        "simulation.funds.updated",
        lambda e: payloads.setdefault("sim", e.payload),
    )
    bus.subscribe("sugar.sync", lambda e: payloads.setdefault("sugar", e.payload))

    bus.publish_simulation_event("funds.updated", funds=999)
    bus.publish_sugar_message("sync", payload={"status": "ok"})

    assert payloads["sim"] == {"funds": 999}
    assert payloads["sugar"] == {"status": "ok"}


def test_default_event_bus_helpers_return_singleton(bus: EventBus) -> None:
    original = get_default_event_bus()
    try:
        set_default_event_bus(bus)
        assert get_default_event_bus() is bus
    finally:
        set_default_event_bus(original)
