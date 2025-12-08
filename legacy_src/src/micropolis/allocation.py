"""
allocation.py - Memory allocation and initialization for Micropolis Python port

This module contains the memory allocation and initialization functions ported from s_alloc.c,
adapted for Python's automatic memory management while maintaining exact compatibility.
"""

import logging

from result import Err, Ok, Result

from .constants import WORLD_X, WORLD_Y, HWLDX, HWLDY, QWX, QWY, SM_X, SM_Y, OBJN, HISTLEN, MISCHISTLEN, PWRMAPSIZE, \
    HISTORIES, PROBNUM, NMAPS
from .context import AppContext

logger = logging.getLogger(__name__)

# ============================================================================
# Memory Allocation Functions (Python equivalents)
# ============================================================================


def init_map_arrays(context: AppContext) -> Result[int, Exception]:
    """
    Initialize all map arrays and data structures.

    This function allocates and initializes all the global arrays used by the
    Micropolis simulation. In Python, this means setting up the proper data
    structures rather than manual memory allocation.

    Returns:
        0 on success, -1 on failure (though Python allocation rarely fails)
    """
    try:
        # Main map array is already initialized in types.py
        # Here we ensure it's properly sized
        if (
            len(context.map_data) != WORLD_X
            or len(context.map_data[0]) != WORLD_Y
        ):
            context.map_data = [
                [0 for _ in range(WORLD_Y)]
                for _ in range(WORLD_X)
            ]

        # Population density overlay (already initialized in types.py)
        if (
            len(context.pop_density) != HWLDX
            or len(context.pop_density[0]) != HWLDY
        ):
            context.pop_density = [
                [0 for _ in range(HWLDY)]
                for _ in range(HWLDX)
            ]

        # Traffic density overlay (already initialized in types.py)
        if (
            len(context.trf_density) != HWLDX
            or len(context.trf_density[0]) != HWLDY
        ):
            context.trf_density = [
                [0 for _ in range(HWLDY)]
                for _ in range(HWLDX)
            ]

        # Pollution overlay (already initialized in types.py)
        if (
            len(context.pollution_mem) != HWLDX
            or len(context.pollution_mem[0]) != HWLDY
        ):
            context.pollution_mem = [
                [0 for _ in range(HWLDY)]
                for _ in range(HWLDX)
            ]

        # Land value overlay (already initialized in types.py)
        if (
            len(context.land_value_mem) != HWLDX
            or len(context.land_value_mem[0]) != HWLDY
        ):
            context.land_value_mem = [
                [0 for _ in range(HWLDY)]
                for _ in range(HWLDX)
            ]

        # Crime overlay (already initialized in types.py)
        if (
            len(context.crime_mem) != HWLDX
            or len(context.crime_mem[0]) != HWLDY
        ):
            context.crime_mem = [
                [0 for _ in range(HWLDY)]
                for _ in range(HWLDX)
            ]

        # Temporary overlays (already initialized in types.py)
        if (
            len(context.tem) != HWLDX
            or len(context.tem[0]) != HWLDY
        ):
            context.tem = [
                [0 for _ in range(HWLDY)]
                for _ in range(HWLDX)
            ]
        if (
            len(context.tem2) != HWLDX
            or len(context.tem2[0]) != HWLDY
        ):
            context.tem2 = [
                [0 for _ in range(HWLDY)]
                for _ in range(HWLDX)
            ]

        # Terrain memory (already initialized in types.py)
        if (
            len(context.terrain_mem) != QWX
            or len(context.terrain_mem[0]) != QWY
        ):
            context.terrain_mem = [
                [0 for _ in range(QWY)]
                for _ in range(QWX)
            ]
        if (
            len(context.Qtem) != QWX
            or len(context.Qtem[0]) != QWY
        ):
            context.Qtem = [
                [0 for _ in range(QWY)]
                for _ in range(QWX)
            ]

        # Rate of growth (already initialized in types.py)
        if (
            len(context.rate_og_mem) != SM_X
            or len(context.rate_og_mem[0]) != SM_Y
        ):
            context.rate_og_mem = [
                [0 for _ in range(SM_Y)]
                for _ in range(SM_X)
            ]

        # Fire station coverage (already initialized in types.py)
        if (
            len(context.fire_st_map) != SM_X
            or len(context.fire_st_map[0]) != SM_Y
        ):
            context.fire_st_map = [
                [0 for _ in range(SM_Y)]
                for _ in range(SM_X)
            ]

        # Police station coverage (already initialized in types.py)
        if (
            len(context.police_map) != SM_X
            or len(context.police_map[0]) != SM_Y
        ):
            context.police_map = [
                [0 for _ in range(SM_Y)]
                for _ in range(SM_X)
            ]
        if (
            len(context.police_map_effect) != SM_X
            or len(context.police_map_effect[0]) != SM_Y
        ):
            context.police_map_effect = [
                [0 for _ in range(SM_Y)]
                for _ in range(SM_X)
            ]

        # Commercial rate (already initialized in types.py)
        if (
            len(context.com_rate) != SM_X
            or len(context.com_rate[0]) != SM_Y
        ):
            context.com_rate = [
                [0 for _ in range(SM_Y)]
                for _ in range(SM_X)
            ]

        # Fire rate (already initialized in types.py)
        if (
            len(context.fire_rate) != SM_X
            or len(context.fire_rate[0]) != SM_Y
        ):
            context.fire_rate = [
                [0 for _ in range(SM_Y)]
                for _ in range(SM_X)
            ]

        # Temporary storage (already initialized in types.py)
        if (
            len(context.stem) != SM_X
            or len(context.stem[0]) != SM_Y
        ):
            context.stem = [
                [0 for _ in range(SM_Y)]
                for _ in range(SM_X)
            ]

        # Sprite offsets (already initialized in types.py)
        if len(context.sprite_x_offset) != OBJN:
            context.sprite_x_offset = [0] * OBJN
        if len(context.sprite_y_offset) != OBJN:
            context.sprite_y_offset = [0] * OBJN

        # History arrays - initialize as proper lists
        if not context.res_his or len(context.res_his) != HISTLEN:
            context.res_his = [0] * HISTLEN
        if not context.com_his or len(context.com_his) != HISTLEN:
            context.com_his = [0] * HISTLEN
        if not context.ind_his or len(context.ind_his) != HISTLEN:
            context.ind_his = [0] * HISTLEN
        if not context.money_his or len(context.money_his) != HISTLEN:
            context.money_his = [0] * HISTLEN
        if not context.crime_his or len(context.crime_his) != HISTLEN:
            context.crime_his = [0] * HISTLEN
        if not context.pollution_his or len(context.pollution_his) != HISTLEN:
            context.pollution_his = [0] * HISTLEN
        if not context.misc_his or len(context.misc_his) != MISCHISTLEN:
            context.misc_his = [0] * MISCHISTLEN

        # Power grid (already initialized in types.py as array.array)
        if len(context.power_map) != PWRMAPSIZE:
            context.power_map = [0] * PWRMAPSIZE

        # History buffers (already initialized in types.py)
        if len(context.History10) != HISTORIES:
            context.History10 = [[] for _ in range(HISTORIES)]
        if len(context.History120) != HISTORIES:
            context.History120 = [[] for _ in range(HISTORIES)]

        # Problem tracking arrays (already initialized in types.py)
        if len(context.problem_table) != PROBNUM:
            context.problem_table = [0] * PROBNUM
        if len(context.problem_votes) != PROBNUM:
            context.problem_votes = [0] * PROBNUM

        # Dynamic data (already initialized in types.py)
        if len(context.dynamic_data) != 32:
            context.dynamic_data = [0] * 32

        # Color intensities (already initialized in types.py)
        if len(context.color_intensities) != 16:
            context.color_intensities = [0] * 16

        # Map update flags (already initialized in types.py)
        if len(context.new_map_flags) != NMAPS:
            context.new_map_flags = [0] * NMAPS

        # Date strings (already initialized in types.py)
        if len(context.date_str) != 12:
            context.date_str = [""] * 12

        # Tool configuration (already initialized in types.py as empty lists)
        # These will be populated by other initialization code

        return Ok(0)  # Success

    except Exception as e:
        # print(f"Error initializing map arrays: {e}", file=__import__("sys").stderr)
        # return Err(e)  # Failure
        return Err(e)


# ============================================================================
# Memory Management Utilities
# ============================================================================


def validate_array_dimensions(context: AppContext) -> bool:
    """
    ported from validateArrayDimensions

    Validate that all global arrays have the correct dimensions.

    Returns:
        True if all arrays have correct dimensions, False otherwise
    """
    try:
        # Check main map
        assert len(context.map_data) == WORLD_X
        assert len(context.map_data[0]) == WORLD_Y

        # Check overlays
        assert len(context.pop_density) == HWLDX
        assert len(context.pop_density[0]) == HWLDY
        assert len(context.trf_density) == HWLDX
        assert len(context.trf_density[0]) == HWLDY
        assert len(context.pollution_mem) == HWLDX
        assert len(context.pollution_mem[0]) == HWLDY
        assert len(context.land_value_mem) == HWLDX
        assert len(context.land_value_mem[0]) == HWLDY
        assert len(context.crime_mem) == HWLDX
        assert len(context.crime_mem[0]) == HWLDY

        # Check temporary arrays
        assert len(context.tem) == HWLDX
        assert len(context.tem[0]) == HWLDY
        assert len(context.tem2) == HWLDX
        assert len(context.tem2[0]) == HWLDY

        # Check terrain arrays
        assert len(context.terrain_mem) == QWX
        assert len(context.terrain_mem[0]) == QWY
        assert len(context.Qtem) == QWX
        assert len(context.Qtem[0]) == QWY

        # Check small arrays
        assert len(context.rate_og_mem) == SM_X
        assert len(context.rate_og_mem[0]) == SM_Y
        assert len(context.fire_st_map) == SM_X
        assert len(context.fire_st_map[0]) == SM_Y
        assert len(context.police_map) == SM_X
        assert len(context.police_map[0]) == SM_Y

        # Check history arrays
        assert len(context.res_his) == HISTLEN
        assert len(context.com_his) == HISTLEN
        assert len(context.ind_his) == HISTLEN
        assert len(context.money_his) == HISTLEN
        assert len(context.crime_his) == HISTLEN
        assert len(context.pollution_his) == HISTLEN
        assert len(context.misc_his) == MISCHISTLEN

        # Check power map
        assert len(context.power_map) == PWRMAPSIZE

        return True

    except (AssertionError, IndexError):
        return False


def reset_all_arrays(context: AppContext) -> None:
    """
    ported from resetAllArrays
    Reset all global arrays to their initial state (all zeros).
    """
    # Reset main map
    context.map_data = [
        [0 for _ in range(WORLD_Y)]
        for _ in range(WORLD_X)
    ]

    # Reset overlays
    context.pop_density = [
        [0 for _ in range(HWLDY)]
        for _ in range(HWLDX)
    ]
    context.trf_density = [
        [0 for _ in range(HWLDY)]
        for _ in range(HWLDX)
    ]
    context.pollution_mem = [
        [0 for _ in range(HWLDY)]
        for _ in range(HWLDX)
    ]
    context.land_value_mem = [
        [0 for _ in range(HWLDY)]
        for _ in range(HWLDX)
    ]
    context.crime_mem = [
        [0 for _ in range(HWLDY)]
        for _ in range(HWLDX)
    ]

    # Reset temporary arrays
    context.tem = [
        [0 for _ in range(HWLDY)]
        for _ in range(HWLDX)
    ]
    context.tem2 = [
        [0 for _ in range(HWLDY)]
        for _ in range(HWLDX)
    ]

    # Reset terrain arrays
    context.terrain_mem = [
        [0 for _ in range(QWY)]
        for _ in range(QWX)
    ]
    context.Qtem = [
        [0 for _ in range(QWY)]
        for _ in range(QWX)
    ]

    # Reset small arrays
    context.rate_og_mem = [
        [0 for _ in range(SM_Y)]
        for _ in range(SM_X)
    ]
    context.fire_st_map = [
        [0 for _ in range(SM_Y)]
        for _ in range(SM_X)
    ]
    context.police_map = [
        [0 for _ in range(SM_Y)]
        for _ in range(SM_X)
    ]
    context.police_map_effect = [
        [0 for _ in range(SM_Y)]
        for _ in range(SM_X)
    ]
    context.com_rate = [
        [0 for _ in range(SM_Y)]
        for _ in range(SM_X)
    ]
    context.fire_rate = [
        [0 for _ in range(SM_Y)]
        for _ in range(SM_X)
    ]
    context.stem = [
        [0 for _ in range(SM_Y)]
        for _ in range(SM_X)
    ]

    # Reset history arrays
    context.res_his = [0] * HISTLEN
    context.com_his = [0] * HISTLEN
    context.ind_his = [0] * HISTLEN
    context.money_his = [0] * HISTLEN
    context.crime_his = [0] * HISTLEN
    context.pollution_his = [0] * HISTLEN
    context.misc_his = [0] * MISCHISTLEN

    # Reset power map
    context.power_map = [0] * PWRMAPSIZE

    # Reset sprite offsets
    context.sprite_x_offset = [0] * OBJN
    context.sprite_y_offset = [0] * OBJN


def get_memory_usage() -> dict:
    """
    ported from getMemoryUsage
    Get an estimate of memory usage for all allocated arrays.

    Returns:
        Dictionary with memory usage information
    """
    usage = {"main_map": (
            WORLD_X * WORLD_Y * 2
    ), "overlays": (
            5 * HWLDX * HWLDY
    ), "temp_arrays": (
            2 * HWLDX * HWLDY
    ), "terrain": 2 * QWX * QWY, "small_arrays": (
            7 * SM_X * SM_Y * 2
    ), "history": (6 * HISTLEN + MISCHISTLEN) * 2, "power_map": PWRMAPSIZE * 2}

    # Calculate sizes for different array types

    usage["total"] = sum(usage.values())

    return usage
