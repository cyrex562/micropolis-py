"""
Test suite for power grid functionality.

Tests the power distribution system including flood-fill algorithm,
power bit manipulation, and connectivity checking.
"""

from micropolis import power
import micropolis.constants
from micropolis.app_config import AppConfig
from micropolis.context import AppContext
import pytest


@pytest.fixture
def app_context() -> AppContext:
    """Provide a fresh application context for power tests."""
    return AppContext(config=AppConfig())


def test_power_constants():
    """Test that power constants are correctly defined."""
    assert power.POWERMAPROW == (micropolis.constants.WORLD_X + 15) // 16
    assert power.PWRMAPSIZE == power.POWERMAPROW * micropolis.constants.WORLD_Y
    assert (
        power.PWRSTKSIZE
        == (micropolis.constants.WORLD_X * micropolis.constants.WORLD_Y) // 4
    )
    assert power.PWRBIT == 32768  # 0x8000
    assert power.CONDBIT == 16384  # 0x4000


def test_power_bit_operations(app_context: AppContext):
    """Test power bit manipulation functions."""
    context = app_context
    context.power_map = [0] * power.PWRMAPSIZE

    power.SetPowerBit(context, 10, 20)
    assert power.TestPowerBit(context, 10, 20)
    assert not power.TestPowerBit(context, 11, 20)

    power.ClearPowerBit(context, 10, 20)
    assert not power.TestPowerBit(context, 10, 20)


def test_move_map_sim():
    """Test coordinate movement function."""
    assert power.MoveMapSim(5, 5, 0) == (5, 4)
    assert power.MoveMapSim(5, 5, 1) == (6, 5)
    assert power.MoveMapSim(5, 5, 2) == (5, 6)
    assert power.MoveMapSim(5, 5, 3) == (4, 5)
    assert power.MoveMapSim(5, 5, 4) == (5, 5)


def test_test_for_cond(app_context: AppContext):
    """Test conductive tile detection."""
    context = app_context
    context.map_data = [
        [0 for _ in range(micropolis.constants.WORLD_Y)]
        for _ in range(micropolis.constants.WORLD_X)
    ]

    context.map_data[5][5] = 0
    assert not power.TestForCond(context, 5, 5)

    context.map_data[5][5] = power.CONDBIT
    assert power.TestForCond(context, 5, 5)

    context.map_data[5][5] = power.CONDBIT | 0x1234
    assert power.TestForCond(context, 5, 5)


def test_power_scan_basic(app_context: AppContext):
    """Test basic power scan functionality."""
    context = app_context
    context.map_data = [
        [0 for _ in range(micropolis.constants.WORLD_Y)]
        for _ in range(micropolis.constants.WORLD_X)
    ]
    context.power_map = [0] * power.PWRMAPSIZE
    context.coal_pop = 1
    context.nuclear_pop = 0
    context.power_stack_num = 0
    context.max_power = 0
    context.num_power = 0
    context.power_stack_x = [0] * power.PWRSTKSIZE
    context.power_stack_y = [0] * power.PWRSTKSIZE

    context.map_data[10][10] = power.PWRBIT

    power.DoPowerScan(context)

    assert power.TestPowerBit(context, 10, 10)
    assert context.max_power == 700

