# test_animations.py: Unit tests for animations.py
#
# Tests the tile animation system to ensure animated tiles are properly
# updated according to the animation tables and preserve tile flags.

import unittest
from unittest.mock import patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from micropolis import animations
from micropolis import macros
from micropolis import types
from micropolis import animation


class TestAnimations(unittest.TestCase):
    """Test cases for the tile animation system"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Initialize a fresh map for each test
        types.Map = [[0 for _ in range(macros.WORLD_Y)] for _ in range(macros.WORLD_X)]

    def test_animate_tiles_no_animated_tiles(self):
        """Test animate_tiles with no animated tiles."""
        # Fill map with non-animated tiles
        for x in range(macros.WORLD_X):
            for y in range(macros.WORLD_Y):
                types.Map[x][y] = 100  # Regular tile, no ANIMBIT

        original_map = [row[:] for row in types.Map]
        animations.animate_tiles()

        # Map should be unchanged
        self.assertEqual(types.Map, original_map)

    def test_animate_tiles_fire_animation(self):
        """Test animation of fire tiles."""
        # Place a fire tile (index 56, which should animate to 57)
        test_x, test_y = 10, 20
        fire_tile = 56 | macros.ANIMBIT  # Fire tile with animation bit
        types.Map[test_x][test_y] = fire_tile

        animations.animate_tiles()

        # Fire tile should have animated to next frame (57) but kept ANIMBIT
        expected_tile = 57 | macros.ANIMBIT
        self.assertEqual(types.Map[test_x][test_y], expected_tile)

    def test_animate_tiles_traffic_animation(self):
        """Test animation of traffic tiles."""
        # Place a light traffic tile (index 80, should animate to 128)
        test_x, test_y = 15, 25
        traffic_tile = 80 | macros.ANIMBIT | macros.PWRBIT  # Traffic with power and animation
        types.Map[test_x][test_y] = traffic_tile

        animations.animate_tiles()

        # Traffic tile should animate but preserve PWRBIT and ANIMBIT
        expected_tile = 128 | macros.ANIMBIT | macros.PWRBIT
        self.assertEqual(types.Map[test_x][test_y], expected_tile)

    def test_animate_tiles_multiple_tiles(self):
        """Test animation of multiple animated tiles simultaneously."""
        # Place several different animated tiles
        tiles_to_test = [
            (5, 5, 56 | macros.ANIMBIT),      # Fire
            (10, 10, 80 | macros.ANIMBIT),    # Light traffic
            (20, 20, 144 | macros.ANIMBIT),   # Heavy traffic
            (30, 30, 833 | macros.ANIMBIT),   # Radar dish
        ]

        expected_results = [
            (5, 5, 57 | macros.ANIMBIT),      # Fire -> 57
            (10, 10, 128 | macros.ANIMBIT),   # Light traffic -> 128
            (20, 20, 192 | macros.ANIMBIT),   # Heavy traffic -> 192
            (30, 30, 834 | macros.ANIMBIT),   # Radar dish -> 834
        ]

        # Set up tiles
        for x, y, tile in tiles_to_test:
            types.Map[x][y] = tile

        animations.animate_tiles()

        # Check all tiles animated correctly
        for x, y, expected_tile in expected_results:
            with self.subTest(x=x, y=y):
                self.assertEqual(types.Map[x][y], expected_tile)

    def test_animate_tiles_preserves_non_animated(self):
        """Test that non-animated tiles are left unchanged."""
        # Mix of animated and non-animated tiles
        animated_tile = 56 | macros.ANIMBIT
        non_animated_tile = 100 | macros.PWRBIT  # No ANIMBIT

        types.Map[5][5] = animated_tile
        types.Map[10][10] = non_animated_tile

        animations.animate_tiles()

        # Animated tile should change
        self.assertEqual(types.Map[5][5], 57 | macros.ANIMBIT)
        # Non-animated tile should remain unchanged
        self.assertEqual(types.Map[10][10], non_animated_tile)

    def test_animate_tiles_invalid_index(self):
        """Test handling of tile indices that get masked to valid animation indices."""
        # Use a tile index that when masked with LOMASK gives a valid animation index
        # Create a tile with only ANIMBIT set, and a base index that masks to 976
        # We need tile_value & LOMASK = 976, and tile_value & ALLBITS = ANIMBIT
        # So tile_value = 976 | ANIMBIT = 976 | 0x1000 = 4976
        tile_value = 976 | macros.ANIMBIT  # This will mask to 976 and animate to ani_tile[976] = 0
        types.Map[5][5] = tile_value

        animations.animate_tiles()

        # Should animate to ani_tile[976] = 0, with ANIMBIT preserved
        expected_tile = 0 | macros.ANIMBIT
        self.assertEqual(types.Map[5][5], expected_tile)

    def test_count_animated_tiles_empty_map(self):
        """Test counting animated tiles on an empty map."""
        count = animations.count_animated_tiles()
        self.assertEqual(count, 0)

    def test_count_animated_tiles_with_animated(self):
        """Test counting animated tiles."""
        # Set up some animated tiles
        types.Map[0][0] = 56 | macros.ANIMBIT
        types.Map[1][1] = 80 | macros.ANIMBIT
        types.Map[2][2] = 100  # Not animated

        count = animations.count_animated_tiles()
        self.assertEqual(count, 2)

    def test_get_animated_tile_positions(self):
        """Test getting positions of all animated tiles."""
        # Set up animated tiles at specific positions
        positions = [(0, 0), (5, 5), (10, 10)]
        for x, y in positions:
            types.Map[x][y] = 56 | macros.ANIMBIT

        # Add a non-animated tile
        types.Map[15][15] = 100

        animated_positions = animations.get_animated_tile_positions()

        # Should only return animated tile positions
        self.assertEqual(len(animated_positions), 3)
        self.assertIn((0, 0), animated_positions)
        self.assertIn((5, 5), animated_positions)
        self.assertIn((10, 10), animated_positions)
        self.assertNotIn((15, 15), animated_positions)

    def test_get_animation_info_non_animated(self):
        """Test getting animation info for non-animated tile."""
        types.Map[5][5] = 100  # Not animated

        info = animations.get_animation_info(5, 5)
        self.assertIsNone(info)

    def test_get_animation_info_animated(self):
        """Test getting animation info for animated tile."""
        tile_value = 56 | macros.ANIMBIT | macros.PWRBIT
        types.Map[5][5] = tile_value

        info = animations.get_animation_info(5, 5)

        self.assertIsNotNone(info)
        self.assertEqual(info['position'], (5, 5))
        self.assertEqual(info['tile_value'], tile_value)
        self.assertEqual(info['tile_index'], 56)
        self.assertEqual(info['tile_flags'], tile_value & macros.ALLBITS)
        self.assertTrue(info['is_animated'])
        self.assertEqual(info['category'], 'fire')
        self.assertEqual(info['sync_value'], 0xff)

    def test_get_animation_info_out_of_bounds(self):
        """Test getting animation info for out-of-bounds coordinates."""
        info = animations.get_animation_info(-1, 0)
        self.assertIsNone(info)

        info = animations.get_animation_info(macros.WORLD_X, 0)
        self.assertIsNone(info)

    def test_animate_tiles_full_world_coverage(self):
        """Test that animate_tiles covers the entire world."""
        # Place animated tiles at edges and corners
        edge_positions = [
            (0, 0),
            (macros.WORLD_X - 1, 0),
            (0, macros.WORLD_Y - 1),
            (macros.WORLD_X - 1, macros.WORLD_Y - 1),
            (50, 50)  # Center
        ]

        for x, y in edge_positions:
            types.Map[x][y] = 56 | macros.ANIMBIT

        animations.animate_tiles()

        # All animated tiles should have been updated
        for x, y in edge_positions:
            expected_tile = 57 | macros.ANIMBIT
            self.assertEqual(types.Map[x][y], expected_tile,
                           f"Tile at ({x}, {y}) was not animated")

    def test_animate_tiles_preserves_all_flags(self):
        """Test that all tile flags are preserved during animation."""
        # Create tile with multiple flags
        original_flags = macros.ANIMBIT | macros.PWRBIT | macros.CONDBIT | macros.BURNBIT
        tile_value = 56 | original_flags
        types.Map[5][5] = tile_value

        animations.animate_tiles()

        # Should animate to 57 but preserve all flags
        expected_tile = 57 | original_flags
        self.assertEqual(types.Map[5][5], expected_tile)

        # Verify specific flags are preserved
        result_tile = types.Map[5][5]
        self.assertTrue(result_tile & macros.ANIMBIT, "ANIMBIT not preserved")
        self.assertTrue(result_tile & macros.PWRBIT, "PWRBIT not preserved")
        self.assertTrue(result_tile & macros.CONDBIT, "CONDBIT not preserved")
        self.assertTrue(result_tile & macros.BURNBIT, "BURNBIT not preserved")


if __name__ == '__main__':
    unittest.main()