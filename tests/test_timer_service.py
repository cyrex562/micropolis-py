from __future__ import annotations

from collections.abc import Callable
from typing import Any

from micropolis.ui.event_bus import EventBus
from micropolis.ui.timer_service import TimerEvent, TimerService


class DummyBus(EventBus):
    def __init__(self) -> None:
        super().__init__()
        self.published: list[tuple[str, dict[str, Any], dict[str, Any]]] = []

    def publish(  # type: ignore[override]
        self,
        topic: str,
        payload: dict[str, Any],
        **kwargs: Any,
    ) -> int:
        self.published.append((topic, payload, kwargs))
        return 0


def make_service() -> TimerService:
    return TimerService(event_bus=DummyBus())


def collect_callback(target: list[int]) -> Callable[[TimerEvent], None]:
    def _handler(event: TimerEvent) -> None:
        target.append(event.run_count)

    return _handler


def test_call_later_executes_once() -> None:
    calls: list[int] = []
    service = make_service()
    service.call_later(100, collect_callback(calls))

    service.tick(50)
    assert calls == []

    service.tick(60)
    assert calls == [1]
    assert service.active_count() == 0


def test_repeating_timer_runs_multiple_times() -> None:
    calls: list[int] = []
    service = make_service()
    service.call_every(25, collect_callback(calls))

    service.tick(25)
    service.tick(50)
    service.tick(25)

    assert calls == [1, 2, 3]


def test_pause_and_resume_preserves_remaining_time() -> None:
    calls: list[int] = []
    service = make_service()
    timer_id = service.call_later(100, collect_callback(calls))

    service.tick(40)
    assert service.pause_timer(timer_id) is True

    service.tick(200)
    assert calls == []

    assert service.resume_timer(timer_id) is True
    service.tick(50)
    assert calls == []

    service.tick(50)
    assert calls == [1]


def test_simulation_pause_only_affects_bound_timers() -> None:
    sim_calls: list[int] = []
    ui_calls: list[int] = []
    service = make_service()
    bound_id = service.call_later(
        60,
        collect_callback(sim_calls),
        simulation_bound=True,
    )
    free_id = service.call_later(60, collect_callback(ui_calls))
    assert bound_id != free_id

    service.set_simulation_paused(True)
    service.tick(100)

    assert ui_calls == [1]
    assert sim_calls == []

    service.set_simulation_paused(False)
    service.tick(59)
    assert sim_calls == []
    service.tick(1)
    assert sim_calls == [1]


def test_cancel_by_tag_and_direct_cancel() -> None:
    calls: list[int] = []
    service = make_service()
    service.call_later(30, collect_callback(calls), tags=("autosave",))
    timer_b = service.call_later(30, collect_callback(calls))

    assert service.cancel_by_tag("autosave") == 1
    assert service.cancel(timer_b) is True

    service.tick(50)
    assert calls == []


def test_event_bus_publish_receives_metadata() -> None:
    bus = DummyBus()
    service = TimerService(event_bus=bus)
    metadata = {"purpose": "blink"}
    service.call_every(10, lambda event: None, tags=("blink",), metadata=metadata)

    service.tick(10)

    assert bus.published, "Expected timer.fired event"
    topic, payload, kwargs = bus.published[-1]
    assert topic == "timer.fired"
    assert payload["metadata"]["purpose"] == "blink"
    assert "timer" in kwargs["tags"]
