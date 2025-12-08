"""Graphs panel implementation for the pygame UI stack.

This module provides the graph display panel showing historical data for:
- Population (Residential, Commercial, Industrial)
- Cash Flow / Money
- Crime
- Pollution

Ported from wgraph.tcl and w_graph.c with year range controls (10/120 years),
hover tooltips, and legend display.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from micropolis import graphs
from micropolis.constants import (
    HIST_COLORS,
    HIST_NAMES,
)
from micropolis.context import AppContext
from micropolis.ui.event_bus import EventBus, get_default_event_bus
from micropolis.ui.timer_service import TimerEvent
from micropolis.ui.uipanel import UIPanel
from micropolis.ui.widgets import (
    NullRenderer,
    RecordingRenderer,
    Theme,
    ThemeManager,
    ThemePalette,
    ToggleButton,
    UIEvent,
    UIWidget,
    WidgetRenderer,
    clamp,
)

try:
    import pygame

    _HAVE_PYGAME = True
except Exception:
    pygame = None  # type: ignore
    _HAVE_PYGAME = False


@dataclass(frozen=True)
class GraphPanelState:
    """Snapshot of the graph panel state for tests and diagnostics."""

    range: int = 10  # 10 or 120 years
    # Bitmask for which histories to show (all by default)
    visible_histories: int = 0x3F
    hover_position: tuple[int, int] | None = None
    hover_values: dict[str, int] | None = None


_UPDATE_INTERVAL_MS = 500  # Update graphs twice per second
_GRAPH_PADDING = 40
_GRAPH_HEIGHT = 150
_LEGEND_WIDTH = 120
_TOOLTIP_OFFSET = 15


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
    ) -> None:
        font_obj = self._font(font, size)
        surface = font_obj.render(text, True, self._color(color))
        text_rect = surface.get_rect()
        text_rect.topleft = position
        self._surface.blit(surface, text_rect)

    def draw_line(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        color: tuple[int, int, int, int],
        width: int = 1,
    ) -> None:
        pygame.draw.line(self._surface, self._color(color), start, end, width)

    def draw_circle(
        self,
        center: tuple[int, int],
        radius: int,
        color: tuple[int, int, int, int],
        filled: bool = True,
    ) -> None:
        pygame.draw.circle(
            self._surface,
            self._color(color),
            center,
            radius,
            width=0 if filled else 1,
        )

    def draw_image(
        self,
        image_id: str,
        dest: tuple[int, int, int, int],
        tint: tuple[int, int, int, int] | None = None,
    ) -> None:
        pass


class _HistoryCheckbox(UIWidget):
    """Checkbox widget for toggling individual history lines."""

    def __init__(
        self,
        label: str,
        history_index: int,
        color: tuple[int, int, int],
        rect: tuple[int, int, int, int],
        theme: Theme,
        on_toggle: Callable[[int, bool], None],
    ) -> None:
        super().__init__(widget_id=f"history-{history_index}", rect=rect, theme=theme)
        self._label = label
        self._history_index = history_index
        self._color = color
        self._on_toggle = on_toggle
        self._checked = True

    def set_checked(self, checked: bool, fire: bool = True) -> None:
        if checked != self._checked:
            self._checked = checked
            self.invalidate()
            if fire and self._on_toggle:
                self._on_toggle(self._history_index, checked)

    def on_event(self, event: UIEvent) -> bool:
        if (
            event.type == "mouse_down"
            and event.position
            and self.contains_point(event.position)
        ):
            self.set_checked(not self._checked)
            return True
        return False

    def on_render(self, renderer: WidgetRenderer) -> None:
        palette = self.theme.palette if self.theme else ThemePalette()
        x, y, w, h = self.rect

        # Draw checkbox square
        checkbox_size = 16
        checkbox_rect = (x, y + (h - checkbox_size) // 2, checkbox_size, checkbox_size)
        renderer.draw_rect(
            checkbox_rect,
            palette.surface,
            border=True,
            border_color=palette.border,
        )

        # Draw check mark if checked
        if self._checked:
            check_color = (*self._color, 255)
            check_rect = (
                x + 3,
                y + (h - checkbox_size) // 2 + 3,
                checkbox_size - 6,
                checkbox_size - 6,
            )
            renderer.draw_rect(check_rect, check_color)

        # Draw color indicator
        color_rect = (x + checkbox_size + 8, y + (h - 12) // 2, 20, 12)
        renderer.draw_rect(color_rect, (*self._color, 255))

        # Draw label
        label_x = x + checkbox_size + 36
        label_y = y + h // 2 - 6
        renderer.draw_text(
            self._label,
            (label_x, label_y),
            palette.text,
            font=self.theme.metrics.font_name if self.theme else None,
            size=14,
        )


class _GraphWidget(UIWidget):
    """Widget for rendering a single history graph with lines and tooltips."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        theme: Theme,
        context: AppContext,
    ) -> None:
        super().__init__(widget_id="graph-display", rect=rect, theme=theme)
        self._context = context
        self._range = 10  # 10 or 120 years
        self._visible_mask = 0x3F  # All histories visible
        self._hover_pos: tuple[int, int] | None = None
        self._hover_values: dict[str, int] = {}

    def set_range(self, range_val: int) -> None:
        if range_val in [10, 120] and range_val != self._range:
            self._range = range_val
            self.invalidate()

    def set_visible_mask(self, mask: int) -> None:
        if mask != self._visible_mask:
            self._visible_mask = mask
            self.invalidate()

    def set_hover_position(self, pos: tuple[int, int] | None) -> None:
        if pos != self._hover_pos:
            self._hover_pos = pos
            self.invalidate()

    def get_hover_values(self) -> dict[str, int]:
        return self._hover_values.copy()

    def on_event(self, event: UIEvent) -> bool:
        if (
            event.type == "mouse_move"
            and event.position
            and self.contains_point(event.position)
        ):
            self.set_hover_position(event.position)
            return True
        elif event.type == "mouse_move":
            self.set_hover_position(None)
        return False

    def on_render(self, renderer: WidgetRenderer) -> None:
        palette = self.theme.palette if self.theme else ThemePalette()
        x, y, w, h = self.rect

        # Clear background
        renderer.draw_rect(self.rect, palette.surface_alt)

        # Draw border
        renderer.draw_rect(
            self.rect,
            palette.surface_alt,
            border=True,
            border_color=palette.border,
        )

        # Calculate plot area
        plot_x = x + _GRAPH_PADDING
        plot_y = y + 20
        plot_w = w - _GRAPH_PADDING * 2
        plot_h = h - _GRAPH_PADDING - 20

        if plot_w < 10 or plot_h < 10:
            return

        # Draw grid lines
        grid_color = (*palette.border[:3], 64)

        # Horizontal grid lines (every 64 units = 25%)
        for i in range(1, 4):
            grid_y = plot_y + int(plot_h * i / 4)
            renderer.draw_line((plot_x, grid_y), (plot_x + plot_w, grid_y), grid_color)

        # Vertical grid lines (every 10 or 120 months depending on range)
        time_markers = 12 if self._range == 10 else 10  # 12 months or 10 decades
        for i in range(1, time_markers):
            grid_x = plot_x + int(plot_w * i / time_markers)
            renderer.draw_line((grid_x, plot_y), (grid_x, plot_y + plot_h), grid_color)

        # Draw axes
        axis_color = palette.border
        renderer.draw_line((plot_x, plot_y), (plot_x, plot_y + plot_h), axis_color, 2)
        renderer.draw_line(
            (plot_x, plot_y + plot_h),
            (plot_x + plot_w, plot_y + plot_h),
            axis_color,
            2,
        )

        # Draw each history line
        self._hover_values = {}
        hover_x_index = None

        for hist_idx in range(6):  # 6 history types
            if not (self._visible_mask & (1 << hist_idx)):
                continue

            hist_data = graphs.get_history_data(self._context, self._range, hist_idx)
            if not hist_data or len(hist_data) == 0:
                continue

            color = HIST_COLORS[hist_idx]
            color_with_alpha = (*color, 255)
            points = []

            # Scale factors
            sx = plot_w / 120.0
            sy = plot_h / 256.0

            for j in range(len(hist_data)):
                px = plot_x + int(j * sx)
                py = plot_y + int(plot_h - (hist_data[j] * sy))
                py = clamp(py, plot_y, plot_y + plot_h)
                points.append((px, py))

            # Draw line
            if len(points) > 1:
                for i in range(len(points) - 1):
                    renderer.draw_line(points[i], points[i + 1], color_with_alpha, 2)

            # Check hover position
            if self._hover_pos:
                hover_x, hover_y = self._hover_pos
                if plot_x <= hover_x <= plot_x + plot_w:
                    hover_x_index = int((hover_x - plot_x) / sx)
                    hover_x_index = int(clamp(hover_x_index, 0, len(hist_data) - 1))
                    if 0 <= hover_x_index < len(hist_data):
                        hist_name = HIST_NAMES[hist_idx]
                        self._hover_values[hist_name] = hist_data[hover_x_index]

        # Draw hover indicator and tooltip
        if self._hover_pos and hover_x_index is not None:
            hover_x, hover_y = self._hover_pos
            if plot_x <= hover_x <= plot_x + plot_w:
                # Draw vertical line at hover position
                indicator_color = (*palette.text[:3], 128)
                renderer.draw_line(
                    (hover_x, plot_y),
                    (hover_x, plot_y + plot_h),
                    indicator_color,
                    1,
                )

                # Draw tooltip with values
                tooltip_x = hover_x + _TOOLTIP_OFFSET
                tooltip_y = plot_y + 10

                # Ensure tooltip stays within bounds
                if tooltip_x + 150 > x + w:
                    tooltip_x = hover_x - 150 - _TOOLTIP_OFFSET

                tooltip_lines = []
                for name, value in self._hover_values.items():
                    tooltip_lines.append(f"{name}: {value}")

                if tooltip_lines:
                    # Draw tooltip background
                    tooltip_h = len(tooltip_lines) * 18 + 10
                    tooltip_rect = (tooltip_x, tooltip_y, 140, tooltip_h)
                    renderer.draw_rect(
                        tooltip_rect,
                        (*palette.surface[:3], 240),
                        border=True,
                        border_color=palette.border,
                    )

                    # Draw tooltip text
                    for idx, line in enumerate(tooltip_lines):
                        text_y = tooltip_y + 5 + idx * 18
                        renderer.draw_text(
                            line,
                            (tooltip_x + 5, text_y),
                            palette.text,
                            size=12,
                        )

        # Draw range label
        range_label = f"{self._range} Year View"
        renderer.draw_text(
            range_label,
            (x + 10, y + 5),
            palette.text,
            size=14,
        )


class _GraphPanelView(UIWidget):
    """Widget tree for the graphs panel."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        theme: Theme,
        context: AppContext,
        on_range_change: Callable[[int], None],
    ) -> None:
        super().__init__(widget_id="graphs-panel", rect=rect, theme=theme)
        self._context = context
        self._on_range_change = on_range_change

        # Range toggle buttons
        self.range_10_button = ToggleButton(
            label="10 Years",
            widget_id="range-10",
            on_toggle=lambda btn, state: self._handle_range_toggle(10, state),
        )
        self.range_120_button = ToggleButton(
            label="120 Years",
            widget_id="range-120",
            on_toggle=lambda btn, state: self._handle_range_toggle(120, state),
        )

        # Graph display
        self.graph_widget = _GraphWidget((0, 0, 0, 0), theme, context)

        # History checkboxes
        self.history_checkboxes: list[_HistoryCheckbox] = []
        for idx, (name, color) in enumerate(zip(HIST_NAMES, HIST_COLORS)):
            checkbox = _HistoryCheckbox(
                label=name,
                history_index=idx,
                color=color,
                rect=(0, 0, 0, 0),
                theme=theme,
                on_toggle=self._handle_history_toggle,
            )
            self.history_checkboxes.append(checkbox)

        # Add all children
        self.add_child(self.range_10_button)
        self.add_child(self.range_120_button)
        self.add_child(self.graph_widget)
        for checkbox in self.history_checkboxes:
            self.add_child(checkbox)

        # Set initial state
        self.set_range(10)

    def layout(self) -> None:
        x, y, w, h = self.rect
        padding = self.theme.metrics.padding if self.theme else 8

        # Range buttons at top
        button_width = 100
        button_height = 28
        self.range_10_button.set_rect(
            (x + padding, y + padding, button_width, button_height)
        )
        self.range_120_button.set_rect(
            (x + padding + button_width + 10, y + padding, button_width, button_height)
        )

        # Legend checkboxes on the right
        legend_x = x + w - _LEGEND_WIDTH - padding
        checkbox_y = y + padding + button_height + 20
        checkbox_height = 24

        for idx, checkbox in enumerate(self.history_checkboxes):
            checkbox_rect = (
                legend_x,
                checkbox_y + idx * (checkbox_height + 6),
                _LEGEND_WIDTH,
                checkbox_height,
            )
            checkbox.set_rect(checkbox_rect)

        # Graph area (left side)
        graph_y = y + padding + button_height + 10
        graph_w = w - _LEGEND_WIDTH - padding * 3
        graph_h = h - padding * 2 - button_height - 10
        self.graph_widget.set_rect((x + padding, graph_y, graph_w, graph_h))

    def set_range(self, range_val: int) -> None:
        self.range_10_button.set_toggled(range_val == 10, fire=False)
        self.range_120_button.set_toggled(range_val == 120, fire=False)
        self.graph_widget.set_range(range_val)

    def _handle_range_toggle(self, range_val: int, toggled: bool) -> None:
        if toggled:
            # Uncheck other button
            if range_val == 10:
                self.range_120_button.set_toggled(False, fire=False)
            else:
                self.range_10_button.set_toggled(False, fire=False)

            self.graph_widget.set_range(range_val)
            if self._on_range_change:
                self._on_range_change(range_val)

    def _handle_history_toggle(self, history_index: int, checked: bool) -> None:
        # Update visibility mask
        current_mask = self.graph_widget._visible_mask
        if checked:
            current_mask |= 1 << history_index
        else:
            current_mask &= ~(1 << history_index)
        self.graph_widget.set_visible_mask(current_mask)


class GraphsPanel(UIPanel):
    """Graphs panel mirroring `wgraph.tcl` with history plotting and tooltips."""

    legacy_name = "GraphWindows"

    def __init__(self, manager, context: AppContext) -> None:
        super().__init__(manager, context)
        self.legacy_name = "GraphWindows"  # Explicitly set after super().__init__
        self._theme = ThemeManager().current
        self._event_bus: EventBus = (
            getattr(context, "event_bus", None) or get_default_event_bus()
        )
        self._timer_id: str | None = None
        self._state = GraphPanelState()
        self._renderer = RecordingRenderer()
        self._view = _GraphPanelView(
            rect=(0, 0, 800, 600),
            theme=self._theme,
            context=context,
            on_range_change=self._handle_range_change,
        )

    # Lifecycle ------------------------------------------------------------
    def did_mount(self) -> None:
        self.set_rect((100, 200, 800, 600))

        # Initialize graph system if needed
        if not self.context.history_initialized:
            graphs.init_history_data(self.context)
            graphs.init_graph_maxima(self.context)

        # Set up periodic updates
        self._timer_id = self.manager.timer_service.call_every(
            _UPDATE_INTERVAL_MS,
            self._handle_timer_tick,
            simulation_bound=False,
            tags=("ui", "graphs-panel"),
        )

        self.refresh_from_context()

    def did_unmount(self) -> None:
        if self._timer_id and self.manager.timer_service.has_timer(self._timer_id):
            self.manager.timer_service.cancel(self._timer_id)
        self._timer_id = None

    def did_resize(self, size: tuple[int, int]) -> None:
        # Keep panel size fixed for now, but could make responsive
        pass

    # Rendering ------------------------------------------------------------
    def draw(self, surface: Any) -> None:
        renderer: WidgetRenderer
        if isinstance(surface, WidgetRenderer):
            renderer = surface
        elif _HAVE_PYGAME and isinstance(surface, pygame.Surface):  # type: ignore
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

    # Data updates ---------------------------------------------------------
    def refresh_from_context(self) -> None:
        """Update graph data from context."""
        # Update all graph history data
        graphs.update_all_graphs(self.context)
        self._view.invalidate()

    def _handle_timer_tick(self, _: TimerEvent) -> None:
        """Periodic update callback."""
        self.refresh_from_context()

    def _handle_range_change(self, range_val: int) -> None:
        """Handle year range toggle."""
        self._state = GraphPanelState(
            range=range_val,
            visible_histories=self._state.visible_histories,
            hover_position=self._state.hover_position,
            hover_values=self._state.hover_values,
        )

        self._event_bus.publish(
            "graphs.range.changed",
            {"range": range_val},
            source="graphs-panel",
            tags=("ui", "graphs"),
            defer=True,
        )

    # Public API -----------------------------------------------------------
    def get_state(self) -> GraphPanelState:
        """Get current panel state snapshot."""
        return self._state

    def set_range(self, range_val: int) -> None:
        """Set year range (10 or 120)."""
        if range_val in [10, 120]:
            self._view.set_range(range_val)
            self._handle_range_change(range_val)

    def toggle_history(self, history_index: int, visible: bool) -> None:
        """Toggle visibility of a specific history line."""
        if 0 <= history_index < 6:
            checkbox = self._view.history_checkboxes[history_index]
            checkbox.set_checked(visible)


def _extract_type_name(event: Any) -> str | None:
    """Extract event type name from various event formats."""
    if hasattr(event, "type"):
        type_val = event.type
        if isinstance(type_val, str):
            return type_val
        if hasattr(type_val, "name"):
            return type_val.name
    return None


__all__ = ["GraphsPanel", "GraphPanelState"]
