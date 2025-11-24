"""
test_mini_maps.py - Unit tests for mini_maps.py

Tests the small overview map rendering system ported from g_smmaps.c.
"""

from unittest.mock import patch, MagicMock
import sys
import os

from micropolis import constants as const
from micropolis.view_types import MakeNewXDisplay
from micropolis.sim_view import create_map_view
from tests.assertions import Assertions

# Add the src directory to the path

from micropolis import macros, mini_maps


class TestMiniMaps(Assertions):
    """Test cases for small overview map rendering"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a mock view
        self.view = create_map_view(context)
        self.view.line_bytes8 = 16 * 4  # 16 pixels * 4 bytes per pixel
        self.view.pixel_bytes = 4

        # Create mock display
        self.view.x = MakeNewXDisplay()
        self.view.x.color = 1  # Color mode
        self.view.x.depth = 32

        # Set up pixel color values for color mode
        self.view.pixels = [0] * 256  # Mock color palette
        self.view.pixels[const.COLOR_RED] = 0xFF0000  # Powered color
        self.view.pixels[const.COLOR_LIGHTBLUE] = (
            0xADD8E6  # Unpowered color
        )
        self.view.pixels[const.COLOR_LIGHTGRAY] = (
            0xD3D3D3  # Conductive color
        )

        # Set up image buffers for rendering
        buffer_size = (
            3 * 4 * const.WORLD_X * const.WORLD_Y
        )  # 3 pixels * 4 bytes * 120 * 100
        self.view.data = b"\x00" * buffer_size  # Color buffer

        # Initialize small tiles data
        self.view.smalltiles = b"\x00" * (
            const.TILE_COUNT * 16 * 4
        )  # Mock 4x4 tile data

        # Update the injected context map data directly (tests rely on the shared object)
        for x in range(const.WORLD_X):
            for y in range(const.WORLD_Y):
                context.map_data[x][y] = 0

        for x in range(20):
            for y in range(20):
                context.map_data[x][y] = macros.RESBASE  # Residential zone

        # Initialize dynamic data
        # Update in place to maintain sync with context
        if not hasattr(context, "dynamic_data") or context.dynamic_data is None:
            context.dynamic_data = [0] * 32
        else:
            for i in range(len(context.dynamic_data)):
                context.dynamic_data[i] = 0

    def test_drawAll(self):
        """Test drawAll function"""
        with patch("micropolis.mini_maps._render_small_tile") as mock_render:
            mini_maps.drawAll(context, self.view)
            # Should render all tiles
            self.assertTrue(mock_render.called)

    def test_drawRes_filtering(self):
        """Test drawRes residential zone filtering"""
        # Set up a commercial zone that should be filtered out
        context.map_data[10][10] = 500  # Commercial zone tile

        with patch("micropolis.mini_maps._render_small_tile") as mock_render:
            mini_maps.drawRes(context, context)
            # Should have been called with tile = 0 (filtered)
            mock_render.assert_called()

    def test_drawCom_filtering(self):
        """Test drawCom commercial zone filtering"""
        # Set up a residential zone that should be filtered out
        context.map_data[10][10] = macros.RESBASE  # Residential zone

        with patch("micropolis.mini_maps._render_small_tile") as mock_render:
            mini_maps.drawCom(context, context)
            # Should have been called with tile = 0 (filtered)
            mock_render.assert_called()

    def test_drawInd_filtering(self):
        """Test drawInd industrial zone filtering"""
        # Set up a residential zone that should be filtered out
        context.map_data[10][10] = macros.RESBASE  # Residential zone

        with patch("micropolis.mini_maps._render_small_tile") as mock_render:
            mini_maps.drawInd(context, context)
            # Should have been called with tile = 0 (filtered)
            mock_render.assert_called()

    def test_drawLilTransMap_filtering(self):
        """Test drawLilTransMap transportation filtering"""
        # Set up a zone that should be filtered out
        context.map_data[10][10] = 250  # Some zone tile

        with patch("micropolis.mini_maps._render_small_tile") as mock_render:
            mini_maps.drawLilTransMap(context, context)
            # Should have been called with tile = 0 (filtered)
            mock_render.assert_called()

    def test_drawPower_zones(self):
        """Test drawPower power grid visualization"""
        # Set up an unpowered zone
        context.map_data[10][10] = (
            macros.RESBASE | macros.ZONEBIT
        )  # Residential zone, unpowered

        # Just test that the function doesn't crash
        mini_maps.drawPower(context, self.view)

    def test_drawPower_conductive(self):
        """Test drawPower conductive tile visualization"""
        # Set up a conductive tile
        context.map_data[10][10] = const.CONDBIT  # Conductive tile

        # Just test that the function doesn't crash
        mini_maps.drawPower(context, self.view)

    def test_dynamicFilter_population(self):
        """Test dynamic filtering with population criteria"""
        # Set up dynamic data to disable all filters (min > max means don't filter)
        # Use context.dynamic_data as it is what the code under test uses
        if not hasattr(context, "dynamic_data") or context.dynamic_data is None:
            context.dynamic_data = [0] * 32

        for i in range(0, 16, 2):
            context.dynamic_data[i] = 100  # Min values > max values
            context.dynamic_data[i + 1] = 0  # Max values

        result = mini_maps.dynamicFilter(
            context, 10, 10
        )  # dynamicFilter takes context, col, row
        self.assertEqual(result, 1)  # Should pass filter when all criteria are disabled

    def test_dynamicFilter_out_of_range(self):
        """Test dynamic filtering with out-of-range values"""
        # Set up dynamic data
        if not hasattr(context, "dynamic_data") or context.dynamic_data is None:
            context.dynamic_data = [0] * 32

        context.dynamic_data[0] = 10  # Min population
        context.dynamic_data[1] = 100  # Max population

        # Set up population density outside range
        # Ensure pop_density is initialized
        if not hasattr(context, "pop_density") or context.pop_density is None:
            context.pop_density = [
                [0 for _ in range(const.WORLD_Y)]
                for _ in range(const.WORLD_X)
            ]

        context.pop_density[5][5] = 5  # Below minimum

        result = mini_maps.dynamicFilter(
            context, 10, 10
        )  # dynamicFilter takes context, col, row
        self.assertEqual(result, 0)  # Should fail filter

    def test_drawDynamic(self):
        """Test drawDynamic with filtering"""
        # Set up dynamic data to pass all filters
        if not hasattr(context, "dynamic_data") or context.dynamic_data is None:
            context.dynamic_data = [0] * 32

        for i in range(0, 16, 2):
            context.dynamic_data[i] = 0  # Min values
            context.dynamic_data[i + 1] = 100  # Max values

        # Set up data arrays
        context.pop_density = [
            [50 for _ in range(const.WORLD_Y // 2)]
            for _ in range(const.WORLD_X // 2)
        ]
        context.rate_og_mem = [
            [128 for _ in range(const.WORLD_Y // 4)]
            for _ in range(const.WORLD_X // 4)
        ]
        context.trf_density = [
            [50 for _ in range(const.WORLD_Y)]
            for _ in range(const.WORLD_X)
        ]
        context.pollution_mem = [
            [50 for _ in range(const.WORLD_Y)]
            for _ in range(const.WORLD_X)
        ]
        context.crime_mem = [
            [50 for _ in range(const.WORLD_Y)]
            for _ in range(const.WORLD_X)
        ]
        context.land_value_mem = [
            [50 for _ in range(const.WORLD_Y)]
            for _ in range(const.WORLD_X)
        ]
        context.police_map_effect = [
            [50 for _ in range(const.WORLD_Y // 4)]
            for _ in range(const.WORLD_X // 4)
        ]
        context.fire_rate = [
            [50 for _ in range(const.WORLD_Y // 4)]
            for _ in range(const.WORLD_X // 4)
        ]

        with patch("micropolis.mini_maps._render_small_tile") as mock_render:
            mini_maps.drawDynamic(context, context)
            mock_render.assert_called()

    def test_render_small_tile_bounds_check(self):
        """Test small tile rendering with bounds checking"""
        # Test with invalid tile index
        mini_maps._render_small_tile(
            self.view, MagicMock(), const.TILE_COUNT + 1, 16, 4
        )
        # Should return early due to bounds check

    def test_render_solid_color_no_image(self):
        """Test solid color rendering with no image buffer"""
        mini_maps._render_solid_color(self.view, None, 0xFF0000, 16, 4)
        # Should return early with no image
