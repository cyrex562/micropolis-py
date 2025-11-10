"""
test_sim_control.py - Unit tests for the sim_control.py module

This module contains comprehensive tests for the simulation control functionality.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from micropolis import sim_control


class TestSimControl(unittest.TestCase):
    """Test cases for the sim_control module"""

    def setUp(self):
        """Set up test fixtures"""
        # Reset module state
        sim_control.initialize_sim_control()

        # Mock the types module
        self.types_patcher = patch('micropolis.sim_control.types')
        self.mock_types = self.types_patcher.start()

        # Set up common mock values
        self.mock_types.WORLD_X = 120
        self.mock_types.WORLD_Y = 100
        self.mock_types.SimSpeed = 3
        self.mock_types.sim_delay = 10
        self.mock_types.sim_skips = 0
        self.mock_types.sim_skip = 0
        self.mock_types.heat_steps = 0
        self.mock_types.heat_flow = 0
        self.mock_types.heat_rule = 0
        self.mock_types.TotalFunds = 10000
        self.mock_types.CityTax = 7
        self.mock_types.firePercent = 0.5
        self.mock_types.policePercent = 0.5
        self.mock_types.roadPercent = 0.5
        self.mock_types.fireMaxValue = 1000
        self.mock_types.policeMaxValue = 1000
        self.mock_types.roadMaxValue = 1000
        self.mock_types.GameLevel = 1
        self.mock_types.LVAverage = 50
        self.mock_types.CrimeAverage = 25
        self.mock_types.PolluteAverage = 30
        self.mock_types.CCx = 60
        self.mock_types.CCy = 50
        self.mock_types.PolMaxX = 70
        self.mock_types.PolMaxY = 45
        self.mock_types.CrimeMaxX = 65
        self.mock_types.CrimeMaxY = 55
        self.mock_types.TrafMaxX = 75
        self.mock_types.TrafMaxY = 40
        self.mock_types.FloodX = 80
        self.mock_types.FloodY = 35
        self.mock_types.CrashX = 85
        self.mock_types.CrashY = 30
        self.mock_types.MeltX = 90
        self.mock_types.MeltY = 25
        self.mock_types.OverRide = 0
        self.mock_types.Expensive = 0
        self.mock_types.Players = 1
        self.mock_types.Votes = 0
        self.mock_types.BobHeight = 8
        self.mock_types.PendingTool = -1
        self.mock_types.PendingX = 0
        self.mock_types.PendingY = 0
        self.mock_types.Displays = "test"
        self.mock_types.MicropolisVersion = "1.0"
        self.mock_types.LakeLevel = 2
        self.mock_types.TreeLevel = 3
        self.mock_types.CurveLevel = 1
        self.mock_types.CreateIsland = 0
        self.mock_types.DoOverlay = 2
        self.mock_types.DonDither = 0
        self.mock_types.FlushStyle = 0
        self.mock_types.tkCollapseMotion = 0
        self.mock_types.NeedRest = False
        self.mock_types.Kick = Mock()

    def tearDown(self):
        """Clean up test fixtures"""
        self.types_patcher.stop()

    def test_sim_speed_control(self):
        """Test simulation speed control"""
        # Test default speed
        self.assertEqual(sim_control.get_sim_speed(), 3)

        # Test setting speed
        sim_control.set_sim_speed(5)
        self.assertEqual(sim_control.get_sim_speed(), 5)
        self.mock_types.Kick.assert_called()

        # Test invalid speed (should not change)
        sim_control.set_sim_speed(10)
        self.assertEqual(sim_control.get_sim_speed(), 5)

    def test_sim_pause_resume(self):
        """Test simulation pause/resume"""
        # Test default state
        self.assertFalse(sim_control.is_sim_paused())

        # Test pause
        sim_control.pause_simulation()
        self.assertTrue(sim_control.is_sim_paused())
        self.mock_types.Kick.assert_called()

        # Test resume
        sim_control.resume_simulation()
        self.assertFalse(sim_control.is_sim_paused())

    def test_sim_delay_control(self):
        """Test simulation delay control"""
        # Test default delay
        self.assertEqual(sim_control.get_sim_delay(), 10)

        # Test setting delay
        sim_control.set_sim_delay(20)
        self.assertEqual(sim_control.get_sim_delay(), 20)
        self.mock_types.Kick.assert_called()

    def test_sim_skips_control(self):
        """Test simulation skips control"""
        # Test default skips
        self.assertEqual(sim_control.get_sim_skips(), 0)

        # Test setting skips
        sim_control.set_sim_skips(5)
        self.assertEqual(sim_control.get_sim_skips(), 5)
        self.mock_types.Kick.assert_called()

    def test_heat_simulation_control(self):
        """Test heat simulation parameters"""
        # Test heat steps
        sim_control.set_heat_steps(10)
        self.assertEqual(sim_control.get_heat_steps(), 10)
        self.mock_types.Kick.assert_called()

        # Test heat flow
        sim_control.set_heat_flow(5)
        self.assertEqual(sim_control.get_heat_flow(), 5)

        # Test heat rule
        sim_control.set_heat_rule(2)
        self.assertEqual(sim_control.get_heat_rule(), 2)

    def test_game_state_management(self):
        """Test game state management"""
        # Test initial state
        self.assertFalse(sim_control.is_game_started())

        # Test setting game started
        sim_control.set_game_started(True)
        self.assertTrue(sim_control.is_game_started())
        self.mock_types.Kick.assert_called()

    @patch('micropolis.sim_control.initialization.InitGame')
    def test_init_game(self, mock_init):
        """Test game initialization"""
        sim_control.init_game()

        mock_init.assert_called_once()
        self.assertTrue(sim_control.is_game_started())
        self.mock_types.Kick.assert_called()

    @patch('micropolis.sim_control.file_io.save_city')
    def test_save_city(self, mock_save):
        """Test city saving"""
        mock_save.return_value = True

        result = sim_control.save_city()
        self.assertTrue(result)
        mock_save.assert_called_with("autosave.cty")

    @patch('micropolis.sim_control.generation.GenerateNewCity')
    def test_generate_new_city(self, mock_generate):
        """Test new city generation"""
        sim_control.generate_new_city()

        mock_generate.assert_called_once()
        self.assertTrue(sim_control.is_game_started())
        self.mock_types.Kick.assert_called()

    @patch('micropolis.sim_control.generation.GenerateSomeCity')
    def test_generate_some_city(self, mock_generate):
        """Test city generation with level"""
        sim_control.generate_some_city(1)

        mock_generate.assert_called_once_with(1)
        self.assertTrue(sim_control.is_game_started())
        self.mock_types.Kick.assert_called()

    def test_city_name_management(self):
        """Test city name management"""
        # Test default name
        self.assertEqual(sim_control.get_city_name(), "Micropolis")

        # Test setting name
        sim_control.set_city_name("Test City")
        self.mock_types.setCityName.assert_called_with("Test City")

    def test_city_file_name_management(self):
        """Test city file name management"""
        # Test setting filename
        sim_control.set_city_file_name("test.cty")
        self.assertEqual(sim_control.get_city_file_name(), "test.cty")

    def test_disaster_functions(self):
        """Test disaster control functions"""
        with patch('micropolis.sim_control.disasters.MakeFire') as mock_fire, \
             patch('micropolis.sim_control.disasters.MakeFlood') as mock_flood, \
             patch('micropolis.sim_control.disasters.MakeTornado') as mock_tornado, \
             patch('micropolis.sim_control.disasters.MakeEarthquake') as mock_quake, \
             patch('micropolis.sim_control.disasters.MakeMonster') as mock_monster, \
             patch('micropolis.sim_control.disasters.MakeMeltdown') as mock_meltdown, \
             patch('micropolis.sim_control.disasters.FireBomb') as mock_bomb, \
             patch('micropolis.sim_control.disasters.MakeExplosion') as mock_explosion:

            sim_control.make_fire()
            mock_fire.assert_called_once()
            self.mock_types.Kick.assert_called()

            sim_control.make_flood()
            mock_flood.assert_called_once()

            sim_control.make_tornado()
            mock_tornado.assert_called_once()

            sim_control.make_earthquake()
            mock_quake.assert_called_once()

            sim_control.make_monster()
            mock_monster.assert_called_once()

            sim_control.make_meltdown()
            mock_meltdown.assert_called_once()

            sim_control.fire_bomb()
            mock_bomb.assert_called_once()

            sim_control.make_explosion(10, 20)
            mock_explosion.assert_called_once_with(10, 20)

    def test_funds_management(self):
        """Test funds management"""
        # Test getting funds
        self.assertEqual(sim_control.get_total_funds(), 10000)

        # Test setting funds
        sim_control.set_total_funds(50000)
        self.assertEqual(sim_control.get_total_funds(), 50000)
        self.assertEqual(self.mock_types.MustUpdateFunds, 1)
        self.mock_types.Kick.assert_called()

    def test_tax_rate_management(self):
        """Test tax rate management"""
        # Test getting tax rate
        self.assertEqual(sim_control.get_tax_rate(), 7)

        # Test setting tax rate
        sim_control.set_tax_rate(10)
        self.assertEqual(sim_control.get_tax_rate(), 10)
        self.mock_types.Kick.assert_called()

    def test_budget_management(self):
        """Test budget management"""
        # Test fire funding
        sim_control.set_fire_fund_percentage(75)
        self.assertEqual(sim_control.get_fire_fund_percentage(), 75)
        self.mock_types.UpdateFundEffects.assert_called()

        # Test police funding
        sim_control.set_police_fund_percentage(60)
        self.assertEqual(sim_control.get_police_fund_percentage(), 60)

        # Test road funding
        sim_control.set_road_fund_percentage(80)
        self.assertEqual(sim_control.get_road_fund_percentage(), 80)

    def test_game_level_management(self):
        """Test game level management"""
        # Test getting level
        self.assertEqual(sim_control.get_game_level(), 1)

        # Test setting level
        sim_control.set_game_level(2)
        self.mock_types.SetGameLevelFunds.assert_called_with(2)

    def test_auto_settings(self):
        """Test auto settings"""
        # Test auto budget
        sim_control.set_auto_budget(False)
        self.assertFalse(sim_control.get_auto_budget())
        self.assertEqual(self.mock_types.MustUpdateOptions, 1)

        # Test auto goto
        sim_control.set_auto_goto(False)
        self.assertFalse(sim_control.get_auto_goto())

        # Test auto bulldoze
        sim_control.set_auto_bulldoze(False)
        self.assertFalse(sim_control.get_auto_bulldoze())

    def test_configuration_options(self):
        """Test configuration options"""
        # Test disasters
        sim_control.set_disasters_enabled(False)
        self.assertFalse(sim_control.get_disasters_enabled())
        self.assertEqual(self.mock_types.MustUpdateOptions, 1)

        # Test sound
        sim_control.set_sound_enabled(False)
        self.assertFalse(sim_control.get_sound_enabled())

        # Test animation
        sim_control.set_do_animation(False)
        self.assertFalse(sim_control.get_do_animation())

        # Test messages
        sim_control.set_do_messages(False)
        self.assertFalse(sim_control.get_do_messages())

        # Test notices
        sim_control.set_do_notices(False)
        self.assertFalse(sim_control.get_do_notices())

    def test_bulldozer_control(self):
        """Test bulldozer control"""
        sim_control.start_bulldozer()
        self.mock_types.StartBulldozer.assert_called_once()
        self.mock_types.Kick.assert_called()

        sim_control.stop_bulldozer()
        self.mock_types.StopBulldozer.assert_called_once()

    def test_map_operations(self):
        """Test map operations"""
        # Mock map
        self.mock_types.Map = [[0 for _ in range(100)] for _ in range(120)]

        # Test tile operations
        sim_control.set_tile(10, 20, 5)
        self.assertEqual(sim_control.get_tile(10, 20), 5)

        # Test fill operation
        sim_control.fill_map(99)
        self.assertEqual(sim_control.get_tile(10, 20), 99)

        # Test out of bounds
        self.assertEqual(sim_control.get_tile(200, 200), 0)

    @patch('micropolis.sim_control.terrain.ClearMap')
    @patch('micropolis.sim_control.terrain.ClearUnnatural')
    @patch('micropolis.sim_control.terrain.SmoothTrees')
    @patch('micropolis.sim_control.terrain.SmoothWater')
    @patch('micropolis.sim_control.terrain.SmoothRiver')
    def test_terrain_operations(self, mock_river, mock_water, mock_trees, mock_unnatural, mock_clear):
        """Test terrain operations"""
        sim_control.clear_map()
        mock_clear.assert_called_once()
        self.mock_types.Kick.assert_called()

        sim_control.clear_unnatural()
        mock_unnatural.assert_called_once()

        sim_control.smooth_trees()
        mock_trees.assert_called_once()

        sim_control.smooth_water()
        mock_water.assert_called_once()

        sim_control.smooth_river()
        mock_river.assert_called_once()

    def test_city_statistics(self):
        """Test city statistics access"""
        # Test land value
        self.assertEqual(sim_control.get_land_value(), 50)

        # Test crime
        self.assertEqual(sim_control.get_crime_average(), 25)

        # Test pollution
        self.assertEqual(sim_control.get_pollution_average(), 30)

        # Test population center
        center = sim_control.get_population_center()
        self.assertEqual(center, (60 * 16 + 8, 50 * 16 + 8))

        # Test pollution center
        pol_center = sim_control.get_pollution_center()
        self.assertEqual(pol_center, (70 * 16 + 8, 45 * 16 + 8))

    @patch('micropolis.sim_control.traffic.AverageTrf')
    def test_traffic_statistics(self, mock_avg_trf):
        """Test traffic statistics"""
        mock_avg_trf.return_value = 75
        self.assertEqual(sim_control.get_traffic_average(), 75)
        mock_avg_trf.assert_called_once()

    @patch('micropolis.sim_control.evaluation.GetUnemployment')
    @patch('micropolis.sim_control.evaluation.GetFire')
    def test_evaluation_statistics(self, mock_fire, mock_unemployment):
        """Test evaluation statistics"""
        mock_unemployment.return_value = 5
        mock_fire.return_value = 95

        self.assertEqual(sim_control.get_unemployment_rate(), 5)
        self.assertEqual(sim_control.get_fire_coverage(), 95)

        mock_unemployment.assert_called_once()
        mock_fire.assert_called_once()

    def test_dynamic_data(self):
        """Test dynamic data operations"""
        # Mock dynamic data
        self.mock_types.DynamicData = [0] * 32
        self.mock_types.NewMapFlags = [0] * 10
        self.mock_types.DYMAP = 5

        # Test set/get
        sim_control.set_dynamic_data(5, 100)
        self.assertEqual(sim_control.get_dynamic_data(5), 100)
        self.assertEqual(self.mock_types.NewMapFlags[5], 1)
        self.mock_types.Kick.assert_called()

        # Test out of bounds
        self.assertEqual(sim_control.get_dynamic_data(50), 0)

    def test_reset_dynamic_data(self):
        """Test dynamic data reset"""
        self.mock_types.DynamicData = [0] * 32
        self.mock_types.NewMapFlags = [0] * 10
        self.mock_types.DYMAP = 5

        sim_control.reset_dynamic_data()

        # Check alternating pattern
        for i in range(16):
            expected = 99999 if (i & 1) else -99999
            self.assertEqual(self.mock_types.DynamicData[i], expected)

        self.assertEqual(self.mock_types.NewMapFlags[5], 1)
        self.mock_types.Kick.assert_called()

    def test_performance_timing(self):
        """Test performance timing"""
        # Mock editor view
        mock_view = Mock()
        mock_view.updates = 5
        mock_view.update_real = 1.0
        mock_view.update_user = 2.0
        mock_view.update_system = 3.0
        mock_view.next = None

        self.mock_types.sim = Mock()
        self.mock_types.sim.editor = mock_view

        sim_control.start_performance_timing()

        self.assertTrue(sim_control.get_performance_timing())
        # Check that view timing was reset
        self.assertEqual(mock_view.updates, 0)
        self.assertEqual(mock_view.update_real, 0.0)

    def test_world_size(self):
        """Test world size access"""
        size = sim_control.get_world_size()
        self.assertEqual(size, (120, 100))

    def test_override_and_expensive(self):
        """Test override and expensive settings"""
        sim_control.set_override(5)
        self.assertEqual(sim_control.get_override(), 5)

        sim_control.set_expensive(3)
        self.assertEqual(sim_control.get_expensive(), 3)

    def test_players_and_votes(self):
        """Test players and votes"""
        sim_control.set_players(4)
        self.assertEqual(sim_control.get_players(), 4)

        sim_control.set_votes(100)
        self.assertEqual(sim_control.get_votes(), 100)

    def test_bob_height_and_pending_tool(self):
        """Test bob height and pending tool"""
        sim_control.set_bob_height(12)
        self.assertEqual(sim_control.get_bob_height(), 12)

        sim_control.set_pending_tool(5)
        self.assertEqual(sim_control.get_pending_tool(), 5)

        sim_control.set_pending_position(10, 20)
        pos = sim_control.get_pending_position()
        self.assertEqual(pos, (10, 20))

    def test_displays_and_version(self):
        """Test displays and version"""
        self.assertEqual(sim_control.get_displays(), "test")
        self.assertEqual(sim_control.get_version(), "1.0")

    def test_platform_detection(self):
        """Test platform detection"""
        platform = sim_control.get_platform()
        # Should be either "msdos" or "unix"
        self.assertIn(platform, ["msdos", "unix"])

    def test_random_number_generation(self):
        """Test random number generation"""
        # Test with max value
        result = sim_control.get_random_number(100)
        self.assertGreaterEqual(result, 0)
        self.assertLess(result, 100)

        # Test without max value
        result2 = sim_control.get_random_number()
        self.assertIsInstance(result2, int)

    def test_dollar_formatting(self):
        """Test dollar amount formatting"""
        formatted = sim_control.format_dollars(12345)
        self.assertEqual(formatted, "$12,345")

    def test_terrain_generation_parameters(self):
        """Test terrain generation parameters"""
        # Test lake level
        sim_control.set_lake_level(4)
        self.assertEqual(sim_control.get_lake_level(), 4)

        # Test tree level
        sim_control.set_tree_level(6)
        self.assertEqual(sim_control.get_tree_level(), 6)

        # Test curve level
        sim_control.set_curve_level(2)
        self.assertEqual(sim_control.get_curve_level(), 2)

        # Test create island
        sim_control.set_create_island(1)
        self.assertEqual(sim_control.get_create_island(), 1)

    def test_display_options(self):
        """Test display options"""
        sim_control.set_do_overlay(3)
        self.assertEqual(sim_control.get_do_overlay(), 3)

        sim_control.set_don_dither(1)
        self.assertEqual(sim_control.get_don_dither(), 1)

        sim_control.set_flush_style(2)
        self.assertEqual(sim_control.get_flush_style(), 2)

        sim_control.set_collapse_motion(1)
        self.assertEqual(sim_control.get_collapse_motion(), 1)

    def test_need_rest(self):
        """Test need rest flag"""
        sim_control.set_need_rest(True)
        self.assertTrue(sim_control.get_need_rest())
        self.assertEqual(self.mock_types.NeedRest, True)

    def test_multi_player_and_sugar_mode(self):
        """Test multiplayer and sugar mode"""
        # These are read-only in the current implementation
        self.assertFalse(sim_control.get_multi_player_mode())
        self.assertFalse(sim_control.get_sugar_mode())

    @patch('webbrowser.open')
    def test_open_web_browser(self, mock_open):
        """Test web browser opening"""
        mock_open.return_value = True
        result = sim_control.open_web_browser("http://example.com")
        self.assertEqual(result, 0)
        mock_open.assert_called_with("http://example.com")

    @patch('webbrowser.open')
    def test_open_web_browser_failure(self, mock_open):
        """Test web browser opening failure"""
        mock_open.side_effect = Exception("Browser not available")
        result = sim_control.open_web_browser("http://example.com")
        self.assertEqual(result, 1)

    def test_quote_url(self):
        """Test URL quoting"""
        quoted = sim_control.quote_url("http://example.com/path with spaces")
        self.assertEqual(quoted, "http%3A//example.com/path%20with%20spaces")

    def test_update_functions(self):
        """Test UI update functions"""
        sim_control.update_heads()
        self.mock_types.Kick.assert_called()

        sim_control.update_maps()
        sim_control.update_editors()
        sim_control.update_graphs()
        sim_control.update_evaluation()

        # Check that Kick was called multiple times
        self.assertGreater(self.mock_types.Kick.call_count, 1)

    @patch('micropolis.sim_control.evaluation.UpdateBudget')
    @patch('micropolis.sim_control.evaluation.DoBudget')
    @patch('micropolis.sim_control.evaluation.DoBudgetFromMenu')
    def test_budget_functions(self, mock_budget_menu, mock_do_budget, mock_update_budget):
        """Test budget functions"""
        sim_control.update_budget()
        mock_update_budget.assert_called_once()
        self.mock_types.Kick.assert_called()

        sim_control.do_budget()
        mock_do_budget.assert_called_once()

        sim_control.do_budget_from_menu()
        mock_budget_menu.assert_called_once()

    @patch('micropolis.sim_control.engine.sim_update')
    def test_update_simulation(self, mock_sim_update):
        """Test simulation update"""
        sim_control.update_simulation()
        mock_sim_update.assert_called_once()


if __name__ == '__main__':
    unittest.main()