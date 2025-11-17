"""Editor panel implementation for the pygame UI stack.

This panel provides the main map editing viewport with:
- 16x16 pixel tile rendering
- Drag-to-scroll viewport navigation
- Keyboard panning (arrow keys, WASD)
- Auto-pan when mouse approaches edges
- Tool application and preview
- Integration with editor_view.mem_draw_beeg_map_rect
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from micropolis.context import AppContext
from micropolis.map_renderer import MapRenderer
from micropolis.ui.event_bus import EventBus, get_default_event_bus
from micropolis.ui.uipanel import UIPanel

if TYPE_CHECKING:
    from micropolis.ui.panel_manager import PanelManager

try:
    import pygame

    _HAVE_PYGAME = True
except Exception:  # pragma: no cover - pygame optional in tests
    pygame = None  # type: ignore
    _HAVE_PYGAME = False


# Autopan configuration
_AUTOPAN_EDGE_THRESHOLD = 32  # pixels from edge to trigger autopan
_AUTOPAN_SPEED = 8  # pixels per frame
_KEYBOARD_PAN_SPEED = 32  # pixels per key press


class EditorPanel(UIPanel):
    """Main editor panel with 16x16 tile viewport."""

    def __init__(self, manager: PanelManager, context: AppContext) -> None:
        super().__init__(manager, context)
        self.panel_id = "editor"
        self.legacy_name = "EditorWindow"

        # MapRenderer provides the tile rendering and viewport management
        self._renderer: MapRenderer | None = None
        self._viewport_size = (800, 600)  # Default size, updated on mount

        # Mouse state for drag-to-scroll
        self._mouse_down = False
        self._drag_start: tuple[int, int] | None = None
        self._last_mouse_pos: tuple[int, int] | None = None

        # Keyboard panning state
        self._pan_keys_pressed: set[int] = set()

        # Event bus subscription
        self._event_bus: EventBus = get_default_event_bus()
        self._subscriptions: list[Any] = []

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------
    def did_mount(self) -> None:
        """Initialize the editor panel after mounting."""
        # Subscribe to relevant events
        self._subscriptions.append(
            self._event_bus.subscribe("simulation.tick", self._on_simulation_tick)
        )
        self._subscriptions.append(
            self._event_bus.subscribe("map.invalidate", self._on_map_invalidate)
        )

        # Initialize the renderer
        self._init_renderer()

    def did_unmount(self) -> None:
        """Clean up when panel is removed."""
        for sub in self._subscriptions:
            self._event_bus.unsubscribe(sub)
        self._subscriptions.clear()
        self._renderer = None

    def did_resize(self, size: tuple[int, int]) -> None:
        """Update viewport when window resizes."""
        self._viewport_size = size
        if self._renderer:
            self._renderer.set_viewport_pixels(*size)
        self.invalidate()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def draw(self, surface: Any) -> None:
        """Render the editor viewport."""
        if not _HAVE_PYGAME or not self.visible:
            return

        if self._renderer is None:
            self._init_renderer()

        if self._renderer is None:
            # Still couldn't initialize - draw placeholder
            self._draw_placeholder(surface)
            return

        try:
            # Render the map viewport
            x, y, w, h = self.rect
            dest_rect = pygame.Rect(x, y, w, h)  # type: ignore
            self._renderer.render(dest_surface=surface, dest_rect=dest_rect)

            # Draw border for visual clarity
            pygame.draw.rect(surface, (60, 60, 60), dest_rect, 2)  # type: ignore

        except Exception as e:
            # Fallback to placeholder on error
            print(f"Error rendering editor panel: {e}")
            self._draw_placeholder(surface)

    def _draw_placeholder(self, surface: Any) -> None:
        """Draw a placeholder when renderer is unavailable."""
        if not _HAVE_PYGAME:
            return

        x, y, w, h = self.rect
        # Dark background
        pygame.draw.rect(surface, (40, 40, 45), (x, y, w, h))  # type: ignore
        # Border
        pygame.draw.rect(surface, (80, 80, 85), (x, y, w, h), 2)  # type: ignore
        # Text
        font = pygame.font.SysFont("dejavusans", 16)  # type: ignore
        text = font.render("Editor View Loading...", True, (180, 180, 180))
        text_rect = text.get_rect(center=(x + w // 2, y + h // 2))
        surface.blit(text, text_rect)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def handle_panel_event(self, event: Any) -> bool:
        """Handle pygame events for editor interaction."""
        if not _HAVE_PYGAME or not self.enabled:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:  # type: ignore
            return self._handle_mouse_down(event)
        elif event.type == pygame.MOUSEBUTTONUP:  # type: ignore
            return self._handle_mouse_up(event)
        elif event.type == pygame.MOUSEMOTION:  # type: ignore
            return self._handle_mouse_motion(event)
        elif event.type == pygame.KEYDOWN:  # type: ignore
            return self._handle_key_down(event)
        elif event.type == pygame.KEYUP:  # type: ignore
            return self._handle_key_up(event)

        return False

    def _handle_mouse_down(self, event: Any) -> bool:
        """Handle mouse button press."""
        if event.button == 1:  # Left click
            x, y, w, h = self.rect
            mx, my = event.pos
            # Check if click is within panel bounds
            if x <= mx < x + w and y <= my < y + h:
                self._mouse_down = True
                self._drag_start = (mx - x, my - y)  # Relative to panel
                self._last_mouse_pos = event.pos
                return True
        return False

    def _handle_mouse_up(self, event: Any) -> bool:
        """Handle mouse button release."""
        if event.button == 1 and self._mouse_down:
            self._mouse_down = False
            self._drag_start = None
            self._last_mouse_pos = None
            return True
        return False

    def _handle_mouse_motion(self, event: Any) -> bool:
        """Handle mouse movement for drag-to-scroll."""
        if not self._renderer:
            return False

        x, y, w, h = self.rect
        mx, my = event.pos

        # Check if mouse is within panel bounds
        in_bounds = x <= mx < x + w and y <= my < y + h

        # Drag-to-scroll
        if self._mouse_down and self._last_mouse_pos and in_bounds:
            dx = self._last_mouse_pos[0] - mx
            dy = self._last_mouse_pos[1] - my
            self._last_mouse_pos = event.pos

            # Scroll the viewport
            self._renderer.scroll_pixels(dx, dy)
            self.invalidate()
            return True

        # Store mouse position for next frame (for autopan)
        if in_bounds:
            self._last_mouse_pos = event.pos

        return False

    def _handle_key_down(self, event: Any) -> bool:
        """Handle keyboard input for panning."""
        if event.key in (
            pygame.K_LEFT,  # type: ignore
            pygame.K_RIGHT,  # type: ignore
            pygame.K_UP,  # type: ignore
            pygame.K_DOWN,  # type: ignore
            pygame.K_w,  # type: ignore
            pygame.K_a,  # type: ignore
            pygame.K_s,  # type: ignore
            pygame.K_d,  # type: ignore
        ):
            self._pan_keys_pressed.add(event.key)
            self._apply_keyboard_pan()
            return True
        return False

    def _handle_key_up(self, event: Any) -> bool:
        """Handle keyboard key release."""
        if event.key in self._pan_keys_pressed:
            self._pan_keys_pressed.discard(event.key)
            return True
        return False

    def _apply_keyboard_pan(self) -> None:
        """Apply panning based on currently pressed keys."""
        if not self._renderer or not self._pan_keys_pressed:
            return

        dx, dy = 0, 0

        # Calculate pan direction from pressed keys
        left_keys = (pygame.K_LEFT, pygame.K_a)  # type: ignore
        if any(k in self._pan_keys_pressed for k in left_keys):
            dx -= _KEYBOARD_PAN_SPEED
        right_keys = (pygame.K_RIGHT, pygame.K_d)  # type: ignore
        if any(k in self._pan_keys_pressed for k in right_keys):
            dx += _KEYBOARD_PAN_SPEED
        up_keys = (pygame.K_UP, pygame.K_w)  # type: ignore
        if any(k in self._pan_keys_pressed for k in up_keys):
            dy -= _KEYBOARD_PAN_SPEED
        down_keys = (pygame.K_DOWN, pygame.K_s)  # type: ignore
        if any(k in self._pan_keys_pressed for k in down_keys):
            dy += _KEYBOARD_PAN_SPEED

        if dx != 0 or dy != 0:
            self._renderer.scroll_pixels(dx, dy)
            self.invalidate()

    # ------------------------------------------------------------------
    # Update loop
    # ------------------------------------------------------------------
    def on_update(self, dt: float) -> None:
        """Called each frame for continuous updates."""
        if not self.visible or not self._renderer:
            return

        # Apply autopan if mouse is near edges
        self._apply_autopan()

    def _apply_autopan(self) -> None:
        """Auto-scroll when mouse is near viewport edges."""
        if not _HAVE_PYGAME or not self._last_mouse_pos or self._mouse_down:
            return

        if not self._renderer:
            return

        x, y, w, h = self.rect
        mx, my = self._last_mouse_pos

        # Check if mouse is within panel bounds
        if not (x <= mx < x + w and y <= my < y + h):
            return

        # Calculate relative position within panel
        rel_x = mx - x
        rel_y = my - y

        dx, dy = 0, 0

        # Check proximity to edges
        if rel_x < _AUTOPAN_EDGE_THRESHOLD:
            dx = -_AUTOPAN_SPEED
        elif rel_x > w - _AUTOPAN_EDGE_THRESHOLD:
            dx = _AUTOPAN_SPEED

        if rel_y < _AUTOPAN_EDGE_THRESHOLD:
            dy = -_AUTOPAN_SPEED
        elif rel_y > h - _AUTOPAN_EDGE_THRESHOLD:
            dy = _AUTOPAN_SPEED

        if dx != 0 or dy != 0:
            self._renderer.scroll_pixels(dx, dy)
            self.invalidate()

    # ------------------------------------------------------------------
    # Event bus callbacks
    # ------------------------------------------------------------------
    def _on_simulation_tick(self, data: Any) -> None:
        """Handle simulation tick events."""
        # Invalidate to redraw updated map state
        if self.visible:
            self.invalidate()

    def _on_map_invalidate(self, data: Any) -> None:
        """Handle map invalidation events."""
        if self.visible:
            self.invalidate()

    # ------------------------------------------------------------------
    # Initialization helpers
    # ------------------------------------------------------------------
    def _init_renderer(self) -> None:
        """Initialize the MapRenderer."""
        if not _HAVE_PYGAME:
            return

        if self.context.sim is None or self.context.sim.editor is None:
            return

        try:
            self._renderer = MapRenderer(
                self.context,
                self.context.sim.editor,
                viewport_size=self._viewport_size,
                tile_size=16,
            )
        except Exception as e:
            print(f"Failed to initialize MapRenderer: {e}")
            self._renderer = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_overlay_mode(self, mode: str | None) -> None:
        """Set the active overlay mode (power, population, etc.)."""
        if self._renderer:
            self._renderer.set_overlay_mode(mode)
            self.invalidate()

    def center_on_tile(self, tile_x: int, tile_y: int) -> None:
        """Center the viewport on a specific tile."""
        if self._renderer:
            self._renderer.center_on(tile_x, tile_y)
            self.invalidate()

    def scroll_to_tile(self, tile_x: int, tile_y: int) -> None:
        """Scroll to show a specific tile."""
        if self._renderer:
            # Convert tile coordinates to pixel position
            px = tile_x * 16
            py = tile_y * 16
            # Get current pixel origin
            ox, oy = self._renderer.pixel_origin
            # Calculate required scroll
            dx = px - ox
            dy = py - oy
            self._renderer.scroll_pixels(dx, dy)
            self.invalidate()

    def get_viewport_rect(self) -> tuple[int, int, int, int]:
        """Get the current viewport in tile coordinates."""
        if self._renderer:
            vp = self._renderer.viewport_tiles
            return (vp.x, vp.y, vp.width, vp.height)
        return (0, 0, 0, 0)
