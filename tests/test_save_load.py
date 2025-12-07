import pytest
import numpy as np
from citysim.simulation.world import GameMap
from citysim.simulation.tile import TileType


def test_map_serialization():
    # 1. Create a map and modify it
    original_map = GameMap(10, 10)
    original_map.set_tile(1, 1, TileType.ROAD)
    original_map.set_tile(2, 2, TileType.RESIDENTIAL)
    original_map.set_tile(3, 3, TileType.WATER)

    # 2. Serialize
    data = original_map.to_dict()

    # Check structure
    assert data["width"] == 10
    assert data["height"] == 10
    assert len(data["grid"]) == 100

    # 3. Deserialize
    restored_map = GameMap.from_dict(data)

    # 4. Verify contents
    assert restored_map.width == 10
    assert restored_map.height == 10
    assert restored_map.get_tile(1, 1) == TileType.ROAD
    assert restored_map.get_tile(2, 2) == TileType.RESIDENTIAL
    assert restored_map.get_tile(3, 3) == TileType.WATER
    assert restored_map.get_tile(0, 0) == TileType.DIRT  # Default

    # Verify arrays match
    np.testing.assert_array_equal(original_map.grid, restored_map.grid)


def test_large_map_serialization():
    # Test with standard size
    game_map = GameMap(64, 64)
    game_map.set_tile(63, 63, TileType.POWER_PLANT)

    data = game_map.to_dict()
    restored = GameMap.from_dict(data)

    assert restored.get_tile(63, 63) == TileType.POWER_PLANT
