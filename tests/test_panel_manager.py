from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from micropolis.app_config import AppConfig
from micropolis.context import AppContext
from micropolis.ui.panel_manager import (
    PanelLookupError,
    PanelManager,
    PanelRegistrationError,
)
from micropolis.ui.timer_service import TimerService


class DummyPanel:
    def __init__(
        self,
        manager: PanelManager,
        context: AppContext,
        *,
        consume_events: tuple[Any, ...] | None = None,
    ) -> None:
        self.manager = manager
        self.context = context
        self.panel_id = ""
        self.legacy_name = ""
        self.mounted = 0
        self.unmounted = 0
        self.resize_events: list[tuple[int, int]] = []
        self.render_order: list[str] = []
        self.events: list[Any] = []
        self.consume_events = set(consume_events or ())

    def on_mount(self) -> None:
        self.mounted += 1

    def on_unmount(self) -> None:
        self.unmounted += 1

    def on_resize(self, size: tuple[int, int]) -> None:
        self.resize_events.append(size)

    def render(self, surface: Any) -> None:
        surface.calls.append(self.panel_id)

    def handle_event(self, event: Any) -> bool:
        self.events.append(event)
        return event in self.consume_events


class FakeSurface:
    def __init__(self, size: tuple[int, int] = (640, 480)) -> None:
        self._size = size
        self.calls: list[str] = []

    def get_size(self) -> tuple[int, int]:
        return self._size


class AttributeSurface:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.calls: list[str] = []


@pytest.fixture
def context() -> AppContext:
    repo_root = Path(__file__).resolve().parents[1]
    config = AppConfig(home=repo_root, resource_dir=repo_root / "assets")
    return AppContext(config=config)


def make_factory(**defaults: Any):
    def _factory(
        manager: PanelManager,
        context: AppContext,
        **overrides: Any,
    ) -> DummyPanel:
        params = defaults | overrides
        return DummyPanel(manager, context, **params)

    return _factory


def test_panel_manager_provides_timer_service(context: AppContext) -> None:
    manager = PanelManager(context)

    assert isinstance(manager.timer_service, TimerService)
    assert getattr(context, "timer_service", None) is manager.timer_service


def test_register_panel_type_prevents_duplicates(context: AppContext) -> None:
    manager = PanelManager(context)
    factory = make_factory()
    manager.register_panel_type("HeadWindows", factory)

    with pytest.raises(PanelRegistrationError):
        manager.register_panel_type("HeadWindows", factory)

    # Allow replacement when requested
    manager.register_panel_type("HeadWindows", make_factory(), replace=True)


def test_create_panel_sets_metadata_and_hooks(context: AppContext) -> None:
    surface = FakeSurface((800, 600))
    manager = PanelManager(context)
    manager.attach_surface(surface)
    manager.register_panel_type("HeadWindows", make_factory())

    panel = manager.create_panel("HeadWindows")
    assert isinstance(panel, DummyPanel)

    assert panel.mounted == 1
    assert panel.panel_id in manager.legacy_window_snapshot()["HeadWindows"]
    assert panel.resize_events[-1] == (800, 600)
    assert panel.legacy_name == "HeadWindows"


def test_destroy_panel_cleans_internal_state(context: AppContext) -> None:
    manager = PanelManager(context)
    manager.register_panel_type("HeadWindows", make_factory())

    panel = manager.create_panel("HeadWindows")
    manager.set_modal(panel.panel_id, modal=True)
    manager.destroy_panel(panel.panel_id)

    with pytest.raises(PanelLookupError):
        manager.get_panel(panel.panel_id)

    assert "HeadWindows" not in manager.legacy_window_snapshot()


def test_handle_event_respects_z_order_and_modal(context: AppContext) -> None:
    manager = PanelManager(context)
    manager.register_panel_type("HeadWindows", make_factory())
    manager.register_panel_type("MapWindows", make_factory())

    first = manager.create_panel("HeadWindows", panel_id="first")
    second = manager.create_panel(
        "MapWindows",
        panel_id="second",
        factory=make_factory(consume_events=("consume",)),
    )
    assert isinstance(first, DummyPanel)
    assert isinstance(second, DummyPanel)

    manager.bring_to_front(second.panel_id)
    assert manager.handle_event("noop") is False
    assert first.events == ["noop"]

    manager.set_modal(second.panel_id, modal=True)
    assert manager.handle_event("consume") is True
    assert first.events == ["noop"]

    manager.set_modal(second.panel_id, modal=False)
    assert manager.handle_event("passthrough") is False
    assert first.events == ["noop", "passthrough"]


def test_render_uses_z_order(context: AppContext) -> None:
    surface = FakeSurface()
    manager = PanelManager(context, surface=surface)
    manager.register_panel_type("HeadWindows", make_factory())
    manager.register_panel_type("MapWindows", make_factory())

    first = manager.create_panel("HeadWindows", panel_id="first")
    second = manager.create_panel("MapWindows", panel_id="second")

    manager.render()
    assert surface.calls == [first.panel_id, second.panel_id]

    manager.bring_to_front(second.panel_id)
    surface.calls.clear()
    manager.render()
    assert surface.calls == [first.panel_id, second.panel_id]


def test_attach_surface_and_resize_updates_existing_panels(context: AppContext) -> None:
    surface = AttributeSurface(1024, 768)
    manager = PanelManager(context)
    manager.register_panel_type("HeadWindows", make_factory())
    panel = manager.create_panel("HeadWindows")
    assert isinstance(panel, DummyPanel)

    manager.attach_surface(surface)

    assert panel.resize_events[-1] == (1024, 768)


def test_render_requires_surface(context: AppContext) -> None:
    manager = PanelManager(context)
    manager.register_panel_type("HeadWindows", make_factory())
    manager.create_panel("HeadWindows")

    with pytest.raises(RuntimeError):
        manager.render()


def test_handle_event_publishes_to_event_bus(context: AppContext) -> None:
    bus = MagicMock()
    manager = PanelManager(context, event_bus=bus)
    manager.register_panel_type("HeadWindows", make_factory())
    manager.create_panel("HeadWindows")

    class SimpleEvent:
        def __init__(self, event_type: str) -> None:
            self.type = event_type

    event_payload = SimpleEvent("KEYDOWN")
    manager.handle_event(event_payload)

    bus.publish_pygame_event.assert_called_once_with(
        event_payload,
        tags=("panel-manager",),
    )
