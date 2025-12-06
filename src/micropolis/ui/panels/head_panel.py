"""Head/status panel implementation for the pygame UI stack."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib import import_module
from types import ModuleType
from typing import Any

from micropolis import ui_utilities, updates
from micropolis.context import AppContext

import sys


# Avoid importing sim_control at module import time to prevent circular imports.
def get_sim_speed(context: AppContext) -> int:
    from micropolis.sim_control import get_sim_speed as _impl

    return _impl(context)


def is_sim_paused(context: AppContext) -> bool:
    from micropolis.sim_control import is_sim_paused as _impl

    return _impl(context)


def _get_ui_utilities() -> ModuleType:
    return (
        sys.modules.get("src.micropolis.ui_utilities")
        or sys.modules.get("micropolis.ui_utilities")
        or ui_utilities
    )


from micropolis.ui.event_bus import EventBus, get_default_event_bus
from micropolis.ui.timer_service import TimerEvent
from micropolis.ui.uipanel import UIPanel
from micropolis.ui.widgets import (
    NullRenderer,
    RecordingRenderer,
    TextLabel,
    Theme,
    ThemeManager,
    ThemePalette,
    ToggleButton,
    UIEvent,
    UIWidget,
    WidgetRenderer,
    clamp,
)

try:  # Optional dependency for real rendering
    import pygame

    _HAVE_PYGAME = True
except Exception:  # pragma: no cover - pygame optional in tests
    pygame = None  # type: ignore
    _HAVE_PYGAME = False


@dataclass(frozen=True)
class HeadPanelState:
    """Snapshot of the head panel display for tests and diagnostics."""

    city_name: str = "New City"
    date_text: str = "Jan 1900"
    funds_text: str = "Funds: $0"
    population_text: str = "Pop: 0"
    level_text: str = "Easy"
    ticker_text: str = ""
    speed: int = 1
    paused: bool = False
    demand: tuple[int, int, int] = (0, 0, 0)


_LEVEL_LABELS = {0: "Easy", 1: "Medium", 2: "Hard"}
_DEMAND_RANGE = 15  # +/- 15 (hundredths) matches legacy valve display
_UPDATE_INTERVAL_MS = 250


class _PygameWidgetRenderer(WidgetRenderer):
    """Minimal pygame-backed renderer satisfying the widget protocol."""

    def __init__(self, surface: Any) -> None:
        if not _HAVE_PYGAME or surface is None:
            raise RuntimeError("pygame surface required")
        self._surface = surface
        self._font_cache: dict[tuple[str | None, int | None], Any] = {}

    def _color(self, color: tuple[int, int, int, int]) -> tuple[int, int, int]:
        r, g, b, _ = color
        return int(r), int(g), int(b)

    def _font(self, font: str | None, size: int | None) -> Any:
        key = (font, size)
        cached = self._font_cache.get(key)
        if cached is not None:
            return cached
        resolved = pygame.font.SysFont(font or "dejavusans", size or 16)
        self._font_cache[key] = resolved
        return resolved

    def draw_rect(
        self,
        rect: tuple[int, int, int, int],
        color: tuple[int, int, int, int],
        border: bool = False,
        border_color: tuple[int, int, int, int] | None = None,
        radius: int = 0,
    ) -> None:
        pg_rect = pygame.Rect(rect)
        pygame.draw.rect(
            self._surface,
            self._color(color),
            pg_rect,
            width=0 if not border else 0,
            border_radius=radius,
        )
        if border:
            pygame.draw.rect(
                self._surface,
                self._color(border_color or color),
                pg_rect,
                width=1,
                border_radius=radius,
            )

    def draw_text(
        self,
        text: str,
        position: tuple[int, int],
        color: tuple[int, int, int, int],
        font: str | None = None,
        size: int | None = None,
        anchor: str = "center",
    ) -> None:
        font_obj = self._font(font, size)
        surface = font_obj.render(text, True, self._color(color))
        text_rect = surface.get_rect()
        setattr(text_rect, anchor, position)
        self._surface.blit(surface, text_rect)

    def draw_line(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        color: tuple[int, int, int, int],
        width: int = 1,
    ) -> None:
        pygame.draw.line(self._surface, self._color(color), start, end, width)

    def draw_image(
        self,
        image_id: str,
        dest: tuple[int, int, int, int],
        tint: tuple[int, int, int, int] | None = None,
    ) -> None:  # pragma: no cover - images not yet used
        return None


class _TickerWidget(UIWidget):
    def __init__(self, rect: tuple[int, int, int, int], theme: Theme) -> None:
        super().__init__(widget_id="ticker", rect=rect, theme=theme)
        self._text = ""

    def set_text(self, text: str) -> None:
        if text != self._text:
            self._text = text
            self.invalidate()

    def on_render(self, renderer: WidgetRenderer) -> None:
        palette = self.theme.palette if self.theme else ThemePalette()
        renderer.draw_rect(
            self.rect,
            palette.surface_alt,
            border=True,
            border_color=palette.border,
        )
        renderer.draw_text(
            self._text or "Welcome to Micropolis",
            (self.rect[0] + self.rect[2] // 2, self.rect[1] + self.rect[3] // 2),
            palette.text,
            font=self.theme.metrics.font_name if self.theme else None,
        )


class _DemandBar(UIWidget):
    def __init__(
        self,
        label: str,
        rect: tuple[int, int, int, int],
        theme: Theme,
    ) -> None:
        super().__init__(widget_id=f"demand-{label.lower()}", rect=rect, theme=theme)
        self._label = label
        self._value = 0

    def set_value(self, value: int) -> None:
        value = int(clamp(value, -_DEMAND_RANGE, _DEMAND_RANGE))
        if value != self._value:
            self._value = value
            self.invalidate()

    def on_render(self, renderer: WidgetRenderer) -> None:
        palette = self.theme.palette if self.theme else ThemePalette()
        x, y, w, h = self.rect
        renderer.draw_rect(
            self.rect,
            palette.surface,
            border=True,
            border_color=palette.border,
        )
        renderer.draw_text(
            f"{self._label}: {self._value:+d}",
            (x + 50, y + h // 2),
            palette.text,
            font=self.theme.metrics.font_name if self.theme else None,
        )
        center_x = x + w // 2
        renderer.draw_line((center_x, y + 4), (center_x, y + h - 4), palette.border)
        fill_ratio = self._value / _DEMAND_RANGE if _DEMAND_RANGE else 0
        fill_width = int((w // 2 - 10) * abs(fill_ratio))
        if fill_width > 0:
            if self._value > 0:
                rect = (center_x + 2, y + 6, fill_width, h - 12)
                color = palette.success
            else:
                rect = (center_x - fill_width - 2, y + 6, fill_width, h - 12)
                color = palette.danger
            renderer.draw_rect(rect, color)


@dataclass
class _SpeedPreset:
    key: str
    label: str
    speed: int


class _HeadPanelView(UIWidget):
    """Widget tree for the head/status panel."""

    _SPEED_PRESETS: tuple[_SpeedPreset, ...] = (
        _SpeedPreset("slow", "Slow", 1),
        _SpeedPreset("normal", "Normal", 2),
        _SpeedPreset("fast", "Fast", 3),
    )

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        theme: Theme,
        on_speed_change: Callable[[int], None],
        on_pause_toggle: Callable[[bool], None],
    ) -> None:
        super().__init__(widget_id="head-panel", rect=rect, theme=theme)
        self._on_speed_change = on_speed_change
        self._on_pause_toggle = on_pause_toggle
        self.city_label = TextLabel("City", widget_id="city-label")
        self.date_label = TextLabel("Jan 1900", widget_id="date-label")
        self.funds_label = TextLabel("Funds: $0", widget_id="funds-label")
        self.pop_label = TextLabel("Pop: 0", widget_id="pop-label")
        self.level_label = TextLabel("Easy", widget_id="level-label")
        self.pause_button = ToggleButton(
            label="Pause",
            widget_id="pause-toggle",
            on_toggle=self._handle_pause_toggle,
        )
        self.speed_buttons: dict[str, ToggleButton] = {}
        for preset in self._SPEED_PRESETS:
            button = ToggleButton(
                label=preset.label,
                widget_id=f"speed-{preset.key}",
                on_toggle=lambda btn, state, preset=preset: self._handle_speed_toggle(
                    preset,
                    state,
                ),
            )
            self.speed_buttons[preset.key] = button
            self.add_child(button)
        self.ticker = _TickerWidget((0, 0, 0, 0), theme)
        self.demand_widgets = {
            "res": _DemandBar("Res", (0, 0, 0, 0), theme),
            "com": _DemandBar("Com", (0, 0, 0, 0), theme),
            "ind": _DemandBar("Ind", (0, 0, 0, 0), theme),
        }
        for widget in (
            self.city_label,
            self.date_label,
            self.funds_label,
            self.pop_label,
            self.level_label,
            self.pause_button,
            self.ticker,
            *self.demand_widgets.values(),
        ):
            self.add_child(widget)
        self.set_speed_state(speed=1, paused=False)

    def layout(self) -> None:
        x, y, w, h = self.rect
        padding = self.theme.metrics.padding if self.theme else 8
        column_width = w // 5
        labels = [
            self.city_label,
            self.date_label,
            self.funds_label,
            self.pop_label,
            self.level_label,
        ]
        for idx, label in enumerate(labels):
            label.set_rect(
                (
                    x + padding + idx * column_width,
                    y + padding,
                    column_width - padding * 2,
                    24,
                )
            )
        button_width = 110
        self.pause_button.set_rect((x + padding, y + 48, button_width, 28))
        for idx, preset in enumerate(self._SPEED_PRESETS):
            button = self.speed_buttons[preset.key]
            button.set_rect(
                (
                    x + padding + (idx + 1) * (button_width + 6),
                    y + 48,
                    button_width,
                    28,
                )
            )
        bar_top = y + 80
        bar_height = 30
        bar_width = (w - padding * 2 - 12) // 3
        for idx, widget in enumerate(self.demand_widgets.values()):
            widget.set_rect(
                (
                    x + padding + idx * (bar_width + 6),
                    bar_top,
                    bar_width,
                    bar_height,
                )
            )
        self.ticker.set_rect((x + padding, y + 115, w - padding * 2, 28))

    # Data binding helpers -------------------------------------------------
    def set_city_name(self, text: str) -> None:
        self.city_label.set_text(text)

    def set_date_text(self, text: str) -> None:
        self.date_label.set_text(text)

    def set_funds_text(self, text: str) -> None:
        self.funds_label.set_text(text)

    def set_population_text(self, text: str) -> None:
        self.pop_label.set_text(text)

    def set_level_text(self, text: str) -> None:
        self.level_label.set_text(text)

    def set_ticker_text(self, text: str) -> None:
        self.ticker.set_text(text)

    def set_demand(self, res: int, com: int, ind: int) -> None:
        self.demand_widgets["res"].set_value(res)
        self.demand_widgets["com"].set_value(com)
        self.demand_widgets["ind"].set_value(ind)

    def set_speed_state(self, *, speed: int, paused: bool) -> None:
        for preset in self._SPEED_PRESETS:
            button = self.speed_buttons[preset.key]
            button.set_toggled(preset.speed == speed and not paused, fire=False)
        self.pause_button.set_toggled(paused, fire=False)

    # Event handlers -------------------------------------------------------
    def _handle_speed_toggle(self, preset: _SpeedPreset, toggled: bool) -> None:
        if toggled:
            for other in self._SPEED_PRESETS:
                if other.key != preset.key:
                    self.speed_buttons[other.key].set_toggled(False, fire=False)
            self.pause_button.set_toggled(False, fire=False)
            self._on_speed_change(preset.speed)

    def _handle_pause_toggle(self, _: ToggleButton, toggled: bool) -> None:
        if toggled:
            for button in self.speed_buttons.values():
                button.set_toggled(False, fire=False)
        self._on_pause_toggle(toggled)


class HeadPanel(UIPanel):
    """Top status bar mirroring `whead.tcl`."""

    legacy_name = "HeadWindows"

    def __init__(self, manager, context: AppContext) -> None:
        super().__init__(manager, context)
        self._theme = ThemeManager().current
        self._event_bus: EventBus = (
            getattr(context, "event_bus", None) or get_default_event_bus()
        )
        self._update_manager = updates.update_manager
        self._timer_id: str | None = None
        self._state = HeadPanelState()
        self._renderer = RecordingRenderer()
        self._view = _HeadPanelView(
            rect=(0, 0, 1024, 150),
            theme=self._theme,
            on_speed_change=self._handle_speed_request,
            on_pause_toggle=self._handle_pause_request,
        )
        self._last_snapshot: dict[str, Any] = {}

    # Lifecycle ------------------------------------------------------------
    def did_mount(self) -> None:
        self.set_rect((0, 0, 1024, 150))
        self._register_update_callbacks()
        self.refresh_from_context()
        self._timer_id = self.manager.timer_service.call_every(
            _UPDATE_INTERVAL_MS,
            self._handle_timer_tick,
            simulation_bound=False,
            tags=("ui", "head-panel"),
        )

    def did_unmount(self) -> None:
        self._unregister_update_callbacks()
        if self._timer_id and self.manager.timer_service.has_timer(self._timer_id):
            self.manager.timer_service.cancel(self._timer_id)
        self._timer_id = None

    def did_resize(self) -> None:
        self._view.set_rect(self.rect)
        self._view.layout()

    # Rendering ------------------------------------------------------------
    def draw(self, surface: Any) -> None:
        renderer: WidgetRenderer
        if isinstance(surface, WidgetRenderer):
            renderer = surface
        elif _HAVE_PYGAME and isinstance(
            surface,
            pygame.Surface,
        ):  # pragma: no cover - depends on pygame
            renderer = _PygameWidgetRenderer(surface)
        else:
            renderer = self._renderer if surface is None else NullRenderer()
        self._view.layout_if_needed()
        self._view.render(renderer)

    # Event handling -------------------------------------------------------
    def handle_panel_event(self, event: Any) -> bool:
        ui_event = self._convert_event(event)
        if ui_event is None:
            return False
        return self._view.handle_event(ui_event)

    def _convert_event(self, event: Any) -> UIEvent | None:
        if isinstance(event, UIEvent):
            return event
        if event is None:
            return None
        type_name = _extract_type_name(event)
        if not type_name:
            return None
        type_lower = type_name.lower()
        pos = getattr(event, "pos", None) or getattr(event, "position", None)
        button = getattr(event, "button", None)
        key = getattr(event, "key", None)
        unicode_text = getattr(event, "unicode", None)
        if type_lower in ("mousemotion", "mouse_move"):
            return UIEvent(type="mouse_move", position=pos)
        if type_lower in ("mousebuttondown", "mouse_down"):
            return UIEvent(type="mouse_down", position=pos, button=button)
        if type_lower in ("mousebuttonup", "mouse_up"):
            return UIEvent(type="mouse_up", position=pos, button=button)
        if type_lower in ("keydown", "key_down"):
            return UIEvent(type="key_down", key=key, unicode=unicode_text)
        if type_lower in ("keyup", "key_up"):
            return UIEvent(type="key_up", key=key, unicode=unicode_text)
        return None

    # Data + timer ---------------------------------------------------------
    def refresh_from_context(self) -> None:
        ctx = self.context
        snapshot_changes = {
            "city_name": ctx.city_name,
            "funds": ctx.total_funds,
            "pop": ctx.total_pop,
            "level": ctx.game_level,
            "message": ctx.last_message if ctx.have_last_message else "",
            "speed": get_sim_speed(ctx),
            "paused": is_sim_paused(ctx),
            "r_valve": ctx.r_valve,
            "c_valve": ctx.c_valve,
            "i_valve": ctx.i_valve,
            "city_time": ctx.city_time,
            "starting_year": ctx.starting_year,
        }
        if snapshot_changes["city_name"] != self._state.city_name:
            self._view.set_city_name(snapshot_changes["city_name"])
        current_pop = _safe_int(self._state.population_text.split(":")[-1])
        if snapshot_changes["pop"] != current_pop:
            self._view.set_population_text(f"Pop: {snapshot_changes['pop']:,}")
        desired_level = _LEVEL_LABELS.get(
            snapshot_changes["level"],
            f"Lvl {snapshot_changes['level']}",
        )
        if desired_level != self._state.level_text:
            self._view.set_level_text(desired_level)
        if snapshot_changes["message"] != self._state.ticker_text:
            self._view.set_ticker_text(snapshot_changes["message"])
            self._event_bus.publish(
                "head_panel.ticker.updated",
                {"message": snapshot_changes["message"]},
                source="head-panel",
                tags=("ui", "head-panel"),
                defer=True,
            )
        self._update_manager.total_funds = snapshot_changes["funds"]
        self._update_manager.must_update_funds = True
        self._update_manager.city_time = snapshot_changes["city_time"]
        self._update_manager.starting_year = snapshot_changes["starting_year"]
        self._update_manager.r_valve = snapshot_changes["r_valve"]
        self._update_manager.c_valve = snapshot_changes["c_valve"]
        self._update_manager.i_valve = snapshot_changes["i_valve"]
        self._update_manager.valve_flag = True
        self._update_manager.really_update_funds()
        self._update_manager.update_date()
        self._update_manager.draw_valve()
        self._view.set_speed_state(
            speed=snapshot_changes["speed"],
            paused=snapshot_changes["paused"],
        )
        self._state = HeadPanelState(
            city_name=snapshot_changes["city_name"],
            date_text=self._state.date_text,
            funds_text=self._state.funds_text,
            population_text=f"Pop: {snapshot_changes['pop']:,}",
            level_text=desired_level,
            ticker_text=snapshot_changes["message"],
            speed=snapshot_changes["speed"],
            paused=snapshot_changes["paused"],
            demand=self._state.demand,
        )

    def _register_update_callbacks(self) -> None:
        self._update_manager.register_callback("funds", self._handle_funds_update)
        self._update_manager.register_callback("date", self._handle_date_update)
        self._update_manager.register_callback("demand", self._handle_demand_update)

    def _unregister_update_callbacks(self) -> None:
        for key in ("funds", "date", "demand"):
            self._update_manager.unregister_callback(key)

    def _handle_timer_tick(self, _: TimerEvent) -> None:
        self.refresh_from_context()

    # Update callbacks -----------------------------------------------------
    def _handle_funds_update(self, text: str) -> None:
        self._view.set_funds_text(text)
        self._state = dataclass_replace(self._state, funds_text=text)
        self._event_bus.publish(
            "funds.updated",
            {"text": text, "value": self.context.total_funds},
            source="head-panel",
            tags=("funds", "ui"),
            defer=True,
        )

    def _handle_date_update(self, text: str, month: int, year: int) -> None:
        self._view.set_date_text(text)
        self._state = dataclass_replace(self._state, date_text=text)
        self._event_bus.publish(
            "date.updated",
            {"text": text, "month": month, "year": year},
            source="head-panel",
            tags=("date", "ui"),
            defer=True,
        )

    def _handle_demand_update(self, res: int, com: int, ind: int) -> None:
        self._view.set_demand(res, com, ind)
        self._state = dataclass_replace(self._state, demand=(res, com, ind))

    # Speed controls -------------------------------------------------------
    def _handle_speed_request(self, speed: int) -> None:
        _get_ui_utilities().set_speed(self.context, speed)
        self._publish_speed_event(paused=False, speed=speed)
        self.refresh_from_context()

    def _handle_pause_request(self, paused: bool) -> None:
        if paused:
            _get_ui_utilities().pause(self.context)
        else:
            _get_ui_utilities().resume(self.context)
        self._publish_speed_event(paused=paused, speed=get_sim_speed(self.context))
        self.refresh_from_context()

    def _publish_speed_event(self, *, paused: bool, speed: int) -> None:
        self._event_bus.publish(
            "simulation.speed.change_request",
            {"speed": speed, "paused": paused},
            source="head-panel",
            tags=("simulation", "ui"),
            defer=True,
        )

    # Snapshot -------------------------------------------------------------
    def get_state(self) -> HeadPanelState:
        return self._state


def _extract_type_name(event: Any) -> str | None:
    if isinstance(event, Mapping):
        return str(event.get("type")) if event.get("type") else None
    type_attr = getattr(event, "type", None)
    if isinstance(type_attr, str):
        return type_attr
    type_name = getattr(event, "type_name", None)
    if isinstance(type_name, str):
        return type_name
    return None


def _safe_int(value: str) -> int:
    try:
        return int(value.replace(",", "").strip())
    except Exception:
        return 0


def dataclass_replace(state: HeadPanelState, **changes: Any) -> HeadPanelState:
    data = state.__dict__ | changes
    return HeadPanelState(**data)


__all__ = ["HeadPanel", "HeadPanelState"]
