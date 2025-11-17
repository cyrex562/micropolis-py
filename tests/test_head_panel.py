from __future__ import annotations

from pathlib import Path

import pytest

from src.micropolis import ui_utilities, updates
from micropolis.app_config import AppConfig
from micropolis.context import AppContext
from micropolis.ui.event_bus import EventBus
from micropolis.ui.panel_manager import PanelManager
from micropolis.ui.panels.head_panel import HeadPanel


@pytest.fixture
def context() -> AppContext:
    repo_root = Path(__file__).resolve().parents[1]
    config = AppConfig(home=repo_root, resource_dir=repo_root / "assets")
    return AppContext(config=config)


@pytest.fixture
def event_bus() -> EventBus:
    bus = EventBus()
    yield bus
    bus.clear()


@pytest.fixture
def panel_manager(context: AppContext, event_bus: EventBus) -> PanelManager:
    return PanelManager(context, event_bus=event_bus)


@pytest.fixture
def update_manager(monkeypatch: pytest.MonkeyPatch):
    manager = updates.UIUpdateManager()
    monkeypatch.setattr(updates, "update_manager", manager)
    return manager


@pytest.fixture(autouse=True)
def patch_speed_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.micropolis.ui.panels.head_panel.get_sim_speed",
        lambda ctx: ctx.sim_speed,
    )
    monkeypatch.setattr(
        "src.micropolis.ui.panels.head_panel.is_sim_paused",
        lambda ctx: bool(ctx.sim_paused),
    )


@pytest.fixture
def head_panel(
    panel_manager: PanelManager,
    context: AppContext,
    update_manager: updates.UIUpdateManager,
) -> HeadPanel:
    panel = HeadPanel(panel_manager, context)
    yield panel
    if panel.mounted:
        panel.on_unmount()
    panel_manager.timer_service.clear()


def _subscribe(bus: EventBus, topic: str) -> list:
    events: list = []

    def _capture(event) -> None:
        events.append(event.payload)

    bus.subscribe(topic, _capture)
    return events


def test_head_panel_refresh_from_context_updates_state_and_events(
    context: AppContext,
    head_panel: HeadPanel,
    event_bus: EventBus,
) -> None:
    context.city_name = "AlphaVile"
    context.total_funds = 123_456
    context.total_pop = 7_890
    context.game_level = 1
    context.sim_speed = 2
    context.sim_paused = False
    context.have_last_message = True
    context.last_message = "All systems go"
    context.city_time = 96  # Jan 1902 given starting_year 1900
    context.starting_year = 1900
    context.r_valve = 900
    context.c_valve = -300
    context.i_valve = 0

    funds_events = _subscribe(event_bus, "funds.updated")
    date_events = _subscribe(event_bus, "date.updated")
    ticker_events = _subscribe(event_bus, "head_panel.ticker.updated")

    head_panel.on_mount()
    event_bus.flush()

    state = head_panel.get_state()
    assert state.city_name == "AlphaVile"
    assert state.population_text == "Pop: 7,890"
    assert state.level_text == "Medium"
    assert state.ticker_text == "All systems go"
    assert state.demand == (9, -3, 0)
    assert state.speed == 2
    assert state.paused is False

    assert funds_events[-1]["text"] == "Funds: 123,456"
    assert funds_events[-1]["value"] == 123_456
    assert date_events[-1]["text"] == "Jan 1902"
    assert ticker_events[-1]["message"] == "All systems go"


def test_head_panel_speed_and_pause_requests_dispatch(
    monkeypatch: pytest.MonkeyPatch,
    context: AppContext,
    head_panel: HeadPanel,
    event_bus: EventBus,
) -> None:
    context.sim_speed = 1
    context.sim_paused = False

    speed_calls: list[int] = []

    def fake_set_speed(ctx: AppContext, speed: int) -> None:
        speed_calls.append(speed)
        ctx.sim_speed = speed

    pause_resume_calls: list[str] = []

    def fake_pause(ctx: AppContext) -> None:
        pause_resume_calls.append("pause")
        ctx.sim_paused = True

    def fake_resume(ctx: AppContext) -> None:
        pause_resume_calls.append("resume")
        ctx.sim_paused = False

    monkeypatch.setattr(ui_utilities, "set_speed", fake_set_speed)
    monkeypatch.setattr(ui_utilities, "pause", fake_pause)
    monkeypatch.setattr(ui_utilities, "resume", fake_resume)

    speed_events = _subscribe(event_bus, "simulation.speed.change_request")

    head_panel.on_mount()
    event_bus.flush()
    speed_events.clear()

    head_panel._handle_speed_request(3)
    event_bus.flush()

    assert speed_calls == [3]
    assert speed_events[-1] == {"speed": 3, "paused": False}
    assert head_panel.get_state().speed == 3
    assert head_panel.get_state().paused is False

    head_panel._handle_pause_request(True)
    event_bus.flush()

    assert pause_resume_calls[-1] == "pause"
    assert speed_events[-1] == {"speed": 3, "paused": True}
    assert head_panel.get_state().paused is True

    head_panel._handle_pause_request(False)
    event_bus.flush()

    assert pause_resume_calls[-1] == "resume"
    assert speed_events[-1] == {"speed": 3, "paused": False}
    assert head_panel.get_state().paused is False
