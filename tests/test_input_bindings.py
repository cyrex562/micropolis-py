from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.micropolis import input_actions as input_actions_module
from micropolis.app_config import AppConfig
from micropolis.context import AppContext
import micropolis.input_actions as canonical_input_actions
from micropolis.input_actions import InputActionDispatcher
from micropolis.ui.event_bus import EventBus
from micropolis.ui.input_bindings import InputBindingManager, InputChord

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "keybindings.json"
_CTRL_MASK = 0x40


class _FakeEvent:
    def __init__(self, key: int, mod: int = 0) -> None:
        self.key = key
        self.mod = mod


@pytest.fixture()
def binding_manager(tmp_path):  # type: ignore[override]
    bus = EventBus()
    override_path = tmp_path / "overrides.json"
    manager = InputBindingManager(
        context=None,
        event_bus=bus,
        default_config=CONFIG_PATH,
        override_path=override_path,
    )
    try:
        yield manager, override_path
    finally:
        manager.shutdown()


def test_handle_event_dispatches_registered_action(binding_manager) -> None:
    manager, _ = binding_manager
    seen: list[tuple[str, str]] = []

    manager.register_action_listener(
        "simulation.pause",
        lambda action, chord, event: seen.append((action.action_id, chord.signature())),
    )

    handled = manager.handle_pygame_event(_FakeEvent(key=32))

    assert handled is True
    assert seen == [("simulation.pause", "space")]


def test_modifier_bindings_match_mask(binding_manager) -> None:
    manager, _ = binding_manager
    triggered: list[str] = []

    manager.register_action_listener(
        "system.save",
        lambda action, chord, event: triggered.append(chord.signature()),
    )

    handled = manager.handle_pygame_event(_FakeEvent(key=ord("s"), mod=_CTRL_MASK))

    assert handled is True
    assert triggered == ["ctrl+s"]


def test_remap_persists_override_file(binding_manager) -> None:
    manager, override_path = binding_manager
    new_binding = InputChord(key="k", modifiers=frozenset({"ctrl"}))

    manager.remap_action("simulation.pause", [new_binding])

    assert override_path.exists()
    override_data = json.loads(override_path.read_text(encoding="utf-8"))
    assert override_data["bindings"]["simulation.pause"] == ["ctrl+k"]
    assert [ch.signature() for ch in manager.bindings_for("simulation.pause")] == [
        "ctrl+k"
    ]


def test_restore_defaults_removes_override_file(binding_manager) -> None:
    manager, override_path = binding_manager
    manager.remap_action("simulation.pause", [InputChord(key="m")])

    manager.restore_defaults("simulation.pause")

    assert not override_path.exists()
    assert [ch.signature() for ch in manager.bindings_for("simulation.pause")] == [
        "space"
    ]


def test_request_capture_rebinds_on_next_event(binding_manager) -> None:
    manager, _ = binding_manager
    capture_log: list[str] = []
    dispatched: list[str] = []

    manager.register_action_listener(
        "simulation.pause",
        lambda action, chord, event: dispatched.append(chord.signature()),
    )

    manager.request_capture(
        "simulation.pause", lambda chord: capture_log.append(chord.signature())
    )
    handled = manager.handle_pygame_event(_FakeEvent(key=ord("k")))

    assert handled is True
    assert capture_log == ["k"]
    assert dispatched == []
    assert [ch.signature() for ch in manager.bindings_for("simulation.pause")] == ["k"]


def test_change_listeners_fire_on_remap(binding_manager) -> None:
    manager, _ = binding_manager
    changed: list[str] = []

    manager.register_change_listener(lambda action: changed.append(action.action_id))
    manager.remap_action("simulation.pause", [InputChord(key="y")])

    assert changed == ["simulation.pause"]


class _DummyManager:
    def __init__(self) -> None:
        self.listeners: dict[str, list[Callable]] = {}

    def register_action_listener(self, action_id: str, callback: Callable) -> None:
        self.listeners.setdefault(action_id, []).append(callback)

    def unregister_action_listener(self, action_id: str, callback: Callable) -> None:
        callbacks = self.listeners.get(action_id)
        if not callbacks:
            return
        if callback in callbacks:
            callbacks.remove(callback)
        if not callbacks:
            self.listeners.pop(action_id, None)


def test_input_action_dispatcher_routes_actions(monkeypatch) -> None:
    manager = _DummyManager()
    context = AppContext(config=AppConfig())
    keybinding_calls: list[int] = []

    class _StubUI:
        def __init__(self) -> None:
            self.speed_calls: list[int] = []
            self.overlay_calls: list[int] = []
            self.pause_calls = 0
            self.budget_calls = 0
            self.eval_calls = 0

        def set_speed(self, _ctx, value: int) -> None:
            self.speed_calls.append(value)

        def set_map_overlay(self, _ctx, value: int) -> None:
            self.overlay_calls.append(value)

        def toggle_pause(self, _ctx) -> None:  # type: ignore[no-untyped-def]
            self.pause_calls += 1

        def _open_budget_window(self, _ctx) -> None:
            self.budget_calls += 1

        def toggle_evaluation_display(self, _ctx) -> None:
            self.eval_calls += 1

    stub_ui = _StubUI()
    monkeypatch.setattr(input_actions_module, "_UI_UTILITIES", stub_ui)
    monkeypatch.setattr(canonical_input_actions, "_UI_UTILITIES", stub_ui)

    dispatcher = InputActionDispatcher(
        context,
        manager,  # type: ignore[arg-type]
        on_show_keybindings=lambda: keybinding_calls.append(1),
    )

    def trigger(action_id: str) -> None:
        callbacks = manager.listeners[action_id]
        callbacks[0](SimpleNamespace(action_id=action_id), None, None)

    trigger("simulation.speed.cheetah")
    trigger("overlay.pollution")
    trigger("simulation.pause")
    trigger("system.budget")
    trigger("system.evaluation")
    trigger("ui.show_keybindings")

    assert stub_ui.speed_calls == [2]
    assert stub_ui.overlay_calls
    assert stub_ui.pause_calls == 1
    assert stub_ui.budget_calls == 1
    assert stub_ui.eval_calls == 1
    assert keybinding_calls == [1]

    dispatcher.shutdown()
    assert manager.listeners == {}
