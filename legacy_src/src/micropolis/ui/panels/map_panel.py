"""Map/minimap panel implementation for the pygame UI stack."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from micropolis.context import AppContext
from micropolis.mini_map_renderer import (
    available_minimap_overlays,
    get_or_create_minimap_renderer,
)
from micropolis.ui.event_bus import EventBus, get_default_event_bus
from micropolis.ui.uipanel import UIPanel
from micropolis.ui.widgets import (
    NullRenderer,
    Theme,
    ThemePalette,
    ToggleButton,
    UIWidget,
    WidgetRenderer,
)

if TYPE_CHECKING:  # Avoid circular import
    from micropolis.ui.panel_manager import PanelManager

try:  # Optional dependency for real rendering
    import pygame

    _HAVE_PYGAME = True
except Exception:  # pragma: no cover - pygame optional in tests
    pygame = None  # type: ignore
    _HAVE_PYGAME = False


@dataclass(frozen=True)
class MapPanelState:
    """Snapshot of the map panel display for tests and diagnostics."""

    overlay_mode: str | None = None
    zoom_level: int = 1
    viewport_visible: bool = True


_OVERLAY_NAMES = {
    "power": "Power",
    "population": "Population",
    "traffic": "Traffic",
    "pollution": "Pollution",
    "crime": "Crime",
    "land_value": "Land Value",
}

_ZOOM_LEVELS = [1, 2, 3]  # overall (1x), city (2x), district (3x)
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
        resolved = pygame.font.SysFont(font or "dejavusans", size or 12)
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
        text_rect.center = position
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


class _MinimapWidget(UIWidget):
    """Widget that renders the minimap with current overlay."""

    def __init__(
        self, rect: tuple[int, int, int, int], theme: Theme, context: AppContext
    ) -> None:
        super().__init__(widget_id="minimap", rect=rect, theme=theme)
        self.context = context
        self._overlay_mode: str | None = None
        self._zoom_level: int = 1

    def set_overlay_mode(self, mode: str | None) -> None:
        if mode != self._overlay_mode:
            self._overlay_mode = mode
            self.invalidate()

    def set_zoom_level(self, level: int) -> None:
        if level != self._zoom_level:
            self._zoom_level = max(1, min(3, level))
            self.invalidate()

    def on_render(self, renderer: WidgetRenderer) -> None:
        palette = self.theme.palette if self.theme else ThemePalette()
        bg = palette.background

        # Draw background
        renderer.draw_rect(self.rect, bg, border=True, border_color=palette.border)

        # Render minimap if pygame is available
        if not _HAVE_PYGAME:
            return

        try:
            mmr = get_or_create_minimap_renderer(self.context)
            mmr.set_overlay_mode(self._overlay_mode)

            # Calculate scaled dimensions based on zoom level
            base_width = 120 * 4  # WORLD_X * tile_size
            base_height = 100 * 4  # WORLD_Y * tile_size
            scaled_width = base_width * self._zoom_level
            scaled_height = base_height * self._zoom_level

            # Center the minimap in the widget
            x, y, w, h = self.rect
            dest_x = x + (w - scaled_width) // 2
            dest_y = y + (h - scaled_height) // 2

            dest_rect = pygame.Rect(dest_x, dest_y, scaled_width, scaled_height)

            # Render to the underlying pygame surface
            if hasattr(renderer, "_surface"):
                mmr.render(dest_surface=renderer._surface, dest_rect=dest_rect)

        except RuntimeError:
            pass  # No map view available yet

    def on_mouse_down(
        self, position: tuple[int, int], button: int
    ) -> bool:  # pragma: no cover
        if button != 1:  # Left click only
            return False

        # Check if click is within minimap bounds
        x, y, w, h = self.rect
        if not (x <= position[0] < x + w and y <= position[1] < y + h):
            return False

        # Calculate minimap bounds with zoom
        base_width = 120 * 4
        base_height = 100 * 4
        scaled_width = base_width * self._zoom_level
        scaled_height = base_height * self._zoom_level
        dest_x = x + (w - scaled_width) // 2
        dest_y = y + (h - scaled_height) // 2

        # Translate click position to minimap-relative coords
        rel_x = position[0] - dest_x
        rel_y = position[1] - dest_y

        if 0 <= rel_x < scaled_width and 0 <= rel_y < scaled_height:
            try:
                mmr = get_or_create_minimap_renderer(self.context)
                dest_rect = pygame.Rect(dest_x, dest_y, scaled_width, scaled_height)
                mmr.quick_jump_to(position, dest_rect=dest_rect)
                return True
            except RuntimeError:
                pass

        return False


class _OverlayButton(ToggleButton):
    """Button for selecting overlay mode."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        label: str,
        callback: Callable[[str | None], None],
        overlay_key: str | None,
    ) -> None:
        super().__init__(
            label=label,
            widget_id=f"overlay_{overlay_key or 'none'}",
            rect=rect,
        )
        self._callback = callback
        self._overlay_key = overlay_key

    def on_toggle(self, toggled: bool) -> None:
        if toggled:
            self._callback(self._overlay_key)


class _ZoomButton(ToggleButton):
    """Button for selecting zoom level."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        label: str,
        callback: Callable[[int], None],
        zoom_level: int,
    ) -> None:
        super().__init__(label=label, widget_id=f"zoom_{zoom_level}", rect=rect)
        self._callback = callback
        self._zoom_level = zoom_level

    def on_toggle(self, toggled: bool) -> None:
        if toggled:
            self._callback(self._zoom_level)


class _MapPanelView(UIWidget):
    """Root widget container for the map panel."""

    def __init__(
        self, rect: tuple[int, int, int, int], theme: Theme, context: AppContext
    ) -> None:
        super().__init__(widget_id="map_panel_root", rect=rect, theme=theme)
        self.context = context

        # Layout parameters
        x, y, w, h = rect
        button_height = 28
        button_spacing = 4
        minimap_margin = 8

        # Calculate minimap area (top section)
        buttons_height = button_height * 2 + button_spacing * 3
        margins = minimap_margin * 2
        minimap_height = h - buttons_height - margins
        minimap_rect = (
            x + minimap_margin,
            y + minimap_margin,
            w - minimap_margin * 2,
            minimap_height,
        )
        self._minimap = _MinimapWidget(minimap_rect, theme, context)
        self.add_child(self._minimap)

        # Overlay buttons (middle section)
        overlay_y = y + minimap_height + minimap_margin + button_spacing
        overlay_button_width = (w - button_spacing * 7) // 6
        self._overlay_buttons: list[_OverlayButton] = []
        self._current_overlay: str | None = None

        available = list(available_minimap_overlays())
        overlay_keys = ["none"] + available

        for i, key in enumerate(overlay_keys):
            if i >= 6:  # Only show 6 buttons
                break
            button_x = x + button_spacing + i * (overlay_button_width + button_spacing)
            button_rect = (button_x, overlay_y, overlay_button_width, button_height)
            if key != "none":
                label = _OVERLAY_NAMES.get(key, key.capitalize())
            else:
                label = "None"
            button = _OverlayButton(
                button_rect,
                label,
                self._on_overlay_selected,
                None if key == "none" else key,
            )
            self._overlay_buttons.append(button)
            self.add_child(button)

        # Default to "None" selected
        if self._overlay_buttons:
            self._overlay_buttons[0].set_toggled(True)

        # Zoom buttons (bottom section)
        zoom_y = overlay_y + button_height + button_spacing
        zoom_button_width = (w - button_spacing * 4) // 3
        self._zoom_buttons: list[_ZoomButton] = []
        self._current_zoom: int = 1

        zoom_labels = ["Overall", "City", "District"]
        for i, (level, label) in enumerate(zip(_ZOOM_LEVELS, zoom_labels)):
            button_x = x + button_spacing + i * (zoom_button_width + button_spacing)
            button_rect = (button_x, zoom_y, zoom_button_width, button_height)
            button = _ZoomButton(button_rect, label, self._on_zoom_selected, level)
            self._zoom_buttons.append(button)
            self.add_child(button)

        # Default to "Overall" selected
        if self._zoom_buttons:
            self._zoom_buttons[0].set_toggled(True)

    def layout(self) -> None:
        """Layout children based on the current root rect.

        This recomputes the positions/sizes of the minimap, overlay
        buttons and zoom buttons so that when the parent view rect
        changes (for example during tests that set the panel rect)
        the internal widgets reflect the new bounds for hit-testing
        and rendering.
        """
        # Recompute layout using the same algorithm as __init__ but
        # based on the current self._rect so children are updated when
        # the root view changes after construction.
        x, y, w, h = self._rect.as_tuple()
        button_height = 28
        button_spacing = 4
        minimap_margin = 8

        buttons_height = button_height * 2 + button_spacing * 3
        margins = minimap_margin * 2
        minimap_height = h - buttons_height - margins
        minimap_rect = (
            x + minimap_margin,
            y + minimap_margin,
            w - minimap_margin * 2,
            minimap_height,
        )
        try:
            self._minimap.set_rect(minimap_rect)
        except Exception:
            pass

        # Overlay buttons layout
        overlay_y = y + minimap_height + minimap_margin + button_spacing
        overlay_button_width = (w - button_spacing * 7) // 6
        for i, button in enumerate(self._overlay_buttons):
            if i >= 6:
                break
            button_x = x + button_spacing + i * (overlay_button_width + button_spacing)
            button_rect = (button_x, overlay_y, overlay_button_width, button_height)
            try:
                button.set_rect(button_rect)
            except Exception:
                pass

        # Zoom buttons layout
        zoom_y = overlay_y + button_height + button_spacing
        zoom_button_width = (w - button_spacing * 4) // 3
        for i, button in enumerate(self._zoom_buttons):
            button_x = x + button_spacing + i * (zoom_button_width + button_spacing)
            button_rect = (button_x, zoom_y, zoom_button_width, button_height)
            try:
                button.set_rect(button_rect)
            except Exception:
                pass

    def _on_overlay_selected(self, overlay_key: str | None) -> None:
        """Handle overlay button selection (exclusive)."""
        self._current_overlay = overlay_key
        self._minimap.set_overlay_mode(overlay_key)

        # Ensure only one overlay button is toggled
        for button in self._overlay_buttons:
            should_toggle = button._overlay_key == overlay_key
            if button.toggled != should_toggle:
                button.set_toggled(should_toggle)

    def _on_zoom_selected(self, zoom_level: int) -> None:
        """Handle zoom button selection (exclusive)."""
        self._current_zoom = zoom_level
        self._minimap.set_zoom_level(zoom_level)

        # Ensure only one zoom button is toggled
        for button in self._zoom_buttons:
            should_toggle = button._zoom_level == zoom_level
            if button.toggled != should_toggle:
                button.set_toggled(should_toggle)

    def get_state(self) -> MapPanelState:
        """Return current panel state for testing."""
        return MapPanelState(
            overlay_mode=self._current_overlay,
            zoom_level=self._current_zoom,
            viewport_visible=True,
        )

    def on_render(self, renderer: WidgetRenderer) -> None:
        # Background is handled by minimap and buttons
        pass


class MapPanel(UIPanel):
    """Map/minimap panel with overlay selection and zoom controls."""

    def __init__(
        self,
        manager: PanelManager,  # type: ignore[name-defined]
        context: AppContext,
        *,
        theme_name: str | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        super().__init__(manager, context)
        self._event_bus = event_bus or get_default_event_bus()

        # Theme setup
        from micropolis.ui.widgets import THEME_MANAGER

        theme_mgr = THEME_MANAGER
        self._theme = theme_mgr.get(theme_name or "MicropolisDark")

        # For testing - allow construction without rect
        test_rect = (10, 10, 500, 600)
        self._view = _MapPanelView(test_rect, self._theme, context)

        # Timer subscription for periodic updates
        self._timer_subscription_id: str | None = None
        self._setup_timer()

    def _setup_timer(self) -> None:
        """Subscribe to timer events for periodic updates."""

        def on_timer(event: Any) -> None:
            if hasattr(event, "elapsed_ms") and event.elapsed_ms % 250 == 0:
                self._view.invalidate()

        self._timer_subscription_id = self._event_bus.subscribe("timer", on_timer)

    def did_mount(self) -> None:
        """When the panel mounts, ensure the internal view matches the panel rect
        (compatibility for tests that construct panels with a rect kwarg)."""
        # Align the root view to the panel rect so mouse hit-testing uses the
        # bounds provided by tests.
        try:
            self._view.set_rect(self.rect)
            self._view.layout_if_needed()
        except Exception:
            pass

    def draw(self, surface: Any) -> None:
        """Render the map panel."""
        if surface is None or not _HAVE_PYGAME:
            renderer = NullRenderer()
        else:
            renderer = _PygameWidgetRenderer(surface)

        self._view.render(renderer)

    def handle_panel_event(self, event: Any) -> bool:
        """Handle UI events for interaction.

        Backwards-compatible: tests send raw pygame events directly to panels.
        Convert common mouse button events and emit a concise
        ``map.location.selected`` payload so tests can subscribe to it.
        """
        # If this is a pygame mouse button event, handle click translation
        try:
            import pygame  # type: ignore

            if hasattr(event, "type") and event.type == pygame.MOUSEBUTTONDOWN:
                pos = getattr(event, "pos", None)
                button = getattr(event, "button", None)
                if pos and button == 1:
                    # Check if click falls within the minimap widget
                    mm_rect = self._view._minimap.rect

                    x, y = pos
                    rx, ry, rw, rh = mm_rect
                    if rx <= x < rx + rw and ry <= y < ry + rh:
                        # Publish a simple location payload for tests
                        self._event_bus.publish(
                            "map.location.selected",
                            {"x": int(x), "y": int(y)},
                            source="map-panel",
                            tags=("ui", "map"),
                        )
                        return True
        except Exception:
            # If pygame isn't available or something goes wrong, fall through
            pass

        # Fallback to widget event handling (some widgets expect UIEvent objects)
        try:
            return self._view.handle_event(event)
        except Exception:
            return False

    def on_update(self, dt: float) -> None:
        """Update panel state (called periodically)."""
        pass  # Updates triggered by timer events

    def get_state(self) -> MapPanelState:
        """Return current panel state for testing."""
        return self._view.get_state()

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._timer_subscription_id is not None:
            self._event_bus.unsubscribe(self._timer_subscription_id)
            self._timer_subscription_id = None


__all__ = ["MapPanel", "MapPanelState"]
