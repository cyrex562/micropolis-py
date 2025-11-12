# animation.py: Animation tables and tile animation data for Micropolis Python port
#
# This module provides animation tables that control how tiles animate in the
# Micropolis city simulation. These tables define which tiles are animated,
# their animation sequences, and timing synchronization.
#
# Original C header: headers/animtab.h
# Ported to maintain compatibility with Micropolis animation system
from src.micropolis.constants import ani_tile, ani_synch


# ============================================================================
# Animation Tile Table
# ============================================================================




# ============================================================================
# Animation Synchronization Table
# ============================================================================





# ============================================================================
# Animation Utility Functions
# ============================================================================

def get_animated_tile(base_index: int, animation_frame: int = 0) -> int:
    """
    Get the actual tile ID for an animated tile at a specific frame.

    Args:
        base_index: Base animation index (0-1023)
        animation_frame: Current animation frame (0-7 typically)

    Returns:
        Actual tile ID to render
    """
    if 0 <= base_index < len(ani_tile):
        return ani_tile[base_index]
    return 0


def get_animation_sync(base_index: int) -> int:
    """
    Get the animation synchronization value for a tile.

    Args:
        base_index: Base animation index (0-1023)

    Returns:
        Animation sync value (0xff = no animation, other values control timing)
    """
    if 0 <= base_index < len(ani_synch):
        return ani_synch[base_index]
    return 0xff


def is_tile_animated(base_index: int) -> bool:
    """
    Check if a tile index represents an animated tile.

    Args:
        base_index: Base animation index (0-1023)

    Returns:
        True if tile is animated, False otherwise
    """
    sync = get_animation_sync(base_index)
    return sync != 0xff


def get_animation_phase(base_index: int, game_tick: int) -> int:
    """
    Calculate the current animation phase for an animated tile.

    Args:
        base_index: Base animation index (0-1023)
        game_tick: Current game tick/frame counter

    Returns:
        Animation phase (0-7 typically, depending on sync value)
    """
    sync = get_animation_sync(base_index)
    if sync == 0xff:
        return 0  # No animation

    # Use sync value to determine animation speed
    # Higher bits = slower animation
    if sync & 0x80:
        phase = (game_tick >> 3) & 0x7
    elif sync & 0x40:
        phase = (game_tick >> 2) & 0x7
    elif sync & 0x20:
        phase = (game_tick >> 1) & 0x7
    else:
        phase = game_tick & 0x7

    return phase


# ============================================================================
# Animation Categories
# ============================================================================

# Define ranges for different animation categories
ANIMATION_RANGES = {
    'fire': (56, 64),
    'no_traffic': (64, 80),
    'light_traffic': (80, 144),
    'heavy_traffic': (144, 208),
    'wires_rails': (208, 240),
    'residential': (240, 423),
    'commercial': (423, 612),
    'industrial': (612, 693),
    'seaport': (693, 709),
    'airport': (709, 745),
    'coal_power': (745, 761),
    'fire_police': (761, 779),
    'stadium': (779, 795),
    'stadium_full': (795, 811),
    'nuclear_power': (811, 827),
    'power_out_bridges': (827, 832),
    'radar_dish': (833, 841),
    'fountain_flag': (841, 861),
    'zone_destruct': (861, 869),
    'smoke_stacks': (885, 933),
    'stadium_playfield': (933, 949),
    'bridge_up': (949, 953),
    'nuclear_swirl': (953, 957),
}


def get_animation_category(base_index: int) -> str:
    """
    Get the animation category for a given tile index.

    Args:
        base_index: Base animation index (0-1023)

    Returns:
        Category name string, or 'unknown' if not categorized
    """
    for category, (start, end) in ANIMATION_RANGES.items():
        if start <= base_index < end:
            return category
    return 'unknown'
