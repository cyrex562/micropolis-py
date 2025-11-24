#!/usr/bin/env python3
"""
test_generation.py - Unit tests for the city generation system

Tests the generation module functions including map clearing, island creation,
river generation, lake placement, and tree generation.
"""

from micropolis import constants as const
from src.micropolis import generation


from tests.assertions import Assertions


class TestGeneration(Assertions):
    """Test cases for the generation system."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reset generation parameters
        generation.tree_level = -1
        generation.lake_level = -1
        generation.curve_level = -1
        generation.create_island = -1

        # Initialize map to dirt
        generation.ClearMap(context)

    def test_clear_map(self):
        """Test map clearing functionality."""
        # Set some tiles to non-dirt values
        context.map_data[10][10] = const.RIVER
        context.map_data[20][20] = const.WOODS

        generation.ClearMap(context)

        # Check that all tiles are dirt
        for x in range(const.WORLD_X):
            for y in range(const.WORLD_Y):
                self.assertEqual(context.map_data[x][y], const.DIRT)

    def test_clear_unnatural(self):
        """Test clearing unnatural structures."""
        # Set up map with natural and unnatural tiles
        context.map_data[10][10] = const.DIRT  # Natural
        context.map_data[20][20] = const.WOODS  # Natural
        context.map_data[30][30] = const.ROADBASE  # Unnatural (road)
        context.map_data[40][40] = const.RESBASE  # Unnatural (residential)

        generation.ClearUnnatural(context)

        # Natural tiles should remain
        self.assertEqual(context.map_data[10][10], const.DIRT)
        self.assertEqual(context.map_data[20][20], const.WOODS)
        # Unnatural tiles should be cleared to dirt
        self.assertEqual(context.map_data[30][30], const.DIRT)
        self.assertEqual(context.map_data[40][40], const.DIRT)

    def test_make_naked_island(self):
        """Test basic island creation."""
        generation.MakeNakedIsland(context)

        # Check that edges are river
        self.assertEqual(context.map_data[0][0], const.RIVER)
        self.assertEqual(
            context.map_data[const.WORLD_X - 1][
                const.WORLD_Y - 1
            ],
            const.RIVER,
        )

        # Check that center area is dirt
        center_x = const.WORLD_X // 2
        center_y = const.WORLD_Y // 2
        self.assertEqual(context.map_data[center_x][center_y], const.DIRT)

    def test_make_island(self):
        """Test complete island creation with smoothing and trees."""
        generation.MakeIsland(context)

        # Should create island, smooth rivers, and add trees
        # Check that some areas have trees
        has_trees = False
        for x in range(const.WORLD_X):
            for y in range(const.WORLD_Y):
                if (context.map_data[x][y] & const.LOMASK) >= generation.WOODS_LOW:
                    has_trees = True
                    break
            if has_trees:
                break
        self.assertTrue(has_trees, "Island should contain trees")

    def test_get_rand_start(self):
        """Test random starting position generation."""
        generation.GetRandStart(context)

        # Check that starting position is within valid bounds
        self.assertGreaterEqual(generation.x_start, 40)
        self.assertLess(
            generation.x_start, const.WORLD_X - 40
        )  # Allow some margin
        self.assertGreaterEqual(generation.y_start, 33)
        self.assertLess(
            generation.y_start, const.WORLD_Y - 33
        )  # Allow some margin

        # Check that MapX and MapY are set
        self.assertEqual(generation.map_x, generation.x_start)
        self.assertEqual(generation.map_y, generation.y_start)

    def test_move_map(self):
        """Test map position movement."""
        generation.map_x = 50
        generation.map_y = 50

        # Test movement in different directions
        generation.MoveMap(context, 0)  # North
        self.assertEqual(generation.map_x, 50)
        self.assertEqual(generation.map_y, 49)

        generation.MoveMap(context, 2)  # East
        self.assertEqual(generation.map_x, 51)
        self.assertEqual(generation.map_y, 49)

    def test_put_on_map(self):
        """Test tile placement on map."""
        generation.map_x = 10
        generation.map_y = 10

        # Place a river tile
        generation.PutOnMap(context, const.RIVER, 0, 0)
        self.assertEqual(context.map_data[10][10], const.RIVER)

        # Try to place channel on river (should work)
        generation.PutOnMap(context, const.CHANNEL, 0, 0)
        self.assertEqual(context.map_data[10][10], const.CHANNEL)

        # Try to place non-channel on channel (should fail)
        generation.PutOnMap(context, const.RIVER, 0, 0)
        self.assertEqual(context.map_data[10][10], const.CHANNEL)

    def test_briv_plop(self):
        """Test big river segment placement."""
        generation.map_x = 10
        generation.map_y = 10

        generation.BRivPlop(context)

        # Check that a 9x9 area around the center has been modified
        # The exact pattern depends on the BRMatrix, but some tiles should be non-zero
        modified = False
        for x in range(9):
            for y in range(9):
                if (
                    context.map_data[generation.map_x + x][generation.map_y + y]
                    != const.DIRT
                ):
                    modified = True
                    break
            if modified:
                break
        self.assertTrue(modified, "BRivPlop should modify tiles")

    def test_sriv_plop(self):
        """Test small river segment placement."""
        generation.map_x = 10
        generation.map_y = 10

        generation.SRivPlop(context)

        # Check that a 6x6 area around the center has been modified
        modified = False
        for x in range(6):
            for y in range(6):
                if (
                    context.map_data[generation.map_x + x][generation.map_y + y]
                    != const.DIRT
                ):
                    modified = True
                    break
            if modified:
                break
        self.assertTrue(modified, "SRivPlop should modify tiles")

    def test_tree_splash(self):
        """Test tree cluster generation."""
        # Clear map first
        generation.ClearMap(context)

        generation.TreeSplash(context, 50, 50)

        # Check that some trees were placed
        has_trees = False
        for x in range(max(0, 50 - 20), min(const.WORLD_X, 50 + 20)):
            for y in range(max(0, 50 - 20), min(const.WORLD_Y, 50 + 20)):
                if (context.map_data[x][y] & const.LOMASK) == const.WOODS:
                    has_trees = True
                    break
            if has_trees:
                break
        self.assertTrue(has_trees, "TreeSplash should create trees")

    def test_do_trees(self):
        """Test forest generation across the map."""
        generation.ClearMap(context)
        generation.tree_level = 5  # Fixed amount

        generation.DoTrees(context)

        # Should create multiple tree clusters
        tree_count = 0
        for x in range(const.WORLD_X):
            for y in range(const.WORLD_Y):
                if (context.map_data[x][y] & const.LOMASK) == const.WOODS:
                    tree_count += 1

        self.assertGreater(tree_count, 0, "DoTrees should create trees")

    def test_smooth_river(self):
        """Test river edge smoothing."""
        # Create some REDGE tiles
        context.map_data[10][10] = const.REDGE
        context.map_data[20][20] = const.REDGE

        generation.SmoothRiver(context)

        # REDGE tiles should be converted to appropriate river edge tiles
        # The exact result depends on neighboring tiles, but they should change
        self.assertNotEqual(context.map_data[10][10], const.REDGE)
        self.assertNotEqual(context.map_data[20][20], const.REDGE)

    def test_is_tree(self):
        """Test tree tile detection."""
        # Test tree tiles
        self.assertTrue(generation.IsTree(const.WOODS))
        self.assertTrue(generation.IsTree(const.WOODS + const.BLBNBIT))

        # Test non-tree tiles
        self.assertFalse(generation.IsTree(const.DIRT))
        self.assertFalse(generation.IsTree(const.RIVER))

        # Test boundary conditions
        self.assertTrue(generation.IsTree(generation.WOODS_LOW))
        self.assertTrue(generation.IsTree(generation.WOODS_HIGH))
        self.assertFalse(generation.IsTree(generation.WOODS_LOW - 1))
        self.assertFalse(generation.IsTree(generation.WOODS_HIGH + 1))

    def test_smooth_trees(self):
        """Test tree edge smoothing."""
        # Create some tree tiles
        context.map_data[10][10] = const.WOODS + const.BLBNBIT
        context.map_data[10][11] = const.WOODS + const.BLBNBIT
        context.map_data[11][10] = const.WOODS + const.BLBNBIT

        generation.SmoothTrees(context)

        # Tree tiles should be converted to appropriate forest edge tiles
        # The exact result depends on neighboring trees
        self.assertNotEqual(context.map_data[10][10] & const.LOMASK, const.WOODS)

    def test_smooth_water(self):
        """Test water edge smoothing."""
        # Create a simple water/land boundary
        for x in range(5, 15):
            for y in range(5, 15):
                context.map_data[x][y] = const.RIVER
        for x in range(6, 14):
            for y in range(6, 14):
                context.map_data[x][y] = const.DIRT

        generation.SmoothWater(context)

        # Should create REDGE tiles at water/land boundaries
        has_redge = False
        for x in range(const.WORLD_X):
            for y in range(const.WORLD_Y):
                if context.map_data[x][y] == const.REDGE:
                    has_redge = True
                    break
            if has_redge:
                break
        self.assertTrue(has_redge, "SmoothWater should create REDGE tiles")

    def test_generate_map_basic(self):
        """Test basic map generation."""
        generation.GenerateMap(context, 12345)

        # Map should be modified from initial dirt state
        modified = False
        for x in range(const.WORLD_X):
            for y in range(const.WORLD_Y):
                if context.map_data[x][y] != const.DIRT:
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
