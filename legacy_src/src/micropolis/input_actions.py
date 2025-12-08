"""Bridges input binding actions to engine/UI behaviors."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from .constants import (
    CRMAP,
    DYMAP,
    FIMAP,
    LVMAP,
    PDMAP,
    PLMAP,
    POMAP,
    PRMAP,
    RGMAP,
    TDMAP,
)
from .context import AppContext
from .ui.input_bindings import InputAction, InputBindingManager

logger = logging.getLogger(__name__)

_UI_UTILITIES: Any | None = None


def _get_ui_utilities():
    global _UI_UTILITIES
    if _UI_UTILITIES is None:
        from . import ui_utilities as _ui_module

        _UI_UTILITIES = _ui_module
    return _UI_UTILITIES


def _noop(_: InputAction) -> None:  # pragma: no cover - placeholder
    logger.debug("No handler registered for input action")


class InputActionDispatcher:
    """Register default handlers for logical input actions."""

    _SPEED_ACTIONS = {
        "simulation.speed.turtle": 0,
        "simulation.speed.llama": 1,
        "simulation.speed.cheetah": 2,
        "simulation.speed.ludicrous": 3,
    }

    _OVERLAY_ACTIONS = {
        "overlay.population": PDMAP,
        "overlay.pollution": PLMAP,
        "overlay.crime": CRMAP,
        "overlay.traffic": TDMAP,
        "overlay.power": PRMAP,
        "overlay.land_value": LVMAP,
        "overlay.growth": RGMAP,
        "overlay.fire": FIMAP,
        "overlay.police": POMAP,
        "overlay.dynamic_filter": DYMAP,
    }

    def __init__(
        self,
        context: AppContext,
        manager: InputBindingManager,
        *,
        on_show_keybindings: Callable[[], None] | None = None,
    ) -> None:
        self._context = context
        self._manager = manager
        self._on_show_keybindings = on_show_keybindings
        self._registrations: dict[str, Callable[[InputAction, Any, Any], None]] = {}
        self._register_core_handlers()

    # ------------------------------------------------------------------
    def shutdown(self) -> None:
        for action_id, callback in list(self._registrations.items()):
            try:
                self._manager.unregister_action_listener(action_id, callback)
            except KeyError:  # pragma: no cover - defensive guard
                continue
        self._registrations.clear()

    # ------------------------------------------------------------------
    def _register_core_handlers(self) -> None:
        self._register_handler("simulation.pause", self._handle_pause)
        for action_id, speed in self._SPEED_ACTIONS.items():
            self._register_handler(
                action_id,
                lambda _action, value=speed: _get_ui_utilities().set_speed(
                    self._context, value
                ),
            )
        for action_id, overlay in self._OVERLAY_ACTIONS.items():
            self._register_handler(
                action_id,
                lambda _action, value=overlay: _get_ui_utilities().set_map_overlay(
                    self._context, value
                ),
            )
        self._register_handler(
            "system.budget",
            lambda _action: _get_ui_utilities()._open_budget_window(self._context),
        )
        self._register_handler(
            "system.evaluation",
            lambda _action: _get_ui_utilities().toggle_evaluation_display(
                self._context
            ),
        )
        if self._on_show_keybindings is not None:
            callback = self._on_show_keybindings
            self._register_handler(
                "ui.show_keybindings",
                lambda _action, cb=callback: cb(),
            )

    def _register_handler(
        self,
        action_id: str,
        handler: Callable[[InputAction], None] | None,
    ) -> None:
        def _callback(action: InputAction, _chord: Any, _event: Any) -> None:
            try:
                (handler or _noop)(action)
            except Exception:  # pragma: no cover - log and continue
                logger.exception("Input handler for %s failed", action.action_id)

        try:
            self._manager.register_action_listener(action_id, _callback)
        except KeyError:
            logger.debug(
                "Skipping handler registration for unknown action %s", action_id
            )
            return
        self._registrations[action_id] = _callback

    # ------------------------------------------------------------------
    def _handle_pause(self, _: InputAction) -> None:
        _get_ui_utilities().toggle_pause(self._context)


__all__ = ["InputActionDispatcher"]
