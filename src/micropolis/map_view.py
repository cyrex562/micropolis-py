"""
map_view.py - Map overview rendering for Micropolis Python port

This module implements map overview visualization that displays various city data
overlays (population density, traffic, pollution, crime, etc.) using pygame graphics.
Ported from g_map.c with pygame-compatible rendering instead of X11.

Key features:
- 15 different map overlay types (ALMAP through DYMAP)
- Value-based color mapping for data intensity visualization
- Dithering algorithms for grayscale displays
- Pygame surface rendering instead of X11 pixmaps
"""

# Import local modules
from typing import Any

import pygame

from src.micropolis.constants import VAL_NONE, VAL_LOW, VAL_MEDIUM, VAL_HIGH, VAL_VERYHIGH, valGrayMap, valMap, WORLD_X, \
    WORLD_Y, \
    LOMASK, RESBASE, COMBASE, INDBASE, TILE_COUNT, ZONEBIT, PWRBIT, CONDBIT, HWLDX, HWLDY, SM_X, SM_Y, \
    VAL_VERYPLUS, VAL_PLUS, VAL_VERYMINUS, VAL_MINUS, ALMAP, REMAP, COMAP, INMAP, PRMAP, RDMAP, PDMAP, RGMAP, TDMAP, \
    PLMAP, CRMAP, LVMAP, FIMAP, POMAP, DYMAP
from src.micropolis.context import AppContext


# ============================================================================
# Map Procedure Array
# ============================================================================




# ============================================================================
# Utility Functions
# ============================================================================


def GetCI(x: int) -> int:
    """
    Get color intensity value based on data value.
    Maps data values to VAL_NONE through VAL_VERYHIGH categories.

    Args:
        x: Data value to classify

    Returns:
        Color intensity category (VAL_NONE to VAL_VERYHIGH)
    """
    if x < 50:
        return VAL_NONE
    elif x < 100:
        return VAL_LOW
    elif x < 150:
        return VAL_MEDIUM
    elif x < 200:
        return VAL_HIGH
    else:
        return VAL_VERYHIGH


def maybeDrawRect(view: Any, val: int, x: int, y: int, w: int, h: int) -> None:
    """
    Draw a rectangle if the value is not VAL_NONE.

    Args:
        view: SimView containing rendering context
        val: Color intensity value
        x, y: Position coordinates
        w, h: Width and height
    """
    if val == VAL_NONE:
        return

    # Use pygame-compatible drawing
    drawRect(view, val, x, y, w, h)


def drawRect(view: Any, val: int, x: int, y: int, w: int, h: int) -> None:
    """
    Draw a colored rectangle on the view surface.

    Args:
        view: SimView containing pygame surface
        val: Color intensity value
        x, y: Position coordinates
        w, h: Width and height
    """
    # Get the color value
    if hasattr(view, "x") and view.x and not view.x.color:
        # Grayscale mode
        color_value = valGrayMap[val]
        # Convert grayscale to RGB for pygame
        color = (color_value, color_value, color_value)
    else:
        # Color mode - map to pygame color
        color_index = valMap[val]
        if hasattr(view, "pixels") and view.pixels and color_index < len(view.pixels):
            color_value = view.pixels[color_index]
            # Convert to RGB tuple for pygame
            color = (
                (color_value >> 16) & 0xFF,  # Red
                (color_value >> 8) & 0xFF,  # Green
                color_value & 0xFF,  # Blue
            )
        else:
            # Fallback colors
            fallback_colors = [
                (0, 0, 0),  # VAL_NONE (black)
                (192, 192, 192),  # VAL_LOW (light gray)
                (255, 255, 0),  # VAL_MEDIUM (yellow)
                (255, 165, 0),  # VAL_HIGH (orange)
                (255, 0, 0),  # VAL_VERYHIGH (red)
                (0, 100, 0),  # VAL_PLUS (dark green)
                (144, 238, 144),  # VAL_VERYPLUS (light green)
                (255, 165, 0),  # VAL_MINUS (orange)
                (255, 255, 0),  # VAL_VERYMINUS (yellow)
            ]
            color = fallback_colors[val] if val < len(fallback_colors) else (0, 0, 0)

    # Ensure we have a valid surface to draw on
    if hasattr(view, "surface") and view.surface:
        pygame.draw.rect(view.surface, color, (x, y, w, h))


# ============================================================================
# Map Drawing Functions
# ============================================================================


def drawAll(context: AppContext, view: Any) -> None:
    """
    Draw the full map view showing all tiles.

    Args:
        view: SimView to render into
    """
    # For pygame implementation, we'll render tiles directly
    # This is a simplified version - full implementation would need tile graphics
    if hasattr(view, "surface") and view.surface:
        # Clear surface with black
        view.surface.fill((0, 0, 0))

        # Draw a simple representation - in full implementation this would
        # render actual tile graphics from view.smalltiles
        for x in range(min(WORLD_X, view.m_width // 3)):
            for y in range(min(WORLD_Y, view.m_height // 3)):
                tile = context.map_data[x][y] & LOMASK
                if tile > 0:
                    # Simple tile representation - color based on tile type
                    color = (100, 100, 100)  # Default gray
                    if RESBASE <= tile < COMBASE:
                        color = (0, 255, 0)  # Residential - green
                    elif COMBASE <= tile < INDBASE:
                        color = (0, 0, 255)  # Commercial - blue
                    elif tile >= INDBASE:
                        color = (255, 255, 0)  # Industrial - yellow

                    pygame.draw.rect(view.surface, color, (x * 3, y * 3, 3, 3))


def drawRes(context: AppContext, view: Any) -> None:
    """
    Draw residential zones only.

    Args:
        view: SimView to render into
        :param context:
    """
    drawAll(context, view)
    # Filter to show only residential tiles
    if hasattr(view, "surface") and view.surface:
        for x in range(min(WORLD_X, view.m_width // 3)):
            for y in range(min(WORLD_Y, view.m_height // 3)):
                tile = context.map_data[x][y] & LOMASK
                if tile > 422:  # Non-residential tile
                    # Draw black rectangle to hide non-residential tiles
                    pygame.draw.rect(view.surface, (0, 0, 0), (x * 3, y * 3, 3, 3))


def drawCom(context: AppContext, view: Any) -> None:
    """
    Draw commercial zones only.

    Args:
        view: SimView to render into
        :param context:
    """
    drawAll(context, view)
    # Filter to show only commercial tiles
    if hasattr(view, "surface") and view.surface:
        for x in range(min(WORLD_X, view.m_width // 3)):
            for y in range(min(WORLD_Y, view.m_height // 3)):
                tile = context.map_data[x][y] & LOMASK
                if (tile > 609) or (
                    (tile >= 232) and (tile < 423)
                ):  # Non-commercial tile
                    # Draw black rectangle to hide non-commercial tiles
                    pygame.draw.rect(view.surface, (0, 0, 0), (x * 3, y * 3, 3, 3))


def drawInd(context: AppContext, view: Any) -> None:
    """
    Draw industrial zones only.

    Args:
        view: SimView to render into
        :param context:
    """
    drawAll(context, view)
    # Filter to show only industrial tiles
    if hasattr(view, "surface") and view.surface:
        for x in range(min(WORLD_X, view.m_width // 3)):
            for y in range(min(WORLD_Y, view.m_height // 3)):
                tile = context.map_data[x][y] & LOMASK
                if (
                    ((tile >= 240) and (tile <= 611))
                    or ((tile >= 693) and (tile <= 851))
                    or ((tile >= 860) and (tile <= 883))
                    or (tile >= 932)
                ):  # Non-industrial tile
                    # Draw black rectangle to hide non-industrial tiles
                    pygame.draw.rect(view.surface, (0, 0, 0), (x * 3, y * 3, 3, 3))


def drawPower(context: AppContext, view: Any) -> None:
    """
    Draw power grid view showing powered/unpowered zones.

    Args:
        view: SimView to render into
        :param context:
    """
    if not (hasattr(view, "surface") and view.surface):
        return



    # Get color values
    if hasattr(view, "x") and view.x and not view.x.color:
        # Grayscale mode
        powered_color = (255, 255, 255)  # White
        unpowered_color = (0, 0, 0)  # Black
        conductive_color = (127, 127, 127)  # Gray
    else:
        # Color mode
        powered_color = (255, 0, 0)  # Red
        unpowered_color = (173, 216, 230)  # Light blue
        conductive_color = (211, 211, 211)  # Light gray

    view.surface.fill((0, 0, 0))  # Clear background

    for x in range(min(WORLD_X, view.m_width // 3)):
        for y in range(min(WORLD_Y, view.m_height // 3)):
            tile = context.map_data[x][y]

            if (tile & LOMASK) >= TILE_COUNT:
                tile -= TILE_COUNT

            tile_val = tile & LOMASK

            if tile_val <= 63:
                # Terrain tile - show normally
                color = (100, 100, 100)  # Gray
            elif tile & ZONEBIT:
                # Zone tile - show power status
                if tile & PWRBIT:
                    color = powered_color
                else:
                    color = unpowered_color
            else:
                # Infrastructure tile
                if tile & CONDBIT:
                    color = conductive_color
                else:
                    color = (0, 0, 0)  # Black for non-conductive

            pygame.draw.rect(view.surface, color, (x * 3, y * 3, 3, 3))


def drawLilTransMap(context: AppContext, view: Any) -> None:
    """
    Draw transportation map (roads/rails) only.

    Args:
        view: SimView to render into
        :param context:
    """
    drawAll(context, view)
    # Filter to show only transportation tiles
    if hasattr(view, "surface") and view.surface:
        for x in range(min(WORLD_X, view.m_width // 3)):
            for y in range(min(WORLD_Y, view.m_height // 3)):
                tile = context.map_data[x][y] & LOMASK
                if (
                    (tile >= 240) or ((tile >= 207) and tile <= 220) or (tile == 223)
                ):  # Non-transportation tile
                    # Draw black rectangle to hide non-transportation tiles
                    pygame.draw.rect(view.surface, (0, 0, 0), (x * 3, y * 3, 3, 3))


def drawPopDensity(context: AppContext, view: Any) -> None:
    """
    Draw population density overlay.

    Args:
        view: SimView to render into
        :param context:
    """
    drawAll(context, view)

    # Draw population density overlay
    for x in range(min(HWLDX, view.m_width // 6)):
        for y in range(min(HWLDY, view.m_height // 6)):
            val = GetCI(context.pop_density[x][y])
            maybeDrawRect(view, val, x * 6, y * 6, 6, 6)


def drawRateOfGrowth(context: AppContext, view: Any) -> None:
    """
    Draw rate of growth overlay.

    Args:
        view: SimView to render into
        :param context:
    """
    drawAll(context, view)

    # Draw rate of growth overlay
    for x in range(min(SM_X, view.m_width // 24)):
        for y in range(min(SM_Y, view.m_height // 24)):
            z = context.rate_og_mem[x][y]
            if z > 100:
                val = VAL_VERYPLUS
            elif z > 20:
                val = VAL_PLUS
            elif z < -100:
                val = VAL_VERYMINUS
            elif z < -20:
                val = VAL_MINUS
            else:
                val = VAL_NONE

            maybeDrawRect(view, val, x * 24, y * 24, 24, 24)


def drawTrafMap(context: AppContext, view: Any) -> None:
    """
    Draw traffic density overlay.

    Args:
        view: SimView to render into
        :param context:
    """
    drawLilTransMap(context, view)

    # Draw traffic density overlay
    for x in range(min(HWLDX, view.m_width // 6)):
        for y in range(min(HWLDY, view.m_height // 6)):
            val = GetCI(context.trf_density[x][y])
            maybeDrawRect(view, val, x * 6, y * 6, 6, 6)


def drawPolMap(context: AppContext, view: Any) -> None:
    """
    Draw pollution overlay.

    Args:
        view: SimView to render into
        :param context:
    """
    drawAll(context, view)

    # Draw pollution overlay
    for x in range(min(HWLDX, view.m_width // 6)):
        for y in range(min(HWLDY, view.m_height // 6)):
            val = GetCI(10 + context.pollution_mem[x][y])
            maybeDrawRect(view, val, x * 6, y * 6, 6, 6)


def drawCrimeMap(context: AppContext, view: Any) -> None:
    """
    Draw crime overlay.

    Args:
        view: SimView to render into
        :param context:
    """
    drawAll(context, view)

    # Draw crime overlay
    for x in range(min(HWLDX, view.m_width // 6)):
        for y in range(min(HWLDY, view.m_height // 6)):
            val = GetCI(context.crime_mem[x][y])
            maybeDrawRect(view, val, x * 6, y * 6, 6, 6)


def drawLandMap(context: AppContext, view: Any) -> None:
    """
    Draw land value overlay.

    Args:
        view: SimView to render into
        :param context:
    """
    drawAll(context, view)

    # Draw land value overlay
    for x in range(min(HWLDX, view.m_width // 6)):
        for y in range(min(HWLDY, view.m_height // 6)):
            val = GetCI(context.land_value_mem[x][y])
            maybeDrawRect(view, val, x * 6, y * 6, 6, 6)


def drawFireRadius(context: AppContext, view: Any) -> None:
    """
    Draw fire station coverage overlay.

    Args:
        view: SimView to render into
        :param context:
    """
    drawAll(context, view)

    # Draw fire radius overlay
    for x in range(min(SM_X, view.m_width // 24)):
        for y in range(min(SM_Y, view.m_height // 24)):
            val = GetCI(context.fire_rate[x][y])
            maybeDrawRect(view, val, x * 24, y * 24, 24, 24)


def drawPoliceRadius(context: AppContext, view: Any) -> None:
    """
    Draw police station coverage overlay.

    Args:
        view: SimView to render into
        :param context:
    """
    drawAll(context, view)

    # Draw police radius overlay
    for x in range(min(SM_X, view.m_width // 24)):
        for y in range(min(SM_Y, view.m_height // 24)):
            val = GetCI(context.police_map_effect[x][y])
            maybeDrawRect(view, val, x * 24, y * 24, 24, 24)


def drawDynamic(context: AppContext, view: Any) -> None:
    """
    Draw dynamic filter view based on multiple criteria.

    Args:
        view: SimView to render into
        :param context:
    """
    drawAll(context, view)

    # Apply dynamic filtering
    if hasattr(view, "surface") and view.surface:
        for x in range(min(WORLD_X, view.m_width // 3)):
            for y in range(min(WORLD_Y, view.m_height // 3)):
                tile = context.map_data[x][y] & LOMASK
                if tile > 63:  # Only filter non-terrain tiles
                    if not dynamicFilter(context, x, y):
                        # Hide tiles that don't match dynamic criteria
                        pygame.draw.rect(view.surface, (0, 0, 0), (x * 3, y * 3, 3, 3))


def dynamicFilter(context: AppContext, col: int, row: int) -> bool:
    """
    Apply dynamic filtering based on multiple city data criteria.

    Args:
        col, row: World coordinates

    Returns:
        True if tile should be visible, False otherwise
        :param context:
    """
    r = row >> 1  # Convert to overlay coordinates
    c = col >> 1

    # Check population density
    pop_check = (context.dynamic_data[0] > context.dynamic_data[1]) or (
        (context.pop_density[c][r] >= context.dynamic_data[0])
        and (context.pop_density[c][r] <= context.dynamic_data[1])
    )

    # Check rate of growth
    rate_check = (context.dynamic_data[2] > context.dynamic_data[3]) or (
        (context.rate_og_mem[c >> 2][r >> 2] >= ((2 * context.dynamic_data[2]) - 256))
        and (context.rate_og_mem[c >> 2][r >> 2] <= ((2 * context.dynamic_data[3]) - 256))
    )

    # Check traffic density
    traffic_check = (context.dynamic_data[4] > context.dynamic_data[5]) or (
        (context.trf_density[c][r] >= context.dynamic_data[4])
        and (context.trf_density[c][r] <= context.dynamic_data[5])
    )

    # Check pollution
    pollution_check = (context.dynamic_data[6] > context.dynamic_data[7]) or (
        (context.pollution_mem[c][r] >= context.dynamic_data[6])
        and (context.pollution_mem[c][r] <= context.dynamic_data[7])
    )

    # Check crime
    crime_check = (context.dynamic_data[8] > context.dynamic_data[9]) or (
        (context.crime_mem[c][r] >= context.dynamic_data[8])
        and (context.crime_mem[c][r] <= context.dynamic_data[9])
    )

    # Check land value
    land_check = (context.dynamic_data[10] > context.dynamic_data[11]) or (
        (context.land_value_mem[c][r] >= context.dynamic_data[10])
        and (context.land_value_mem[c][r] <= context.dynamic_data[11])
    )

    # Check police coverage
    police_check = (context.dynamic_data[12] > context.dynamic_data[13]) or (
        (context.police_map_effect[c >> 2][r >> 2] >= context.dynamic_data[12])
        and (context.police_map_effect[c >> 2][r >> 2] <= context.dynamic_data[13])
    )

    # Check fire coverage
    fire_check = (context.dynamic_data[14] > context.dynamic_data[15]) or (
        (context.fire_rate[c >> 2][r >> 2] >= context.dynamic_data[14])
        and (context.fire_rate[c >> 2][r >> 2] <= context.dynamic_data[15])
    )

    return (
        pop_check
        and rate_check
        and traffic_check
        and pollution_check
        and crime_check
        and land_check
        and police_check
        and fire_check
    )


def ditherMap(view: Any) -> None:
    """
    Apply dithering to convert color map to grayscale for monochrome displays.

    Args:
        view: SimView containing the map data to dither
    """
    # This is a simplified dithering implementation
    # Full implementation would need to handle the complex error diffusion
    # algorithm from the original C code

    if not (hasattr(view, "surface") and view.surface):
        return

    # For now, just ensure we're working with a valid surface
    # The original C code did complex error diffusion dithering
    # For pygame, we might handle this differently or skip it
    pass


def MemDrawMap(context: AppContext, view: Any) -> None:
    """
    Main map drawing function that dispatches to the appropriate drawing function
    based on the current map state.

    Args:
        view: SimView to render the map into
        :param context:
    """
    # Call the appropriate drawing function
    if view.map_state < len(context.mapProcs) and context.mapProcs[view.map_state]:
        context.mapProcs[view.map_state](view)

    # Apply dithering if needed for monochrome displays
    if hasattr(view, "x") and view.x and not view.x.color:
        ditherMap(view)


def setUpMapProcs(context: AppContext) -> None:
    """
    Initialize the map procedure array with all drawing functions.
    :param context:
    """
    # global mapProcs

    context.mapProcs[ALMAP] = drawAll
    context.mapProcs[REMAP] = drawRes
    context.mapProcs[COMAP] = drawCom
    context.mapProcs[INMAP] = drawInd
    context.mapProcs[PRMAP] = drawPower
    context.mapProcs[RDMAP] = drawLilTransMap
    context.mapProcs[PDMAP] = drawPopDensity
    context.mapProcs[RGMAP] = drawRateOfGrowth
    context.mapProcs[TDMAP] = drawTrafMap
    context.mapProcs[PLMAP] = drawPolMap
    context.mapProcs[CRMAP] = drawCrimeMap
    context.mapProcs[LVMAP] = drawLandMap
    context.mapProcs[FIMAP] = drawFireRadius
    context.mapProcs[POMAP] = drawPoliceRadius
    context.mapProcs[DYMAP] = drawDynamic


# ============================================================================
# Initialization
# ============================================================================

# Set up the map procedures when module is imported
# TODO: call setupMapProcs in actual init function of game instead of when imported
# setUpMapProcs(context)
