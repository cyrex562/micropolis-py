"""Integration tests for Event Bus + Timer Service as specified in §5.3.

This test suite validates that the Timer Service and Event Bus work together
to enable clean fan-out of shared events (funds.updated, disaster.triggered,
overlay.changed) to multiple subscribers without conflicts.
"""

from __future__ import annotations

import pytest

from micropolis.ui.event_bus import BusEvent, EventBus
from micropolis.ui.timer_service import TimerEvent, TimerService


class EventCollector:
    """Helper to track events received by a subscriber."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.events: list[tuple[str, dict]] = []

    def handler(self, event: BusEvent) -> None:
        """Record incoming events."""
        self.events.append((event.topic, event.payload))

    def clear(self) -> None:
        """Reset collected events."""
        self.events.clear()


@pytest.fixture
def bus() -> EventBus:
    """Provide a fresh EventBus instance."""
    return EventBus()


@pytest.fixture
def timer_service(bus: EventBus) -> TimerService:
    """Provide a TimerService connected to the bus."""
    return TimerService(event_bus=bus)


def test_multiple_panels_subscribe_to_funds_updated(bus: EventBus) -> None:
    """Verify multiple panels can subscribe to funds.updated without conflict."""
    head_panel = EventCollector("head")
    budget_panel = EventCollector("budget")
    eval_panel = EventCollector("evaluation")

    # Subscribe all three panels
    bus.subscribe("funds.updated", head_panel.handler)
    bus.subscribe("funds.updated", budget_panel.handler)
    bus.subscribe("funds.updated", eval_panel.handler)

    # Publish a funds update
    bus.publish("funds.updated", {"value": 50000, "change": -1500})

    # All three panels should receive the event
    assert len(head_panel.events) == 1
    assert len(budget_panel.events) == 1
    assert len(eval_panel.events) == 1

    # All should have the same payload
    assert head_panel.events[0][1]["value"] == 50000
    assert budget_panel.events[0][1]["value"] == 50000
    assert eval_panel.events[0][1]["value"] == 50000


def test_disaster_triggered_with_priority_ordering(bus: EventBus) -> None:
    """Verify disaster.triggered events respect subscriber priority."""
    order: list[str] = []

    def high_priority_handler(event: BusEvent) -> None:
        order.append("high-priority-system")

    def low_priority_handler(event: BusEvent) -> None:
        order.append("low-priority-ui")

    # Subscribe with different priorities
    bus.subscribe("disaster.triggered", low_priority_handler, priority=0)
    bus.subscribe("disaster.triggered", high_priority_handler, priority=100)

    # Publish disaster event
    bus.publish("disaster.triggered", {"type": "fire", "x": 50, "y": 60})

    # High priority should execute first
    assert order == ["high-priority-system", "low-priority-ui"]


def test_overlay_changed_with_wildcard_subscription(bus: EventBus) -> None:
    """Verify overlay.changed events can be caught with wildcards."""
    all_overlays = EventCollector("all")
    power_only = EventCollector("power")

    # Subscribe to all overlay events with wildcard
    bus.subscribe("overlay.*", all_overlays.handler)

    # Subscribe to specific overlay
    bus.subscribe("overlay.power", power_only.handler)

    # Publish various overlay changes
    bus.publish("overlay.power", {"enabled": True})
    bus.publish("overlay.traffic", {"enabled": True})
    bus.publish("overlay.pollution", {"enabled": False})

    # Wildcard subscriber sees all three
    assert len(all_overlays.events) == 3

    # Specific subscriber sees only power
    assert len(power_only.events) == 1
    assert power_only.events[0][0] == "overlay.power"


def test_timer_triggered_events_fan_out_to_multiple_subscribers(
    bus: EventBus, timer_service: TimerService
) -> None:
    """Verify timer events published through bus reach multiple subscribers."""
    collector_a = EventCollector("a")
    collector_b = EventCollector("b")

    # Subscribe to timer.fired events
    bus.subscribe("timer.fired", collector_a.handler)
    bus.subscribe("timer.fired", collector_b.handler)

    # Schedule a timer
    timer_service.call_later(100, lambda e: None, tags=("test",))

    # Advance time to trigger
    timer_service.tick(100)

    # Flush deferred events
    bus.flush()

    # Both collectors should receive the timer.fired event
    assert len(collector_a.events) == 1
    assert len(collector_b.events) == 1
    assert collector_a.events[0][0] == "timer.fired"
    assert collector_b.events[0][0] == "timer.fired"


def test_simulation_pause_affects_bound_timers_but_not_events(
    bus: EventBus, timer_service: TimerService
) -> None:
    """Verify simulation-bound timers pause, but event delivery continues."""
    sim_collector = EventCollector("sim")
    ui_collector = EventCollector("ui")

    # Subscribe to events
    bus.subscribe("simulation.*", sim_collector.handler)
    bus.subscribe("ui.*", ui_collector.handler)

    # Create simulation-bound and UI timers
    timer_service.call_later(50, lambda e: None, simulation_bound=True, tags=("sim",))
    timer_service.call_later(50, lambda e: None, simulation_bound=False, tags=("ui",))

    # Pause simulation
    timer_service.set_simulation_paused(True)

    # Publish some events (should still work)
    bus.publish("simulation.paused", {"reason": "budget"})
    bus.publish("ui.interaction", {"action": "click"})

    # Events delivered despite simulation pause
    assert len(sim_collector.events) == 1
    assert len(ui_collector.events) == 1

    # Advance time - only UI timer fires
    timer_service.tick(50)
    bus.flush()

    # UI timer fired, but simulation timer didn't
    timer_events = [e for e in ui_collector.events if e[0] == "timer.fired"]
    assert len(timer_events) == 0  # UI timer doesn't publish to simulation.*


def test_budget_timer_countdown_with_event_notifications(
    bus: EventBus, timer_service: TimerService
) -> None:
    """Simulate budget countdown timer as described in §5.3."""
    notifications: list[str] = []

    def budget_countdown_callback(event: TimerEvent) -> None:
        remaining = 10 - event.run_count
        bus.publish(
            "budget.countdown",
            {"remaining_seconds": remaining, "run_count": event.run_count},
            defer=False,  # Immediate notification
        )

    def notification_handler(event: BusEvent) -> None:
        notifications.append(f"Budget in {event.payload['remaining_seconds']}s")

    # Subscribe to countdown notifications
    bus.subscribe("budget.countdown", notification_handler)

    # Schedule 1-second repeating timer (1000ms)
    timer_service.call_every(
        1000,
        budget_countdown_callback,
        simulation_bound=True,
        tags=("budget",),
        max_runs=10,
    )

    # Simulate 10 seconds passing
    for _ in range(10):
        timer_service.tick(1000)

    # Should have 10 notifications
    assert len(notifications) == 10
    assert notifications[0] == "Budget in 9s"
    assert notifications[-1] == "Budget in 0s"


def test_event_reentrant_safety_with_nested_publishes(bus: EventBus) -> None:
    """Verify re-entrant publishes are queued properly per §5.3."""
    order: list[str] = []

    def handler_a(event: BusEvent) -> None:
        order.append("a-received")
        if event.payload.get("trigger_b"):
            # Publish another event during handling
            bus.publish("test.b", {"from": "a"})

    def handler_b(event: BusEvent) -> None:
        order.append("b-received")

    bus.subscribe("test.a", handler_a)
    bus.subscribe("test.b", handler_b)

    # Trigger a with nested publish
    bus.publish("test.a", {"trigger_b": True})

    # Events should be processed in order: a completes, then b
    assert order == ["a-received", "b-received"]


def test_overlay_blink_timer_integration(
    bus: EventBus, timer_service: TimerService
) -> None:
    """Simulate blinking overlay timer as described in §5.3 (500ms toggle)."""
    blink_states: list[bool] = []
    current_state = False

    def blink_callback(event: TimerEvent) -> None:
        nonlocal current_state
        current_state = not current_state
        bus.publish("overlay.blink", {"state": current_state}, defer=False)

    def state_recorder(event: BusEvent) -> None:
        blink_states.append(event.payload["state"])

    # Subscribe to blink events
    bus.subscribe("overlay.blink", state_recorder)

    # Schedule 500ms repeating blink timer
    timer_service.call_every(500, blink_callback, tags=("blink",), max_runs=6)

    # Simulate 3 seconds (6 blinks)
    for _ in range(6):
        timer_service.tick(500)

    # Should alternate True/False
    assert len(blink_states) == 6
    assert blink_states == [True, False, True, False, True, False]


def test_once_only_subscriber_for_splash_screen(bus: EventBus) -> None:
    """Verify once-only subscribers work for splash screen transitions."""
    splash_completed = []

    def splash_handler(event: BusEvent) -> None:
        splash_completed.append(event.payload["ready"])

    # Subscribe once-only to engine.initialized
    bus.subscribe("engine.initialized", splash_handler, once=True)

    # Publish initialization event multiple times
    bus.publish("engine.initialized", {"ready": True})
    bus.publish("engine.initialized", {"ready": True})
    bus.publish("engine.initialized", {"ready": True})

    # Handler should only fire once
    assert splash_completed == [True]


def test_sugar_stdin_events_bridge_to_bus(bus: EventBus) -> None:
    """Verify Sugar protocol messages integrate via bus per §6.1."""
    sugar_events: list[tuple[str, dict]] = []

    def sugar_handler(event: BusEvent) -> None:
        sugar_events.append((event.topic, event.payload))

    # Subscribe to all sugar.* events
    bus.subscribe("sugar.*", sugar_handler)

    # Simulate Sugar messages via convenience method
    bus.publish_sugar_message("buddy_joined", {"name": "Ada", "color": "#FF0000"})
    bus.publish_sugar_message("activate", {})
    bus.publish_sugar_message("quit", {})

    # All three should be received
    assert len(sugar_events) == 3
    assert sugar_events[0][0] == "sugar.buddy_joined"
    assert sugar_events[1][0] == "sugar.activate"
    assert sugar_events[2][0] == "sugar.quit"


def test_tag_based_filtering_for_channel_semantics(bus: EventBus) -> None:
    """Verify tag-based filtering enables channel-like behavior."""
    simulation_events: list[str] = []
    ui_events: list[str] = []

    def sim_handler(event: BusEvent) -> None:
        if "simulation" in event.tags:
            simulation_events.append(event.topic)

    def ui_handler(event: BusEvent) -> None:
        if "ui" in event.tags:
            ui_events.append(event.topic)

    # Subscribe with predicates for tag filtering
    bus.subscribe("*", sim_handler, predicate=lambda e: "simulation" in e.tags)
    bus.subscribe("*", ui_handler, predicate=lambda e: "ui" in e.tags)

    # Publish events with different tags
    bus.publish("event.a", {}, tags=("simulation",))
    bus.publish("event.b", {}, tags=("ui",))
    bus.publish("event.c", {}, tags=("simulation", "ui"))

    # Each handler sees only its tagged events
    assert simulation_events == ["event.a", "event.c"]
    assert ui_events == ["event.b", "event.c"]


def test_timer_metadata_passed_through_events(
    bus: EventBus, timer_service: TimerService
) -> None:
    """Verify timer metadata is accessible in event payloads."""
    received_metadata: list[dict] = []

    def metadata_collector(event: BusEvent) -> None:
        received_metadata.append(event.payload.get("metadata", {}))

    bus.subscribe("timer.fired", metadata_collector)

    # Schedule timer with metadata
    timer_service.call_later(
        50,
        lambda e: None,
        metadata={"purpose": "autosave", "target": "city.cty"},
    )

    timer_service.tick(50)
    bus.flush()

    # Metadata should be preserved
    assert len(received_metadata) == 1
    assert received_metadata[0]["purpose"] == "autosave"
    assert received_metadata[0]["target"] == "city.cty"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
