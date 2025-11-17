# ruff: noqa: N816 - legacy globals intentionally keep their CamelCase names

"""Legacy compatibility namespace for classic Micropolis globals.

The original C code exposes hundreds of globals via ``types.c``.  The Python
port keeps the modern ``AppContext`` model as the authoritative source of
state, but several legacy subsystems – and the regression tests derived from
them – still import ``micropolis.types`` directly.  This module keeps that
import working by re-exporting the original constants and by providing a small
selection of mutable globals that mirror the original layout.  The structures
here are intentionally simple so tests can freely overwrite them without
needing to instantiate the full simulation stack.
"""

from __future__ import annotations

from micropolis import constants as _constants
from micropolis.constants import (
    HWLDX,
    HWLDY,
    PWRMAPSIZE,
    SM_X,
    SM_Y,
    WORLD_X,
    WORLD_Y,
)


def _re_export_constants() -> None:
    for name in dir(_constants):
        if name.startswith("_"):
            continue
        globals()[name] = getattr(_constants, name)


_re_export_constants()


# ---------------------------------------------------------------------------
# World-sized helper factories
# ---------------------------------------------------------------------------


def _grid(width: int, height: int, default: int = 0) -> list[list[int]]:
    """Return a width × height grid filled with ``default``."""

    return [[default for _ in range(height)] for _ in range(width)]


# ---------------------------------------------------------------------------
# Map / overlay buffers (sized to match the original engine)
# ---------------------------------------------------------------------------

map_data: list[list[int]] = _grid(WORLD_X, WORLD_Y)
power_map = bytearray(PWRMAPSIZE)
land_value_mem: list[list[int]] = _grid(HWLDX, HWLDY)
pollution_mem: list[list[int]] = _grid(HWLDX, HWLDY)
pop_density: list[list[int]] = _grid(HWLDX, HWLDY)
crime_mem: list[list[int]] = _grid(HWLDX, HWLDY)
com_rate: list[list[int]] = _grid(SM_X, SM_Y)
rate_og_mem: list[list[int]] = _grid(SM_X, SM_Y)
# Additional overlays used by legacy code/tests
trf_density: list[list[int]] = _grid(HWLDX, HWLDY)
tem: list[list[int]] = _grid(HWLDX, HWLDY)
tem2: list[list[int]] = _grid(HWLDX, HWLDY)
terrain_mem: list[list[int]] = _grid(QWX, QWY)


# ---------------------------------------------------------------------------
# Legacy counters mirrored from the C globals.  These serve as convenient
# stand-ins that tests can read and mutate directly.
# ---------------------------------------------------------------------------

res_pop = 0
com_pop = 0
ind_pop = 0
hosp_pop = 0
church_pop = 0
pwrd_z_cnt = 0
un_pwrd_z_cnt = 0
need_hosp = 0
need_church = 0
r_value = 0
c_value = 0
i_value = 0
s_map_x = WORLD_X // 2
s_map_y = WORLD_Y // 2
cchr = 0
cchr9 = 0
city_time = 0
starting_year = 1900
city_name = "New City"
SimSpeed = 3
SimMetaSpeed = 3
sim_paused_speed = 0
sim_delay = 0
sim_skips = 0
sim_skip = 0
heat_steps = 0
heat_flow = 0
heat_rule = 0
TotalFunds = 20000
CityTax = 7
firePercent = 0.0
policePercent = 0.0
roadPercent = 0.0
fireMaxValue = 0
policeMaxValue = 0
roadMaxValue = 0
LVAverage = 0
CrimeAverage = 0
PolluteAverage = 0
CCx = WORLD_X // 2
CCy = WORLD_Y // 2
PolMaxX = 0
PolMaxY = 0
CrimeMaxX = 0
CrimeMaxY = 0
TrafMaxX = 0
TrafMaxY = 0
FloodX = 0
FloodY = 0
CrashX = 0
CrashY = 0
MeltX = 0
MeltY = 0
OverRide = 0
Expensive = 0
Players = 1
Votes = 0
BobHeight = 8
PendingTool = -1
PendingX = 0
PendingY = 0
Displays = ""
MicropolisVersion = "1.0"
LakeLevel = 0
TreeLevel = 0
CurveLevel = 0
CreateIsland = 0
DoOverlay = 0
DonDither = 0
FlushStyle = 0
tkCollapseMotion = 0
NeedRest = False
MustUpdateFunds = 0
MustUpdateOptions = 0

doAnimation = 1
doMessages = 1
doNotices = 1

# Lowercase aliases commonly used by tests
total_funds = TotalFunds


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def reset_world_state(default_tile: int = 0) -> None:
    """Reset all world-sized buffers to a uniform value.

    Tests that rely on a pristine map can call this helper instead of manually
    rebuilding every array.
    """

    global map_data, power_map, land_value_mem, pollution_mem, pop_density
    global crime_mem, com_rate, rate_og_mem

    map_data = _grid(WORLD_X, WORLD_Y, default_tile)
    power_map = bytearray(PWRMAPSIZE)
    land_value_mem = _grid(HWLDX, HWLDY)
    pollution_mem = _grid(HWLDX, HWLDY)
    pop_density = _grid(HWLDX, HWLDY)
    crime_mem = _grid(HWLDX, HWLDY)
    com_rate = _grid(SM_X, SM_Y)
    rate_og_mem = _grid(SM_X, SM_Y)


__all__ = [name for name in globals() if not name.startswith("_")]


# ---------------------------------------------------------------------------
# Legacy factory helpers (test/runtime compatibility)
# ---------------------------------------------------------------------------


def MakeNewView():
    """Create a new default map view for legacy code/tests.

    This helper exists for compatibility with older tests that call
    ``types.MakeNewView()``. In the modern API creating views requires an
    ``AppContext``; when running under the test harness we try to locate
    a test-provided context on the package object at
    ``micropolis._AUTO_TEST_CONTEXT`` and use it to construct the view.

    Raises:
        RuntimeError: if no test context is available.
    """

    try:
        import importlib

        pkg = importlib.import_module("micropolis")
        ctx = getattr(pkg, "_AUTO_TEST_CONTEXT", None)
    except Exception:
        ctx = None

    if ctx is None:
        raise RuntimeError(
            "MakeNewView requires an AppContext when called without context"
        )

    # Import the modern factory and create a map view.
    from .sim_view import create_map_view

    return create_map_view(ctx)
