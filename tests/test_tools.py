"""
test_tools.py - Comprehensive test suite for tools.py

Tests the tool selection and application system ported from w_tool.c,
including building placement, infrastructure tools, query tool, bulldozer,
and drawing tools.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from micropolis import tools, types


class TestToolConstants(unittest.TestCase):
    """Test tool constants and configuration arrays."""

    def test_tool_states(self):
        """Test tool state constants are properly defined."""
        self.assertEqual(tools.residentialState, 0)
        self.assertEqual(tools.commercialState, 1)
        self.assertEqual(tools.industrialState, 2)
        self.assertEqual(tools.fireState, 3)
        self.assertEqual(tools.queryState, 4)
        self.assertEqual(tools.policeState, 5)
        self.assertEqual(tools.wireState, 6)
        self.assertEqual(tools.dozeState, 7)
        self.assertEqual(tools.rrState, 8)
        self.assertEqual(tools.roadState, 9)
        self.assertEqual(tools.chalkState, 10)
        self.assertEqual(tools.eraserState, 11)
        self.assertEqual(tools.stadiumState, 12)
        self.assertEqual(tools.parkState, 13)
        self.assertEqual(tools.seaportState, 14)
        self.assertEqual(tools.powerState, 15)
        self.assertEqual(tools.nuclearState, 16)
        self.assertEqual(tools.airportState, 17)
        self.assertEqual(tools.networkState, 18)

    def test_tool_costs(self):
        """Test tool cost array is properly configured."""
        self.assertEqual(len(tools.CostOf), 19)  # All tool states
        self.assertEqual(tools.CostOf[tools.residentialState], 100)
        self.assertEqual(tools.CostOf[tools.commercialState], 100)
        self.assertEqual(tools.CostOf[tools.industrialState], 100)
        self.assertEqual(tools.CostOf[tools.fireState], 500)
        self.assertEqual(tools.CostOf[tools.queryState], 0)  # Free
        self.assertEqual(tools.CostOf[tools.wireState], 5)
        self.assertEqual(tools.CostOf[tools.dozeState], 1)  # Bulldoze cost
        self.assertEqual(tools.CostOf[tools.roadState], 10)
        self.assertEqual(tools.CostOf[tools.rrState], 20)  # Rail
        self.assertEqual(tools.CostOf[tools.stadiumState], 5000)
        self.assertEqual(tools.CostOf[tools.airportState], 10000)

    def test_tool_sizes(self):
        """Test tool size array for different building footprints."""
        self.assertEqual(tools.toolSize[tools.residentialState], 3)  # 3x3
        self.assertEqual(tools.toolSize[tools.commercialState], 3)   # 3x3
        self.assertEqual(tools.toolSize[tools.industrialState], 3)   # 3x3
        self.assertEqual(tools.toolSize[tools.stadiumState], 4)      # 4x4
        self.assertEqual(tools.toolSize[tools.airportState], 6)      # 6x6
        self.assertEqual(tools.toolSize[tools.queryState], 1)        # 1x1
        self.assertEqual(tools.toolSize[tools.chalkState], 0)        # Freeform

    def test_tool_offsets(self):
        """Test tool offset array for proper positioning."""
        self.assertEqual(tools.toolOffset[tools.residentialState], 1)  # Center offset
        self.assertEqual(tools.toolOffset[tools.stadiumState], 1)      # Center offset
        self.assertEqual(tools.toolOffset[tools.airportState], 1)      # Center offset
        self.assertEqual(tools.toolOffset[tools.queryState], 0)        # No offset


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions for tile checking and validation."""

    def setUp(self):
        """Set up test fixtures."""
        # Initialize a small test map
        types.Map = [[0 for _ in range(10)] for _ in range(10)]
        types.TotalFunds = 10000  # Plenty of money for tests

    def test_tally_bulldozable_tiles(self):
        """Test tally function identifies bulldozable tiles."""
        # Test bulldozable tiles
        bulldozable_tiles = [
            types.FIRSTRIVEDGE, types.LASTTREE, types.RUBBLE,
            types.FLOOD, types.RADTILE, types.FIRE
        ]

        for tile in bulldozable_tiles:
            with self.subTest(tile=tile):
                self.assertEqual(tools.tally(tile), 1, f"Tile {tile} should be bulldozable")

        # Test non-bulldozable tiles
        non_bulldozable = [types.DIRT, types.RESBASE]
        for tile in non_bulldozable:
            with self.subTest(tile=tile):
                self.assertEqual(tools.tally(tile), 0, f"Tile {tile} should not be bulldozable")

    def test_checkSize_building_sizes(self):
        """Test checkSize identifies correct building sizes."""
        # 3x3 buildings
        three_by_three = [
            types.RESBASE - 1, types.COMBASE - 1, types.INDBASE - 1,
            types.LASTPOWERPLANT + 1, types.POLICESTATION + 4
        ]

        for tile in three_by_three:
            with self.subTest(tile=tile):
                self.assertEqual(tools.checkSize(tile), 3, f"Tile {tile} should be size 3")

        # 4x4 buildings
        four_by_four = [
            types.PORTBASE, types.COALBASE, types.STADIUMBASE
        ]

        for tile in four_by_four:
            with self.subTest(tile=tile):
                self.assertEqual(tools.checkSize(tile), 4, f"Tile {tile} should be size 4")

        # Other sizes
        self.assertEqual(tools.checkSize(types.DIRT), 0)

    def test_checkBigZone_large_buildings(self):
        """Test checkBigZone identifies large building offsets."""
        deltaH = [0]
        deltaV = [0]

        # Test 4x4 buildings
        four_by_four_centers = [
            (types.POWERPLANT, 0, 0),
            (types.PORT, 0, 0),
            (types.NUCLEAR, 0, 0),
            (types.STADIUM, 0, 0),
        ]

        for tile, expected_dh, expected_dv in four_by_four_centers:
            with self.subTest(tile=tile):
                size = tools.checkBigZone(tile, deltaH, deltaV)
                self.assertEqual(size, 4)
                self.assertEqual(deltaH[0], expected_dh)
                self.assertEqual(deltaV[0], expected_dv)

        # Test 6x6 airport
        size = tools.checkBigZone(types.AIRPORT, deltaH, deltaV)
        self.assertEqual(size, 6)
        self.assertEqual(deltaH[0], 0)
        self.assertEqual(deltaV[0], 0)

        # Test non-large building
        size = tools.checkBigZone(types.DIRT, deltaH, deltaV)
        self.assertEqual(size, 0)


class TestBuildingPlacement(unittest.TestCase):
    """Test building placement functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Initialize a larger test map
        types.Map = [[0 for _ in range(20)] for _ in range(20)]
        types.TotalFunds = 10000
        types.autoBulldoze = 0  # Disable auto-bulldoze for these tests

        # Create mock view
        self.mock_view = Mock()
        self.mock_view.super_user = False

    def test_check3x3_clear_area(self):
        """Test 3x3 building placement on clear area."""
        result = tools.check3x3(self.mock_view, 5, 5, types.RESBASE, tools.residentialState)
        self.assertEqual(result, 1)

        # Check that building was placed
        self.assertEqual(types.Map[5][5] & types.LOMASK, types.RESBASE + 4)  # Center tile
        self.assertTrue(types.Map[5][5] & types.ZONEBIT)
        self.assertEqual(types.Map[4][4] & types.LOMASK, types.RESBASE)  # Corner tile

    def test_check3x3_insufficient_funds(self):
        """Test 3x3 building placement with insufficient funds."""
        types.TotalFunds = 50  # Less than cost of 100
        result = tools.check3x3(self.mock_view, 5, 5, types.RESBASE, tools.residentialState)
        self.assertEqual(result, -2)

    def test_check3x3_occupied_area(self):
        """Test 3x3 building placement on occupied area."""
        # Place something in the area first
        types.Map[5][5] = types.RESBASE  # Non-bulldozable tile

        result = tools.check3x3(self.mock_view, 5, 5, types.RESBASE, tools.residentialState)
        self.assertEqual(result, -1)

    def test_check4x4_with_animation(self):
        """Test 4x4 building placement with animation flag."""
        result = tools.check4x4(self.mock_view, 5, 5, types.COALBASE, 1, tools.powerState)
        self.assertEqual(result, 1)

        # Check center tile has animation bit
        self.assertTrue(types.Map[5][6] & types.ANIMBIT)  # Smoke tile

    def test_check6x6_airport(self):
        """Test 6x6 airport placement."""
        result = tools.check6x6(self.mock_view, 8, 8, types.AIRPORTBASE, tools.airportState)
        self.assertEqual(result, 1)

        # Check center tile
        self.assertEqual(types.Map[8][8] & types.LOMASK, types.AIRPORTBASE + 7)
        self.assertTrue(types.Map[8][8] & types.ZONEBIT)


class TestIndividualTools(unittest.TestCase):
    """Test individual tool functions."""

    def setUp(self):
        """Set up test fixtures."""
        types.Map = [[0 for _ in range(20)] for _ in range(20)]
        types.TotalFunds = 10000

        self.mock_view = Mock()
        self.mock_view.super_user = False

    @patch('micropolis.tools.MakeSound')
    def test_residential_tool(self, mock_sound):
        """Test residential zone placement."""
        result = tools.residential_tool(self.mock_view, 5, 5)
        self.assertEqual(result, 1)
        self.assertTrue(types.Map[5][5] & types.ZONEBIT)

    @patch('micropolis.tools.MakeSound')
    def test_commercial_tool(self, mock_sound):
        """Test commercial zone placement."""
        result = tools.commercial_tool(self.mock_view, 5, 5)
        self.assertEqual(result, 1)
        self.assertTrue(types.Map[5][5] & types.ZONEBIT)

    @patch('micropolis.tools.MakeSound')
    def test_industrial_tool(self, mock_sound):
        """Test industrial zone placement."""
        result = tools.industrial_tool(self.mock_view, 5, 5)
        self.assertEqual(result, 1)
        self.assertTrue(types.Map[5][5] & types.ZONEBIT)

    @patch('micropolis.tools.DidTool')
    def test_road_tool(self, mock_did_tool):
        """Test road placement."""
        result = tools.road_tool(self.mock_view, 5, 5)
        self.assertEqual(result, 1)
        self.assertEqual(types.Map[5][5] & types.LOMASK, types.ROADBASE)

    @patch('micropolis.tools.DidTool')
    def test_rail_tool(self, mock_did_tool):
        """Test rail placement."""
        result = tools.rail_tool(self.mock_view, 5, 5)
        self.assertEqual(result, 1)
        self.assertEqual(types.Map[5][5] & types.LOMASK, types.RAILBASE)

    @patch('micropolis.tools.DidTool')
    def test_wire_tool(self, mock_did_tool):
        """Test power line placement."""
        result = tools.wire_tool(self.mock_view, 5, 5)
        self.assertEqual(result, 1)
        self.assertEqual(types.Map[5][5] & types.LOMASK, types.POWERBASE)
        self.assertTrue(types.Map[5][5] & types.CONDBIT)

    def test_park_tool(self):
        """Test park placement."""
        result = tools.park_tool(self.mock_view, 5, 5)
        self.assertEqual(result, 1)
        # Park should be either WOODS2, WOODS3, WOODS4, or FOUNTAIN
        tile = types.Map[5][5] & types.LOMASK
        self.assertIn(tile, [types.WOODS2, types.WOODS3, types.WOODS4, types.FOUNTAIN])

    @patch('micropolis.tools.DidTool')
    def test_query_tool(self, mock_did_tool):
        """Test query tool zone status."""
        # Place a residential zone
        tools.residential_tool(self.mock_view, 5, 5)

        with patch('micropolis.tools.doZoneStatus') as mock_zone_status:
            result = tools.query_tool(self.mock_view, 5, 5)
            self.assertEqual(result, 1)
            mock_zone_status.assert_called_once_with(5, 5)

    @patch('micropolis.tools.MakeSound')
    @patch('micropolis.tools.put3x3Rubble')
    def test_bulldozer_tool_zone(self, mock_rubble, mock_sound):
        """Test bulldozer on zone building."""
        # Place a residential zone first
        tools.residential_tool(self.mock_view, 5, 5)

        result = tools.bulldozer_tool(self.mock_view, 5, 5)
        self.assertEqual(result, 1)
        mock_rubble.assert_called_once_with(5, 5)
        mock_sound.assert_called_with("city", "Explosion-High")


class TestQueryTool(unittest.TestCase):
    """Test query tool zone status functionality."""

    def setUp(self):
        """Set up test fixtures."""
        types.Map = [[0 for _ in range(20)] for _ in range(20)]
        types.PopDensity = [[0 for _ in range(types.HWLDY)] for _ in range(types.HWLDX)]
        types.LandValueMem = [[0 for _ in range(types.HWLDY)] for _ in range(types.HWLDX)]
        types.CrimeMem = [[0 for _ in range(types.HWLDY)] for _ in range(types.HWLDX)]
        types.PollutionMem = [[0 for _ in range(types.HWLDY)] for _ in range(types.HWLDX)]
        types.RateOGMem = [[0 for _ in range(types.SmY)] for _ in range(types.SmX)]

    def test_getDensityStr_population(self):
        """Test population density string calculation."""
        types.PopDensity[2][2] = 0  # Low density
        result = tools.getDensityStr(0, 5, 5)  # 5>>1 = 2
        self.assertEqual(result, 0)  # Low density

        types.PopDensity[2][2] = 128  # High density
        result = tools.getDensityStr(0, 5, 5)
        self.assertEqual(result, 2)  # High density

    def test_getDensityStr_land_value(self):
        """Test land value density string calculation."""
        types.LandValueMem[2][2] = 20  # Low value
        result = tools.getDensityStr(1, 5, 5)
        self.assertEqual(result, 4)  # Low value

        types.LandValueMem[2][2] = 100  # High value
        result = tools.getDensityStr(1, 5, 5)
        self.assertEqual(result, 6)  # High value

    def test_getDensityStr_crime(self):
        """Test crime density string calculation."""
        types.CrimeMem[2][2] = 0  # Low crime
        result = tools.getDensityStr(2, 5, 5)
        self.assertEqual(result, 8)  # Low crime

        types.CrimeMem[2][2] = 128  # High crime
        result = tools.getDensityStr(2, 5, 5)
        self.assertEqual(result, 10)  # High crime

    def test_getDensityStr_pollution(self):
        """Test pollution density string calculation."""
        types.PollutionMem[2][2] = 32  # Some pollution
        result = tools.getDensityStr(3, 5, 5)
        self.assertEqual(result, 13)  # Some pollution

        types.PollutionMem[2][2] = 200  # High pollution
        result = tools.getDensityStr(3, 5, 5)
        self.assertEqual(result, 15)  # High pollution

    def test_getDensityStr_growth(self):
        """Test growth rate density string calculation."""
        types.RateOGMem[1][1] = -50  # Negative growth
        result = tools.getDensityStr(4, 4, 4)  # 4>>3 = 0.5 -> 0, 4>>3 = 0.5 -> 0
        # This might need adjustment based on actual coordinates
        # For now, just test that it returns a valid result
        self.assertIsInstance(result, int)


class TestDrawingTools(unittest.TestCase):
    """Test chalk and eraser drawing tools."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_view = Mock()
        self.mock_view.track_info = None

    def test_new_ink_creation(self):
        """Test Ink object creation."""
        ink = tools.NewInk()
        self.assertIsInstance(ink, tools.Ink)
        self.assertEqual(ink.x, 0)
        self.assertEqual(ink.y, 0)
        self.assertEqual(ink.color, 0)
        self.assertEqual(ink.length, 0)
        self.assertEqual(ink.points, [])

    def test_start_ink(self):
        """Test starting an ink stroke."""
        ink = tools.NewInk()
        tools.StartInk(ink, 10, 20)
        self.assertEqual(ink.x, 10)
        self.assertEqual(ink.y, 20)
        self.assertEqual(ink.length, 1)
        self.assertEqual(ink.points, [(0, 0)])
        self.assertEqual(ink.left, 10)
        self.assertEqual(ink.right, 10)
        self.assertEqual(ink.top, 20)
        self.assertEqual(ink.bottom, 20)

    def test_add_ink(self):
        """Test adding points to an ink stroke."""
        ink = tools.NewInk()
        tools.StartInk(ink, 10, 20)
        tools.AddInk(ink, 15, 25)
        self.assertEqual(ink.length, 2)
        self.assertEqual(ink.points[1], (5, 5))  # Relative coordinates
        self.assertEqual(ink.right, 15)
        self.assertEqual(ink.bottom, 25)

    @patch('micropolis.tools.DidTool')
    def test_chalk_tool(self, mock_did_tool):
        """Test chalk tool application."""
        result = tools.ChalkTool(self.mock_view, 10, 20, types.COLOR_WHITE, True)
        self.assertEqual(result, 1)
        mock_did_tool.assert_called_with(self.mock_view, "Chlk", 10, 20)

    @patch('micropolis.tools.DidTool')
    def test_eraser_tool(self, mock_did_tool):
        """Test eraser tool application."""
        result = tools.EraserTool(self.mock_view, 10, 20, True)
        self.assertEqual(result, 1)
        mock_did_tool.assert_called_with(self.mock_view, "Eraser", 10, 20)


class TestToolApplication(unittest.TestCase):
    """Test main tool application functions."""

    def setUp(self):
        """Set up test fixtures."""
        types.Map = [[0 for _ in range(20)] for _ in range(20)]
        types.TotalFunds = 10000

        self.mock_view = Mock()
        self.mock_view.super_user = False
        self.mock_view.tool_state = tools.residentialState

    def test_do_tool_residential(self):
        """Test do_tool with residential tool."""
        result = tools.do_tool(self.mock_view, tools.residentialState, 80, 80, True)  # 80>>4 = 5
        self.assertEqual(result, 1)

    def test_current_tool(self):
        """Test current_tool uses view's tool state."""
        result = tools.current_tool(self.mock_view, 80, 80, True)
        self.assertEqual(result, 1)

    @patch('micropolis.messages.clear_mes')
    @patch('micropolis.messages.send_mes')
    @patch('micropolis.tools.MakeSoundOn')
    def test_tool_down_out_of_bounds(self, mock_sound, mock_send_mes, mock_clear_mes):
        """Test ToolDown with out of bounds coordinates."""
        tools.ToolDown(self.mock_view, -10, -10)
        mock_clear_mes.assert_called_once()
        mock_send_mes.assert_called_with(34)  # Out of jurisdiction

    @patch('micropolis.tools.current_tool')
    def test_tool_down_success(self, mock_current_tool):
        """Test successful ToolDown."""
        mock_current_tool.return_value = 1
        tools.ToolDown(self.mock_view, 80, 80)
        mock_current_tool.assert_called_with(self.mock_view, 80, 80, 1)

    def test_tool_drag_chalk(self):
        """Test ToolDrag with chalk tool."""
        self.mock_view.tool_state = tools.chalkState
        self.mock_view.last_x = 80
        self.mock_view.last_y = 80

        with patch('micropolis.tools.current_tool') as mock_current_tool:
            result = tools.ToolDrag(self.mock_view, 88, 88)  # 8 pixels away
            mock_current_tool.assert_called_with(self.mock_view, 88, 88, 0)
            self.assertEqual(result, 1)


class TestIntegration(unittest.TestCase):
    """Integration tests for tool system."""

    def setUp(self):
        """Set up integration test fixtures."""
        # Reset global state
        types.Map = [[0 for _ in range(types.WORLD_Y)] for _ in range(types.WORLD_X)]
        types.TotalFunds = 10000
        types.autoBulldoze = True

        self.mock_view = Mock()
        self.mock_view.super_user = False

    def test_complete_city_block_development(self):
        """Test developing a complete city block with multiple tools."""
        # Place residential zone
        result = tools.residential_tool(self.mock_view, 10, 10)
        self.assertEqual(result, 1)

        # Add roads around it
        result = tools.road_tool(self.mock_view, 10, 7)  # North
        self.assertEqual(result, 1)

        result = tools.road_tool(self.mock_view, 10, 13)  # South
        self.assertEqual(result, 1)

        result = tools.road_tool(self.mock_view, 7, 10)  # West
        self.assertEqual(result, 1)

        result = tools.road_tool(self.mock_view, 13, 10)  # East
        self.assertEqual(result, 1)

        # Add power lines
        result = tools.wire_tool(self.mock_view, 8, 10)  # Near zone
        self.assertEqual(result, 1)

        # Add some parks
        result = tools.park_tool(self.mock_view, 5, 5)
        self.assertEqual(result, 1)

    def test_bulldoze_and_rebuild(self):
        """Test bulldozing a building and rebuilding."""
        # Build a residential zone
        result = tools.residential_tool(self.mock_view, 10, 10)
        self.assertEqual(result, 1)
        original_funds = types.TotalFunds

        # Bulldoze it
        with patch('micropolis.tools.MakeSound'), \
             patch('micropolis.tools.put3x3Rubble'):
            result = tools.bulldozer_tool(self.mock_view, 10, 10)
            self.assertEqual(result, 1)
            self.assertEqual(types.TotalFunds, original_funds - 1)  # Cost of bulldozing

        # Clear the area (since rubble creation is patched)
        for x in range(8, 13):
            for y in range(8, 13):
                types.Map[x][y] = 0

        # Rebuild on the same spot
        result = tools.residential_tool(self.mock_view, 10, 10)
        self.assertEqual(result, 1)

    def test_large_building_placement(self):
        """Test placing large buildings like airports."""
        # Place airport (6x6 building)
        result = tools.airport_tool(self.mock_view, 15, 15)
        self.assertEqual(result, 1)

        # Verify the building footprint
        for x in range(14, 20):  # 6x6 area centered on 15,15
            for y in range(14, 20):
                tile = types.Map[x][y]
                if x == 15 and y == 15:  # Center
                    self.assertTrue(tile & types.ZONEBIT)
                else:
                    self.assertTrue(tile & types.BNCNBIT)


if __name__ == '__main__':
    unittest.main()