"""Tool preview system for the Micropolis editor.

This module provides visual feedback for tool placement:
- Translucent ghost tile that follows the cursor
- Red overlay for invalid placements
- Error sound effects for invalid placement attempts
- Line/rectangle drawing for roads/zones with Shift+Drag

Features:
- Preview rendering with alpha blending
- Validation checking before placement
- Visual and audio feedback
- Multi-tile tool support
- Line and area drawing modes
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from micropolis.context import AppContext
    from micropolis.types import SimView

try:
    import pygame

    _HAVE_PYGAME = True
except Exception:  # pragma: no cover
    pygame = None  # type: ignore
    _HAVE_PYGAME = False


class PreviewMode(Enum):
    """Tool preview modes."""

    SINGLE = "single"  # Single tile placement
    LINE = "line"  # Line drawing (Shift+Drag)
    RECT = "rect"  # Rectangle drawing (Shift+Drag for zones)


@dataclass
class PreviewState:
    """State for tool preview rendering."""

    tool_id: int
    start_x: int
    start_y: int
    end_x: int | None = None
    end_y: int | None = None
    mode: PreviewMode = PreviewMode.SINGLE
    is_valid: bool = True
    shift_held: bool = False


class ToolPreview:
    """Manages tool preview rendering and validation."""

    def __init__(self, context: AppContext):
        """Initialize the tool preview system.

        Args:
            context: Application context
        """
        self.context = context
        self.preview_state: PreviewState | None = None

        # Preview colors (RGBA)
        self.valid_color = (255, 255, 255, 128)  # White translucent
        self.invalid_color = (255, 0, 0, 128)  # Red translucent
        self.line_color = (100, 200, 255, 180)  # Blue for line preview

        # Cache for tool surfaces
        self._tool_surfaces: dict[int, pygame.Surface] = {}

        # Sound flags to prevent duplicate error sounds
        self._last_invalid_sound_time = 0.0
        self._invalid_sound_cooldown = 0.5  # seconds

    def start_preview(
        self, tool_id: int, tile_x: int, tile_y: int, shift_held: bool = False
    ) -> None:
        """Start a tool preview at the given position.

        Args:
            tool_id: Tool ID to preview
            tile_x: Starting tile X coordinate
            tile_y: Starting tile Y coordinate
            shift_held: Whether Shift key is held for line/rect drawing
        """
        if not _HAVE_PYGAME:
            return

        mode = self._determine_preview_mode(tool_id, shift_held)
        is_valid = self._validate_placement(tool_id, tile_x, tile_y)

        self.preview_state = PreviewState(
            tool_id=tool_id,
            start_x=tile_x,
            start_y=tile_y,
            mode=mode,
            is_valid=is_valid,
            shift_held=shift_held,
        )

    def update_preview(
        self, tile_x: int, tile_y: int, shift_held: bool = False
    ) -> None:
        """Update preview position (for drag operations).

        Args:
            tile_x: Current tile X coordinate
            tile_y: Current tile Y coordinate
            shift_held: Whether Shift key is held
        """
        if not self.preview_state:
            return

        # Update mode if shift state changed
        if shift_held != self.preview_state.shift_held:
            self.preview_state.mode = self._determine_preview_mode(
                self.preview_state.tool_id, shift_held
            )
            self.preview_state.shift_held = shift_held

        # Update end position for line/rect modes
        if self.preview_state.mode in (PreviewMode.LINE, PreviewMode.RECT):
            self.preview_state.end_x = tile_x
            self.preview_state.end_y = tile_y
        else:
            self.preview_state.start_x = tile_x
            self.preview_state.start_y = tile_y

        # Validate placement
        self.preview_state.is_valid = self._validate_placement(
            self.preview_state.tool_id, tile_x, tile_y
        )

    def end_preview(self) -> None:
        """End the current tool preview."""
        self.preview_state = None

    def render(
        self, surface: pygame.Surface, view: SimView, tile_size: int = 16
    ) -> None:
        """Render the tool preview on the given surface.

        Args:
            surface: Pygame surface to render on
            view: SimView providing viewport information
            tile_size: Size of each tile in pixels (default 16)
        """
        if not _HAVE_PYGAME or not self.preview_state:
            return

        if self.preview_state.mode == PreviewMode.SINGLE:
            self._render_single_preview(surface, view, tile_size)
        elif self.preview_state.mode == PreviewMode.LINE:
            self._render_line_preview(surface, view, tile_size)
        elif self.preview_state.mode == PreviewMode.RECT:
            self._render_rect_preview(surface, view, tile_size)

    def _render_single_preview(
        self, surface: pygame.Surface, view: SimView, tile_size: int
    ) -> None:
        """Render a single tile preview."""
        if not self.preview_state:
            return

        # Convert tile coordinates to screen coordinates
        screen_x, screen_y = self._tile_to_screen(
            self.preview_state.start_x, self.preview_state.start_y, view, tile_size
        )

        # Get tool size (1x1, 3x3, 4x4, etc.)
        tool_width, tool_height = self._get_tool_size(self.preview_state.tool_id)

        # Create preview surface with alpha
        preview_surf = pygame.Surface(
            (tool_width * tile_size, tool_height * tile_size), pygame.SRCALPHA
        )

        # Choose color based on validity
        color = self.valid_color if self.preview_state.is_valid else self.invalid_color

        # Draw semi-transparent overlay
        preview_surf.fill(color)

        # Draw border
        border_color = (
            (255, 255, 255, 255) if self.preview_state.is_valid else (255, 0, 0, 255)
        )
        pygame.draw.rect(
            preview_surf,
            border_color,
            (0, 0, tool_width * tile_size, tool_height * tile_size),
            2,
        )

        # Blit to main surface
        surface.blit(preview_surf, (screen_x, screen_y))

    def _render_line_preview(
        self, surface: pygame.Surface, view: SimView, tile_size: int
    ) -> None:
        """Render a line drawing preview (for roads/rails/wires)."""
        if not self.preview_state or self.preview_state.end_x is None:
            return

        # Calculate line tiles
        tiles = self._calculate_line_tiles(
            self.preview_state.start_x,
            self.preview_state.start_y,
            self.preview_state.end_x,
            self.preview_state.end_y,
        )

        # Draw each tile in the line
        for tx, ty in tiles:
            screen_x, screen_y = self._tile_to_screen(tx, ty, view, tile_size)

            # Validate each tile
            is_valid = self._validate_placement(self.preview_state.tool_id, tx, ty)
            color = self.line_color if is_valid else self.invalid_color

            # Draw preview tile
            preview_surf = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
            preview_surf.fill(color)
            pygame.draw.rect(
                preview_surf, (255, 255, 255, 255), (0, 0, tile_size, tile_size), 1
            )
            surface.blit(preview_surf, (screen_x, screen_y))

    def _render_rect_preview(
        self, surface: pygame.Surface, view: SimView, tile_size: int
    ) -> None:
        """Render a rectangle drawing preview (for zones)."""
        if not self.preview_state or self.preview_state.end_x is None:
            return

        # Calculate rectangle bounds
        min_x = min(self.preview_state.start_x, self.preview_state.end_x)
        max_x = max(self.preview_state.start_x, self.preview_state.end_x)
        min_y = min(self.preview_state.start_y, self.preview_state.end_y)
        max_y = max(self.preview_state.start_y, self.preview_state.end_y)

        # Get zone size (3x3)
        zone_size = 3

        # Draw each zone in the rectangle
        for zx in range(min_x, max_x + 1, zone_size):
            for zy in range(min_y, max_y + 1, zone_size):
                # Validate zone placement
                is_valid = self._validate_zone_placement(
                    self.preview_state.tool_id, zx, zy
                )
                color = self.valid_color if is_valid else self.invalid_color

                # Draw zone preview
                screen_x, screen_y = self._tile_to_screen(zx, zy, view, tile_size)
                preview_surf = pygame.Surface(
                    (zone_size * tile_size, zone_size * tile_size), pygame.SRCALPHA
                )
                preview_surf.fill(color)
                pygame.draw.rect(
                    preview_surf,
                    (255, 255, 255, 255) if is_valid else (255, 0, 0, 255),
                    (0, 0, zone_size * tile_size, zone_size * tile_size),
                    2,
                )
                surface.blit(preview_surf, (screen_x, screen_y))

    def _tile_to_screen(
        self, tile_x: int, tile_y: int, view: SimView, tile_size: int
    ) -> tuple[int, int]:
        """Convert tile coordinates to screen coordinates.

        Args:
            tile_x: Tile X coordinate
            tile_y: Tile Y coordinate
            view: SimView for viewport offset
            tile_size: Size of each tile in pixels

        Returns:
            Tuple of (screen_x, screen_y)
        """
        # Get viewport offset
        view_x = getattr(view, "tile_x", 0)
        view_y = getattr(view, "tile_y", 0)

        # Calculate screen position
        screen_x = (tile_x - view_x) * tile_size
        screen_y = (tile_y - view_y) * tile_size

        return screen_x, screen_y

    def _get_tool_size(self, tool_id: int) -> tuple[int, int]:
        """Get the size of a tool in tiles.

        Args:
            tool_id: Tool ID

        Returns:
            Tuple of (width, height) in tiles
        """
        # Tool size lookup (from tools.py constants)
        from micropolis.constants import (
            AIRPORTBASE,
            COMBASE,
            FIRESTBASE,
            INDBASE,
            NUCLEARBASE,
            POLICESTBASE,
            POWERPLANTBASE,
            RESBASE,
            SEAPORTBASE,
            STADIUMBASE,
        )

        # Check tool size list if available
        if hasattr(self.context, "tool_size") and self.context.tool_size:
            try:
                size = self.context.tool_size[tool_id]
                return (size, size)
            except (IndexError, KeyError):
                pass

        # Fallback: determine from tile base
        tile_base = tool_id & 0x3FF  # Remove status bits

        # 4x4 buildings
        if tile_base in (
            STADIUMBASE,
            AIRPORTBASE,
            SEAPORTBASE,
            NUCLEARBASE,
            POWERPLANTBASE,
        ):
            return (4, 4)

        # 3x3 zones and service buildings
        if tile_base in (RESBASE, COMBASE, INDBASE, FIRESTBASE, POLICESTBASE):
            return (3, 3)

        # Default to 1x1
        return (1, 1)

    def _determine_preview_mode(self, tool_id: int, shift_held: bool) -> PreviewMode:
        """Determine the preview mode based on tool and modifier keys.

        Args:
            tool_id: Tool ID
            shift_held: Whether Shift key is held

        Returns:
            Preview mode
        """
        from micropolis.constants import (
            COMBASE,
            INDBASE,
            POWERBASE,
            RAILBASE,
            RESBASE,
            ROADBASE,
        )

        if not shift_held:
            return PreviewMode.SINGLE

        tile_base = tool_id & 0x3FF

        # Zones use rectangle mode
        if tile_base in (RESBASE, COMBASE, INDBASE):
            return PreviewMode.RECT

        # Roads, rails, wires use line mode
        if tile_base in (ROADBASE, RAILBASE, POWERBASE):
            return PreviewMode.LINE

        return PreviewMode.SINGLE

    def _validate_placement(self, tool_id: int, tile_x: int, tile_y: int) -> bool:
        """Validate if a tool can be placed at the given position.

        Args:
            tool_id: Tool ID
            tile_x: Tile X coordinate
            tile_y: Tile Y coordinate

        Returns:
            True if placement is valid, False otherwise
        """
        from micropolis.constants import WORLD_X, WORLD_Y

        # Check bounds
        if tile_x < 0 or tile_x >= WORLD_X or tile_y < 0 or tile_y >= WORLD_Y:
            return False

        # Check funds
        if hasattr(self.context, "total_funds"):
            from micropolis.constants import CostOf

            if CostOf and tool_id < len(CostOf):
                cost = CostOf[tool_id]
                if self.context.total_funds < cost:
                    return False

        # Check terrain/existing buildings (would need to check map)
        # This is a simplified check - full validation would inspect the map
        if hasattr(self.context, "map_data") and self.context.map_data:
            try:
                # Get tool size
                width, height = self._get_tool_size(tool_id)

                # Check all tiles in tool footprint
                for dx in range(width):
                    for dy in range(height):
                        tx = tile_x + dx
                        ty = tile_y + dy

                        if tx >= WORLD_X or ty >= WORLD_Y:
                            return False

                        # Check if tile is occupied (simplified)
                        # Full validation would check for valid terrain, etc.

            except (IndexError, KeyError):
                pass

        return True

    def _validate_zone_placement(self, tool_id: int, tile_x: int, tile_y: int) -> bool:
        """Validate zone placement (3x3 area)."""
        width, height = self._get_tool_size(tool_id)

        # Check all tiles in zone
        for dx in range(width):
            for dy in range(height):
                if not self._validate_placement(tool_id, tile_x + dx, tile_y + dy):
                    return False
        return True

    def _calculate_line_tiles(
        self, x1: int, y1: int, x2: int, y2: int
    ) -> list[tuple[int, int]]:
        """Calculate tiles along a line using Bresenham's algorithm.

        Args:
            x1, y1: Start coordinates
            x2, y2: End coordinates

        Returns:
            List of (x, y) tile coordinates
        """
        tiles = []

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1

        err = dx - dy

        x, y = x1, y1

        while True:
            tiles.append((x, y))

            if x == x2 and y == y2:
                break

            e2 = 2 * err

            if e2 > -dy:
                err -= dy
                x += sx

            if e2 < dx:
                err += dx
                y += sy

        return tiles

    def play_error_sound(self) -> None:
        """Play error sound for invalid placement (with cooldown)."""
        if not _HAVE_PYGAME:
            return

        import time

        current_time = time.time()

        # Check cooldown
        if current_time - self._last_invalid_sound_time < self._invalid_sound_cooldown:
            return

        self._last_invalid_sound_time = current_time

        # Play error sound
        try:
            from micropolis.audio import play_sound

            play_sound(self.context, "edit", "UhUh")
        except Exception:
            # Silent failure for sound
            pass

    def check_and_play_error_sound(self) -> None:
        """Check validity and play error sound if invalid."""
        if self.preview_state and not self.preview_state.is_valid:
            self.play_error_sound()
