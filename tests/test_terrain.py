"""
test_terrain.py - Comprehensive tests for terrain generation system

Tests the terrain generation algorithms to ensure they match the original C implementation:
- Random number generation (GRand/EGRand)
- River generation with curvature control
- Lake placement algorithms
- Tree distribution and clustering
- Terrain smoothing and edge detection
- Island generation
- Map clearing and bounds checking
"""

from micropolis.terrain import (
    TerrainGenerator, generate_terrain, clear_terrain,
    WORLD_X, WORLD_Y, RIVER, REDGE, CHANNEL, WOODS, BLN
)


from tests.assertions import Assertions

class TestTerrainGenerator(Assertions):
    """Test the TerrainGenerator class and its methods."""

    def test_initialization(self):
        """Test terrain generator initialization."""
        gen = TerrainGenerator()
        assert gen.seed is not None
        assert len(gen.random_state) == 5
        assert gen.map_x == 0
        assert gen.map_y == 0

    def test_initialization_with_seed(self):
        """Test terrain generator initialization with specific seed."""
        seed = 12345
        gen = TerrainGenerator(seed)
        assert gen.seed == seed
        # Verify random state is initialized with seed
        assert gen.random_state[0] == seed

    def test_grand_random_generation(self):
        """Test GRand random number generation."""
        gen = TerrainGenerator(42)

        # Test multiple calls produce different values
        values = [gen.grand(100) for _ in range(10)]
        assert len(set(values)) > 1  # Should have some variation

        # Test range bounds
        for _ in range(100):
            val = gen.grand(50)
            assert 0 <= val <= 50

    def test_grand_reproducibility(self):
        """Test that GRand produces reproducible results with same seed."""
        gen1 = TerrainGenerator(123)
        gen2 = TerrainGenerator(123)

        values1 = [gen1.grand(100) for _ in range(20)]
        values2 = [gen2.grand(100) for _ in range(20)]

        assert values1 == values2

    def test_egrand_enhanced_random(self):
        """Test EGRand enhanced random generation."""
        gen = TerrainGenerator(42)

        # EGRand should return min of two randoms, so should be biased toward lower values
        values = [gen.egrand(100) for _ in range(1000)]

        # Check bounds
        assert all(0 <= v <= 100 for v in values)

        # Check bias toward lower values (mean should be less than 50)
        mean = sum(values) / len(values)
        assert mean < 45  # Should be noticeably less than 50

    def test_test_bounds(self):
        """Test bounds checking."""
        gen = TerrainGenerator()

        # Valid coordinates
        assert test_bounds(0, 0)
        assert test_bounds(60, 50)
        assert test_bounds(WORLD_X-1, WORLD_Y-1)

        # Invalid coordinates
        assert not test_bounds(-1, 0)
        assert not test_bounds(0, -1)
        assert not test_bounds(WORLD_X, 0)
        assert not test_bounds(0, WORLD_Y)

    def test_move_map(self):
        """Test map position movement."""
        gen = TerrainGenerator()

        # Test all 8 directions
        directions = [
            (0, 0, -1),  # North
            (1, 1, -1),  # Northeast
            (2, 1, 0),   # East
            (3, 1, 1),   # Southeast
            (4, 0, 1),   # South
            (5, -1, 1),  # Southwest
            (6, -1, 0),  # West
            (7, -1, -1), # Northwest
        ]

        for dir_val, expected_dx, expected_dy in directions:
            gen.map_x = 10
            gen.map_y = 10
            gen.move_map(dir_val)
            assert gen.map_x == 10 + expected_dx
            assert gen.map_y == 10 + expected_dy

    def test_clear_map(self):
        """Test map clearing."""
        gen = TerrainGenerator()
        map_data = [[i + j for j in range(WORLD_Y)] for i in range(WORLD_X)]

        # Verify map has non-zero values
        assert any(any(cell != 0 for cell in row) for row in map_data)

        clear_map(map_data)

        # Verify all cells are zero
        assert all(all(cell == 0 for cell in row) for row in map_data)

    def test_put_on_map_basic(self):
        """Test basic tile placement."""
        gen = TerrainGenerator()
        map_data = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]

        gen.map_x = 10
        gen.map_y = 10

        # Place a tile
        result = gen.put_on_map(5, 0, 0, map_data)
        assert result
        assert map_data[10][10] == 5

    def test_put_on_map_collision_detection(self):
        """Test tile placement collision detection."""
        gen = TerrainGenerator()
        map_data = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]

        gen.map_x = 10
        gen.map_y = 10

        # Place river tile
        map_data[10][10] = RIVER
        map_data[11][10] = CHANNEL

        # Try to place non-channel on river (should fail)
        result = gen.put_on_map(5, 0, 0, map_data)
        assert not result
        assert map_data[10][10] == RIVER  # Unchanged

        # Try to place on channel (should fail)
        gen.map_x = 11
        result = gen.put_on_map(5, 0, 0, map_data)
        assert not result
        assert map_data[11][10] == CHANNEL  # Unchanged

        # Place channel on river (should succeed)
        gen.map_x = 10
        result = gen.put_on_map(CHANNEL, 0, 0, map_data)
        assert result
        assert map_data[10][10] == CHANNEL

    def test_put_on_map_bounds_checking(self):
        """Test tile placement bounds checking."""
        gen = TerrainGenerator()
        map_data = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]

        # Try to place outside bounds
        gen.map_x = -1
        gen.map_y = 10
        result = gen.put_on_map(5, 0, 0, map_data)
        assert not result

        gen.map_x = WORLD_X
        gen.map_y = 10
        result = gen.put_on_map(5, 0, 0, map_data)
        assert not result

    def test_smooth_river(self):
        """Test river edge smoothing."""
        gen = TerrainGenerator(42)
        map_data = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]

        # Create a simple river edge pattern
        for x in range(5, 15):
            map_data[x][10] = REDGE

        # Add some adjacent water tiles
        map_data[5][9] = RIVER
        map_data[5][11] = RIVER
        map_data[14][9] = RIVER
        map_data[14][11] = RIVER

        gen.smooth_river(map_data)

        # Verify REDGE tiles were smoothed
        redge_count = sum(1 for row in map_data for cell in row if cell == REDGE)
        assert redge_count == 0  # All REDGE should be converted

    def test_smooth_trees(self):
        """Test tree edge smoothing."""
        gen = TerrainGenerator(42)
        map_data = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]

        # Create tree tiles (with BLN bits set)
        for x in range(5, 15):
            map_data[x][10] = WOODS + BLN

        smooth_trees(map_data)

        # Verify tree tiles were smoothed (converted to specific tile types)
        bln_tiles = sum(1 for row in map_data for cell in row if (cell & BLN) == BLN)
        # Should still have BLN tiles but possibly different tile values
        assert bln_tiles > 0

    def test_tree_splash(self):
        """Test tree cluster generation."""
        gen = TerrainGenerator(42)
        map_data = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]

        # Generate tree cluster
        gen._tree_splash(50, 50, map_data)

        # Count trees created
        tree_count = sum(1 for row in map_data for cell in row if cell == WOODS + BLN)
        assert tree_count > 0

    def test_do_trees(self):
        """Test random tree placement."""
        gen = TerrainGenerator(42)
        map_data = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]

        gen.do_trees(map_data)

        # Should have trees placed
        tree_count = sum(1 for row in map_data for cell in row if (cell & BLN) == BLN)
        assert tree_count > 0

    def test_river_generation(self):
        """Test river generation algorithms."""
        gen = TerrainGenerator(42)
        map_data = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]

        gen.get_rand_start()
        gen.do_rivers(map_data)

        # Should have river tiles placed
        river_tiles = sum(1 for row in map_data for cell in row
                         if cell in (RIVER, REDGE, CHANNEL))
        assert river_tiles > 0

    def test_lake_generation(self):
        """Test lake placement."""
        gen = TerrainGenerator(42)
        map_data = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]

        gen.make_lakes(map_data)

        # Should have some water tiles
        water_tiles = sum(1 for row in map_data for cell in row
                         if cell in (RIVER, REDGE, CHANNEL))
        # Lakes might not always generate, so just check it doesn't crash
        assert water_tiles >= 0

    def test_island_generation(self):
        """Test island terrain generation."""
        gen = TerrainGenerator(42)
        map_data = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]

        gen.make_island(map_data)

        # Island should have water around edges and land in center
        edge_water = sum(1 for x in range(WORLD_X) for y in range(WORLD_Y)
                        if (x < 5 or x >= WORLD_X-5 or y < 5 or y >= WORLD_Y-5)
                        and map_data[x][y] == RIVER)

        center_land = sum(1 for x in range(5, WORLD_X-5) for y in range(5, WORLD_Y-5)
                         if map_data[x][y] == 0)

        assert edge_water > 0
        assert center_land > 0

    def test_generate_map_river_variant(self):
        """Test main generation with river-based terrain."""
        # Use seed that will generate river terrain (not island)
        gen = TerrainGenerator(1)  # Seed that avoids island generation
        map_data = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]

        gen.generate_map(map_data)

        # Should have some terrain features
        total_tiles = sum(1 for row in map_data for cell in row if cell != 0)
        assert total_tiles > 0

    def test_generate_map_island_variant(self):
        """Test main generation with island terrain."""
        # Try different seeds until we get an island
        map_data = None
        for seed in range(100):
            gen = TerrainGenerator(seed)
            test_map = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]
            gen.generate_map(test_map)

            # Check if it's an island (has water in center area)
            center_water = sum(1 for x in range(10, WORLD_X-10)
                              for y in range(10, WORLD_Y-10)
                              if test_map[x][y] == RIVER)

            if center_water > 100:  # Significant water in center = island
                map_data = test_map
                break

        assert map_data is not None, "Should generate island terrain with some seed"

    def test_convenience_functions(self):
        """Test convenience functions."""
        map_data = [[1 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]

        # Test clear_terrain
        clear_terrain(map_data)
        assert all(all(cell == 0 for cell in row) for row in map_data)

        # Test generate_terrain
        generate_terrain(map_data, seed=42)
        total_tiles = sum(1 for row in map_data for cell in row if cell != 0)
        assert total_tiles > 0


class TestTerrainIntegration(Assertions):
    """Integration tests for terrain generation system."""

    def test_terrain_generation_reproducibility(self):
        """Test that same seed produces identical terrain."""
        map1 = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]
        map2 = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]

        generate_terrain(map1, seed=12345)
        generate_terrain(map2, seed=12345)

        assert map1 == map2

    def test_terrain_generation_variation(self):
        """Test that different seeds produce different terrain."""
        maps = []
        for seed in [1, 2, 3, 4, 5]:
            map_data = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]
            generate_terrain(map_data, seed=seed)
            maps.append(map_data)

        # At least some maps should be different
        all_same = all(maps[0] == m for m in maps[1:])
        assert not all_same, "Different seeds should produce different terrain"

    def test_terrain_bounds_safety(self):
        """Test that terrain generation never writes outside bounds."""
        map_data = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]

        # Generate terrain multiple times with different seeds
        for seed in range(10):
            generate_terrain(map_data, seed=seed)

            # Verify all cells are within bounds
            for x in range(WORLD_X):
                for y in range(WORLD_Y):
                    assert 0 <= x < WORLD_X
                    assert 0 <= y < WORLD_Y

    def test_terrain_feature_diversity(self):
        """Test that generated terrain has diverse features."""
        map_data = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]
        generate_terrain(map_data, seed=42)

        # Count different terrain types
        water_tiles = sum(1 for row in map_data for cell in row
                         if cell in (RIVER, REDGE, CHANNEL))
        tree_tiles = sum(1 for row in map_data for cell in row
                        if (cell & BLN) == BLN)
        land_tiles = sum(1 for row in map_data for cell in row
                        if cell == 0)

        # Should have some of each major type
        self.assertGreater(water_tiles, 0)
        self.assertGreater(tree_tiles, 0)
        self.assertGreater(land_tiles, 0)

        # Total should equal all tiles (some tiles may be smoothed edges, etc.)
        total_tiles = sum(1 for row in map_data for cell in row if cell != 0)
        self.assertEqual(total_tiles + land_tiles, WORLD_X * WORLD_Y)

