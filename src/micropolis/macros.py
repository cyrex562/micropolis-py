# macros.py: Core macros and utility functions for Micropolis Python port
#
# This module provides utility functions that were originally implemented as
# C macros in the Micropolis simulation engine. These functions handle common
# operations like bounds checking, tile type testing, and basic math utilities.
#
# Original C header: headers/macros.h
# Ported to maintain compatibility with Micropolis simulation logic

from collections.abc import Iterator

# Re-export selected constants from the canonical constants module so
# legacy code/tests that import values from `micropolis.macros` (e.g.
# `macros.ANIMBIT`) continue to work during the incremental AppContext
# migration. We intentionally list exported names explicitly to satisfy
# linters and make the compatibility surface obvious.
from . import constants as _const

# Explicit names exported by this compatibility shim. Keep in sync with
# values actually referenced across the codebase/tests.
ANIMBIT = _const.ANIMBIT
ALLBITS = _const.ALLBITS
LOMASK = _const.LOMASK
WORLD_X = _const.WORLD_X
WORLD_Y = _const.WORLD_Y
HWLDX = _const.HWLDX
HWLDY = _const.HWLDY

# Tile/base constants used throughout code and tests
RESBASE = _const.RESBASE
COMBASE = _const.COMBASE
INDBASE = _const.INDBASE
ROADBASE = _const.ROADBASE
RAILBASE = _const.RAILBASE
LASTROAD = _const.LASTROAD
POWERBASE = _const.POWERBASE
LASTRAIL = _const.LASTRAIL
RAILHPOWERV = _const.RAILHPOWERV
LHTHR = _const.LHTHR
PORT = _const.PORT
PORTBASE = _const.PORTBASE
AIRPORT = _const.AIRPORT

# Zone/status/range constants
ZONEBIT = _const.ZONEBIT
PWRBIT = _const.PWRBIT
BULLBIT = _const.BULLBIT
BURNBIT = _const.BURNBIT
RUBBLE = _const.RUBBLE
LASTRUBBLE = _const.LASTRUBBLE
DIRT = _const.DIRT
NUCLEAR = _const.NUCLEAR
FIRSTRIVEDGE = _const.FIRSTRIVEDGE
LASTRIVEDGE = _const.LASTRIVEDGE
LASTZONE = _const.LASTZONE

# Downsampled overlay dimensions
HWLDX = _const.HWLDX
HWLDY = _const.HWLDY

# Expose the animation table for any callers that need it
ani_tile = _const.ani_tile

__all__ = [
    # basic masks
    "ANIMBIT",
    "ALLBITS",
    "LOMASK",
    # world dims
    "WORLD_X",
    "WORLD_Y",
    "HWLDX",
    "HWLDY",
    # tiles
    "RESBASE",
    "COMBASE",
    "INDBASE",
    "ROADBASE",
    "RAILBASE",
    "LASTROAD",
    "POWERBASE",
    "LASTRAIL",
    "RAILHPOWERV",
    "LHTHR",
    "PORT",
    "PORTBASE",
    "AIRPORT",
    # status bits
    "ZONEBIT",
    "PWRBIT",
    "BULLBIT",
    "BURNBIT",
    "RUBBLE",
    "LASTRUBBLE",
    "DIRT",
    "NUCLEAR",
    "FIRSTRIVEDGE",
    "LASTRIVEDGE",
    "LASTZONE",
    # animation table
    "ani_tile",
]


# ============================================================================
# Basic Math Utilities
# ============================================================================


def ABS(x: int) -> int:
    """
    Absolute value function (equivalent to C macro ABS).

    Args:
        x: Integer value

    Returns:
        Absolute value of x
    """
    return abs(x)


# ============================================================================
# Coordinate and Bounds Checking
# ============================================================================

# World dimensions (imported from types to maintain a single source of truth)
# WORLD_X = micropolis.constants.WORLD_X
# WORLD_Y = micropolis.constants.WORLD_Y

# Half world dimensions for downsampled maps
# HWLDX = micropolis.constants.HWLDX
# HWLDY = micropolis.constants.HWLDY


def TestBounds(x: int, y: int) -> bool:
    """
    Test if coordinates are within the world bounds.

    Args:
        x: X coordinate (0 to WORLD_X-1)
        y: Y coordinate (0 to WORLD_Y-1)

    Returns:
        True if coordinates are within bounds, False otherwise
    """
    return (x >= 0) and (x < WORLD_X) and (y >= 0) and (y < WORLD_Y)


def clamp_to_bounds(x: int, y: int) -> tuple[int, int]:
    """
    Clamp coordinates to world bounds.

    Args:
        x: X coordinate
        y: Y coordinate

    Returns:
        Tuple of clamped (x, y) coordinates
    """
    return max(0, min(x, WORLD_X - 1)), max(0, min(y, WORLD_Y - 1))


# ============================================================================
# Tile Type Checking Functions
# ============================================================================


# Tile ID constants (placeholder values)
# NUCLEAR = types.NUCLEAR
RBRDR = 0  # Residential zone start (placeholder until port complete)


# LASTZONE = types.LASTZONE
# RESBASE = types.RESBASE
# COMBASE = types.COMBASE
# INDBASE = types.INDBASE
# ROADBASE = types.ROADBASE
# RAILBASE = types.RAILBASE
# LASTROAD = types.LASTROAD
# POWERBASE = types.POWERBASE
# LASTRAIL = types.LASTRAIL
# RAILHPOWERV = types.RAILHPOWERV
# LHTHR = types.LHTHR
# FIRSTRIVEDGE = types.FIRSTRIVEDGE
# LASTRIVEDGE = types.LASTRIVEDGE
# DIRT = types.DIRT
# RUBBLE = types.RUBBLE
# LASTRUBBLE = types.LASTRUBBLE

# Disaster system constants
# FIRE = types.FIRE
# FLOOD = types.FLOOD
# RADTILE = types.RADTILE
# WOODS5 = types.WOODS5

# Building constants
# PORTBASE = types.PORTBASE
# PORT = types.PORT
# AIRPORT = types.AIRPORT


# River tile for monster spawning
# RIVER = types.RIVER


def TILE_IS_NUCLEAR(tile: int) -> bool:
    """
    Check if tile is a nuclear power plant.

    Args:
        tile: Tile ID with status bits

    Returns:
        True if tile is nuclear, False otherwise
    """
    return (tile & LOMASK) == NUCLEAR


def TILE_IS_VULNERABLE(tile: int) -> bool:
    """
    Check if tile is vulnerable to disasters (can be destroyed).

    Args:
        tile: Tile ID with status bits

    Returns:
        True if tile is vulnerable, False otherwise
    """
    return not (tile & ZONEBIT) and RBRDR <= (tile & LOMASK) <= LASTZONE


def TILE_IS_ARSONABLE(tile: int) -> bool:
    """
    Check if tile can be set on fire (arsonable).

    Args:
        tile: Tile ID with status bits

    Returns:
        True if tile can burn, False otherwise
    """
    return not (tile & ZONEBIT) and RBRDR <= (tile & LOMASK) <= LASTZONE


def TILE_IS_RIVER_EDGE(tile: int) -> bool:
    """
    Check if tile is a river edge.

    Args:
        tile: Tile ID with status bits

    Returns:
        True if tile is river edge, False otherwise
    """
    return FIRSTRIVEDGE <= (tile & LOMASK) <= LASTRIVEDGE


def TILE_IS_FLOODABLE(tile: int) -> bool:
    """
    Check if tile can be flooded (original floodable check).

    Args:
        tile: Tile ID with status bits

    Returns:
        True if tile can be flooded, False otherwise
    """
    return bool(tile == DIRT or ((tile & BULLBIT) and (tile & BURNBIT)))


def TILE_IS_RUBBLE(tile: int) -> bool:
    """
    Check if tile is rubble.

    Args:
        tile: Tile ID with status bits

    Returns:
        True if tile is rubble, False otherwise
    """
    return RUBBLE <= (tile & LOMASK) <= LASTRUBBLE


def TILE_IS_FLOODABLE2(tile: int) -> bool:
    """
    Check if tile can be flooded (alternative floodable check).

    Args:
        tile: Tile ID with status bits

    Returns:
        True if tile can be flooded, False otherwise
    """
    return bool(tile == 0 or (tile & BURNBIT) or TILE_IS_RUBBLE(tile))


# ============================================================================
# Utility Functions
# ============================================================================


def get_tile_base_id(tile: int) -> int:
    """
    Extract the base tile ID from a tile with status bits.

    Args:
        tile: Tile ID with status bits

    Returns:
        Base tile ID (low 12 bits)
    """
    return tile & LOMASK


def has_tile_status(tile: int, status_bit: int) -> bool:
    """
    Check if a tile has a specific status bit set.

    Args:
        tile: Tile ID with status bits
        status_bit: Status bit to check (e.g., ZONEBIT, BURNBIT)

    Returns:
        True if status bit is set, False otherwise
    """
    return (tile & status_bit) != 0


def set_tile_status(tile: int, status_bit: int) -> int:
    """
    Set a status bit on a tile.

    Args:
        tile: Tile ID with status bits
        status_bit: Status bit to set

    Returns:
        Tile with status bit set
    """
    return tile | status_bit


def clear_tile_status(tile: int, status_bit: int) -> int:
    """
    Clear a status bit from a tile.

    Args:
        tile: Tile ID with status bits
        status_bit: Status bit to clear

    Returns:
        Tile with status bit cleared
    """
    return tile & ~status_bit


# ============================================================================
# Coordinate Conversion Utilities
# ============================================================================


def world_to_screen_coords(
    world_x: int, world_y: int, tile_size: int = 16
) -> tuple[int, int]:
    """
    Convert world coordinates to screen coordinates.

    Args:
        world_x: World X coordinate
        world_y: World Y coordinate
        tile_size: Size of each tile in pixels (default 16 for editor view)

    Returns:
        Tuple of screen (x, y) coordinates
    """
    return world_x * tile_size, world_y * tile_size


def screen_to_world_coords(
    screen_x: int, screen_y: int, tile_size: int = 16
) -> tuple[int, int]:
    """
    Convert screen coordinates to world coordinates.

    Args:
        screen_x: Screen X coordinate
        screen_y: Screen Y coordinate
        tile_size: Size of each tile in pixels

    Returns:
        Tuple of world (x, y) coordinates
    """
    return screen_x // tile_size, screen_y // tile_size


# ============================================================================
# Range and Iteration Utilities
# ============================================================================


def iterate_world_coords() -> Iterator[tuple[int, int]]:
    """
    Generator that yields all valid world coordinates.

    Yields:
        Tuples of (x, y) coordinates for every position in the world
    """
    for y in range(WORLD_Y):
        for x in range(WORLD_X):
            yield x, y


def get_adjacent_coords(x: int, y: int, include_diagonals: bool = True) -> list:
    """
    Get coordinates of adjacent tiles.

    Args:
        x: Center X coordinate
        y: Center Y coordinate
        include_diagonals: Whether to include diagonal neighbors

    Returns:
        List of (x, y) tuples for adjacent coordinates within bounds
    """
    adjacent = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Cardinal directions

    if include_diagonals:
        directions.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])  # Diagonals

    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if TestBounds(nx, ny):
            adjacent.append((nx, ny))

    return adjacent
