"""
Test initialization functions implementation

Tests for setUpMapProcs, ClearMap, InitFundingLevel, SetFunds, SetGameLevelFunds
"""

import sys
from pathlib import Path

# Add src to path - handle both absolute imports and relative imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(
    0, str(project_root)
)  # Also add project root for 'src.micropolis' imports

from micropolis.app_config import AppConfig
from micropolis.constants import ALMAP, DIRT, NMAPS, WORLD_X, WORLD_Y
from micropolis.context import AppContext
from micropolis.engine import (
    ClearMap,
    InitFundingLevel,
    SetFunds,
    SetGameLevelFunds,
    setUpMapProcs,
)


def test_set_funds_basic():
    """Test SetFunds sets funds correctly"""
    config = AppConfig()
    context = AppContext(config=config)

    # Test positive amount
    SetFunds(context, 15000)
    assert context.total_funds == 15000
    assert context.last_funds == 15000

    # Test negative amount (should be clamped to 0)
    SetFunds(context, -500)
    assert context.total_funds == 0
    assert context.last_funds == 0

    print("✓ test_set_funds_basic passed")


def test_set_game_level_funds():
    """Test SetGameLevelFunds applies correct amounts"""
    config = AppConfig()
    context = AppContext(config=config)

    # Test Easy (level 0)
    SetGameLevelFunds(context, 0)
    assert context.total_funds == 20000

    # Test Medium (level 1)
    SetGameLevelFunds(context, 1)
    assert context.total_funds == 10000

    # Test Hard (level 2)
    SetGameLevelFunds(context, 2)
    assert context.total_funds == 5000

    # Test invalid level (should clamp)
    SetGameLevelFunds(context, 99)
    assert context.total_funds == 5000  # Should use hardest level

    SetGameLevelFunds(context, -1)
    assert context.total_funds == 20000  # Should use easiest level

    print("✓ test_set_game_level_funds passed")


def test_init_funding_level():
    """Test InitFundingLevel sets up budget properly"""
    config = AppConfig()
    context = AppContext(config=config, startup_game_level=1)

    InitFundingLevel(context)

    # Check funding percentages
    assert context.road_percent == 1.0
    assert context.police_percent == 0.0
    assert context.fire_percent == 0.0

    # Check max values
    assert context.road_max_value == 100
    assert context.police_max_value == 100
    assert context.fire_max_value == 100

    # Check effects
    assert context.road_effect == 32
    assert context.police_effect == 1000
    assert context.fire_effect == 1000

    # Check tax
    assert context.city_tax == 7

    # Check funds were set based on level
    assert context.total_funds == 10000  # Level 1 = Medium = $10,000

    print("✓ test_init_funding_level passed")


def test_clear_map():
    """Test ClearMap initializes map to all DIRT"""
    config = AppConfig()
    context = AppContext(config=config)

    # Corrupt some map tiles first
    context.map_data[0][0] = 999
    context.map_data[50][50] = 888
    context.map_data[WORLD_X - 1][WORLD_Y - 1] = 777

    # Clear the map
    ClearMap(context)

    # Check all tiles are DIRT
    for x in range(WORLD_X):
        for y in range(WORLD_Y):
            assert context.map_data[x][y] == DIRT, (
                f"Tile at ({x},{y}) is {context.map_data[x][y]}, expected {DIRT}"
            )

    # Check new_map flag is set
    assert context.new_map == 1

    print("✓ test_clear_map passed")


def test_setup_map_procs():
    """Test setUpMapProcs registers all overlay callbacks"""
    config = AppConfig()
    context = AppContext(config=config)

    # Initially mapProcs should be empty or None
    assert len(context.mapProcs) == NMAPS

    # Set up the map procedures
    setUpMapProcs(context)

    # Check that the first overlay (ALMAP) has a callback
    assert context.mapProcs[ALMAP] is not None
    assert callable(context.mapProcs[ALMAP])

    # Check that multiple overlays are registered
    registered_count = sum(1 for proc in context.mapProcs if proc is not None)
    assert registered_count > 0, "No map procedures were registered"

    print(
        f"✓ test_setup_map_procs passed (registered {registered_count} overlay callbacks)"
    )


def test_full_initialization_sequence():
    """Test the full initialization sequence as called in sim_init"""
    config = AppConfig()
    context = AppContext(config=config, startup_game_level=0)

    # Run initialization sequence
    InitFundingLevel(context)
    setUpMapProcs(context)
    ClearMap(context)
    SetFunds(context, 0)  # Reset to 0 before applying level funds
    SetGameLevelFunds(context, context.startup_game_level)

    # Verify final state
    assert context.total_funds == 20000  # Easy mode
    assert context.city_tax == 7
    assert context.road_percent == 1.0
    assert context.new_map == 1

    # Verify map is all DIRT
    sample_tiles = [
        context.map_data[0][0],
        context.map_data[60][50],
        context.map_data[WORLD_X - 1][WORLD_Y - 1],
    ]
    assert all(tile == DIRT for tile in sample_tiles)

    # Verify map procs registered
    assert context.mapProcs[ALMAP] is not None

    print("✓ test_full_initialization_sequence passed")


if __name__ == "__main__":
    test_set_funds_basic()
    test_set_game_level_funds()
    test_init_funding_level()
    test_clear_map()
    test_setup_map_procs()
    test_full_initialization_sequence()

    print("\n✅ All initialization function tests passed!")
