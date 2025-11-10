"""
allocation.py - Memory allocation and initialization for Micropolis Python port

This module contains the memory allocation and initialization functions ported from s_alloc.c,
adapted for Python's automatic memory management while maintaining exact compatibility.
"""

import array
from . import types
import logging
from result import Result, Ok, Err

logger = logging.getLogger(__name__)

# ============================================================================
# Memory Allocation Functions (Python equivalents)
# ============================================================================


def initMapArrays() -> Result[int, Exception]:
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
        if len(types.Map) != types.WORLD_X or len(types.Map[0]) != types.WORLD_Y:
            types.Map = [
                [0 for _ in range(types.WORLD_Y)] for _ in range(types.WORLD_X)
            ]

        # Population density overlay (already initialized in types.py)
        if (
            len(types.PopDensity) != types.HWLDX
            or len(types.PopDensity[0]) != types.HWLDY
        ):
            types.PopDensity = [
                [0 for _ in range(types.HWLDY)] for _ in range(types.HWLDX)
            ]

        # Traffic density overlay (already initialized in types.py)
        if (
            len(types.TrfDensity) != types.HWLDX
            or len(types.TrfDensity[0]) != types.HWLDY
        ):
            types.TrfDensity = [
                [0 for _ in range(types.HWLDY)] for _ in range(types.HWLDX)
            ]

        # Pollution overlay (already initialized in types.py)
        if (
            len(types.PollutionMem) != types.HWLDX
            or len(types.PollutionMem[0]) != types.HWLDY
        ):
            types.PollutionMem = [
                [0 for _ in range(types.HWLDY)] for _ in range(types.HWLDX)
            ]

        # Land value overlay (already initialized in types.py)
        if (
            len(types.LandValueMem) != types.HWLDX
            or len(types.LandValueMem[0]) != types.HWLDY
        ):
            types.LandValueMem = [
                [0 for _ in range(types.HWLDY)] for _ in range(types.HWLDX)
            ]

        # Crime overlay (already initialized in types.py)
        if len(types.CrimeMem) != types.HWLDX or len(types.CrimeMem[0]) != types.HWLDY:
            types.CrimeMem = [
                [0 for _ in range(types.HWLDY)] for _ in range(types.HWLDX)
            ]

        # Temporary overlays (already initialized in types.py)
        if len(types.tem) != types.HWLDX or len(types.tem[0]) != types.HWLDY:
            types.tem = [[0 for _ in range(types.HWLDY)] for _ in range(types.HWLDX)]
        if len(types.tem2) != types.HWLDX or len(types.tem2[0]) != types.HWLDY:
            types.tem2 = [[0 for _ in range(types.HWLDY)] for _ in range(types.HWLDX)]

        # Terrain memory (already initialized in types.py)
        if len(types.TerrainMem) != types.QWX or len(types.TerrainMem[0]) != types.QWY:
            types.TerrainMem = [[0 for _ in range(types.QWY)] for _ in range(types.QWX)]
        if len(types.Qtem) != types.QWX or len(types.Qtem[0]) != types.QWY:
            types.Qtem = [[0 for _ in range(types.QWY)] for _ in range(types.QWX)]

        # Rate of growth (already initialized in types.py)
        if len(types.RateOGMem) != types.SmX or len(types.RateOGMem[0]) != types.SmY:
            types.RateOGMem = [[0 for _ in range(types.SmY)] for _ in range(types.SmX)]

        # Fire station coverage (already initialized in types.py)
        if len(types.FireStMap) != types.SmX or len(types.FireStMap[0]) != types.SmY:
            types.FireStMap = [[0 for _ in range(types.SmY)] for _ in range(types.SmX)]

        # Police station coverage (already initialized in types.py)
        if len(types.PoliceMap) != types.SmX or len(types.PoliceMap[0]) != types.SmY:
            types.PoliceMap = [[0 for _ in range(types.SmY)] for _ in range(types.SmX)]
        if (
            len(types.PoliceMapEffect) != types.SmX
            or len(types.PoliceMapEffect[0]) != types.SmY
        ):
            types.PoliceMapEffect = [
                [0 for _ in range(types.SmY)] for _ in range(types.SmX)
            ]

        # Commercial rate (already initialized in types.py)
        if len(types.ComRate) != types.SmX or len(types.ComRate[0]) != types.SmY:
            types.ComRate = [[0 for _ in range(types.SmY)] for _ in range(types.SmX)]

        # Fire rate (already initialized in types.py)
        if len(types.FireRate) != types.SmX or len(types.FireRate[0]) != types.SmY:
            types.FireRate = [[0 for _ in range(types.SmY)] for _ in range(types.SmX)]

        # Temporary storage (already initialized in types.py)
        if len(types.STem) != types.SmX or len(types.STem[0]) != types.SmY:
            types.STem = [[0 for _ in range(types.SmY)] for _ in range(types.SmX)]

        # Sprite offsets (already initialized in types.py)
        if len(types.SpriteXOffset) != types.OBJN:
            types.SpriteXOffset = [0] * types.OBJN
        if len(types.SpriteYOffset) != types.OBJN:
            types.SpriteYOffset = [0] * types.OBJN

        # History arrays - initialize as proper lists
        if not types.ResHis or len(types.ResHis) != types.HISTLEN:
            types.ResHis = [0] * types.HISTLEN
        if not types.ComHis or len(types.ComHis) != types.HISTLEN:
            types.ComHis = [0] * types.HISTLEN
        if not types.IndHis or len(types.IndHis) != types.HISTLEN:
            types.IndHis = [0] * types.HISTLEN
        if not types.MoneyHis or len(types.MoneyHis) != types.HISTLEN:
            types.MoneyHis = [0] * types.HISTLEN
        if not types.CrimeHis or len(types.CrimeHis) != types.HISTLEN:
            types.CrimeHis = [0] * types.HISTLEN
        if not types.PollutionHis or len(types.PollutionHis) != types.HISTLEN:
            types.PollutionHis = [0] * types.HISTLEN
        if not types.MiscHis or len(types.MiscHis) != types.MISCHISTLEN:
            types.MiscHis = [0] * types.MISCHISTLEN

        # Power grid (already initialized in types.py as array.array)
        if len(types.PowerMap) != types.PWRMAPSIZE:
            types.PowerMap = array.array("H", [0] * types.PWRMAPSIZE)

        # History buffers (already initialized in types.py)
        if len(types.History10) != types.HISTORIES:
            types.History10 = [[] for _ in range(types.HISTORIES)]
        if len(types.History120) != types.HISTORIES:
            types.History120 = [[] for _ in range(types.HISTORIES)]

        # Problem tracking arrays (already initialized in types.py)
        if len(types.ProblemTable) != types.PROBNUM:
            types.ProblemTable = [0] * types.PROBNUM
        if len(types.ProblemVotes) != types.PROBNUM:
            types.ProblemVotes = [0] * types.PROBNUM

        # Dynamic data (already initialized in types.py)
        if len(types.DynamicData) != 32:
            types.DynamicData = [0] * 32

        # Color intensities (already initialized in types.py)
        if len(types.ColorIntensities) != 16:
            types.ColorIntensities = [0] * 16

        # Map update flags (already initialized in types.py)
        if len(types.NewMapFlags) != types.NMAPS:
            types.NewMapFlags = [0] * types.NMAPS

        # Date strings (already initialized in types.py)
        if len(types.dateStr) != 12:
            types.dateStr = [""] * 12

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
        assert len(types.Map) == types.WORLD_X
        assert len(types.Map[0]) == types.WORLD_Y

        # Check overlays
        assert len(types.PopDensity) == types.HWLDX
        assert len(types.PopDensity[0]) == types.HWLDY
        assert len(types.TrfDensity) == types.HWLDX
        assert len(types.TrfDensity[0]) == types.HWLDY
        assert len(types.PollutionMem) == types.HWLDX
        assert len(types.PollutionMem[0]) == types.HWLDY
        assert len(types.LandValueMem) == types.HWLDX
        assert len(types.LandValueMem[0]) == types.HWLDY
        assert len(types.CrimeMem) == types.HWLDX
        assert len(types.CrimeMem[0]) == types.HWLDY

        # Check temporary arrays
        assert len(types.tem) == types.HWLDX
        assert len(types.tem[0]) == types.HWLDY
        assert len(types.tem2) == types.HWLDX
        assert len(types.tem2[0]) == types.HWLDY

        # Check terrain arrays
        assert len(types.TerrainMem) == types.QWX
        assert len(types.TerrainMem[0]) == types.QWY
        assert len(types.Qtem) == types.QWX
        assert len(types.Qtem[0]) == types.QWY

        # Check small arrays
        assert len(types.RateOGMem) == types.SmX
        assert len(types.RateOGMem[0]) == types.SmY
        assert len(types.FireStMap) == types.SmX
        assert len(types.FireStMap[0]) == types.SmY
        assert len(types.PoliceMap) == types.SmX
        assert len(types.PoliceMap[0]) == types.SmY

        # Check history arrays
        assert len(types.ResHis) == types.HISTLEN
        assert len(types.ComHis) == types.HISTLEN
        assert len(types.IndHis) == types.HISTLEN
        assert len(types.MoneyHis) == types.HISTLEN
        assert len(types.CrimeHis) == types.HISTLEN
        assert len(types.PollutionHis) == types.HISTLEN
        assert len(types.MiscHis) == types.MISCHISTLEN

        # Check power map
        assert len(types.PowerMap) == types.PWRMAPSIZE

        return True

    except (AssertionError, IndexError):
        return False


def resetAllArrays() -> None:
    """
    Reset all global arrays to their initial state (all zeros).
    """
    # Reset main map
    types.Map = [[0 for _ in range(types.WORLD_Y)] for _ in range(types.WORLD_X)]

    # Reset overlays
    types.PopDensity = [[0 for _ in range(types.HWLDY)] for _ in range(types.HWLDX)]
    types.TrfDensity = [[0 for _ in range(types.HWLDY)] for _ in range(types.HWLDX)]
    types.PollutionMem = [[0 for _ in range(types.HWLDY)] for _ in range(types.HWLDX)]
    types.LandValueMem = [[0 for _ in range(types.HWLDY)] for _ in range(types.HWLDX)]
    types.CrimeMem = [[0 for _ in range(types.HWLDY)] for _ in range(types.HWLDX)]

    # Reset temporary arrays
    types.tem = [[0 for _ in range(types.HWLDY)] for _ in range(types.HWLDX)]
    types.tem2 = [[0 for _ in range(types.HWLDY)] for _ in range(types.HWLDX)]

    # Reset terrain arrays
    types.TerrainMem = [[0 for _ in range(types.QWY)] for _ in range(types.QWX)]
    types.Qtem = [[0 for _ in range(types.QWY)] for _ in range(types.QWX)]

    # Reset small arrays
    types.RateOGMem = [[0 for _ in range(types.SmY)] for _ in range(types.SmX)]
    types.FireStMap = [[0 for _ in range(types.SmY)] for _ in range(types.SmX)]
    types.PoliceMap = [[0 for _ in range(types.SmY)] for _ in range(types.SmX)]
    types.PoliceMapEffect = [[0 for _ in range(types.SmY)] for _ in range(types.SmX)]
    types.ComRate = [[0 for _ in range(types.SmY)] for _ in range(types.SmX)]
    types.FireRate = [[0 for _ in range(types.SmY)] for _ in range(types.SmX)]
    types.STem = [[0 for _ in range(types.SmY)] for _ in range(types.SmX)]

    # Reset history arrays
    types.ResHis = [0] * types.HISTLEN
    types.ComHis = [0] * types.HISTLEN
    types.IndHis = [0] * types.HISTLEN
    types.MoneyHis = [0] * types.HISTLEN
    types.CrimeHis = [0] * types.HISTLEN
    types.PollutionHis = [0] * types.HISTLEN
    types.MiscHis = [0] * types.MISCHISTLEN

    # Reset power map
    types.PowerMap = array.array("H", [0] * types.PWRMAPSIZE)

    # Reset sprite offsets
    types.SpriteXOffset = [0] * types.OBJN
    types.SpriteYOffset = [0] * types.OBJN


def getMemoryUsage() -> dict:
    """
    Get an estimate of memory usage for all allocated arrays.

    Returns:
        Dictionary with memory usage information
    """
    usage = {}

    # Calculate sizes for different array types
    usage["main_map"] = types.WORLD_X * types.WORLD_Y * 2  # shorts
    usage["overlays"] = 5 * types.HWLDX * types.HWLDY  # bytes
    usage["temp_arrays"] = 2 * types.HWLDX * types.HWLDY  # bytes
    usage["terrain"] = 2 * types.QWX * types.QWY  # bytes
    usage["small_arrays"] = 7 * types.SmX * types.SmY * 2  # shorts
    usage["history"] = (6 * types.HISTLEN + types.MISCHISTLEN) * 2  # shorts
    usage["power_map"] = types.PWRMAPSIZE * 2  # shorts

    usage["total"] = sum(usage.values())

    return usage
