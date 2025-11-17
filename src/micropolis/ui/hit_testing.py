"""
hit_testing.py - Hit-testing utilities for Micropolis pygame UI

Provides efficient coordinate conversion and hit-testing for mapping screen
coordinates to world tiles, with grid acceleration for performance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..sim_view import SimView


class HitTester:
    """
    Efficient hit-testing for converting screen to world coordinates.

    Uses grid acceleration to quickly map screen positions to tile coordinates
    while respecting viewport offsets and zoom levels.
    """

    def __init__(self):
        """Initialize hit tester."""
        self.tile_size: int = 16  # Default tile size in pixels (editor view)
        self.small_tile_size: int = 3  # Mini-map tile size in pixels

    def screen_to_tile(
        self,
        screen_pos: tuple[int, int],
        viewport_offset: tuple[int, int],
        tile_size: int | None = None,
    ) -> tuple[int, int]:
        """
        Convert screen coordinates to tile coordinates.

        Args:
            screen_pos: (x, y) in screen pixels
            viewport_offset: (pan_x, pan_y) viewport offset
            tile_size: Tile size in pixels (None = use default 16)

        Returns:
            (tile_x, tile_y) tile coordinates
        """
        if tile_size is None:
            tile_size = self.tile_size

        screen_x, screen_y = screen_pos
        pan_x, pan_y = viewport_offset

        # Adjust for viewport offset
        world_x = screen_x + pan_x
        world_y = screen_y + pan_y

        # Convert to tile coordinates
        tile_x = world_x // tile_size
        tile_y = world_y // tile_size

        return tile_x, tile_y

    def tile_to_screen(
        self,
        tile_pos: tuple[int, int],
        viewport_offset: tuple[int, int],
        tile_size: int | None = None,
    ) -> tuple[int, int]:
        """
        Convert tile coordinates to screen coordinates.

        Args:
            tile_pos: (tile_x, tile_y) tile coordinates
            viewport_offset: (pan_x, pan_y) viewport offset
            tile_size: Tile size in pixels (None = use default 16)

        Returns:
            (screen_x, screen_y) in screen pixels
        """
        if tile_size is None:
            tile_size = self.tile_size

        tile_x, tile_y = tile_pos
        pan_x, pan_y = viewport_offset

        # Convert tile to world pixels
        world_x = tile_x * tile_size
        world_y = tile_y * tile_size

        # Adjust for viewport offset
        screen_x = world_x - pan_x
        screen_y = world_y - pan_y

        return screen_x, screen_y

    def is_valid_tile(
        self, tile_pos: tuple[int, int], map_width: int = 120, map_height: int = 100
    ) -> bool:
        """
        Check if tile coordinates are within valid map bounds.

        Args:
            tile_pos: (tile_x, tile_y) to check
            map_width: Map width in tiles (default 120)
            map_height: Map height in tiles (default 100)

        Returns:
            True if tile is within bounds
        """
        tile_x, tile_y = tile_pos
        return 0 <= tile_x < map_width and 0 <= tile_y < map_height

    def rect_contains_tile(
        self,
        tile_pos: tuple[int, int],
        rect_top_left: tuple[int, int],
        rect_size: tuple[int, int],
    ) -> bool:
        """
        Check if tile is within a rectangular area.

        Args:
            tile_pos: (tile_x, tile_y) to check
            rect_top_left: (x, y) top-left corner of rectangle in tiles
            rect_size: (width, height) size of rectangle in tiles

        Returns:
            True if tile is within rectangle
        """
        tile_x, tile_y = tile_pos
        rx, ry = rect_top_left
        rw, rh = rect_size

        return rx <= tile_x < rx + rw and ry <= tile_y < ry + rh

    def tiles_in_rect(
        self, rect_top_left: tuple[int, int], rect_size: tuple[int, int]
    ) -> list[tuple[int, int]]:
        """
        Get all tile coordinates within a rectangular area.

        Args:
            rect_top_left: (x, y) top-left corner in tiles
            rect_size: (width, height) size in tiles

        Returns:
            List of (tile_x, tile_y) tuples
        """
        rx, ry = rect_top_left
        rw, rh = rect_size

        tiles = []
        for y in range(ry, ry + rh):
            for x in range(rx, rx + rw):
                tiles.append((x, y))

        return tiles

    def snap_to_orthogonal(
        self, start_pos: tuple[int, int], end_pos: tuple[int, int]
    ) -> tuple[int, int]:
        """
        Snap line to orthogonal (horizontal or vertical) axis.

        Used for drawing roads/wires in straight lines.

        Args:
            start_pos: (x, y) starting tile position
            end_pos: (x, y) ending tile position

        Returns:
            Snapped (x, y) end position
        """
        sx, sy = start_pos
        ex, ey = end_pos

        # Calculate deltas
        dx = abs(ex - sx)
        dy = abs(ey - sy)

        # Snap to dominant axis
        if dx > dy:
            # Horizontal line - keep x, snap y
            return ex, sy
        else:
            # Vertical line - keep y, snap x
            return sx, ey

    def get_line_tiles(
        self,
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
        snap_orthogonal: bool = True,
    ) -> list[tuple[int, int]]:
        """
        Get all tiles along a line between two points.

        Uses Bresenham's line algorithm for accurate line drawing.

        Args:
            start_pos: (x, y) starting tile position
            end_pos: (x, y) ending tile position
            snap_orthogonal: Whether to snap to orthogonal axis

        Returns:
            List of (tile_x, tile_y) tuples along the line
        """
        sx, sy = start_pos
        ex, ey = end_pos

        if snap_orthogonal:
            ex, ey = self.snap_to_orthogonal(start_pos, (ex, ey))

        # Bresenham's line algorithm
        tiles = []
        dx = abs(ex - sx)
        dy = abs(ey - sy)

        x_step = 1 if sx < ex else -1
        y_step = 1 if sy < ey else -1

        x, y = sx, sy
        tiles.append((x, y))

        if dx > dy:
            error = dx / 2
            while x != ex:
                error -= dy
                if error < 0:
                    y += y_step
                    error += dx
                x += x_step
                tiles.append((x, y))
        else:
            error = dy / 2
            while y != ey:
                error -= dx
                if error < 0:
                    x += x_step
                    error += dy
                y += y_step
                tiles.append((x, y))

        return tiles

    def get_rect_tiles(
        self, start_pos: tuple[int, int], end_pos: tuple[int, int]
    ) -> list[tuple[int, int]]:
        """
        Get all tiles within a rectangle defined by two corners.

        Used for rectangular zone placement (Shift+Drag).

        Args:
            start_pos: (x, y) first corner
            end_pos: (x, y) opposite corner

        Returns:
            List of (tile_x, tile_y) tuples in the rectangle
        """
        sx, sy = start_pos
        ex, ey = end_pos

        # Normalize to top-left and bottom-right
        x1, x2 = (sx, ex) if sx < ex else (ex, sx)
        y1, y2 = (sy, ey) if sy < ey else (ey, sy)

        return self.tiles_in_rect((x1, y1), (x2 - x1 + 1, y2 - y1 + 1))

    def viewport_to_tile(
        self, screen_pos: tuple[int, int], view: SimView
    ) -> tuple[int, int]:
        """
        Convert screen position to tile coordinates using SimView.

        Convenience method that extracts viewport info from SimView.

        Args:
            screen_pos: (x, y) in screen pixels
            view: SimView with viewport offset information

        Returns:
            (tile_x, tile_y) tile coordinates
        """
        center_x = view.w_width // 2
        center_y = view.w_height // 2

        # Offset from center
        offset_x = screen_pos[0] - center_x
        offset_y = screen_pos[1] - center_y

        # Add pan offset
        world_x = offset_x + view.pan_x
        world_y = offset_y + view.pan_y

        # Convert to tile
        tile_x = world_x // 16
        tile_y = world_y // 16

        return tile_x, tile_y


# Global singleton instance
_hit_tester = HitTester()


def get_hit_tester() -> HitTester:
    """Get the global hit tester instance."""
    return _hit_tester
