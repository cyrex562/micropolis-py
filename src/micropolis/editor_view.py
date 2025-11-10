"""
editor_view.py - Editor view rendering for Micropolis Python port

This module implements the editor view rendering system, displaying detailed
16x16 pixel tiles for map editing. Ported from g_bigmap.c.

Key features:
- 16x16 pixel tile rendering (big tiles)
- Tile caching to avoid redrawing unchanged tiles
- Blinking lightning bolt animation for unpowered zones
- Dynamic filtering based on city data criteria
- Support for different color depths and rendering modes
"""

import pygame

from . import engine, graphics_setup, macros, map_view, types

# ============================================================================
# Editor View Rendering Functions
# ============================================================================

def drawBeegMaps() -> None:
    """
    Update all editor views.

    Ported from drawBeegMaps() in g_bigmap.c.
    """
    engine.sim_update_editors()


def MemDrawBeegMapRect(view: types.SimView, x: int, y: int, w: int, h: int) -> None:
    """
    Draw a rectangle of tiles in the editor view using memory buffer.

    Ported from MemDrawBeegMapRect() in g_bigmap.c.

    Args:
        view: The editor view to draw into
        x, y: Top-left tile coordinates
        w, h: Width and height in tiles
    """
    # Clip to view boundaries
    if x < view.tile_x:
        w -= (view.tile_x - x)
        if w <= 0:
            return
        x = view.tile_x

    if y < view.tile_y:
        h -= (view.tile_y - y)
        if h <= 0:
            return
        y = view.tile_y

    if (x + w) > (view.tile_x + view.tile_width):
        w = (view.tile_x + view.tile_width) - x
        if w <= 0:
            return

    if (y + h) > (view.tile_y + view.tile_height):
        h = (view.tile_y + view.tile_height) - y
        if h <= 0:
            return

    # Get display properties
    line_bytes = view.line_bytes
    pixel_bytes = view.pixel_bytes

    # Check if we have color display
    if view.x and view.x.color:
        # Color rendering mode
        _draw_color_editor_rect(view, x, y, w, h, line_bytes, pixel_bytes)
    else:
        # Monochrome rendering mode
        _draw_mono_editor_rect(view, x, y, w, h, line_bytes)


def _draw_color_editor_rect(view: types.SimView, x: int, y: int, w: int, h: int,
                           line_bytes: int, pixel_bytes: int) -> None:
    """
    Draw editor rectangle in color mode.

    Args:
        view: The editor view
        x, y: Top-left tile coordinates
        w, h: Width and height in tiles
        line_bytes: Bytes per line in display buffer
        pixel_bytes: Bytes per pixel
    """
    surface = _ensure_view_surface(view)
    if surface is None:
        return

    have = view.tiles
    blink = (types.flagBlink <= 0)

    for col in range(w):
        tile_x = x + col
        local_col = tile_x - view.tile_x
        ha = have[local_col] if have else None

        for row in range(h):
            tile_y = y + row
            local_row = tile_y - view.tile_y

            tile = types.Map[tile_x][tile_y]
            if (tile & macros.LOMASK) >= types.TILE_COUNT:
                tile -= types.TILE_COUNT

            if blink and (tile & macros.ZONEBIT) and not (tile & types.PWRBIT):
                tile = types.LIGHTNINGBOLT
            else:
                tile &= macros.LOMASK

            if (tile > 63 and view.dynamic_filter != 0 and
                    not map_view.dynamicFilter(tile_x, tile_y)):
                tile = 0

            if ha and ha[local_row] == tile:
                continue

            if ha:
                ha[local_row] = tile

            dest_x = local_col * 16
            dest_y = local_row * 16
            _blit_tile(view, tile, dest_x, dest_y)


def _draw_mono_editor_rect(view: types.SimView, x: int, y: int, w: int, h: int,
                          line_bytes: int) -> None:
    """
    Draw editor rectangle in monochrome mode.

    Args:
        view: The editor view
        x, y: Top-left tile coordinates
        w, h: Width and height in tiles
        line_bytes: Bytes per line in display buffer
    """
    surface = _ensure_view_surface(view)
    if surface is None:
        return

    have = view.tiles
    blink = (types.flagBlink <= 0)

    for col in range(w):
        tile_x = x + col
        local_col = tile_x - view.tile_x
        ha = have[local_col] if have else None

        for row in range(h):
            tile_y = y + row
            local_row = tile_y - view.tile_y

            tile = types.Map[tile_x][tile_y]
            if (tile & macros.LOMASK) >= types.TILE_COUNT:
                tile -= types.TILE_COUNT

            if blink and (tile & macros.ZONEBIT) and not (tile & types.PWRBIT):
                tile = types.LIGHTNINGBOLT
            else:
                tile &= macros.LOMASK

            if ha and ha[local_row] == tile:
                continue

            if ha:
                ha[local_row] = tile

            dest_x = local_col * 16
            dest_y = local_row * 16
            _blit_tile(view, tile, dest_x, dest_y)


def _blit_tile(view: types.SimView, tile: int, dest_x: int, dest_y: int) -> None:
    """Blit a single tile surface into the editor view."""
    if view.surface is None:
        return None

    tile_surface = graphics_setup.get_tile_surface(tile, view)
    if tile_surface is not None:
        view.surface.blit(tile_surface, (dest_x, dest_y))


def WireDrawBeegMapRect(view: types.SimView, x: int, y: int, w: int, h: int) -> None:
    """
    Draw a rectangle of tiles using wire protocol (X11).

    Ported from WireDrawBeegMapRect() in g_bigmap.c.
    This function is for X11 wire protocol rendering and would need
    adaptation for pygame.

    Args:
        view: The editor view to draw into
        x, y: Top-left tile coordinates
        w, h: Width and height in tiles
    """
    # Clip to view boundaries (same as MemDrawBeegMapRect)
    if x < view.tile_x:
        w -= (view.tile_x - x)
        if w <= 0:
            return
        x = view.tile_x

    if y < view.tile_y:
        h -= (view.tile_y - y)
        if h <= 0:
            return
        y = view.tile_y

    if (x + w) > (view.tile_x + view.tile_width):
        w = (view.tile_x + view.tile_width) - x
        if w <= 0:
            return

    if (y + h) > (view.tile_y + view.tile_height):
        h = (view.tile_y + view.tile_height) - y
        if h <= 0:
            return

    # Get map data - use indexing instead of pointer arithmetic
    map_x = x
    map_y = y

    # Get tile cache
    have = view.tiles

    # Blinking state for lightning bolt
    blink = (types.flagBlink <= 0)

    # Process each column
    for col in range(w):
        # Calculate local column index within view
        local_col = col + (x - view.tile_x)
        
        # Get tile cache for this column
        ha = have[local_col] if have else None

        # Process each row in this column
        for row in range(h):
            # Calculate local row index within view
            local_row = row + (y - view.tile_y)
            
            # Get tile from map
            tile = types.Map[map_x][map_y + row]
            if (tile & macros.LOMASK) >= types.TILE_COUNT:
                tile -= types.TILE_COUNT

            # Handle blinking lightning bolt for unpowered zones
            if blink and (tile & macros.ZONEBIT) and not (tile & types.PWRBIT):
                tile = types.LIGHTNINGBOLT
            else:
                tile &= macros.LOMASK

            # Check if tile changed
            if ha and ha[local_row] != tile:
                # Update cache
                ha[local_row] = tile

                # In X11, this would copy from pixmap to window
                # In pygame, this would be: surface.blit(tile_surface, (col*16, row*16))
                pass

        # Move to next column
        map_x += 1


# ============================================================================
# Pygame Integration Functions
# ============================================================================

def DoUpdateEditor(view: types.SimView) -> None:
    """
    Update an editor view for pygame rendering.

    This replaces the placeholder in engine.py.

    Args:
        view: The editor view to update
    """
    if not view or not view.visible:
        return

    # Mark view as valid
    view.invalid = False

    # Get the visible area that needs updating
    x = view.tile_x
    y = view.tile_y
    w = view.tile_width
    h = view.tile_height

    # Draw the visible rectangle
    MemDrawBeegMapRect(view, x, y, w, h)

    # Update pygame display (placeholder for pygame integration)
    # pygame.display.update() or similar


# ============================================================================
# Utility Functions
# ============================================================================

def initialize_editor_tiles(view: types.SimView) -> None:
    """
    Initialize tile cache for editor view.

    Args:
        view: The editor view to initialize
    """
    if not view:
        return

    # Initialize tile cache as 2D array
    # view.tiles is short **tiles in C (array of arrays)
    view.tiles = []
    for i in range(view.tile_width):
        view.tiles.append([-1] * view.tile_height)  # -1 indicates uninitialized
    _ensure_view_surface(view)


def cleanup_editor_tiles(view: types.SimView) -> None:
    """
    Clean up tile cache for editor view.

    Args:
        view: The editor view to clean up
    """
    if view and view.tiles:
        view.tiles.clear()


def invalidate_editor_view(view: types.SimView) -> None:
    """
    Mark editor view as needing redraw.

    Args:
        view: The editor view to invalidate
    """
    if view:
        view.invalid = True
        # Reset tile cache to force redraw
        if view.tiles:
            for col in view.tiles:
                for i in range(len(col)):
                    col[i] = -1


def _ensure_view_surface(view: types.SimView) -> pygame.Surface:
    """Create a pygame surface for the editor view when missing."""
    surface = getattr(view, "surface", None)
    if surface is not None:
        return surface

    width = view.width or (view.tile_width or types.WORLD_X) * 16
    height = view.height or (view.tile_height or types.WORLD_Y) * 16

    view.width = width
    view.height = height

    view.surface = pygame.Surface((width, height), pygame.SRCALPHA)
    return view.surface
