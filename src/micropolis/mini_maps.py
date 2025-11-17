"""
mini_maps.py - Small overview maps for Micropolis Python port

This module implements the small overview map rendering system, displaying
4x4 pixel tiles for city overview. Ported from g_smmaps.c.

Key features:
- 4x4 pixel tile rendering (small tiles) for overview maps
- Zone-specific filtering (residential, commercial, industrial)
- Transportation network visualization
- Power grid status display (powered/unpowered/conductive)
- Dynamic filtering based on city data criteria
- Support for multiple color depths and rendering modes
"""

from collections.abc import Callable
from typing import Any

from micropolis.constants import WORLD_X, WORLD_Y, POWERED, UNPOWERED, \
    CONDUCTIVE, LOMASK, ZONEBIT, PWRBIT, CONDBIT, TILE_COUNT
from micropolis.context import AppContext
from micropolis.sim_view import SimView


# ============================================================================
# Small Map Rendering Functions
# ============================================================================


def drawAll(context: AppContext, view: SimView) -> None:
    """
    Draw all tiles in the small overview map.

    Ported from drawAll() in g_smmaps.c.

    Args:
        view: The view to draw into
        :param context:
    """
    _draw_filtered_map(context, view, None)


def drawRes(context: AppContext, view: SimView) -> None:
    """
    Draw only residential zones in the small overview map.

    Ported from drawRes() in g_smmaps.c.

    Args:
        view: The view to draw into
        :param context:
    """

    def filter_func(col: int, row: int, tile: int) -> int:
        if tile > 422:
            return 0
        return tile

    _draw_filtered_map(context, view, filter_func)


def drawCom(context: AppContext, view: SimView) -> None:
    """
    Draw only commercial zones in the small overview map.

    Ported from drawCom() in g_smmaps.c.

    Args:
        view: The view to draw into
        :param context:
    """

    def filter_func(col: int, row: int, tile: int) -> int:
        if (tile > 609) or ((tile >= 232) and (tile < 423)):
            return 0
        return tile

    _draw_filtered_map(context, view, filter_func)


def drawInd(context: AppContext,view: SimView) -> None:
    """
    Draw only industrial zones in the small overview map.

    Ported from drawInd() in g_smmaps.c.

    Args:
        view: The view to draw into
        :param context:
    """

    def filter_func(col: int, row: int, tile: int) -> int:
        if (
            ((tile >= 240) and (tile <= 611))
            or ((tile >= 693) and (tile <= 851))
            or ((tile >= 860) and (tile <= 883))
            or (tile >= 932)
        ):
            return 0
        return tile

    _draw_filtered_map(context, view, filter_func)


def drawLilTransMap(context: AppContext, view: SimView) -> None:
    """
    Draw transportation network (roads/rails) in the small overview map.

    Ported from drawLilTransMap() in g_smmaps.c.

    Args:
        view: The view to draw into
        :param context:
    """

    def filter_func(col: int, row: int, tile: int) -> int:
        if (tile >= 240) or ((tile >= 207) and tile <= 220) or (tile == 223):
            return 0
        return tile

    _draw_filtered_map(context, view, filter_func)


def drawPower(context: AppContext, view: SimView) -> None:
    """
    Draw power grid status in the small overview map.

    Shows powered zones (red), unpowered zones (light blue), and conductive tiles (gray).

    Ported from drawPower() in g_smmaps.c.

    Args:
        view: The view to draw into
    """

    # Get pixel values for current color mode
    if view.x and view.x.color:
        powered = view.pixels[POWERED] if view.pixels else 0
        unpowered = view.pixels[UNPOWERED] if view.pixels else 0
        conductive = view.pixels[CONDUCTIVE] if view.pixels else 0
    else:
        powered = 255
        unpowered = 0
        conductive = 127

    line_bytes = view.line_bytes8
    pixel_bytes = view.pixel_bytes

    # Get image buffer
    image_base = view.x.color if view.x else False
    if image_base:
        image_base = view.data  # type: ignore
    else:
        image_base = view.data8  # type: ignore

    # Process each tile
    for col in range(WORLD_X):
        # Calculate image buffer offset (for pygame integration)
        if image_base and isinstance(image_base, bytes):
            # For testing, skip actual buffer manipulation
            image = None
        else:
            image = (
                image_base  # For pygame surfaces, this would be calculated differently
            )

        for row in range(WORLD_Y):
            tile = context.map_data[col][row]

            if (tile & LOMASK) >= TILE_COUNT:
                tile -= TILE_COUNT

            tile &= LOMASK
            pix = -1

            # Determine pixel color based on tile properties
            if tile <= 63:
                # Terrain/water tiles - use normal rendering
                tile &= LOMASK
                pix = -1
            elif tile & ZONEBIT:
                # Zone tiles - show power status
                pix = powered if (tile & PWRBIT) else unpowered
            else:
                # Other tiles - check if conductive
                if tile & CONDBIT:
                    pix = conductive
                else:
                    tile = 0
                    pix = -1

            if pix < 0:
                # Use normal tile rendering
                _render_small_tile(view, image, tile, line_bytes, pixel_bytes)
            else:
                # Use solid color rendering
                _render_solid_color(view, image, pix, line_bytes, pixel_bytes)

            # Move to next row (3 pixels down)
            # In pygame, this would update the surface position

            # Move to next row (3 pixels down)
            if image:
                image += 3 * line_bytes


def drawDynamic(context: AppContext, view: SimView) -> None:
    """
    Draw tiles based on dynamic filtering criteria.

    Ported from drawDynamic() in g_smmaps.c.

    Args:
        view: The view to draw into
        :param context:
    """

    def filter_func(col: int, row: int, tile: int) -> int:
        if tile > 63:
            if not dynamicFilter(context, col, row):
                return 0
        return tile

    _draw_filtered_map(context, view, filter_func)


# ============================================================================
# Helper Functions
# ============================================================================


def _draw_filtered_map(context: AppContext,
    view: SimView,
    filter_func: Callable[[int, int, int], int] | None = None,
) -> None:
    """
    Generic function to draw a filtered small map.

    Args:
        view: The view to draw into
        filter_func: Optional filter function that takes (col, row, tile) and returns filtered tile
        :param context:
    """
    line_bytes = view.line_bytes8
    pixel_bytes = view.pixel_bytes

    # Get image buffer
    image_base = view.x.color if view.x else False
    if image_base:
        image_base = view.data  # type: ignore
    else:
        image_base = view.data8  # type: ignore

    # Process each tile
    for col in range(WORLD_X):
        # Calculate image buffer offset (for pygame integration)
        if image_base and isinstance(image_base, bytes):
            # For testing, skip actual buffer manipulation
            image = None
        else:
            image = (
                image_base  # For pygame surfaces, this would be calculated differently
            )

        for row in range(WORLD_Y):
            tile = context.map_data[col][row]

            if (tile & LOMASK) >= TILE_COUNT:
                tile -= TILE_COUNT

            tile &= LOMASK

            # Apply filtering if provided
            if filter_func:
                tile = filter_func(col, row, tile)

            # Render the tile
            _render_small_tile(view, image, tile, line_bytes, pixel_bytes)

            # Move to next row (3 pixels down)
            # In pygame, this would update the surface position


def _render_small_tile(
    view: SimView,
    image: Any | None,
    tile: int,
    line_bytes: int,
    pixel_bytes: int,
) -> None:
    """
    Render a 4x4 small tile to the display buffer.

    Args:
        view: The view containing tile data
        image: Image buffer position (pygame surface or buffer)
        tile: Tile index to render
        line_bytes: Bytes per line in display buffer
        pixel_bytes: Bytes per pixel
    """
    if not image or not view.smalltiles:
        return

    # Get tile data from smalltiles array
    # Each tile is 4x4 pixels = 16 pixels
    tile_offset = tile * 4 * 4 * pixel_bytes

    if tile_offset + (4 * 4 * pixel_bytes) > len(view.smalltiles):
        return

    # Copy 3x3 pixel area (the visible part of the 4x4 tile)
    # In pygame, this would be: surface.blit(tile_surface, (col*3, row*3))
    # For now, we prepare the data structure for pygame integration

    # The C code copies 3 rows of 3 pixels each from the 4x4 tile
    # This would need pygame surface integration for actual rendering


def _render_solid_color(
    view: SimView,
    image: Any | None,
    color: int,
    line_bytes: int,
    pixel_bytes: int,
) -> None:
    """
    Render a solid color block (3x3 pixels) to the display buffer.

    Args:
        view: The view containing display info
        image: Image buffer position (pygame surface or buffer)
        color: Color value to render
        line_bytes: Bytes per line in display buffer
        pixel_bytes: Bytes per pixel
    """
    if not image:
        return

    # Render 3x3 solid color block
    # In pygame, this would set pixels directly on the surface
    # For now, we prepare the data structure for pygame integration

    # Note: Actual buffer manipulation would depend on pygame surface format
    # The C code modifies memory buffers directly, but pygame uses surfaces


def dynamicFilter(context: AppContext, col: int, row: int) -> int:
    """
    Apply dynamic filtering based on city data criteria.

    Ported from dynamicFilter() in g_smmaps.c.

    Args:
        col: Column coordinate
        row: Row coordinate

    Returns:
        1 if tile should be shown, 0 if filtered out
        :param context:
    """
    r = row >> 1
    c = col >> 1

    # Population density filter
    if not (
        (context.dynamic_data[0] > context.dynamic_data[1])
        or (
            (x := context.pop_density[c][r]) >= context.dynamic_data[0]
            and x <= context.dynamic_data[1]
        )
    ):
        return 0

    # Rate of growth filter
    if not (
        (context.dynamic_data[2] > context.dynamic_data[3])
        or (
            (x := context.rate_og_mem[c >> 2][r >> 2])
            >= ((2 * context.dynamic_data[2]) - 256)
            and x <= ((2 * context.dynamic_data[3]) - 256)
        )
    ):
        return 0

    # Traffic density filter
    if not (
        (context.dynamic_data[4] > context.dynamic_data[5])
        or (
            (x := context.trf_density[c][r]) >= context.dynamic_data[4]
            and x <= context.dynamic_data[5]
        )
    ):
        return 0

    # Pollution filter
    if not (
        (context.dynamic_data[6] > context.dynamic_data[7])
        or (
            (x := context.pollution_mem[c][r]) >= context.dynamic_data[6]
            and x <= context.dynamic_data[7]
        )
    ):
        return 0

    # Crime filter
    if not (
        (context.dynamic_data[8] > context.dynamic_data[9])
        or (
            (x := context.crime_mem[c][r]) >= context.dynamic_data[8]
            and x <= context.dynamic_data[9]
        )
    ):
        return 0

    # Land value filter
    if not (
        (context.dynamic_data[10] > context.dynamic_data[11])
        or (
            (x := context.land_value_mem[c][r]) >= context.dynamic_data[10]
            and x <= context.dynamic_data[11]
        )
    ):
        return 0

    # Police effect filter
    if not (
        (context.dynamic_data[12] > context.dynamic_data[13])
        or (
            (x := context.police_map_effect[c >> 2][r >> 2]) >= context.dynamic_data[12]
            and x <= context.dynamic_data[13]
        )
    ):
        return 0

    # Fire rate filter
    if not (
        (context.dynamic_data[14] > context.dynamic_data[15])
        or (
            (x := context.fire_rate[c >> 2][r >> 2]) >= context.dynamic_data[14]
            and x <= context.dynamic_data[15]
        )
    ):
        return 0

    return 1
