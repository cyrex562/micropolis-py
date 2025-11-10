#!/usr/bin/env python3
"""
test_generation.py - Unit tests for the city generation system

Tests the generation module functions including map clearing, island creation,
river generation, lake placement, and tree generation.
"""

import unittest
from src.micropolis import generation, types


class TestGeneration(unittest.TestCase):
    """Test cases for the generation system."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reset generation parameters
        generation.TreeLevel = -1
        generation.LakeLevel = -1
        generation.CurveLevel = -1
        generation.CreateIsland = -1

        # Initialize map to dirt
        generation.ClearMap()

    def test_clear_map(self):
        """Test map clearing functionality."""
        # Set some tiles to non-dirt values
        types.Map[10][10] = types.RIVER
        types.Map[20][20] = types.WOODS

        generation.ClearMap()

        # Check that all tiles are dirt
        for x in range(types.WORLD_X):
            for y in range(types.WORLD_Y):
                self.assertEqual(types.Map[x][y], types.DIRT)

    def test_clear_unnatural(self):
        """Test clearing unnatural structures."""
        # Set up map with natural and unnatural tiles
        types.Map[10][10] = types.DIRT  # Natural
        types.Map[20][20] = types.WOODS  # Natural
        types.Map[30][30] = types.ROADBASE  # Unnatural (road)
        types.Map[40][40] = types.RESBASE  # Unnatural (residential)

        generation.ClearUnnatural()

        # Natural tiles should remain
        self.assertEqual(types.Map[10][10], types.DIRT)
        self.assertEqual(types.Map[20][20], types.WOODS)
        # Unnatural tiles should be cleared to dirt
        self.assertEqual(types.Map[30][30], types.DIRT)
        self.assertEqual(types.Map[40][40], types.DIRT)

    def test_make_naked_island(self):
        """Test basic island creation."""
        generation.MakeNakedIsland()

        # Check that edges are river
        self.assertEqual(types.Map[0][0], types.RIVER)
        self.assertEqual(types.Map[types.WORLD_X - 1][types.WORLD_Y - 1], types.RIVER)

        # Check that center area is dirt
        center_x = types.WORLD_X // 2
        center_y = types.WORLD_Y // 2
        self.assertEqual(types.Map[center_x][center_y], types.DIRT)

    def test_make_island(self):
        """Test complete island creation with smoothing and trees."""
        generation.MakeIsland()

        # Should create island, smooth rivers, and add trees
        # Check that some areas have trees
        has_trees = False
        for x in range(types.WORLD_X):
            for y in range(types.WORLD_Y):
                if (types.Map[x][y] & types.LOMASK) >= generation.WOODS_LOW:
                    has_trees = True
                    break
            if has_trees:
                break
        self.assertTrue(has_trees, "Island should contain trees")

    def test_get_rand_start(self):
        """Test random starting position generation."""
        generation.GetRandStart()

        # Check that starting position is within valid bounds
        self.assertGreaterEqual(generation.XStart, 40)
        self.assertLess(generation.XStart, types.WORLD_X - 40)  # Allow some margin
        self.assertGreaterEqual(generation.YStart, 33)
        self.assertLess(generation.YStart, types.WORLD_Y - 33)  # Allow some margin

        # Check that MapX and MapY are set
        self.assertEqual(generation.MapX, generation.XStart)
        self.assertEqual(generation.MapY, generation.YStart)

    def test_move_map(self):
        """Test map position movement."""
        generation.MapX = 50
        generation.MapY = 50

        # Test movement in different directions
        generation.MoveMap(0)  # North
        self.assertEqual(generation.MapX, 50)
        self.assertEqual(generation.MapY, 49)

        generation.MoveMap(2)  # East
        self.assertEqual(generation.MapX, 51)
        self.assertEqual(generation.MapY, 49)

    def test_put_on_map(self):
        """Test tile placement on map."""
        generation.MapX = 10
        generation.MapY = 10

        # Place a river tile
        generation.PutOnMap(types.RIVER, 0, 0)
        self.assertEqual(types.Map[10][10], types.RIVER)

        # Try to place channel on river (should work)
        generation.PutOnMap(types.CHANNEL, 0, 0)
        self.assertEqual(types.Map[10][10], types.CHANNEL)

        # Try to place non-channel on channel (should fail)
        generation.PutOnMap(types.RIVER, 0, 0)
        self.assertEqual(types.Map[10][10], types.CHANNEL)

    def test_briv_plop(self):
        """Test big river segment placement."""
        generation.MapX = 10
        generation.MapY = 10

        generation.BRivPlop()

        # Check that a 9x9 area around the center has been modified
        # The exact pattern depends on the BRMatrix, but some tiles should be non-zero
        modified = False
        for x in range(9):
            for y in range(9):
                if types.Map[generation.MapX + x][generation.MapY + y] != types.DIRT:
                    modified = True
                    break
            if modified:
                break
        self.assertTrue(modified, "BRivPlop should modify tiles")

    def test_sriv_plop(self):
        """Test small river segment placement."""
        generation.MapX = 10
        generation.MapY = 10

        generation.SRivPlop()

        # Check that a 6x6 area around the center has been modified
        modified = False
        for x in range(6):
            for y in range(6):
                if types.Map[generation.MapX + x][generation.MapY + y] != types.DIRT:
                    modified = True
                    break
            if modified:
                break
        self.assertTrue(modified, "SRivPlop should modify tiles")

    def test_tree_splash(self):
        """Test tree cluster generation."""
        # Clear map first
        generation.ClearMap()

        generation.TreeSplash(50, 50)

        # Check that some trees were placed
        has_trees = False
        for x in range(max(0, 50 - 20), min(types.WORLD_X, 50 + 20)):
            for y in range(max(0, 50 - 20), min(types.WORLD_Y, 50 + 20)):
                if (types.Map[x][y] & types.LOMASK) == types.WOODS:
                    has_trees = True
                    break
            if has_trees:
                break
        self.assertTrue(has_trees, "TreeSplash should create trees")

    def test_do_trees(self):
        """Test forest generation across the map."""
        generation.ClearMap()
        generation.TreeLevel = 5  # Fixed amount

        generation.DoTrees()

        # Should create multiple tree clusters
        tree_count = 0
        for x in range(types.WORLD_X):
            for y in range(types.WORLD_Y):
                if (types.Map[x][y] & types.LOMASK) == types.WOODS:
                    tree_count += 1

        self.assertGreater(tree_count, 0, "DoTrees should create trees")

    def test_smooth_river(self):
        """Test river edge smoothing."""
        # Create some REDGE tiles
        types.Map[10][10] = types.REDGE
        types.Map[20][20] = types.REDGE

        generation.SmoothRiver()

        # REDGE tiles should be converted to appropriate river edge tiles
        # The exact result depends on neighboring tiles, but they should change
        self.assertNotEqual(types.Map[10][10], types.REDGE)
        self.assertNotEqual(types.Map[20][20], types.REDGE)

    def test_is_tree(self):
        """Test tree tile detection."""
        # Test tree tiles
        self.assertTrue(generation.IsTree(types.WOODS))
        self.assertTrue(generation.IsTree(types.WOODS + types.BLBNBIT))

        # Test non-tree tiles
        self.assertFalse(generation.IsTree(types.DIRT))
        self.assertFalse(generation.IsTree(types.RIVER))

        # Test boundary conditions
        self.assertTrue(generation.IsTree(generation.WOODS_LOW))
        self.assertTrue(generation.IsTree(generation.WOODS_HIGH))
        self.assertFalse(generation.IsTree(generation.WOODS_LOW - 1))
        self.assertFalse(generation.IsTree(generation.WOODS_HIGH + 1))

    def test_smooth_trees(self):
        """Test tree edge smoothing."""
        # Create some tree tiles
        types.Map[10][10] = types.WOODS + types.BLBNBIT
        types.Map[10][11] = types.WOODS + types.BLBNBIT
        types.Map[11][10] = types.WOODS + types.BLBNBIT

        generation.SmoothTrees()

        # Tree tiles should be converted to appropriate forest edge tiles
        # The exact result depends on neighboring trees
        self.assertNotEqual(types.Map[10][10] & types.LOMASK, types.WOODS)

    def test_smooth_water(self):
        """Test water edge smoothing."""
        # Create a simple water/land boundary
        for x in range(5, 15):
            for y in range(5, 15):
                types.Map[x][y] = types.RIVER
        for x in range(6, 14):
            for y in range(6, 14):
                types.Map[x][y] = types.DIRT

        generation.SmoothWater()

        # Should create REDGE tiles at water/land boundaries
        has_redge = False
        for x in range(types.WORLD_X):
            for y in range(types.WORLD_Y):
                if types.Map[x][y] == types.REDGE:
                    has_redge = True
                    break
            if has_redge:
                break
        self.assertTrue(has_redge, "SmoothWater should create REDGE tiles")

    def test_generate_map_basic(self):
        """Test basic map generation."""
        generation.GenerateMap(12345)

        # Map should be modified from initial dirt state
        modified = False
        for x in range(types.WORLD_X):
            for y in range(types.WORLD_Y):
                if types.Map[x][y] != types.DIRT:
                    modified = True
                    break
            if modified:
                break
        self.assertTrue(modified, "GenerateMap should modify the map")

    def test_erand(self):
        """Test enhanced random number generation."""
        # Test that ERand returns values in correct range
        for _ in range(10):
            result = generation.ERand(100)
            self.assertGreaterEqual(result, 0)
            self.assertLess(result, 100)

        # Test that it uses two random calls
        # (This is hard to test directly, but we can check statistical properties)


if __name__ == '__main__':
    unittest.main()