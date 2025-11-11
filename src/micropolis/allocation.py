"""
allocation.py - Memory allocation and initialization for Micropolis Python port

This module contains the memory allocation and initialization functions ported from s_alloc.c,
adapted for Python's automatic memory management while maintaining exact compatibility.
"""

import array
import logging

import micropolis.constants
from result import Err, Ok, Result

from micropolis.context import AppContext

from . import types

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
            len(types.map_data) != micropolis.constants.WORLD_X
            or len(types.map_data[0]) != micropolis.constants.WORLD_Y
        ):
            types.map_data = [
                [0 for _ in range(micropolis.constants.WORLD_Y)]
                for _ in range(micropolis.constants.WORLD_X)
            ]

        # Population density overlay (already initialized in types.py)
        if (
            len(types.pop_density) != micropolis.constants.HWLDX
            or len(types.pop_density[0]) != micropolis.constants.HWLDY
        ):
            types.pop_density = [
                [0 for _ in range(micropolis.constants.HWLDY)]
                for _ in range(micropolis.constants.HWLDX)
            ]

        # Traffic density overlay (already initialized in types.py)
        if (
            len(types.trf_density) != micropolis.constants.HWLDX
            or len(types.trf_density[0]) != micropolis.constants.HWLDY
        ):
            types.trf_density = [
                [0 for _ in range(micropolis.constants.HWLDY)]
                for _ in range(micropolis.constants.HWLDX)
            ]

        # Pollution overlay (already initialized in types.py)
        if (
            len(types.pollution_mem) != micropolis.constants.HWLDX
            or len(types.pollution_mem[0]) != micropolis.constants.HWLDY
        ):
            types.pollution_mem = [
                [0 for _ in range(micropolis.constants.HWLDY)]
                for _ in range(micropolis.constants.HWLDX)
            ]

        # Land value overlay (already initialized in types.py)
        if (
            len(types.land_value_mem) != micropolis.constants.HWLDX
            or len(types.land_value_mem[0]) != micropolis.constants.HWLDY
        ):
            types.land_value_mem = [
                [0 for _ in range(micropolis.constants.HWLDY)]
                for _ in range(micropolis.constants.HWLDX)
            ]

        # Crime overlay (already initialized in types.py)
        if (
            len(types.crime_mem) != micropolis.constants.HWLDX
            or len(types.crime_mem[0]) != micropolis.constants.HWLDY
        ):
            types.crime_mem = [
                [0 for _ in range(micropolis.constants.HWLDY)]
                for _ in range(micropolis.constants.HWLDX)
            ]

        # Temporary overlays (already initialized in types.py)
        if (
            len(types.tem) != micropolis.constants.HWLDX
            or len(types.tem[0]) != micropolis.constants.HWLDY
        ):
            types.tem = [
                [0 for _ in range(micropolis.constants.HWLDY)]
                for _ in range(micropolis.constants.HWLDX)
            ]
        if (
            len(types.tem2) != micropolis.constants.HWLDX
            or len(types.tem2[0]) != micropolis.constants.HWLDY
        ):
            types.tem2 = [
                [0 for _ in range(micropolis.constants.HWLDY)]
                for _ in range(micropolis.constants.HWLDX)
            ]

        # Terrain memory (already initialized in types.py)
        if (
            len(types.terrain_mem) != micropolis.constants.QWX
            or len(types.terrain_mem[0]) != micropolis.constants.QWY
        ):
            types.terrain_mem = [
                [0 for _ in range(micropolis.constants.QWY)]
                for _ in range(micropolis.constants.QWX)
            ]
        if (
            len(types.Qtem) != micropolis.constants.QWX
            or len(types.Qtem[0]) != micropolis.constants.QWY
        ):
            types.Qtem = [
                [0 for _ in range(micropolis.constants.QWY)]
                for _ in range(micropolis.constants.QWX)
            ]

        # Rate of growth (already initialized in types.py)
        if (
            len(types.rate_og_mem) != micropolis.constants.SM_X
            or len(types.rate_og_mem[0]) != micropolis.constants.SM_Y
        ):
            types.rate_og_mem = [
                [0 for _ in range(micropolis.constants.SM_Y)]
                for _ in range(micropolis.constants.SM_X)
            ]

        # Fire station coverage (already initialized in types.py)
        if (
            len(types.fire_st_map) != micropolis.constants.SM_X
            or len(types.fire_st_map[0]) != micropolis.constants.SM_Y
        ):
            types.fire_st_map = [
                [0 for _ in range(micropolis.constants.SM_Y)]
                for _ in range(micropolis.constants.SM_X)
            ]

        # Police station coverage (already initialized in types.py)
        if (
            len(types.police_map) != micropolis.constants.SM_X
            or len(types.police_map[0]) != micropolis.constants.SM_Y
        ):
            types.police_map = [
                [0 for _ in range(micropolis.constants.SM_Y)]
                for _ in range(micropolis.constants.SM_X)
            ]
        if (
            len(types.police_map_effect) != micropolis.constants.SM_X
            or len(types.police_map_effect[0]) != micropolis.constants.SM_Y
        ):
            types.police_map_effect = [
                [0 for _ in range(micropolis.constants.SM_Y)]
                for _ in range(micropolis.constants.SM_X)
            ]

        # Commercial rate (already initialized in types.py)
        if (
            len(types.com_rate) != micropolis.constants.SM_X
            or len(types.com_rate[0]) != micropolis.constants.SM_Y
        ):
            types.com_rate = [
                [0 for _ in range(micropolis.constants.SM_Y)]
                for _ in range(micropolis.constants.SM_X)
            ]

        # Fire rate (already initialized in types.py)
        if (
            len(types.fire_rate) != micropolis.constants.SM_X
            or len(types.fire_rate[0]) != micropolis.constants.SM_Y
        ):
            types.fire_rate = [
                [0 for _ in range(micropolis.constants.SM_Y)]
                for _ in range(micropolis.constants.SM_X)
            ]

        # Temporary storage (already initialized in types.py)
        if (
            len(types.stem) != micropolis.constants.SM_X
            or len(types.stem[0]) != micropolis.constants.SM_Y
        ):
            types.stem = [
                [0 for _ in range(micropolis.constants.SM_Y)]
                for _ in range(micropolis.constants.SM_X)
            ]

        # Sprite offsets (already initialized in types.py)
        if len(types.sprite_x_offset) != types.OBJN:
            types.sprite_x_offset = [0] * types.OBJN
        if len(types.sprite_y_offset) != types.OBJN:
            types.sprite_y_offset = [0] * types.OBJN

        # History arrays - initialize as proper lists
        if not types.res_his or len(types.res_his) != types.HISTLEN:
            types.res_his = [0] * types.HISTLEN
        if not types.com_his or len(types.com_his) != types.HISTLEN:
            types.com_his = [0] * types.HISTLEN
        if not types.ind_his or len(types.ind_his) != types.HISTLEN:
            types.ind_his = [0] * types.HISTLEN
        if not types.money_his or len(types.money_his) != types.HISTLEN:
            types.money_his = [0] * types.HISTLEN
        if not types.crime_his or len(types.crime_his) != types.HISTLEN:
            types.crime_his = [0] * types.HISTLEN
        if not types.pollution_his or len(types.pollution_his) != types.HISTLEN:
            types.pollution_his = [0] * types.HISTLEN
        if not types.misc_his or len(types.misc_his) != types.MISCHISTLEN:
            types.misc_his = [0] * types.MISCHISTLEN

        # Power grid (already initialized in types.py as array.array)
        if len(types.power_map) != types.PWRMAPSIZE:
            types.power_map = array.array("H", [0] * types.PWRMAPSIZE)

        # History buffers (already initialized in types.py)
        if len(types.History10) != types.HISTORIES:
            types.History10 = [[] for _ in range(types.HISTORIES)]
        if len(types.History120) != types.HISTORIES:
            types.History120 = [[] for _ in range(types.HISTORIES)]

        # Problem tracking arrays (already initialized in types.py)
        if len(types.problem_table) != types.PROBNUM:
            types.problem_table = [0] * types.PROBNUM
        if len(types.problem_votes) != types.PROBNUM:
            types.problem_votes = [0] * types.PROBNUM

        # Dynamic data (already initialized in types.py)
        if len(types.dynamic_data) != 32:
            types.dynamic_data = [0] * 32

        # Color intensities (already initialized in types.py)
        if len(types.color_intensities) != 16:
            types.color_intensities = [0] * 16

        # Map update flags (already initialized in types.py)
        if len(types.new_map_flags) != micropolis.constants.NMAPS:
            types.new_map_flags = [0] * micropolis.constants.NMAPS

        # Date strings (already initialized in types.py)
        if len(types.date_str) != 12:
            types.date_str = [""] * 12

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


def validateArrayDimensions() -> bool:
    """
    Validate that all global arrays have the correct dimensions.

    Returns:
        True if all arrays have correct dimensions, False otherwise
    """
    try:
        # Check main map
        assert len(types.map_data) == micropolis.constants.WORLD_X
        assert len(types.map_data[0]) == micropolis.constants.WORLD_Y

        # Check overlays
        assert len(types.pop_density) == micropolis.constants.HWLDX
        assert len(types.pop_density[0]) == micropolis.constants.HWLDY
        assert len(types.trf_density) == micropolis.constants.HWLDX
        assert len(types.trf_density[0]) == micropolis.constants.HWLDY
        assert len(types.pollution_mem) == micropolis.constants.HWLDX
        assert len(types.pollution_mem[0]) == micropolis.constants.HWLDY
        assert len(types.land_value_mem) == micropolis.constants.HWLDX
        assert len(types.land_value_mem[0]) == micropolis.constants.HWLDY
        assert len(types.crime_mem) == micropolis.constants.HWLDX
        assert len(types.crime_mem[0]) == micropolis.constants.HWLDY

        # Check temporary arrays
        assert len(types.tem) == micropolis.constants.HWLDX
        assert len(types.tem[0]) == micropolis.constants.HWLDY
        assert len(types.tem2) == micropolis.constants.HWLDX
        assert len(types.tem2[0]) == micropolis.constants.HWLDY

        # Check terrain arrays
        assert len(types.terrain_mem) == micropolis.constants.QWX
        assert len(types.terrain_mem[0]) == micropolis.constants.QWY
        assert len(types.Qtem) == micropolis.constants.QWX
        assert len(types.Qtem[0]) == micropolis.constants.QWY

        # Check small arrays
        assert len(types.rate_og_mem) == micropolis.constants.SM_X
        assert len(types.rate_og_mem[0]) == micropolis.constants.SM_Y
        assert len(types.fire_st_map) == micropolis.constants.SM_X
        assert len(types.fire_st_map[0]) == micropolis.constants.SM_Y
        assert len(types.police_map) == micropolis.constants.SM_X
        assert len(types.police_map[0]) == micropolis.constants.SM_Y

        # Check history arrays
        assert len(types.res_his) == types.HISTLEN
        assert len(types.com_his) == types.HISTLEN
        assert len(types.ind_his) == types.HISTLEN
        assert len(types.money_his) == types.HISTLEN
        assert len(types.crime_his) == types.HISTLEN
        assert len(types.pollution_his) == types.HISTLEN
        assert len(types.misc_his) == types.MISCHISTLEN

        # Check power map
        assert len(types.power_map) == types.PWRMAPSIZE

        return True

    except (AssertionError, IndexError):
        return False


def resetAllArrays() -> None:
    """
    Reset all global arrays to their initial state (all zeros).
    """
    # Reset main map
    types.map_data = [
        [0 for _ in range(micropolis.constants.WORLD_Y)]
        for _ in range(micropolis.constants.WORLD_X)
    ]

    # Reset overlays
    types.pop_density = [
        [0 for _ in range(micropolis.constants.HWLDY)]
        for _ in range(micropolis.constants.HWLDX)
    ]
    types.trf_density = [
        [0 for _ in range(micropolis.constants.HWLDY)]
        for _ in range(micropolis.constants.HWLDX)
    ]
    types.pollution_mem = [
        [0 for _ in range(micropolis.constants.HWLDY)]
        for _ in range(micropolis.constants.HWLDX)
    ]
    types.land_value_mem = [
        [0 for _ in range(micropolis.constants.HWLDY)]
        for _ in range(micropolis.constants.HWLDX)
    ]
    types.crime_mem = [
        [0 for _ in range(micropolis.constants.HWLDY)]
        for _ in range(micropolis.constants.HWLDX)
    ]

    # Reset temporary arrays
    types.tem = [
        [0 for _ in range(micropolis.constants.HWLDY)]
        for _ in range(micropolis.constants.HWLDX)
    ]
    types.tem2 = [
        [0 for _ in range(micropolis.constants.HWLDY)]
        for _ in range(micropolis.constants.HWLDX)
    ]

    # Reset terrain arrays
    types.terrain_mem = [
        [0 for _ in range(micropolis.constants.QWY)]
        for _ in range(micropolis.constants.QWX)
    ]
    types.Qtem = [
        [0 for _ in range(micropolis.constants.QWY)]
        for _ in range(micropolis.constants.QWX)
    ]

    # Reset small arrays
    types.rate_og_mem = [
        [0 for _ in range(micropolis.constants.SM_Y)]
        for _ in range(micropolis.constants.SM_X)
    ]
    types.fire_st_map = [
        [0 for _ in range(micropolis.constants.SM_Y)]
        for _ in range(micropolis.constants.SM_X)
    ]
    types.police_map = [
        [0 for _ in range(micropolis.constants.SM_Y)]
        for _ in range(micropolis.constants.SM_X)
    ]
    types.police_map_effect = [
        [0 for _ in range(micropolis.constants.SM_Y)]
        for _ in range(micropolis.constants.SM_X)
    ]
    types.com_rate = [
        [0 for _ in range(micropolis.constants.SM_Y)]
        for _ in range(micropolis.constants.SM_X)
    ]
    types.fire_rate = [
        [0 for _ in range(micropolis.constants.SM_Y)]
        for _ in range(micropolis.constants.SM_X)
    ]
    types.stem = [
        [0 for _ in range(micropolis.constants.SM_Y)]
        for _ in range(micropolis.constants.SM_X)
    ]

    # Reset history arrays
    types.res_his = [0] * types.HISTLEN
    types.com_his = [0] * types.HISTLEN
    types.ind_his = [0] * types.HISTLEN
    types.money_his = [0] * types.HISTLEN
    types.crime_his = [0] * types.HISTLEN
    types.pollution_his = [0] * types.HISTLEN
    types.misc_his = [0] * types.MISCHISTLEN

    # Reset power map
    types.power_map = array.array("H", [0] * types.PWRMAPSIZE)

    # Reset sprite offsets
    types.sprite_x_offset = [0] * types.OBJN
    types.sprite_y_offset = [0] * types.OBJN


def getMemoryUsage() -> dict:
    """
    Get an estimate of memory usage for all allocated arrays.

    Returns:
        Dictionary with memory usage information
    """
    usage = {}

    # Calculate sizes for different array types
    usage["main_map"] = (
        micropolis.constants.WORLD_X * micropolis.constants.WORLD_Y * 2
    )  # shorts
    usage["overlays"] = (
        5 * micropolis.constants.HWLDX * micropolis.constants.HWLDY
    )  # bytes
    usage["temp_arrays"] = (
        2 * micropolis.constants.HWLDX * micropolis.constants.HWLDY
    )  # bytes
    usage["terrain"] = 2 * micropolis.constants.QWX * micropolis.constants.QWY  # bytes
    usage["small_arrays"] = (
        7 * micropolis.constants.SM_X * micropolis.constants.SM_Y * 2
    )  # shorts
    usage["history"] = (6 * types.HISTLEN + types.MISCHISTLEN) * 2  # shorts
    usage["power_map"] = types.PWRMAPSIZE * 2  # shorts

    usage["total"] = sum(usage.values())

    return usage
