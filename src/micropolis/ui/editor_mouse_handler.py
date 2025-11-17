"""
editor_mouse_handler.py - Mouse interaction handler for editor panel

Implements mouse interactions for the editor panel including tool application,
drag painting, panning, and chalk overlay mode.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .hit_testing import get_hit_tester
from .mouse_controller import MouseButton, MouseMode

if TYPE_CHECKING:
    from ..context import AppContext
    from ..sim_view import SimView
    from .mouse_controller import MouseInputController


class EditorMouseHandler:
    """
    Handles mouse interactions for the editor panel.

    Features:
    - Left-click tool application
    - Drag painting with orthogonal snapping for roads/wires
    - Shift+Drag rectangle selection for zones
    - Right-click panning
    - Middle-click chalk annotation
    - Mouse wheel zoom
    """

    def __init__(
        self, context: AppContext, view: SimView, controller: MouseInputController
    ):
        """
        Initialize editor mouse handler.

        Args:
            context: Application context
            view: Editor view
            controller: Mouse input controller
        """
        self.context = context
        self.view = view
        self.controller = controller
        self.hit_tester = get_hit_tester()

        # Painting state
        self.painting_tiles: list[tuple[int, int]] = []
        self.paint_start_tile: tuple[int, int] | None = None

        # Chalk state
        self.chalk_strokes: list[list[tuple[int, int]]] = []
        self.current_chalk_stroke: list[tuple[int, int]] = []

        # Panning state
        self.pan_start_offset: tuple[int, int] | None = None

        # Hook up event handlers
        controller.on_click = self.handle_click
        controller.on_drag = self.handle_drag
        controller.on_drag_end = self.handle_drag_end
        controller.on_wheel = self.handle_wheel
        controller.on_hover = self.handle_hover

    def handle_click(self, pos: tuple[int, int], button: MouseButton) -> None:
        """
        Handle mouse click.

        Args:
            pos: Click position in screen coordinates
            button: Button that was clicked
        """
        tile_pos = self.hit_tester.viewport_to_tile(pos, self.view)

        if button == MouseButton.LEFT:
            # Apply tool at clicked tile
            if self.hit_tester.is_valid_tile(tile_pos):
                self._apply_tool_at_tile(tile_pos)
                self.paint_start_tile = tile_pos
                self.painting_tiles = [tile_pos]

        elif button == MouseButton.MIDDLE:
            # Start chalk stroke
            self.current_chalk_stroke = [tile_pos]

        elif button == MouseButton.RIGHT:
            # Start panning
            self.pan_start_offset = (self.view.pan_x, self.view.pan_y)

    def handle_drag(
        self, start_pos: tuple[int, int], current_pos: tuple[int, int]
    ) -> None:
        """
        Handle mouse drag.

        Args:
            start_pos: Drag start position
            current_pos: Current position
        """
        mode = self.controller.mode

        if mode == MouseMode.PAINTING:
            self._handle_paint_drag(start_pos, current_pos)
        elif mode == MouseMode.SELECTING:
            self._handle_select_drag(start_pos, current_pos)
        elif mode == MouseMode.CHALKING:
            self._handle_chalk_drag(current_pos)
        elif mode == MouseMode.PANNING:
            self._handle_pan_drag(start_pos, current_pos)

    def handle_drag_end(self, end_pos: tuple[int, int]) -> None:
        """
        Handle end of drag operation.

        Args:
            end_pos: Final drag position
        """
        mode = self.controller.mode

        if mode == MouseMode.PAINTING:
            # Complete painting operation
            self.painting_tiles.clear()
            self.paint_start_tile = None

        elif mode == MouseMode.SELECTING:
            # Apply tool to selected rectangle
            self._apply_tool_to_selection()

        elif mode == MouseMode.CHALKING:
            # Save chalk stroke
            if self.current_chalk_stroke:
                self.chalk_strokes.append(self.current_chalk_stroke)
                self.current_chalk_stroke = []

        elif mode == MouseMode.PANNING:
            # End panning
            self.pan_start_offset = None

    def handle_wheel(self, delta: int) -> None:
        """
        Handle mouse wheel scroll.

        Args:
            delta: Scroll delta (positive = up, negative = down)
        """
        # Zoom in/out (if zoom is implemented)
        # For now, we could use it to cycle overlays or adjust tool size
        pass

    def handle_hover(self, pos: tuple[int, int]) -> None:
        """
        Handle mouse hover (no buttons pressed).

        Args:
            pos: Mouse position
        """
        # Update cursor based on tile under mouse
        tile_pos = self.hit_tester.viewport_to_tile(pos, self.view)
        _is_valid = self.hit_tester.is_valid_tile(tile_pos)

        # Could update cursor manager here to show valid/invalid placement
        # cursor_manager.update_cursor_for_context(is_valid=_is_valid)

    def _handle_paint_drag(
        self, start_pos: tuple[int, int], current_pos: tuple[int, int]
    ) -> None:
        """Handle drag painting (roads, wires, etc.)."""
        if self.paint_start_tile is None:
            return

        current_tile = self.hit_tester.viewport_to_tile(current_pos, self.view)

        # Get tiles along line with orthogonal snapping
        line_tiles = self.hit_tester.get_line_tiles(
            self.paint_start_tile, current_tile, snap_orthogonal=True
        )

        # Apply tool to new tiles only
        for tile in line_tiles:
            if tile not in self.painting_tiles:
                if self.hit_tester.is_valid_tile(tile):
                    self._apply_tool_at_tile(tile)
                    self.painting_tiles.append(tile)

    def _handle_select_drag(
        self, start_pos: tuple[int, int], current_pos: tuple[int, int]
    ) -> None:
        """Handle Shift+Drag rectangle selection for zones."""
        start_tile = self.hit_tester.viewport_to_tile(start_pos, self.view)
        current_tile = self.hit_tester.viewport_to_tile(current_pos, self.view)

        # Store selection bounds for rendering
        # The actual tool application happens in handle_drag_end
        self.selection_rect = (start_tile, current_tile)

    def _handle_chalk_drag(self, current_pos: tuple[int, int]) -> None:
        """Handle chalk annotation dragging."""
        current_tile = self.hit_tester.viewport_to_tile(current_pos, self.view)

        # Add to current stroke if not duplicate
        if (
            not self.current_chalk_stroke
            or current_tile != self.current_chalk_stroke[-1]
        ):
            self.current_chalk_stroke.append(current_tile)

    def _handle_pan_drag(
        self, start_pos: tuple[int, int], current_pos: tuple[int, int]
    ) -> None:
        """Handle right-click drag panning."""
        if self.pan_start_offset is None:
            return

        dx = start_pos[0] - current_pos[0]
        dy = start_pos[1] - current_pos[1]

        # Apply pan offset
        self.view.pan_x = self.pan_start_offset[0] + dx
        self.view.pan_y = self.pan_start_offset[1] + dy

        # Clamp to map bounds (optional)
        self._clamp_pan()

    def _apply_tool_at_tile(self, tile_pos: tuple[int, int]) -> None:
        """
        Apply current tool at tile position.

        Args:
            tile_pos: (tile_x, tile_y) to apply tool
        """
        # Import here to avoid circular dependency
        from .. import tools

        tile_x, tile_y = tile_pos

        # Apply tool using the tools module
        # This will call DoTool or similar function
        tools.DoTool(self.context, self.view, self.view.tool_state, tile_x, tile_y)

    def _apply_tool_to_selection(self) -> None:
        """Apply tool to rectangular selection (Shift+Drag zones)."""
        if not hasattr(self, "selection_rect"):
            return

        start_tile, end_tile = self.selection_rect

        # Get all tiles in rectangle
        rect_tiles = self.hit_tester.get_rect_tiles(start_tile, end_tile)

        # Apply tool to each tile
        for tile in rect_tiles:
            if self.hit_tester.is_valid_tile(tile):
                self._apply_tool_at_tile(tile)

        # Clear selection
        delattr(self, "selection_rect")

    def _clamp_pan(self) -> None:
        """Clamp pan offset to valid map bounds."""
        # Map is 120x100 tiles, each 16 pixels
        map_width_px = 120 * 16
        map_height_px = 100 * 16

        # Clamp to keep some of the map visible
        min_pan = -self.view.w_width // 2
        max_pan_x = map_width_px + self.view.w_width // 2
        max_pan_y = map_height_px + self.view.w_height // 2

        self.view.pan_x = max(min_pan, min(self.view.pan_x, max_pan_x))
        self.view.pan_y = max(min_pan, min(self.view.pan_y, max_pan_y))

    def clear_chalk(self) -> None:
        """Clear all chalk strokes."""
        self.chalk_strokes.clear()
        self.current_chalk_stroke.clear()

    def get_chalk_strokes(self) -> list[list[tuple[int, int]]]:
        """Get all chalk strokes for rendering."""
        if self.current_chalk_stroke:
            return self.chalk_strokes + [self.current_chalk_stroke]
        return self.chalk_strokes
