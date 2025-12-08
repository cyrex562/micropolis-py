"""Synchronization helpers between AppContext and legacy CamelCase globals."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from types import SimpleNamespace

from micropolis.context import AppContext


def _to_int(value: Any) -> int:
    return int(value)


def _to_bool_flag(value: Any) -> int:
    return 1 if bool(value) else 0


def _from_bool_flag(value: Any) -> bool:
    return bool(value)


@dataclass(frozen=True)
class Binding:
    field: str
    legacy: str
    to_legacy: Callable[[Any], Any]
    from_legacy: Callable[[Any], Any]


class LegacyTypes(SimpleNamespace):
    """SimpleNamespace variant that supports change watchers."""

    def __init__(self) -> None:  # pragma: no cover - trivial init
        super().__setattr__("_watchers", {})

    def add_watcher(
        self, name: str, callback: Callable[[str, Any], None]
    ) -> Callable[[], None]:
        watchers_list = self._watchers.setdefault(name, [])
        watchers_list.append(callback)

        def remove_watcher() -> None:
            slots = self._watchers.get(name)
            if slots and callback in slots:
                slots.remove(callback)

        return remove_watcher

    def __setattr__(self, name: str, value: Any) -> None:  # pragma: no cover - glue
        super().__setattr__(name, value)
        watchers = self._watchers.get(name)
        if watchers:
            for watcher in list(watchers):
                watcher(name, value)


class LegacyStateContract:
    """Bidirectionally sync AppContext fields with CamelCase globals."""

    _bindings: tuple[Binding, ...] = (
        # City metadata
        Binding("city_name", "CityName", str, str),
        Binding("game_level", "GameLevel", _to_int, _to_int),
        Binding("city_time", "CityTime", _to_int, _to_int),
        Binding("scenario_id", "ScenarioID", _to_int, _to_int),
        Binding("city_pop", "CityPop", _to_int, _to_int),
        Binding("total_funds", "TotalFunds", _to_int, _to_int),
        # Toggles
        Binding("auto_goto", "AutoGoto", _to_bool_flag, _from_bool_flag),
        Binding("auto_budget", "AutoBudget", _to_bool_flag, _from_bool_flag),
        Binding(
            "auto_bulldoze",
            "AutoBulldoze",
            _to_bool_flag,
            _from_bool_flag,
        ),
        Binding("no_disasters", "noDisasters", _to_bool_flag, _from_bool_flag),
        Binding("user_sound_on", "UserSoundOn", _to_bool_flag, _from_bool_flag),
        Binding("do_animation", "doAnimation", _to_bool_flag, _from_bool_flag),
        Binding("do_messages", "doMessages", _to_bool_flag, _from_bool_flag),
        Binding("do_notices", "doNotices", _to_bool_flag, _from_bool_flag),
        # Overlay selection
        Binding("do_overlay", "DoOverlay", _to_int, _to_int),
        # Budget state
        Binding("road_fund", "BudgetRoadFund", _to_int, _to_int),
        Binding("fire_fund", "BudgetFireFund", _to_int, _to_int),
        Binding("police_fund", "BudgetPoliceFund", _to_int, _to_int),
        Binding("city_tax", "BudgetTaxRate", _to_int, _to_int),
        Binding("budget_timer", "BudgetTimer", _to_int, _to_int),
        Binding("budget_timeout", "BudgetTimeout", _to_int, _to_int),
    )

    def __init__(self) -> None:
        self._context: AppContext | None = None
        self._types: LegacyTypes | None = None
        self._bindings_by_field: dict[str, Binding] = {
            binding.field: binding for binding in self._bindings
        }
        self._bindings_by_legacy: dict[str, Binding] = {
            binding.legacy: binding for binding in self._bindings
        }
        self._legacy_watch_handles: list[Callable[[], None]] = []
        self._ignore_legacy: set[str] = set()

    def bind(self, context: AppContext, types: LegacyTypes) -> None:
        """Attach the contract to a context/types pair."""

        self._clear_watchers()
        self._context = context
        self._types = types
        context.attach_state_contract(self)
        self._register_watchers()
        self._prime_from_types()

    def on_context_update(self, context: AppContext, field: str, value: Any) -> None:
        binding = self._bindings_by_field.get(field)
        if binding is None or self._types is None:
            return
        self._update_legacy(binding, value)

    # Internal helpers -------------------------------------------------
    def _register_watchers(self) -> None:
        types = self._types
        if types is None:
            return
        add_watcher = getattr(types, "add_watcher", None)
        if add_watcher is None:
            return
        for binding in self._bindings:
            remover = add_watcher(
                binding.legacy,
                lambda name, value, binding=binding: self._handle_legacy_update(
                    binding, value
                ),
            )
            self._legacy_watch_handles.append(remover)

    def _clear_watchers(self) -> None:
        while self._legacy_watch_handles:
            remover = self._legacy_watch_handles.pop()
            remover()

    def _prime_from_types(self) -> None:
        if self._context is None or self._types is None:
            return
        for binding in self._bindings:
            if hasattr(self._types, binding.legacy):
                self._set_context(binding, getattr(self._types, binding.legacy))
            else:
                self._update_legacy(
                    binding,
                    getattr(self._context, binding.field),
                )

    def _update_legacy(self, binding: Binding, value: Any) -> None:
        types = self._types
        if types is None:
            return
        converted = binding.to_legacy(value)
        if getattr(types, binding.legacy, None) == converted:
            return
        self._ignore_legacy.add(binding.legacy)
        try:
            setattr(types, binding.legacy, converted)
        finally:
            self._ignore_legacy.discard(binding.legacy)

    def _handle_legacy_update(self, binding: Binding, value: Any) -> None:
        if binding.legacy in self._ignore_legacy:
            return
        self._set_context(binding, value)

    def _set_context(self, binding: Binding, legacy_value: Any) -> None:
        context = self._context
        if context is None:
            return
        converted = binding.from_legacy(legacy_value)
        if getattr(context, binding.field, None) == converted:
            return
        context._suspend_contract_notifications()
        try:
            setattr(context, binding.field, converted)
        finally:
            context._resume_contract_notifications()
