"""Input binding manager for pygame keymaps and runtime remapping."""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .event_bus import BusEvent, EventBus, get_default_event_bus

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..context import AppContext

logger = logging.getLogger(__name__)

ModifierSet = frozenset[str]
ActionListener = Callable[["InputAction", "InputChord", Any], None]
ChangeListener = Callable[["InputAction"], None]

_MODIFIER_ORDER = ("ctrl", "shift", "alt", "meta")
_DEFAULT_OVERRIDE_FILE = "keybindings.overrides.json"

try:  # pragma: no cover - optional pygame dependency
    import pygame
except Exception:  # pragma: no cover - fallback when pygame missing
    pygame = None  # type: ignore


@dataclass(slots=True)
class InputChord:
    key: str
    modifiers: ModifierSet = field(default_factory=frozenset)

    def signature(self) -> str:
        mods = [m for m in _MODIFIER_ORDER if m in self.modifiers]
        return "+".join((*mods, self.key)) if mods else self.key


@dataclass(slots=True)
class InputAction:
    action_id: str
    label: str
    description: str
    category: str
    default_bindings: list[InputChord]
    bindings: list[InputChord]


class InputBindingManager:
    """Central registry for keyboard shortcuts with event bus integration."""

    def __init__(
        self,
        *,
        context: AppContext | None = None,
        event_bus: EventBus | None = None,
        default_config: Path | None = None,
        override_path: Path | None = None,
    ) -> None:
        self._context = context
        self._event_bus = event_bus or get_default_event_bus()
        self._default_config = default_config or self._discover_default_config()
        base_override_dir = self._resolve_override_dir(context)
        self._override_path = override_path or (
            base_override_dir / _DEFAULT_OVERRIDE_FILE
        )
        self._actions: dict[str, InputAction] = {}
        self._action_order: list[str] = []
        self._listeners: dict[str, list[ActionListener]] = defaultdict(list)
        self._change_listeners: list[ChangeListener] = []
        self._chord_index: dict[str, list[str]] = defaultdict(list)
        self._pending_capture: tuple[str, Callable[[InputChord], None]] | None = None
        self._subscription_id: str | None = None
        self._load_actions()
        self._subscription_id = self._event_bus.subscribe(
            "pygame.event.keydown", self._handle_bus_key_event, priority=50
        )

    # ------------------------------------------------------------------
    def shutdown(self) -> None:
        if self._subscription_id is not None:
            self._event_bus.unsubscribe(self._subscription_id)
            self._subscription_id = None

    # ------------------------------------------------------------------
    def actions(self, category: str | None = None) -> list[InputAction]:
        if category is None:
            return [self._actions[action_id] for action_id in self._action_order]
        category_lower = category.lower()
        return [
            self._actions[action_id]
            for action_id in self._action_order
            if self._actions[action_id].category == category_lower
        ]

    def bindings_for(self, action_id: str) -> list[InputChord]:
        action = self._actions[action_id]
        return list(action.bindings)

    def format_binding(self, chord: InputChord | None) -> str:
        if chord is None:
            return ""
        return chord.signature().replace("+", " + ")

    def register_action_listener(
        self, action_id: str, callback: ActionListener
    ) -> None:
        if action_id not in self._actions:
            raise KeyError(action_id)
        self._listeners[action_id].append(callback)

    def unregister_action_listener(
        self, action_id: str, callback: ActionListener
    ) -> None:
        listeners = self._listeners.get(action_id)
        if not listeners:
            return
        self._listeners[action_id] = [cb for cb in listeners if cb is not callback]

    def register_change_listener(self, callback: ChangeListener) -> None:
        self._change_listeners.append(callback)

    # ------------------------------------------------------------------
    def request_capture(
        self, action_id: str, on_complete: Callable[[InputChord], None] | None = None
    ) -> None:
        if action_id not in self._actions:
            raise KeyError(action_id)
        self._pending_capture = (
            action_id,
            on_complete or (lambda chord: None),
        )

    def cancel_capture(self) -> None:
        self._pending_capture = None

    def remap_action(self, action_id: str, chords: Iterable[InputChord]) -> None:
        action = self._actions[action_id]
        normalized = self._sanitize_bindings(chords)
        if normalized == action.bindings:
            return
        action.bindings = normalized
        self._notify_binding_change(action)

    def restore_defaults(self, action_id: str) -> None:
        action = self._actions[action_id]
        if action.bindings == action.default_bindings:
            return
        action.bindings = list(action.default_bindings)
        self._notify_binding_change(action)

    def categories(self) -> list[str]:
        return sorted({action.category for action in self._actions.values()})

    def get_action(self, action_id: str) -> InputAction:
        return self._actions[action_id]

    # ------------------------------------------------------------------
    def handle_pygame_event(self, event: Any) -> bool:
        chord = self._event_to_chord(event)
        if chord is None:
            return False
        return self._dispatch_for_chord(chord, event)

    # ------------------------------------------------------------------
    def _handle_bus_key_event(self, bus_event: BusEvent) -> None:
        payload = bus_event.payload or {}
        pygame_event = payload.get("event")
        if pygame_event is None:
            return
        self.handle_pygame_event(pygame_event)

    # ------------------------------------------------------------------
    def _dispatch_for_chord(self, chord: InputChord, event: Any) -> bool:
        if self._pending_capture is not None:
            action_id, callback = self._pending_capture
            self._pending_capture = None
            self.remap_action(action_id, [chord])
            callback(chord)
            return True
        token = chord.signature()
        action_ids = self._chord_index.get(token)
        if not action_ids:
            return False
        handled = False
        for action_id in action_ids:
            action = self._actions[action_id]
            for listener in self._listeners.get(action_id, ()):  # direct listeners
                try:
                    listener(action, chord, event)
                except Exception:  # pragma: no cover - defensive
                    logger.exception("Listener for %s failed", action_id)
            self._event_bus.publish(
                f"input.action.{action_id}",
                {
                    "action": action_id,
                    "binding": chord.signature(),
                    "event": event,
                },
                source="input-bindings",
                tags=("input", "action"),
                defer=True,
            )
            handled = True
        return handled

    # ------------------------------------------------------------------
    def _load_actions(self) -> None:
        data = self._read_json(self._default_config)
        overrides = (
            self._read_json(self._override_path) if self._override_path.exists() else {}
        )
        bindings_override = (
            overrides.get("bindings", {}) if isinstance(overrides, Mapping) else {}
        )
        actions: list[InputAction] = []
        for entry in data.get("actions", []):
            try:
                action = self._build_action(entry, bindings_override)
            except ValueError as exc:
                logger.warning("Skipping keybinding entry: %s", exc)
                continue
            actions.append(action)
        self._actions = {action.action_id: action for action in actions}
        self._action_order = [action.action_id for action in actions]
        self._rebuild_index()

    def _build_action(
        self,
        entry: Mapping[str, Any],
        overrides: Mapping[str, Iterable[str]],
    ) -> InputAction:
        action_id = entry.get("id")
        if not action_id:
            raise ValueError("action id missing")
        label = entry.get("label", action_id)
        description = entry.get("description", "")
        category = entry.get("category", "general").lower()
        default_bindings = [self._parse_chord(ch) for ch in entry.get("bindings", [])]
        override_values = overrides.get(action_id)
        bindings = (
            [self._parse_chord(ch) for ch in override_values]
            if override_values
            else list(default_bindings)
        )
        return InputAction(
            action_id=action_id,
            label=label,
            description=description,
            category=category,
            default_bindings=default_bindings,
            bindings=bindings,
        )

    # ------------------------------------------------------------------
    def _persist_overrides(self) -> None:
        overrides: dict[str, list[str]] = {}
        for action in self._actions.values():
            default_tokens = [ch.signature() for ch in action.default_bindings]
            current_tokens = [ch.signature() for ch in action.bindings]
            if current_tokens != default_tokens:
                overrides[action.action_id] = current_tokens
        if overrides:
            data = {"bindings": overrides, "version": 1}
            self._override_path.parent.mkdir(parents=True, exist_ok=True)
            with self._override_path.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
        elif self._override_path.exists():
            try:
                self._override_path.unlink()
            except OSError:  # pragma: no cover - best effort cleanup
                logger.warning("Failed to remove override file %s", self._override_path)

    # ------------------------------------------------------------------
    def _rebuild_index(self) -> None:
        index: dict[str, list[str]] = defaultdict(list)
        for action_id, action in self._actions.items():
            for chord in action.bindings:
                token = chord.signature()
                if action_id not in index[token]:
                    index[token].append(action_id)
        self._chord_index = index

    def _sanitize_bindings(self, chords: Iterable[InputChord]) -> list[InputChord]:
        normalized: list[InputChord] = []
        seen: set[str] = set()
        for chord in chords:
            normalized_chord = self._normalize_chord(chord)
            signature = normalized_chord.signature()
            if signature in seen:
                continue
            normalized.append(normalized_chord)
            seen.add(signature)
        return normalized

    def _notify_binding_change(self, action: InputAction) -> None:
        self._rebuild_index()
        self._persist_overrides()
        for listener in self._change_listeners:
            listener(action)
        self._event_bus.publish(
            "input.keymap.changed",
            {
                "action": action.action_id,
                "bindings": [ch.signature() for ch in action.bindings],
            },
            source="input-bindings",
            tags=("input", "keybindings"),
            defer=True,
        )

    # ------------------------------------------------------------------
    def _parse_chord(self, text: str) -> InputChord:
        parts = [part.strip().lower() for part in text.split("+") if part.strip()]
        if not parts:
            raise ValueError("Chord string cannot be empty")
        modifiers: set[str] = set()
        key: str | None = None
        for part in parts:
            if part in _MODIFIER_ORDER:
                modifiers.add(part)
            else:
                key = part
        if key is None:
            raise ValueError(f"Chord '{text}' is missing a key component")
        return self._normalize_chord(
            InputChord(key=key, modifiers=frozenset(modifiers))
        )

    def _normalize_chord(self, chord: InputChord) -> InputChord:
        key = chord.key.lower()
        modifiers = frozenset(mod for mod in chord.modifiers if mod in _MODIFIER_ORDER)
        return InputChord(key=key, modifiers=modifiers)

    # ------------------------------------------------------------------
    def _event_to_chord(self, event: Any) -> InputChord | None:
        key_name = self._extract_key_name(event)
        if key_name is None:
            return None
        modifiers = self._extract_modifiers(event)
        return InputChord(key=key_name, modifiers=modifiers)

    def _extract_key_name(self, event: Any) -> str | None:
        if hasattr(event, "key_name") and event.key_name:
            return str(event.key_name).lower()
        key = getattr(event, "key", None)
        if key is not None:
            if pygame is not None and hasattr(pygame, "key"):
                try:
                    return pygame.key.name(key).lower()
                except Exception:  # pragma: no cover - optional dependency
                    pass
            mapped = _KEYCODE_TO_NAME.get(int(key))
            if mapped:
                return mapped
        unicode_value = getattr(event, "unicode", "") or getattr(event, "text", "")
        if unicode_value:
            return str(unicode_value).lower()
        return None

    def _extract_modifiers(self, event: Any) -> ModifierSet:
        mod_mask = int(getattr(event, "mod", 0))
        modifiers: set[str] = set()
        for name, mask in _MODIFIER_TO_MASK.items():
            if mod_mask & mask:
                modifiers.add(name)
        return frozenset(modifiers)

    # ------------------------------------------------------------------
    def _resolve_override_dir(self, context: AppContext | None) -> Path:
        if context is not None:
            config = getattr(context, "config", None)
            home = getattr(config, "home", None)
            if home:
                return Path(home)
        return Path.home()

    # ------------------------------------------------------------------
    def _read_json(self, path: Path) -> Mapping[str, Any]:
        if not path.exists():
            logger.warning("Keybinding config %s is missing", path)
            return {"actions": []}
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _discover_default_config(self) -> Path:
        return Path(__file__).resolve().parents[3] / "config" / "keybindings.json"


def get_default_input_binding_manager(
    *,
    context: AppContext | None = None,
) -> InputBindingManager:
    global _DEFAULT_INPUT_MANAGER
    if _DEFAULT_INPUT_MANAGER is None:
        _DEFAULT_INPUT_MANAGER = InputBindingManager(context=context)
    return _DEFAULT_INPUT_MANAGER


def set_default_input_binding_manager(
    manager: InputBindingManager,
) -> InputBindingManager:
    global _DEFAULT_INPUT_MANAGER
    _DEFAULT_INPUT_MANAGER = manager
    return _DEFAULT_INPUT_MANAGER


_DEFAULT_INPUT_MANAGER: InputBindingManager | None = None


_KEYCODE_TO_NAME = {
    8: "backspace",
    9: "tab",
    13: "return",
    27: "escape",
    32: "space",
    44: ",",
    45: "-",
    46: ".",
    47: "/",
    48: "0",
    49: "1",
    50: "2",
    51: "3",
    52: "4",
    53: "5",
    54: "6",
    55: "7",
    56: "8",
    57: "9",
    59: ";",
    61: "=",
    91: "[",
    92: "\\",
    93: "]",
    96: "kp0",
    97: "kp1",
    98: "kp2",
    99: "kp3",
    100: "kp4",
    101: "kp5",
    102: "kp6",
    103: "kp7",
    104: "kp8",
    105: "kp9",
    107: "kp+",
    109: "kp-",
    110: "kp.",
    112: "f1",
    113: "f2",
    114: "f3",
    115: "f4",
    116: "f5",
    117: "f6",
    118: "f7",
    119: "f8",
    120: "f9",
    121: "f10",
    122: "f11",
    123: "f12",
    127: "delete",
    273: "up",
    274: "down",
    275: "right",
    276: "left",
}

_MODIFIER_TO_MASK = {
    "shift": 0x1,
    "ctrl": 0x40,
    "alt": 0x100,
    "meta": 0x200,
}


__all__ = [
    "InputBindingManager",
    "InputAction",
    "InputChord",
    "get_default_input_binding_manager",
    "set_default_input_binding_manager",
]
