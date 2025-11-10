"""
Test suite for power grid functionality.

Tests the power distribution system including flood-fill algorithm,
power bit manipulation, and connectivity checking.
"""

import array
from src.micropolis import types, power


def test_power_constants():
    """Test that power constants are correctly defined"""
    assert power.POWERMAPROW == (types.WORLD_X + 15) // 16
    assert power.PWRMAPSIZE == power.POWERMAPROW * types.WORLD_Y
    assert power.PWRSTKSIZE == (types.WORLD_X * types.WORLD_Y) // 4
    assert power.PWRBIT == 32768  # 0x8000
    assert power.CONDBIT == 16384  # 0x4000
    print("✓ Power constants test passed")


def test_power_bit_operations():
    """Test power bit manipulation functions"""
    # Initialize power map
    types.PowerMap = array.array('H', [0] * power.PWRMAPSIZE)

    # Test setting and testing power bits
    power.SetPowerBit(10, 20)
    assert power.TestPowerBit(10, 20)
    assert not power.TestPowerBit(11, 20)  # Adjacent bit should be clear

    # Test clearing power bits
    power.ClearPowerBit(10, 20)
    assert not power.TestPowerBit(10, 20)

    print("✓ Power bit operations test passed")


def test_move_map_sim():
    """Test coordinate movement function"""
    # Test all four directions
    assert power.MoveMapSim(5, 5, 0) == (5, 4)  # North
    assert power.MoveMapSim(5, 5, 1) == (6, 5)  # East
    assert power.MoveMapSim(5, 5, 2) == (5, 6)  # South
    assert power.MoveMapSim(5, 5, 3) == (4, 5)  # West

    # Test invalid direction (should return same position)
    assert power.MoveMapSim(5, 5, 4) == (5, 5)

    print("✓ MoveMapSim test passed")


def test_test_for_cond():
    """Test conductive tile detection"""
    # Set up test map
    types.Map = [[0 for _ in range(types.WORLD_Y)] for _ in range(types.WORLD_X)]

    # Test non-conductive tile
    types.Map[5][5] = 0
    assert not power.TestForCond(5, 5)

    # Test conductive tile
    types.Map[5][5] = power.CONDBIT
    assert power.TestForCond(5, 5)

    # Test tile with other bits but conductive
    types.Map[5][5] = power.CONDBIT | 0x1234
    assert power.TestForCond(5, 5)

    print("✓ TestForCond test passed")


def test_power_scan_basic():
    """Test basic power scan functionality"""
    # Initialize simulation state
    types.Map = [[0 for _ in range(types.WORLD_Y)] for _ in range(types.WORLD_X)]
    types.PowerMap = array.array('H', [0] * power.PWRMAPSIZE)
    types.CoalPop = 1
    types.NuclearPop = 0

    # Reset power stack
    power.PowerStackNum = 0
    power.MaxPower = 0
    power.NumPower = 0

    # Place a power plant at (10, 10)
    types.Map[10][10] = power.PWRBIT

    # Run power scan
    power.DoPowerScan()

    # Check that power plant has power
    assert power.TestPowerBit(10, 10)

    # Check that MaxPower was calculated correctly (CoalPop * 700)
    assert power.MaxPower == 700

    print("✓ Basic power scan test passed")


def run_power_tests():
    """Run all power grid tests"""
    print("Running power grid tests...")

    test_power_constants()
    test_power_bit_operations()
    test_move_map_sim()
    test_test_for_cond()
    test_power_scan_basic()

    print("\n✅ All power grid tests passed!")

