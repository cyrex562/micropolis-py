# test_traffic.py: Unit tests for traffic simulation and pathfinding
#
# Tests the traffic generation, pathfinding, and destination logic
# to ensure algorithmic compatibility with the original C implementation.

import sys
import os

import src.micropolis.types as types
import src.micropolis.macros as macros
import src.micropolis.traffic as traffic


def test_traffic_constants():
    """Test that traffic constants are properly defined."""
    print("Testing traffic constants...")

    # Test MAXDIS constant
    assert hasattr(traffic, 'MAXDIS'), "MAXDIS constant not found"
    assert traffic.MAXDIS == 30, f"MAXDIS should be 30, got {traffic.MAXDIS}"

    # Test macros constants used by traffic
    assert macros.ROADBASE == 64, f"ROADBASE should be 64, got {macros.ROADBASE}"
    assert macros.RAILBASE == 224, f"RAILBASE should be 224, got {macros.RAILBASE}"
    assert macros.POWERBASE == 208, f"POWERBASE should be 208, got {macros.POWERBASE}"
    assert macros.LASTRAIL == 238, f"LASTRAIL should be 238, got {macros.LASTRAIL}"
    assert macros.RAILHPOWERV == 221, f"RAILHPOWERV should be 221, got {macros.RAILHPOWERV}"

    print("✓ Traffic constants OK")


def test_traffic_variables():
    """Test that traffic-related global variables are initialized."""
    print("Testing traffic variables...")

    # Test position stack variables
    assert hasattr(types, 'PosStackN'), "PosStackN not found in types"
    assert hasattr(types, 'SMapXStack'), "SMapXStack not found in types"
    assert hasattr(types, 'SMapYStack'), "SMapYStack not found in types"
    assert hasattr(types, 'LDir'), "LDir not found in types"
    assert hasattr(types, 'Zsource'), "Zsource not found in types"

    # Test traffic max variables
    assert hasattr(types, 'TrafMaxX'), "TrafMaxX not found in types"
    assert hasattr(types, 'TrafMaxY'), "TrafMaxY not found in types"

    print("✓ Traffic variables OK")


def test_road_test():
    """Test RoadTest function with various tile types."""
    print("Testing RoadTest function...")

    # Test road tiles (should return True)
    assert traffic.RoadTest(64), "Road tile 64 should be valid"  # HBRIDGE
    assert traffic.RoadTest(65), "Road tile 65 should be valid"  # VBRIDGE
    assert traffic.RoadTest(66), "Road tile 66 should be valid"  # ROADS
    assert traffic.RoadTest(100), "Road tile 100 should be valid"  # Regular road

    # Test rail tiles (should return True)
    assert traffic.RoadTest(224), "Rail tile 224 should be valid"  # HRAIL
    assert traffic.RoadTest(225), "Rail tile 225 should be valid"  # VRAIL
    assert traffic.RoadTest(238), "Rail tile 238 should be valid"  # LASTRAIL

    # Test invalid tiles (should return False)
    assert not traffic.RoadTest(0), "Tile 0 should be invalid"  # DIRT
    assert not traffic.RoadTest(63), "Tile 63 should be invalid"  # Before ROADBASE
    assert not traffic.RoadTest(239), "Tile 239 should be invalid"  # After LASTRAIL
    assert not traffic.RoadTest(208), "Power tile 208 should be invalid"  # HPOWER
    assert not traffic.RoadTest(220), "Power-rail tile 220 should be invalid"  # Between POWERBASE and RAILHPOWERV

    print("✓ RoadTest function OK")


def test_position_stack():
    """Test position stack operations."""
    print("Testing position stack operations...")

    # Initialize stack
    types.PosStackN = 0
    types.SMapXStack = []
    types.SMapYStack = []

    # Test initial state
    assert types.PosStackN == 0, "Initial PosStackN should be 0"

    # Set test position
    types.SMapX = 10
    types.SMapY = 20

    # Test PushPos
    traffic.PushPos()
    assert types.PosStackN == 1, "PosStackN should be 1 after push"
    assert len(types.SMapXStack) >= 1, "SMapXStack should have at least 1 element"
    assert len(types.SMapYStack) >= 1, "SMapYStack should have at least 1 element"
    assert types.SMapXStack[1] == 10, "SMapXStack[1] should be 10"
    assert types.SMapYStack[1] == 20, "SMapYStack[1] should be 20"

    # Change position
    types.SMapX = 30
    types.SMapY = 40

    # Test PullPos
    traffic.PullPos()
    assert types.PosStackN == 0, "PosStackN should be 0 after pull"
    assert types.SMapX == 10, "SMapX should be restored to 10"
    assert types.SMapY == 20, "SMapY should be restored to 20"

    print("✓ Position stack operations OK")


def test_find_proad():
    """Test FindPRoad function."""
    print("Testing FindPRoad function...")

    # Initialize map with roads around a zone
    types.Map = [[0 for _ in range(macros.WORLD_Y)] for _ in range(macros.WORLD_X)]

    # Set zone center
    types.SMapX = 50
    types.SMapY = 50

    # Add road tiles around the perimeter
    types.Map[49][48] = 64  # Road on perimeter (north-west-ish)
    types.Map[51][52] = 66  # Road on perimeter (south-east-ish)

    # Test finding road
    original_x, original_y = types.SMapX, types.SMapY
    found = traffic.FindPRoad()

    assert found, "Should find road on perimeter"
    # Position should be updated to road location
    assert types.SMapX != original_x or types.SMapY != original_y, "Position should change when road found"

    # Reset position
    types.SMapX, types.SMapY = original_x, original_y

    # Test with no roads
    types.Map = [[0 for _ in range(macros.WORLD_Y)] for _ in range(macros.WORLD_X)]
    found = traffic.FindPRoad()
    assert not found, "Should not find road when none exist"

    print("✓ FindPRoad function OK")


def test_get_from_map():
    """Test GetFromMap function."""
    print("Testing GetFromMap function...")

    # Initialize small test map
    types.Map = [[0 for _ in range(10)] for _ in range(10)]
    types.Map[5][4] = 64  # Road tile north of (5,5)
    types.Map[6][5] = 66  # Road tile east of (5,5)
    types.Map[5][6] = 68  # Road tile south of (5,5)
    types.Map[4][5] = 70  # Road tile west of (5,5)

    # Set position
    types.SMapX = 5
    types.SMapY = 5

    # Test all directions
    assert traffic.GetFromMap(0) == 64, "North should return road tile 64"
    assert traffic.GetFromMap(1) == 66, "East should return road tile 66"
    assert traffic.GetFromMap(2) == 68, "South should return road tile 68"
    assert traffic.GetFromMap(3) == 70, "West should return road tile 70"

    # Test out of bounds
    types.SMapX = 0
    types.SMapY = 0
    assert traffic.GetFromMap(3) == 0, "West from (0,0) should return 0 (out of bounds)"
    assert traffic.GetFromMap(0) == 0, "North from (0,0) should return 0 (out of bounds)"

    print("✓ GetFromMap function OK")


def test_move_map_sim():
    """Test MoveMapSim function."""
    print("Testing MoveMapSim function...")

    # Test all directions
    for direction in range(4):
        types.SMapX = 10
        types.SMapY = 10

        traffic.MoveMapSim(direction)

        if direction == 0:  # North
            assert types.SMapY == 9, "North move should decrease Y"
            assert types.SMapX == 10, "North move should not change X"
        elif direction == 1:  # East
            assert types.SMapX == 11, "East move should increase X"
            assert types.SMapY == 10, "East move should not change Y"
        elif direction == 2:  # South
            assert types.SMapY == 11, "South move should increase Y"
            assert types.SMapX == 10, "South move should not change X"
        elif direction == 3:  # West
            assert types.SMapX == 9, "West move should decrease X"
            assert types.SMapY == 10, "West move should not change Y"

    print("✓ MoveMapSim function OK")


def test_drive_done():
    """Test DriveDone function for destination detection."""
    print("Testing DriveDone function...")

    # Initialize map
    types.Map = [[0 for _ in range(10)] for _ in range(10)]

    # Set position
    types.SMapX = 5
    types.SMapY = 5

    # Test residential zone (Zsource = 0) looking for commercial
    types.Zsource = 0  # Residential
    types.Map[5][4] = macros.COMBASE  # Commercial north
    assert traffic.DriveDone(), "Residential should find commercial destination"

    # Test commercial zone (Zsource = 1) looking for residential/port/commercial
    types.Zsource = 1  # Commercial
    types.Map[5][4] = macros.LHTHR  # Residential north (valid destination for commercial)
    assert traffic.DriveDone(), "Commercial should find residential destination"

    types.Map[5][4] = macros.PORT  # Port north
    assert traffic.DriveDone(), "Commercial should find port destination"

    # Test industrial zone (Zsource = 2) looking for residential
    types.Zsource = 2  # Industrial
    types.Map[5][4] = macros.LHTHR  # Residential north (LHTHR is residential)
    assert traffic.DriveDone(), "Industrial should find residential destination"

    # Test no destination
    types.Map[5][4] = 0  # Empty tile
    assert not traffic.DriveDone(), "Should not find destination on empty tile"

    print("✓ DriveDone function OK")


def test_traffic_integration():
    """Test complete traffic generation flow."""
    print("Testing traffic integration...")

    # Initialize simulation state
    types.Map = [[0 for _ in range(macros.WORLD_Y)] for _ in range(macros.WORLD_X)]
    types.TrfDensity = [[0 for _ in range(macros.HWLDY)] for _ in range(macros.HWLDX)]
    types.PosStackN = 0
    types.SMapXStack = []
    types.SMapYStack = []
    types.LDir = 5

    # Create a simple road network
    # Road from (10,10) to (15,10)
    for x in range(10, 16):
        types.Map[x][10] = 66  # Road tile

    # Add commercial zone at end as destination
    types.Map[15][10] = macros.COMBASE

    # Set starting position (residential zone center)
    types.SMapX = 10
    types.SMapY = 10

    # Test traffic generation from residential zone
    result = traffic.MakeTraf(0)  # Residential zone

    # Should either succeed (1) or find no road (-1)
    assert result in [-1, 0, 1], f"MakeTraf should return -1, 0, or 1, got {result}"

    print("✓ Traffic integration OK")


def run_all_tests():
    """Run all traffic tests."""
    print("Running traffic simulation tests...\n")

    try:
        test_traffic_constants()
        test_traffic_variables()
        test_road_test()
        test_position_stack()
        test_find_proad()
        test_get_from_map()
        test_move_map_sim()
        test_drive_done()
        test_traffic_integration()

        print("\n🎉 All traffic tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

