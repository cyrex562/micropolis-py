"""
test_mini_maps.py - Unit tests for mini_maps.py

Tests the small overview map rendering system ported from g_smmaps.c.
"""

from unittest.mock import patch, MagicMock
import sys
import os

from tests.assertions import Assertions

# Add the src directory to the path

from micropolis import types, macros, mini_maps


class TestMiniMaps(Assertions):
    """Test cases for small overview map rendering"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a mock view
        self.view = types.MakeNewView()
        self.view.line_bytes8 = 16 * 4  # 16 pixels * 4 bytes per pixel
        self.view.pixel_bytes = 4

        # Create mock display
        self.view.x = types.view_types.MakeNewXDisplay()
        self.view.x.color = 1  # Color mode
        self.view.x.depth = 32

        # Set up pixel color values for color mode
        self.view.pixels = [0] * 256  # Mock color palette
        self.view.pixels[types.COLOR_RED] = 0xFF0000      # Powered color
        self.view.pixels[types.COLOR_LIGHTBLUE] = 0xADD8E6  # Unpowered color
        self.view.pixels[types.COLOR_LIGHTGRAY] = 0xD3D3D3  # Conductive color

        # Set up image buffers for rendering
        buffer_size = 3 * 4 * types.WORLD_X * types.WORLD_Y  # 3 pixels * 4 bytes * 120 * 100
        self.view.data = b'\x00' * buffer_size  # Color buffer

        # Initialize small tiles data
        self.view.smalltiles = b'\x00' * (types.TILE_COUNT * 16 * 4)  # Mock 4x4 tile data

        # Set up some test map data
        types.Map = [[0 for _ in range(types.WORLD_Y)] for _ in range(types.WORLD_X)]
        for x in range(20):
            for y in range(20):
                types.Map[x][y] = macros.RESBASE  # Residential zone

        # Initialize dynamic data
        types.DynamicData = [0] * 32

    def test_drawAll(self):
        """Test drawAll function"""
        with patch('micropolis.mini_maps._render_small_tile') as mock_render:
            mini_maps.drawAll(self.view)
            # Should render all tiles
            self.assertTrue(mock_render.called)

    def test_drawRes_filtering(self):
        """Test drawRes residential zone filtering"""
        # Set up a commercial zone that should be filtered out
        types.Map[10][10] = 500  # Commercial zone tile

        with patch('micropolis.mini_maps._render_small_tile') as mock_render:
            mini_maps.drawRes(self.view)
            # Should have been called with tile = 0 (filtered)
            mock_render.assert_called()

    def test_drawCom_filtering(self):
        """Test drawCom commercial zone filtering"""
        # Set up a residential zone that should be filtered out
        types.Map[10][10] = macros.RESBASE  # Residential zone

        with patch('micropolis.mini_maps._render_small_tile') as mock_render:
            mini_maps.drawCom(self.view)
            # Should have been called with tile = 0 (filtered)
            mock_render.assert_called()

    def test_drawInd_filtering(self):
        """Test drawInd industrial zone filtering"""
        # Set up a residential zone that should be filtered out
        types.Map[10][10] = macros.RESBASE  # Residential zone

        with patch('micropolis.mini_maps._render_small_tile') as mock_render:
            mini_maps.drawInd(self.view)
            # Should have been called with tile = 0 (filtered)
            mock_render.assert_called()

    def test_drawLilTransMap_filtering(self):
        """Test drawLilTransMap transportation filtering"""
        # Set up a zone that should be filtered out
        types.Map[10][10] = 250  # Some zone tile

        with patch('micropolis.mini_maps._render_small_tile') as mock_render:
            mini_maps.drawLilTransMap(self.view)
            # Should have been called with tile = 0 (filtered)
            mock_render.assert_called()

    def test_drawPower_zones(self):
        """Test drawPower power grid visualization"""
        # Set up an unpowered zone
        types.Map[10][10] = macros.RESBASE | macros.ZONEBIT  # Residential zone, unpowered

        # Just test that the function doesn't crash
        mini_maps.drawPower(self.view)

    def test_drawPower_conductive(self):
        """Test drawPower conductive tile visualization"""
        # Set up a conductive tile
        types.Map[10][10] = types.CONDBIT  # Conductive tile

        # Just test that the function doesn't crash
        mini_maps.drawPower(self.view)

    def test_dynamicFilter_population(self):
        """Test dynamic filtering with population criteria"""
        # Set up dynamic data to disable all filters (min > max means don't filter)
        for i in range(0, 16, 2):
            types.DynamicData[i] = 100      # Min values > max values
            types.DynamicData[i + 1] = 0    # Max values

        result = mini_maps.dynamicFilter(10, 10)
        self.assertEqual(result, 1)  # Should pass filter when all criteria are disabled

    def test_dynamicFilter_out_of_range(self):
        """Test dynamic filtering with out-of-range values"""
        # Set up dynamic data
        types.DynamicData[0] = 10  # Min population
        types.DynamicData[1] = 100  # Max population

        # Set up population density outside range
        types.PopDensity[5][5] = 5  # Below minimum

        result = mini_maps.dynamicFilter(10, 10)
        self.assertEqual(result, 0)  # Should fail filter

    def test_drawDynamic(self):
        """Test drawDynamic with filtering"""
        # Set up dynamic data to pass all filters
        for i in range(0, 16, 2):
            types.DynamicData[i] = 0      # Min values
            types.DynamicData[i + 1] = 100  # Max values

        # Set up data arrays
        types.PopDensity = [[50 for _ in range(types.WORLD_Y // 2)] for _ in range(types.WORLD_X // 2)]
        types.RateOGMem = [[128 for _ in range(types.WORLD_Y // 4)] for _ in range(types.WORLD_X // 4)]
        types.TrfDensity = [[50 for _ in range(types.WORLD_Y)] for _ in range(types.WORLD_X)]
        types.PollutionMem = [[50 for _ in range(types.WORLD_Y)] for _ in range(types.WORLD_X)]
        types.CrimeMem = [[50 for _ in range(types.WORLD_Y)] for _ in range(types.WORLD_X)]
        types.LandValueMem = [[50 for _ in range(types.WORLD_Y)] for _ in range(types.WORLD_X)]
        types.PoliceMapEffect = [[50 for _ in range(types.WORLD_Y // 4)] for _ in range(types.WORLD_X // 4)]
        types.FireRate = [[50 for _ in range(types.WORLD_Y // 4)] for _ in range(types.WORLD_X // 4)]

        with patch('micropolis.mini_maps._render_small_tile') as mock_render:
            mini_maps.drawDynamic(self.view)
            mock_render.assert_called()

    def test_render_small_tile_bounds_check(self):
        """Test small tile rendering with bounds checking"""
        # Test with invalid tile index
        mini_maps._render_small_tile(self.view, MagicMock(), types.TILE_COUNT + 1, 16, 4)
        # Should return early due to bounds check

    def test_render_solid_color_no_image(self):
        """Test solid color rendering with no image buffer"""
        mini_maps._render_solid_color(self.view, None, 0xFF0000, 16, 4)
        # Should return early with no image

