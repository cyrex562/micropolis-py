from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from micropolis.app_config import AppConfig
from micropolis.context import AppContext
from micropolis.ui.panel_manager import PanelManager
from micropolis.ui.uipanel import UIPanel


@pytest.fixture
def context() -> AppContext:
    repo_root = Path(__file__).resolve().parents[1]
    config = AppConfig(home=repo_root, resource_dir=repo_root / "assets")
    return AppContext(config=config)


@pytest.fixture
def manager(context: AppContext) -> PanelManager:
    return PanelManager(context)


class FakeSurface:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def append(self, value: str) -> None:
        self.calls.append(value)


class SamplePanel(UIPanel):
    def __init__(self, manager: PanelManager, context: AppContext) -> None:
        super().__init__(manager, context)
        self.mounts = 0
        self.unmounts = 0
        self.resizes: list[tuple[int, int]] = []
        self.draw_calls: list[str] = []
        self.local_events: list[Any] = []
        self.visibility_changes: list[bool] = []
        self.updates: list[float] = []

    def did_mount(self) -> None:
        self.mounts += 1

    def did_unmount(self) -> None:
        self.unmounts += 1

    def did_resize(self, size: tuple[int, int]) -> None:
        self.resizes.append(size)

    def draw(self, surface: FakeSurface) -> None:  # type: ignore[override]
        surface.calls.append("drawn")
        self.draw_calls.append("draw")

    def handle_panel_event(self, event: Any) -> bool:
        self.local_events.append(event)
        return event == "local"

    def on_visibility_changed(self, is_visible: bool) -> None:
        self.visibility_changes.append(is_visible)

    def on_update(self, dt: float) -> None:
        self.updates.append(dt)


@pytest.fixture
def panel(manager: PanelManager, context: AppContext) -> SamplePanel:
    return SamplePanel(manager, context)


def test_lifecycle_and_dirty_tracking(panel: SamplePanel) -> None:
    panel.on_mount()
    panel.on_resize((800, 600))
    panel.set_rect((10, 20, 100, 50))
    panel.invalidate((15, 25, 10, 10))
    panel.move(30, 40)
    panel.resize_to(200, 75)
    dirty = panel.consume_dirty_rects()
    panel.on_unmount()

    assert panel.mounts == 1
    assert panel.unmounts == 1
    assert panel.resizes[-1] == (800, 600)
    assert panel.rect == (30, 40, 200, 75)
    assert dirty[-1] == (30, 40, 200, 75)
    assert not panel.has_dirty_region()


def test_visibility_controls_affect_render_and_focus(panel: SamplePanel) -> None:
    surface = FakeSurface()
    panel.render(surface)
    assert surface.calls == ["drawn"]

    panel.hide()
    panel.render(surface)
    assert surface.calls == ["drawn"]  # no additional draw
    assert panel.visibility_changes[-1] is False

    panel.show()
    assert panel.visibility_changes[-1] is True


def test_focus_management_and_event_routing(panel: SamplePanel) -> None:
    focus_log: list[str] = []
    event_log: list[str] = []

    def make_handler(name: str):
        def _handle(event: Any) -> bool:
            event_log.append(f"{name}:{event}")
            return event == f"{name}-consume"

        return _handle

    panel.register_focus_target(
        "alpha",
        on_focus=lambda: focus_log.append("alpha-focus"),
        on_blur=lambda: focus_log.append("alpha-blur"),
        handle_event=make_handler("alpha"),
    )
    enabled = False

    def beta_enabled() -> bool:
        return enabled

    panel.register_focus_target(
        "beta",
        on_focus=lambda: focus_log.append("beta-focus"),
        on_blur=lambda: focus_log.append("beta-blur"),
        handle_event=make_handler("beta"),
        is_enabled=beta_enabled,
    )

    assert panel.focus_next() is True
    assert panel.focused_target() == "alpha"
    assert panel.handle_event("alpha-consume") is True
    assert event_log == ["alpha:alpha-consume"]

    enabled = True
    assert panel.focus_next() is True
    assert panel.focused_target() == "beta"
    assert panel.handle_event("beta-event") is False
    assert event_log[-1] == "beta:beta-event"

    panel.focus_previous()
    assert panel.focused_target() == "alpha"

    panel.clear_focus()
    assert panel.focused_target() is None

    assert panel.handle_event("local") is True
    assert panel.local_events == ["beta-event", "local"]


def test_update_skips_when_hidden(panel: SamplePanel) -> None:
    panel.hide()
    panel.update(0.5)
    panel.show()
    panel.update(0.25)
    assert panel.updates == [0.25]
