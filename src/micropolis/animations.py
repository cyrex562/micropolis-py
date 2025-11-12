# animations.py: Tile animation system for Micropolis Python port
#
# This module handles tile animation for the Micropolis city simulation.
# It provides functions to animate tiles that have the ANIMBIT flag set,
# cycling through different visual states for dynamic elements like traffic,
# fires, and other animated city features.
#
# Original C source: src/sim/g_ani.c
# Animation tables: headers/animtab.h
# Ported to maintain compatibility with Micropolis animation system

from typing import Any

from . import animation, macros
from .constants import WORLD_X, WORLD_Y
from .context import AppContext


def animate_tiles(context: AppContext) -> None:
    """
    Animate all tiles in the world map that have the ANIMBIT flag set.

    This function iterates through the entire WORLD_X x WORLD_Y tile map
    and updates any tiles that are marked for animation. Animated tiles
    cycle through different visual states based on the ani_tile lookup table.

    The animation preserves tile flags (status bits) while updating the
    base tile ID to create the animation effect.

    Called from: moveWorld, doEditWindow, scoreDoer, doMapInFront, graphDoer
    """
    # Iterate through all tiles in the world map
    for x in range(WORLD_X):
        for y in range(WORLD_Y):
            tile_value = context.map_data[x][y]

            # Check if this tile should be animated
            if tile_value & macros.ANIMBIT:
                # Extract tile flags (upper bits including ANIMBIT)
                tile_flags = tile_value & macros.ALLBITS

                # Clear the low 10 bits to get the animation index
                tile_index = tile_value & macros.LOMASK

                # Look up the next animation frame
                # Note: Original C code had commented synchronization logic
                # that is not currently implemented
                if tile_index < len(animation.ani_tile):
                    new_tile_index = animation.ani_tile[tile_index]
                else:
                    new_tile_index = tile_index  # Fallback for invalid indices

                # Restore the flags and update the tile
                context.map_data[x][y] = new_tile_index | tile_flags


# ============================================================================
# Animation Statistics and Debugging
# ============================================================================


def count_animated_tiles(context: AppContext) -> int:
    """
    Count the total number of animated tiles in the world map.

    Returns:
        Number of tiles with ANIMBIT flag set
    """
    count = 0
    for x in range(macros.WORLD_X):
        for y in range(macros.WORLD_Y):
            if context.map_data[x][y] & macros.ANIMBIT:
                count += 1
    return count


def get_animated_tile_positions(context: AppContext) -> list[tuple[int, int]]:
    """
    Get a list of all positions containing animated tiles.

    Returns:
        List of (x, y) coordinate tuples for animated tiles
    """
    positions = []
    for x in range(macros.WORLD_X):
        for y in range(macros.WORLD_Y):
            if context.map_data[x][y] & macros.ANIMBIT:
                positions.append((x, y))
    return positions


def get_animation_info(context: AppContext,
                       x: int,
                       y: int) -> dict[str, Any] | None:
    """
    Get detailed animation information for a specific tile.

    Args:
        x: X coordinate (0 to WORLD_X-1)
        y: Y coordinate (0 to WORLD_Y-1)

    Returns:
        Dictionary with animation information, or None if not animated or out of bounds
        :rtype: dict[str, Any] | None
        :type context: AppContext
        :param context:
    """
    if not macros.TestBounds(x, y):
        return None

    tile_value = context.map_data[x][y]

    if not (tile_value & macros.ANIMBIT):
        return None

    tile_index = tile_value & macros.LOMASK
    tile_flags = tile_value & macros.ALLBITS

    return {
        "position": (x, y),
        "tile_value": tile_value,
        "tile_index": tile_index,
        "tile_flags": tile_flags,
        "is_animated": True,
        "category": animation.get_animation_category(tile_index),
        "sync_value": animation.get_animation_sync(tile_index),
    }
