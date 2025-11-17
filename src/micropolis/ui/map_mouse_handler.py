"""
map_mouse_handler.py - Mouse interaction handler for map/minimap panels

Implements click-to-center, drag selection, and overlay toggles for map panels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .hit_testing import get_hit_tester
from .mouse_controller import MouseButton

if TYPE_CHECKING:
    from ..context import AppContext
    from .mouse_controller import MouseInputController


class MapMouseHandler:
    """
    Handles mouse interactions for map and minimap panels.

    Features:
    - Click to center editor view on clicked tile
    - Drag selection rectangle for autopan target
    - Overlay toggles via UI controls
    """

    def __init__(
        self,
        context: AppContext,
        controller: MouseInputController,
        is_minimap: bool = False,
    ):
        """
        Initialize map mouse handler.

        Args:
            context: Application context
            controller: Mouse input controller
            is_minimap: True for minimap (3px tiles), False (16px tiles)
        """
        self.context = context
        self.controller = controller
        self.is_minimap = is_minimap
        self.hit_tester = get_hit_tester()

        # Selection rectangle state
        self.selection_start: tuple[int, int] | None = None
        self.selection_end: tuple[int, int] | None = None

        # Hook up event handlers
        controller.on_click = self.handle_click
        controller.on_drag = self.handle_drag
        controller.on_drag_end = self.handle_drag_end

    def handle_click(self, pos: tuple[int, int], button: MouseButton) -> None:
        """
        Handle mouse click on map.

        Args:
            pos: Click position
            button: Button clicked
        """
        if button != MouseButton.LEFT:
            return

        # Convert screen position to tile coordinates
        tile_size = 3 if self.is_minimap else 16
        tile_pos = self.hit_tester.screen_to_tile(pos, (0, 0), tile_size)

        # Center editor view on clicked tile
        self._center_editor_on_tile(tile_pos)

    def handle_drag(
        self, start_pos: tuple[int, int], current_pos: tuple[int, int]
    ) -> None:
        """
        Handle drag for selection rectangle.

        Args:
            start_pos: Drag start position
            current_pos: Current position
        """
        tile_size = 3 if self.is_minimap else 16

        self.selection_start = self.hit_tester.screen_to_tile(
            start_pos, (0, 0), tile_size
        )
        self.selection_end = self.hit_tester.screen_to_tile(
            current_pos, (0, 0), tile_size
        )

    def handle_drag_end(self, end_pos: tuple[int, int]) -> None:
        """
        Handle end of drag - apply selection.

        Args:
            end_pos: Final position
        """
        if self.selection_start and self.selection_end:
            # Could use selection rectangle for autopan target area
            # For now, just center on the selection center
            cx = (self.selection_start[0] + self.selection_end[0]) // 2
            cy = (self.selection_start[1] + self.selection_end[1]) // 2
            self._center_editor_on_tile((cx, cy))

        # Clear selection
        self.selection_start = None
        self.selection_end = None

    def _center_editor_on_tile(self, tile_pos: tuple[int, int]) -> None:
        """
        Center editor view on specified tile.

        Args:
            tile_pos: (tile_x, tile_y) to center on
        """
        # This would interact with the editor view to update pan offset
        # For now, just store the target position in context
        if hasattr(self.context, "map_click_target"):
            self.context.map_click_target = tile_pos

    def get_selection_rect(self) -> tuple[int, int, int, int] | None:
        """
        Get current selection rectangle for rendering.

        Returns:
            (x, y, w, h) in tile coordinates or None
        """
        if not self.selection_start or not self.selection_end:
            return None

        x1, y1 = self.selection_start
        x2, y2 = self.selection_end

        # Normalize to top-left and size
        x = min(x1, x2)
        y = min(y1, y2)
        w = abs(x2 - x1) + 1
        h = abs(y2 - y1) + 1

        return x, y, w, h


class GraphMouseHandler:
    """
    Handles mouse interactions for graph panels.

    Features:
    - Hover to show data cursor with values
    - Drag to scrub through historical data
    """

    def __init__(self, context: AppContext, controller: MouseInputController):
        """
        Initialize graph mouse handler.

        Args:
            context: Application context
            controller: Mouse input controller
        """
        self.context = context
        self.controller = controller

        # Data cursor state
        self.cursor_position: int | None = None  # Time index
        self.is_scrubbing: bool = False

        # Hook up event handlers
        controller.on_hover = self.handle_hover
        controller.on_drag = self.handle_drag
        controller.on_drag_end = self.handle_drag_end

    def handle_hover(self, pos: tuple[int, int]) -> None:
        """
        Handle hover to show data cursor.

        Args:
            pos: Mouse position
        """
        # Convert x position to time index in graph
        # This would depend on graph layout
        # For now, just store the position
        self.cursor_position = pos[0]

    def handle_drag(
        self, start_pos: tuple[int, int], current_pos: tuple[int, int]
    ) -> None:
        """
        Handle drag to scrub through data.

        Args:
            start_pos: Drag start
            current_pos: Current position
        """
        self.is_scrubbing = True
        self.cursor_position = current_pos[0]

    def handle_drag_end(self, end_pos: tuple[int, int]) -> None:
        """
        End scrubbing.

        Args:
            end_pos: Final position
        """
        self.is_scrubbing = False

    def get_cursor_data(
        self,
        graph_rect: tuple[int, int, int, int],
        data_points: list[float],
        time_range: int,
    ) -> tuple[int, float] | None:
        """
        Get data value at cursor position.

        Args:
            graph_rect: (x, y, w, h) graph area
            data_points: List of data values
            time_range: Time range in years (10 or 120)

        Returns:
            (time_index, value) or None
        """
        if self.cursor_position is None or not data_points:
            return None

        gx, gy, gw, gh = graph_rect

        # Check if cursor is in graph area
        if not (gx <= self.cursor_position < gx + gw):
            return None

        # Convert x position to data index
        relative_x = self.cursor_position - gx
        data_index = int((relative_x / gw) * len(data_points))
        data_index = max(0, min(data_index, len(data_points) - 1))

        value = data_points[data_index]
        return data_index, value
