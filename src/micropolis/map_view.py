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
from . import types
from . import macros
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    pygame = None

from typing import List, Optional, Callable, Any


# ============================================================================
# Value Mapping Constants
# ============================================================================

VAL_NONE = 0
VAL_LOW = 1
VAL_MEDIUM = 2
VAL_HIGH = 3
VAL_VERYHIGH = 4
VAL_PLUS = 5
VAL_VERYPLUS = 6
VAL_MINUS = 7
VAL_VERYMINUS = 8

# Color mapping arrays (pygame color indices)
valMap: List[int] = [
    -1,  # VAL_NONE
    types.COLOR_LIGHTGRAY,  # VAL_LOW
    types.COLOR_YELLOW,     # VAL_MEDIUM
    types.COLOR_ORANGE,     # VAL_HIGH
    types.COLOR_RED,        # VAL_VERYHIGH
    types.COLOR_DARKGREEN,  # VAL_PLUS
    types.COLOR_LIGHTGREEN, # VAL_VERYPLUS
    types.COLOR_ORANGE,     # VAL_MINUS
    types.COLOR_YELLOW      # VAL_VERYMINUS
]

# Grayscale mapping for monochrome displays
valGrayMap: List[int] = [
    -1,   # VAL_NONE
    31,   # VAL_LOW
    127,  # VAL_MEDIUM
    191,  # VAL_HIGH
    255,  # VAL_VERYHIGH
    223,  # VAL_PLUS
    255,  # VAL_VERYPLUS
    31,   # VAL_MINUS
    0     # VAL_VERYMINUS
]

# ============================================================================
# Map Procedure Array
# ============================================================================

# Forward declarations for map drawing functions
mapProcs: List[Optional[Callable]] = [None] * types.NMAPS


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
    if hasattr(view, 'x') and view.x and not view.x.color:
        # Grayscale mode
        color_value = valGrayMap[val]
        # Convert grayscale to RGB for pygame
        color = (color_value, color_value, color_value)
    else:
        # Color mode - map to pygame color
        color_index = valMap[val]
        if hasattr(view, 'pixels') and view.pixels and color_index < len(view.pixels):
            color_value = view.pixels[color_index]
            # Convert to RGB tuple for pygame
            color = (
                (color_value >> 16) & 0xFF,  # Red
                (color_value >> 8) & 0xFF,   # Green
                color_value & 0xFF           # Blue
            )
        else:
            # Fallback colors
            fallback_colors = [
                (0, 0, 0),        # VAL_NONE (black)
                (192, 192, 192),  # VAL_LOW (light gray)
                (255, 255, 0),    # VAL_MEDIUM (yellow)
                (255, 165, 0),    # VAL_HIGH (orange)
                (255, 0, 0),      # VAL_VERYHIGH (red)
                (0, 100, 0),      # VAL_PLUS (dark green)
                (144, 238, 144),  # VAL_VERYPLUS (light green)
                (255, 165, 0),    # VAL_MINUS (orange)
                (255, 255, 0)     # VAL_VERYMINUS (yellow)
            ]
            color = fallback_colors[val] if val < len(fallback_colors) else (0, 0, 0)

    # Ensure we have a valid surface to draw on
    if hasattr(view, 'surface') and view.surface:
        pygame.draw.rect(view.surface, color, (x, y, w, h))


# ============================================================================
# Map Drawing Functions
# ============================================================================

def drawAll(view: Any) -> None:
    """
    Draw the full map view showing all tiles.

    Args:
        view: SimView to render into
    """
    # For pygame implementation, we'll render tiles directly
    # This is a simplified version - full implementation would need tile graphics
    if hasattr(view, 'surface') and view.surface:
        # Clear surface with black
        view.surface.fill((0, 0, 0))

        # Draw a simple representation - in full implementation this would
        # render actual tile graphics from view.smalltiles
        for x in range(min(types.WORLD_X, view.m_width // 3)):
            for y in range(min(types.WORLD_Y, view.m_height // 3)):
                tile = types.Map[x][y] & macros.LOMASK
                if tile > 0:
                    # Simple tile representation - color based on tile type
                    color = (100, 100, 100)  # Default gray
                    if tile >= macros.RESBASE and tile < types.COMBASE:
                        color = (0, 255, 0)  # Residential - green
                    elif tile >= types.COMBASE and tile < types.INDBASE:
                        color = (0, 0, 255)  # Commercial - blue
                    elif tile >= types.INDBASE:
                        color = (255, 255, 0)  # Industrial - yellow

                    pygame.draw.rect(view.surface, color, (x * 3, y * 3, 3, 3))


def drawRes(view: Any) -> None:
    """
    Draw residential zones only.

    Args:
        view: SimView to render into
    """
    drawAll(view)
    # Filter to show only residential tiles
    if hasattr(view, 'surface') and view.surface:
        for x in range(min(types.WORLD_X, view.m_width // 3)):
            for y in range(min(types.WORLD_Y, view.m_height // 3)):
                tile = types.Map[x][y] & macros.LOMASK
                if tile > 422:  # Non-residential tile
                    # Draw black rectangle to hide non-residential tiles
                    pygame.draw.rect(view.surface, (0, 0, 0), (x * 3, y * 3, 3, 3))


def drawCom(view: Any) -> None:
    """
    Draw commercial zones only.

    Args:
        view: SimView to render into
    """
    drawAll(view)
    # Filter to show only commercial tiles
    if hasattr(view, 'surface') and view.surface:
        for x in range(min(types.WORLD_X, view.m_width // 3)):
            for y in range(min(types.WORLD_Y, view.m_height // 3)):
                tile = types.Map[x][y] & macros.LOMASK
                if (tile > 609) or ((tile >= 232) and (tile < 423)):  # Non-commercial tile
                    # Draw black rectangle to hide non-commercial tiles
                    pygame.draw.rect(view.surface, (0, 0, 0), (x * 3, y * 3, 3, 3))


def drawInd(view: Any) -> None:
    """
    Draw industrial zones only.

    Args:
        view: SimView to render into
    """
    drawAll(view)
    # Filter to show only industrial tiles
    if hasattr(view, 'surface') and view.surface:
        for x in range(min(types.WORLD_X, view.m_width // 3)):
            for y in range(min(types.WORLD_Y, view.m_height // 3)):
                tile = types.Map[x][y] & macros.LOMASK
                if (((tile >= 240) and (tile <= 611)) or
                    ((tile >= 693) and (tile <= 851)) or
                    ((tile >= 860) and (tile <= 883)) or
                    (tile >= 932)):  # Non-industrial tile
                    # Draw black rectangle to hide non-industrial tiles
                    pygame.draw.rect(view.surface, (0, 0, 0), (x * 3, y * 3, 3, 3))


def drawPower(view: Any) -> None:
    """
    Draw power grid view showing powered/unpowered zones.

    Args:
        view: SimView to render into
    """
    if not (hasattr(view, 'surface') and view.surface):
        return

    # Color definitions for power view
    UNPOWERED = types.COLOR_LIGHTBLUE
    POWERED = types.COLOR_RED
    CONDUCTIVE = types.COLOR_LIGHTGRAY

    # Get color values
    if hasattr(view, 'x') and view.x and not view.x.color:
        # Grayscale mode
        powered_color = (255, 255, 255)    # White
        unpowered_color = (0, 0, 0)        # Black
        conductive_color = (127, 127, 127) # Gray
    else:
        # Color mode
        powered_color = (255, 0, 0)        # Red
        unpowered_color = (173, 216, 230)  # Light blue
        conductive_color = (211, 211, 211) # Light gray

    view.surface.fill((0, 0, 0))  # Clear background

    for x in range(min(types.WORLD_X, view.m_width // 3)):
        for y in range(min(types.WORLD_Y, view.m_height // 3)):
            tile = types.Map[x][y]

            if (tile & macros.LOMASK) >= types.TILE_COUNT:
                tile -= types.TILE_COUNT

            tile_val = tile & macros.LOMASK

            if tile_val <= 63:
                # Terrain tile - show normally
                color = (100, 100, 100)  # Gray
            elif tile & macros.ZONEBIT:
                # Zone tile - show power status
                if tile & types.PWRBIT:
                    color = powered_color
                else:
                    color = unpowered_color
            else:
                # Infrastructure tile
                if tile & types.CONDBIT:
                    color = conductive_color
                else:
                    color = (0, 0, 0)  # Black for non-conductive

            pygame.draw.rect(view.surface, color, (x * 3, y * 3, 3, 3))


def drawLilTransMap(view: Any) -> None:
    """
    Draw transportation map (roads/rails) only.

    Args:
        view: SimView to render into
    """
    drawAll(view)
    # Filter to show only transportation tiles
    if hasattr(view, 'surface') and view.surface:
        for x in range(min(types.WORLD_X, view.m_width // 3)):
            for y in range(min(types.WORLD_Y, view.m_height // 3)):
                tile = types.Map[x][y] & macros.LOMASK
                if ((tile >= 240) or
                    ((tile >= 207) and tile <= 220) or
                    (tile == 223)):  # Non-transportation tile
                    # Draw black rectangle to hide non-transportation tiles
                    pygame.draw.rect(view.surface, (0, 0, 0), (x * 3, y * 3, 3, 3))


def drawPopDensity(view: Any) -> None:
    """
    Draw population density overlay.

    Args:
        view: SimView to render into
    """
    drawAll(view)

    # Draw population density overlay
    for x in range(min(types.HWLDX, view.m_width // 6)):
        for y in range(min(types.HWLDY, view.m_height // 6)):
            val = GetCI(types.PopDensity[x][y])
            maybeDrawRect(view, val, x * 6, y * 6, 6, 6)


def drawRateOfGrowth(view: Any) -> None:
    """
    Draw rate of growth overlay.

    Args:
        view: SimView to render into
    """
    drawAll(view)

    # Draw rate of growth overlay
    for x in range(min(types.SmX, view.m_width // 24)):
        for y in range(min(types.SmY, view.m_height // 24)):
            z = types.RateOGMem[x][y]
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


def drawTrafMap(view: Any) -> None:
    """
    Draw traffic density overlay.

    Args:
        view: SimView to render into
    """
    drawLilTransMap(view)

    # Draw traffic density overlay
    for x in range(min(types.HWLDX, view.m_width // 6)):
        for y in range(min(types.HWLDY, view.m_height // 6)):
            val = GetCI(types.TrfDensity[x][y])
            maybeDrawRect(view, val, x * 6, y * 6, 6, 6)


def drawPolMap(view: Any) -> None:
    """
    Draw pollution overlay.

    Args:
        view: SimView to render into
    """
    drawAll(view)

    # Draw pollution overlay
    for x in range(min(types.HWLDX, view.m_width // 6)):
        for y in range(min(types.HWLDY, view.m_height // 6)):
            val = GetCI(10 + types.PollutionMem[x][y])
            maybeDrawRect(view, val, x * 6, y * 6, 6, 6)


def drawCrimeMap(view: Any) -> None:
    """
    Draw crime overlay.

    Args:
        view: SimView to render into
    """
    drawAll(view)

    # Draw crime overlay
    for x in range(min(types.HWLDX, view.m_width // 6)):
        for y in range(min(types.HWLDY, view.m_height // 6)):
            val = GetCI(types.CrimeMem[x][y])
            maybeDrawRect(view, val, x * 6, y * 6, 6, 6)


def drawLandMap(view: Any) -> None:
    """
    Draw land value overlay.

    Args:
        view: SimView to render into
    """
    drawAll(view)

    # Draw land value overlay
    for x in range(min(types.HWLDX, view.m_width // 6)):
        for y in range(min(types.HWLDY, view.m_height // 6)):
            val = GetCI(types.LandValueMem[x][y])
            maybeDrawRect(view, val, x * 6, y * 6, 6, 6)


def drawFireRadius(view: Any) -> None:
    """
    Draw fire station coverage overlay.

    Args:
        view: SimView to render into
    """
    drawAll(view)

    # Draw fire radius overlay
    for x in range(min(types.SmX, view.m_width // 24)):
        for y in range(min(types.SmY, view.m_height // 24)):
            val = GetCI(types.FireRate[x][y])
            maybeDrawRect(view, val, x * 24, y * 24, 24, 24)


def drawPoliceRadius(view: Any) -> None:
    """
    Draw police station coverage overlay.

    Args:
        view: SimView to render into
    """
    drawAll(view)

    # Draw police radius overlay
    for x in range(min(types.SmX, view.m_width // 24)):
        for y in range(min(types.SmY, view.m_height // 24)):
            val = GetCI(types.PoliceMapEffect[x][y])
            maybeDrawRect(view, val, x * 24, y * 24, 24, 24)


def drawDynamic(view: Any) -> None:
    """
    Draw dynamic filter view based on multiple criteria.

    Args:
        view: SimView to render into
    """
    drawAll(view)

    # Apply dynamic filtering
    if hasattr(view, 'surface') and view.surface:
        for x in range(min(types.WORLD_X, view.m_width // 3)):
            for y in range(min(types.WORLD_Y, view.m_height // 3)):
                tile = types.Map[x][y] & macros.LOMASK
                if tile > 63:  # Only filter non-terrain tiles
                    if not dynamicFilter(x, y):
                        # Hide tiles that don't match dynamic criteria
                        pygame.draw.rect(view.surface, (0, 0, 0), (x * 3, y * 3, 3, 3))


def dynamicFilter(col: int, row: int) -> bool:
    """
    Apply dynamic filtering based on multiple city data criteria.

    Args:
        col, row: World coordinates

    Returns:
        True if tile should be visible, False otherwise
    """
    r = row >> 1  # Convert to overlay coordinates
    c = col >> 1

    # Check population density
    pop_check = ((types.DynamicData[0] > types.DynamicData[1]) or
                 ((types.PopDensity[c][r] >= types.DynamicData[0]) and
                  (types.PopDensity[c][r] <= types.DynamicData[1])))

    # Check rate of growth
    rate_check = ((types.DynamicData[2] > types.DynamicData[3]) or
                  ((types.RateOGMem[c >> 2][r >> 2] >= ((2 * types.DynamicData[2]) - 256)) and
                   (types.RateOGMem[c >> 2][r >> 2] <= ((2 * types.DynamicData[3]) - 256))))

    # Check traffic density
    traffic_check = ((types.DynamicData[4] > types.DynamicData[5]) or
                     ((types.TrfDensity[c][r] >= types.DynamicData[4]) and
                      (types.TrfDensity[c][r] <= types.DynamicData[5])))

    # Check pollution
    pollution_check = ((types.DynamicData[6] > types.DynamicData[7]) or
                       ((types.PollutionMem[c][r] >= types.DynamicData[6]) and
                        (types.PollutionMem[c][r] <= types.DynamicData[7])))

    # Check crime
    crime_check = ((types.DynamicData[8] > types.DynamicData[9]) or
                   ((types.CrimeMem[c][r] >= types.DynamicData[8]) and
                    (types.CrimeMem[c][r] <= types.DynamicData[9])))

    # Check land value
    land_check = ((types.DynamicData[10] > types.DynamicData[11]) or
                  ((types.LandValueMem[c][r] >= types.DynamicData[10]) and
                   (types.LandValueMem[c][r] <= types.DynamicData[11])))

    # Check police coverage
    police_check = ((types.DynamicData[12] > types.DynamicData[13]) or
                    ((types.PoliceMapEffect[c >> 2][r >> 2] >= types.DynamicData[12]) and
                     (types.PoliceMapEffect[c >> 2][r >> 2] <= types.DynamicData[13])))

    # Check fire coverage
    fire_check = ((types.DynamicData[14] > types.DynamicData[15]) or
                  ((types.FireRate[c >> 2][r >> 2] >= types.DynamicData[14]) and
                   (types.FireRate[c >> 2][r >> 2] <= types.DynamicData[15])))

    return pop_check and rate_check and traffic_check and pollution_check and crime_check and land_check and police_check and fire_check


def ditherMap(view: Any) -> None:
    """
    Apply dithering to convert color map to grayscale for monochrome displays.

    Args:
        view: SimView containing the map data to dither
    """
    # This is a simplified dithering implementation
    # Full implementation would need to handle the complex error diffusion
    # algorithm from the original C code

    if not (hasattr(view, 'surface') and view.surface):
        return

    # For now, just ensure we're working with a valid surface
    # The original C code did complex error diffusion dithering
    # For pygame, we might handle this differently or skip it
    pass


def MemDrawMap(view: Any) -> None:
    """
    Main map drawing function that dispatches to the appropriate drawing function
    based on the current map state.

    Args:
        view: SimView to render the map into
    """
    # Call the appropriate drawing function
    if view.map_state < len(mapProcs) and mapProcs[view.map_state]:
        mapProcs[view.map_state](view)

    # Apply dithering if needed for monochrome displays
    if hasattr(view, 'x') and view.x and not view.x.color:
        ditherMap(view)


def setUpMapProcs() -> None:
    """
    Initialize the map procedure array with all drawing functions.
    """
    global mapProcs

    mapProcs[types.ALMAP] = drawAll
    mapProcs[types.REMAP] = drawRes
    mapProcs[types.COMAP] = drawCom
    mapProcs[types.INMAP] = drawInd
    mapProcs[types.PRMAP] = drawPower
    mapProcs[types.RDMAP] = drawLilTransMap
    mapProcs[types.PDMAP] = drawPopDensity
    mapProcs[types.RGMAP] = drawRateOfGrowth
    mapProcs[types.TDMAP] = drawTrafMap
    mapProcs[types.PLMAP] = drawPolMap
    mapProcs[types.CRMAP] = drawCrimeMap
    mapProcs[types.LVMAP] = drawLandMap
    mapProcs[types.FIMAP] = drawFireRadius
    mapProcs[types.POMAP] = drawPoliceRadius
    mapProcs[types.DYMAP] = drawDynamic


# ============================================================================
# Initialization
# ============================================================================

# Set up the map procedures when module is imported
setUpMapProcs()