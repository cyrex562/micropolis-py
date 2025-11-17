"""
cursor_manager.py - Global cursor management for Micropolis pygame UI

Manages cursor sprites based on selected tool and context (valid/invalid placement,
autopan zones near edges).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from ..context import AppContext


class CursorManager:
    """
    Global cursor manager that updates sprites based on tool state and context.

    Handles:
    - Tool-specific cursors (bulldozer, road, zone, etc.)
    - Context indicators (valid/invalid placement)
    - Autopan edge detection
    - Chalk and eraser modes
    """

    def __init__(self, context: AppContext):
        """Initialize cursor manager."""
        self.context = context
        self.current_cursor: pygame.cursors.Cursor | None = None
        self.current_tool: int | None = None
        self.is_valid_placement: bool = True
        self.is_in_autopan_zone: bool = False
        self._custom_cursors: dict[str, pygame.cursors.Cursor] = {}

        # Initialize default cursors
        self._init_cursors()

    def _init_cursors(self) -> None:
        """Initialize cursor sprites for different tools and contexts."""
        # Default arrow cursor
        self._custom_cursors["default"] = pygame.cursors.Cursor(
            pygame.SYSTEM_CURSOR_ARROW
        )

        # Pan/drag cursor
        self._custom_cursors["pan"] = pygame.cursors.Cursor(
            pygame.SYSTEM_CURSOR_SIZEALL
        )

        # Crosshair for query tool
        self._custom_cursors["query"] = pygame.cursors.Cursor(
            pygame.SYSTEM_CURSOR_CROSSHAIR
        )

        # Hand cursor for bulldozer/placement
        self._custom_cursors["hand"] = pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND)

        # Wait cursor
        self._custom_cursors["wait"] = pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_WAIT)

        # No cursor (invisible) for chalk/eraser
        # Create a fully transparent 8x8 cursor
        xor_data = (0, 0, 0, 0, 0, 0, 0, 0)
        and_data = (0, 0, 0, 0, 0, 0, 0, 0)
        self._custom_cursors["none"] = pygame.cursors.Cursor(
            (8, 8), (0, 0), xor_data, and_data
        )

    def update_cursor_for_tool(self, tool_state: int, is_valid: bool = True) -> None:
        """
        Update cursor based on current tool state.

        Args:
            tool_state: Current tool state (from editor module constants)
            is_valid: Whether the current placement is valid
        """
        self.current_tool = tool_state
        self.is_valid_placement = is_valid

        # Map tool states to cursor types
        # Tool state constants from editor.py:
        # 0=residential, 1=commercial, 2=industrial, 3=fire, 4=police
        # 5=stadium, 6=seaport, 7=power, 8=nuclear, 9=airport
        # 10=chalk, 11=eraser

        if tool_state == 10:  # chalkState
            cursor_name = "none"  # Hide system cursor for chalk
        elif tool_state == 11:  # eraserState
            cursor_name = "none"  # Hide system cursor for eraser
        elif tool_state == -1:  # Pan mode
            cursor_name = "pan"
        elif tool_state >= 0 and tool_state <= 9:  # Building tools
            cursor_name = "hand" if is_valid else "default"
        else:
            cursor_name = "default"

        self._set_cursor(cursor_name)

    def update_cursor_for_context(
        self, is_valid: bool | None = None, is_autopan_zone: bool | None = None
    ) -> None:
        """
        Update cursor based on current context without changing tool.

        Args:
            is_valid: Whether placement is valid (None to keep current)
            is_autopan_zone: Whether cursor is in autopan zone (None)
        """
        if is_valid is not None:
            self.is_valid_placement = is_valid

        if is_autopan_zone is not None:
            self.is_in_autopan_zone = is_autopan_zone

        # Re-apply cursor based on updated context
        if self.current_tool is not None:
            self.update_cursor_for_tool(self.current_tool, self.is_valid_placement)

    def set_pan_cursor(self) -> None:
        """Set cursor to pan/drag mode."""
        self._set_cursor("pan")

    def set_query_cursor(self) -> None:
        """Set cursor to query/inspect mode."""
        self._set_cursor("query")

    def set_wait_cursor(self) -> None:
        """Set cursor to wait/busy mode."""
        self._set_cursor("wait")

    def reset_cursor(self) -> None:
        """Reset cursor to default."""
        self._set_cursor("default")
        self.current_tool = None
        self.is_valid_placement = True
        self.is_in_autopan_zone = False

    def _set_cursor(self, cursor_name: str) -> None:
        """
        Internal method to set the pygame cursor.

        Args:
            cursor_name: Name of cursor to set
        """
        cursor = self._custom_cursors.get(cursor_name, self._custom_cursors["default"])
        if cursor != self.current_cursor:
            try:
                pygame.mouse.set_cursor(cursor)
                self.current_cursor = cursor
            except pygame.error:
                # Ignore cursor errors (e.g., in headless/dummy mode)
                pass

    def is_edge_autopan_zone(
        self,
        screen_pos: tuple[int, int],
        viewport_rect: pygame.Rect,
        edge_threshold: int = 32,
    ) -> tuple[bool, int, int]:
        """
        Check if cursor is in autopan edge zone.

        Args:
            screen_pos: Current mouse position in screen coordinates
            viewport_rect: Viewport rectangle
            edge_threshold: Distance from edge to trigger autopan (pixels)

        Returns:
            Tuple of (is_in_zone, dx, dy) where dx/dy are autopan velocity
        """
        x, y = screen_pos
        vx, vy = viewport_rect.x, viewport_rect.y
        vw, vh = viewport_rect.w, viewport_rect.h

        # Check if in viewport
        if not viewport_rect.collidepoint(x, y):
            return False, 0, 0

        dx, dy = 0, 0
        is_in_zone = False

        # Check left edge
        if x - vx < edge_threshold:
            dx = -1
            is_in_zone = True
        # Check right edge
        elif (vx + vw) - x < edge_threshold:
            dx = 1
            is_in_zone = True

        # Check top edge
        if y - vy < edge_threshold:
            dy = -1
            is_in_zone = True
        # Check bottom edge
        elif (vy + vh) - y < edge_threshold:
            dy = 1
            is_in_zone = True

        self.is_in_autopan_zone = is_in_zone
        return is_in_zone, dx, dy
