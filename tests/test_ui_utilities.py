""""""

test_ui_utilities.py - Basic tests for ui_utilities.pytest_ui_utilities.py - Comprehensive tests for ui_utilities.py

"""

This module contains comprehensive tests for the UI utility functions

import unittestported from w_util.c.

import sys"""

import os

import unittest

# Add the src directory to the path so we can import micropolis modulesfrom unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))import sys

import os

from src.micropolis import ui_utilities

# Add the src directory to the path so we can import micropolis modules

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class TestDollarFormatting(unittest.TestCase):

    """Test dollar formatting functions."""from src.micropolis import ui_utilities



    def test_make_dollar_decimal_str_exact_multiple_of_three(self):import sys

        """Test formatting when number of digits is exact multiple of 3."""

        result = ui_utilities.make_dollar_decimal_str("123456789")import osimport unittest

        self.assertEqual(result, "$123,456,789")

from unittest.mock import Mock, patch, MagicMock

    def test_make_dollar_decimal_str_four_digits(self):

        """Test formatting with 4 digits."""# Add the src directory to the path so we can import micropolis modules

        result = ui_utilities.make_dollar_decimal_str("1234")

        self.assertEqual(result, "$1,234")sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))# Import the module to test



    def test_make_dollar_decimal_str_large_number(self):from . import ui_utilities

        """Test formatting with large number."""

        result = ui_utilities.make_dollar_decimal_str("123456789012345")from src.micropolis import ui_utilities

        self.assertEqual(result, "$123,456,789,012,345")



    def test_make_dollar_decimal_str_single_digit(self):

        """Test formatting with single digit."""class TestDollarFormatting(unittest.TestCase):

        result = ui_utilities.make_dollar_decimal_str("5")

        self.assertEqual(result, "$5")class TestDollarFormatting(unittest.TestCase):    """Test dollar formatting functions."""



    def test_make_dollar_decimal_str_three_digits(self):    """Test dollar formatting functions."""

        """Test formatting with 3 digits."""

        result = ui_utilities.make_dollar_decimal_str("123")    def test_make_dollar_decimal_str_single_digit(self):

        self.assertEqual(result, "$123")

    def test_make_dollar_decimal_str_exact_multiple_of_three(self):        """Test formatting single digit numbers."""

    def test_make_dollar_decimal_str_two_digits(self):

        """Test formatting with 2 digits."""        """Test formatting when number of digits is exact multiple of 3."""        result = ui_utilities.make_dollar_decimal_str("5")

        result = ui_utilities.make_dollar_decimal_str("12")

        self.assertEqual(result, "$12")        result = ui_utilities.make_dollar_decimal_str("123456789")        self.assertEqual(result, "$5")



        self.assertEqual(result, "$123,456,789")

class TestBasicFunctionality(unittest.TestCase):

    """Test basic functionality without complex mocking."""    def test_make_dollar_decimal_str_two_digits(self):



    def test_set_game_level(self):    def test_make_dollar_decimal_str_four_digits(self):        """Test formatting two digit numbers."""

        """Test setting game level."""

        original_level = ui_utilities.types.GameLevel        """Test formatting with 4 digits."""        result = ui_utilities.make_dollar_decimal_str("42")

        ui_utilities.set_game_level(1)

        self.assertEqual(ui_utilities.types.GameLevel, 1)        result = ui_utilities.make_dollar_decimal_str("1234")        self.assertEqual(result, "$42")

        # Restore original value

        ui_utilities.types.GameLevel = original_level        self.assertEqual(result, "$1,234")



    def test_set_city_name_alphanumeric_only(self):    def test_make_dollar_decimal_str_three_digits(self):

        """Test setting city name with only alphanumeric characters."""

        original_name = ui_utilities.types.CityName    def test_make_dollar_decimal_str_large_number(self):        """Test formatting three digit numbers."""

        ui_utilities.set_city_name("TestCity123")

        self.assertEqual(ui_utilities.types.CityName, "TestCity123")        """Test formatting with large number."""        result = ui_utilities.make_dollar_decimal_str("123")

        # Restore original value

        ui_utilities.types.CityName = original_name        result = ui_utilities.make_dollar_decimal_str("123456789012345")        self.assertEqual(result, "$123")



    def test_set_city_name_sanitized(self):        self.assertEqual(result, "$123,456,789,012,345")

        """Test setting city name with sanitization."""

        original_name = ui_utilities.types.CityName    def test_make_dollar_decimal_str_four_digits(self):

        ui_utilities.set_city_name("Test City!")

        # Should sanitize non-alphanumeric characters    def test_make_dollar_decimal_str_single_digit(self):        """Test formatting four digit numbers with comma."""

        self.assertEqual(ui_utilities.types.CityName, "Test_City_")

        # Restore original value        """Test formatting with single digit."""        result = ui_utilities.make_dollar_decimal_str("1234")

        ui_utilities.types.CityName = original_name

        result = ui_utilities.make_dollar_decimal_str("5")        self.assertEqual(result, "$1,234")

    def test_set_any_city_name(self):

        """Test setting city name without sanitization."""        self.assertEqual(result, "$5")

        original_name = ui_utilities.types.CityName

        ui_utilities.set_any_city_name("Test City!")    def test_make_dollar_decimal_str_large_number(self):

        self.assertEqual(ui_utilities.types.CityName, "Test City!")

        # Restore original value    def test_make_dollar_decimal_str_three_digits(self):        """Test formatting large numbers with multiple commas."""

        ui_utilities.types.CityName = original_name

        """Test formatting with 3 digits."""        result = ui_utilities.make_dollar_decimal_str("1234567")

    def test_current_year(self):

        """Test getting current year."""        result = ui_utilities.make_dollar_decimal_str("123")        self.assertEqual(result, "$1,234,567")

        # Set up test values

        original_city_time = ui_utilities.types.CityTime        self.assertEqual(result, "$123")

        original_starting_year = ui_utilities.types.StartingYear

    def test_make_dollar_decimal_str_exact_multiple_of_three(self):

        ui_utilities.types.CityTime = 480  # 10 years

        ui_utilities.types.StartingYear = 1900    def test_make_dollar_decimal_str_two_digits(self):        """Test formatting numbers that are exact multiples of 3 digits."""



        result = ui_utilities.current_year()        """Test formatting with 2 digits."""        result = ui_utilities.make_dollar_decimal_str("123456")



        # 480 CityTime / 48 = 10 years + 1900 = 1910        result = ui_utilities.make_dollar_decimal_str("12")        self.assertEqual(result, "$123,456")

        self.assertEqual(result, 1910)

        self.assertEqual(result, "$12")

        # Restore original values

        ui_utilities.types.CityTime = original_city_time

        ui_utilities.types.StartingYear = original_starting_year

class TestSimulationControl(unittest.TestCase):

    def test_set_year_valid(self):

        """Test setting year above StartingYear."""class TestSimulationControl(unittest.TestCase):    """Test simulation control functions."""

        # Set up test values

        original_starting_year = ui_utilities.types.StartingYear    """Test simulation control functions."""

        original_city_time = ui_utilities.types.CityTime

    def setUp(self):

        ui_utilities.types.StartingYear = 1900

        ui_utilities.types.CityTime = 0    @patch('src.micropolis.ui_utilities.sim_control.is_sim_paused')        """Set up test fixtures."""



        ui_utilities.set_year(1910)    @patch('src.micropolis.ui_utilities.sim_control.pause_simulation')        self.mock_types = Mock()



        # Year offset = 1910 - 1900 - (0 // 48) = 10 - 0 = 10    @patch('src.micropolis.ui_utilities.sim_control.get_sim_speed')        self.mock_sim_control = Mock()

        # CityTime should increase by 10 * 48 = 480

        self.assertEqual(ui_utilities.types.CityTime, 480)    @patch('src.micropolis.ui_utilities.sim_control.resume_simulation')



        # Restore original values    @patch('src.micropolis.ui_utilities.sim_control.set_sim_speed')        # Patch the modules

        ui_utilities.types.StartingYear = original_starting_year

        ui_utilities.types.CityTime = original_city_time    def test_pause_when_already_paused(self, mock_set_sim_speed, mock_resume_simulation,        with patch('src.micropolis.ui_utilities.types', self.mock_types), \



    def test_update_game_level(self):                                       mock_get_sim_speed, mock_pause_simulation,             patch('src.micropolis.ui_utilities.sim_control', self.mock_sim_control):

        """Test updating game level display."""

        # This is a no-op function, just ensure it doesn't crash                                       mock_is_sim_paused):            pass

        ui_utilities.update_game_level()

        """Test pausing when simulation is already paused."""

    def test_do_generated_city_image(self):

        """Test generated city image stub."""        mock_is_sim_paused.return_value = True    @patch('src.micropolis.ui_utilities.sim_control')

        # This is a stub function, just ensure it doesn't crash

        ui_utilities.do_generated_city_image("TestCity", 100, 50000, "VILLAGE", 85)    @patch('src.micropolis.ui_utilities.types')



    def test_do_pop_up_message(self):        ui_utilities.pause()    def test_pause_when_not_paused(self, mock_types, mock_sim_control):

        """Test popup message stub."""

        # This should print to console, but we can't easily test that        """Test pausing when simulation is not already paused."""

        # Just ensure it doesn't crash

        ui_utilities.do_pop_up_message("Test message")        mock_is_sim_paused.assert_called_once()        mock_sim_control.is_sim_paused.return_value = False



    def test_do_start_elmd(self):        mock_pause_simulation.assert_not_called()        mock_sim_control.get_sim_speed.return_value = 3

        """Test start ELM daemon stub."""

        # This is a stub function, just ensure it doesn't crash        mock_get_sim_speed.assert_not_called()

        ui_utilities.do_start_elmd()

        ui_utilities.pause()



class TestUIUtilitiesCommand(unittest.TestCase):    @patch('src.micropolis.ui_utilities.sim_control.is_sim_paused')

    """Test TCL command interface."""

    @patch('src.micropolis.ui_utilities.sim_control.pause_simulation')        mock_sim_control.is_sim_paused.assert_called_once()

    def setUp(self):

        """Set up test fixtures."""    @patch('src.micropolis.ui_utilities.sim_control.get_sim_speed')        mock_sim_control.get_sim_speed.assert_called_once()

        self.cmd = ui_utilities.UIUtilitiesCommand()

    @patch('src.micropolis.ui_utilities.sim_control.resume_simulation')        mock_sim_control.pause_simulation.assert_called_once()

    def test_handle_command_setspeed_invalid_args(self):

        """Test setspeed command with invalid arguments."""    @patch('src.micropolis.ui_utilities.sim_control.set_sim_speed')        mock_types.__setattr__.assert_called_once_with('sim_paused_speed', 3)

        with self.assertRaises(ValueError):

            self.cmd.handle_command("setspeed")    def test_pause_when_not_paused(self, mock_set_sim_speed, mock_resume_simulation,



    def test_handle_command_setspeed_wrong_arg_count(self):                                   mock_get_sim_speed, mock_pause_simulation,    @patch('src.micropolis.ui_utilities.sim_control')

        """Test setspeed command with wrong argument count."""

        with self.assertRaises(ValueError):                                   mock_is_sim_paused):    @patch('src.micropolis.ui_utilities.types')

            self.cmd.handle_command("setspeed", "1", "2")

        """Test pausing when simulation is not already paused."""    def test_pause_when_already_paused(self, mock_types, mock_sim_control):

    def test_handle_command_unknown(self):

        """Test unknown command."""        mock_is_sim_paused.return_value = False        """Test pausing when simulation is already paused."""

        with self.assertRaises(ValueError):

            self.cmd.handle_command("unknown_command")        mock_get_sim_speed.return_value = 3        mock_sim_control.is_sim_paused.return_value = True





if __name__ == '__main__':

    unittest.main()        ui_utilities.pause()        ui_utilities.pause()



        mock_is_sim_paused.assert_called_once()        mock_sim_control.is_sim_paused.assert_called_once()

        mock_pause_simulation.assert_called_once()        mock_sim_control.pause_simulation.assert_not_called()

        mock_get_sim_speed.assert_called_once()

    @patch('src.micropolis.ui_utilities.sim_control')

    @patch('src.micropolis.ui_utilities.sim_control.is_sim_paused')    @patch('src.micropolis.ui_utilities.types')

    @patch('src.micropolis.ui_utilities.sim_control.pause_simulation')    def test_resume_when_paused(self, mock_types, mock_sim_control):

    @patch('src.micropolis.ui_utilities.sim_control.get_sim_speed')        """Test resuming when simulation is paused."""

    @patch('src.micropolis.ui_utilities.sim_control.resume_simulation')        mock_sim_control.is_sim_paused.return_value = True

    @patch('src.micropolis.ui_utilities.sim_control.set_sim_speed')        mock_types.sim_paused_speed = 2

    def test_resume_when_not_paused(self, mock_set_sim_speed, mock_resume_simulation,

                                    mock_get_sim_speed, mock_pause_simulation,        ui_utilities.resume()

                                    mock_is_sim_paused):

        """Test resuming when simulation is not paused."""        mock_sim_control.is_sim_paused.assert_called_once()

        mock_is_sim_paused.return_value = False        mock_sim_control.resume_simulation.assert_called_once()

        mock_sim_control.set_sim_speed.assert_called_once_with(2)

        ui_utilities.resume()

    @patch('src.micropolis.ui_utilities.sim_control')

        mock_is_sim_paused.assert_called_once()    @patch('src.micropolis.ui_utilities.types')

        mock_resume_simulation.assert_not_called()    def test_resume_when_not_paused(self, mock_types, mock_sim_control):

        mock_set_sim_speed.assert_not_called()        """Test resuming when simulation is not paused."""

        mock_sim_control.is_sim_paused.return_value = False

    @patch('src.micropolis.ui_utilities.sim_control.is_sim_paused')

    @patch('src.micropolis.ui_utilities.sim_control.pause_simulation')        ui_utilities.resume()

    @patch('src.micropolis.ui_utilities.sim_control.get_sim_speed')

    @patch('src.micropolis.ui_utilities.sim_control.resume_simulation')        mock_sim_control.is_sim_paused.assert_called_once()

    @patch('src.micropolis.ui_utilities.sim_control.set_sim_speed')        mock_sim_control.resume_simulation.assert_not_called()

    def test_resume_when_paused(self, mock_set_sim_speed, mock_resume_simulation,

                                mock_get_sim_speed, mock_pause_simulation,    @patch('src.micropolis.ui_utilities.sim_control')

                                mock_is_sim_paused):    @patch('src.micropolis.ui_utilities.types')

        """Test resuming when simulation is paused."""    def test_set_speed_valid_range(self, mock_types, mock_sim_control):

        mock_is_sim_paused.return_value = True        """Test setting speed within valid range."""

        # Set up the paused speed        mock_sim_control.is_sim_paused.return_value = False

        ui_utilities.types.sim_paused_speed = 2

        ui_utilities.set_speed(2)

        ui_utilities.resume()

        self.assertEqual(mock_types.SimMetaSpeed, 2)

        mock_is_sim_paused.assert_called_once()        self.assertEqual(mock_types.SimSpeed, 2)

        mock_resume_simulation.assert_called_once()        mock_sim_control.set_sim_speed.assert_called_once_with(2)

        mock_set_sim_speed.assert_called_once_with(2)

    @patch('src.micropolis.ui_utilities.sim_control')

    @patch('src.micropolis.ui_utilities.sim_control.set_sim_skips')    @patch('src.micropolis.ui_utilities.types')

    def test_set_skips(self, mock_set_sim_skips):    def test_set_speed_clamp_low(self, mock_types, mock_sim_control):

        """Test setting simulation skips."""        """Test clamping speed to minimum value."""

        ui_utilities.set_skips(5)        mock_sim_control.is_sim_paused.return_value = False



        mock_set_sim_skips.assert_called_once_with(5)        ui_utilities.set_speed(-1)



    @patch('src.micropolis.ui_utilities.sim_control.is_sim_paused')        self.assertEqual(mock_types.SimMetaSpeed, 0)

    @patch('src.micropolis.ui_utilities.sim_control.set_sim_speed')        self.assertEqual(mock_types.SimSpeed, 0)

    def test_set_speed_clamp_high(self, mock_set_sim_speed, mock_is_sim_paused):

        """Test clamping speed to maximum value."""    @patch('src.micropolis.ui_utilities.sim_control')

        mock_is_sim_paused.return_value = False    @patch('src.micropolis.ui_utilities.types')

    def test_set_speed_clamp_high(self, mock_types, mock_sim_control):

        ui_utilities.set_speed(5)        """Test clamping speed to maximum value."""

        mock_sim_control.is_sim_paused.return_value = False

        # Should be clamped to 3

        self.assertEqual(ui_utilities.types.SimMetaSpeed, 3)        ui_utilities.set_speed(5)

        self.assertEqual(ui_utilities.types.SimSpeed, 3)

        mock_set_sim_speed.assert_called_once_with(3)        self.assertEqual(mock_types.SimMetaSpeed, 3)

        self.assertEqual(mock_types.SimSpeed, 3)

    @patch('src.micropolis.ui_utilities.sim_control.is_sim_paused')

    @patch('src.micropolis.ui_utilities.sim_control.set_sim_speed')    @patch('src.micropolis.ui_utilities.sim_control')

    def test_set_speed_clamp_low(self, mock_set_sim_speed, mock_is_sim_paused):    @patch('src.micropolis.ui_utilities.types')

        """Test clamping speed to minimum value."""    def test_set_speed_when_paused(self, mock_types, mock_sim_control):

        mock_is_sim_paused.return_value = False        """Test setting speed when simulation is paused."""

        mock_sim_control.is_sim_paused.return_value = True

        ui_utilities.set_speed(-1)

        ui_utilities.set_speed(2)

        # Should be clamped to 0

        self.assertEqual(ui_utilities.types.SimMetaSpeed, 0)        self.assertEqual(mock_types.SimMetaSpeed, 2)

        self.assertEqual(ui_utilities.types.SimSpeed, 0)        self.assertEqual(mock_types.sim_paused_speed, 2)

        mock_set_sim_speed.assert_called_once_with(0)        self.assertEqual(mock_types.SimSpeed, 0)

        mock_sim_control.set_sim_speed.assert_called_once_with(0)

    @patch('src.micropolis.ui_utilities.sim_control.is_sim_paused')

    @patch('src.micropolis.ui_utilities.sim_control.set_sim_speed')    @patch('src.micropolis.ui_utilities.sim_control')

    def test_set_speed_valid_range(self, mock_set_sim_speed, mock_is_sim_paused):    def test_set_skips(self, mock_sim_control):

        """Test setting speed within valid range."""        """Test setting simulation skips."""

        mock_is_sim_paused.return_value = False        ui_utilities.set_skips(5)



        ui_utilities.set_speed(2)        mock_sim_control.set_sim_skips.assert_called_once_with(5)



        self.assertEqual(ui_utilities.types.SimMetaSpeed, 2)

        self.assertEqual(ui_utilities.types.SimSpeed, 2)class TestGameLevelManagement(unittest.TestCase):

        mock_set_sim_speed.assert_called_once_with(2)    """Test game level management functions."""



    @patch('src.micropolis.ui_utilities.sim_control.is_sim_paused')    @patch('src.micropolis.ui_utilities.types')

    @patch('src.micropolis.ui_utilities.sim_control.set_sim_speed')    def test_set_game_level_funds_easy(self, mock_types):

    def test_set_speed_when_paused(self, mock_set_sim_speed, mock_is_sim_paused):        """Test setting funds for easy difficulty."""

        """Test setting speed when simulation is paused."""        ui_utilities.set_game_level_funds(0)

        mock_is_sim_paused.return_value = True

        mock_types.SetFunds.assert_called_once_with(20000)

        ui_utilities.set_speed(2)        # Should also call set_game_level(0) but that's mocked



        # When paused, should set SimMetaSpeed but not SimSpeed    @patch('src.micropolis.ui_utilities.types')

        self.assertEqual(ui_utilities.types.SimMetaSpeed, 2)    def test_set_game_level_funds_medium(self, mock_types):

        self.assertEqual(ui_utilities.types.sim_paused_speed, 2)        """Test setting funds for medium difficulty."""

        self.assertEqual(ui_utilities.types.SimSpeed, 0)        ui_utilities.set_game_level_funds(1)

        mock_set_sim_speed.assert_called_once_with(0)

        mock_types.SetFunds.assert_called_once_with(10000)



class TestGameLevelManagement(unittest.TestCase):    @patch('src.micropolis.ui_utilities.types')

    """Test game level management functions."""    def test_set_game_level_funds_hard(self, mock_types):

        """Test setting funds for hard difficulty."""

    @patch('src.micropolis.ui_utilities.types.SetFunds')        ui_utilities.set_game_level_funds(2)

    def test_set_game_level_funds_default(self, mock_SetFunds):

        """Test setting funds for invalid difficulty (defaults to easy)."""        mock_types.SetFunds.assert_called_once_with(5000)

        ui_utilities.set_game_level_funds(99)

    @patch('src.micropolis.ui_utilities.types')

        mock_SetFunds.assert_called_once_with(20000)    def test_set_game_level_funds_default(self, mock_types):

        self.assertEqual(ui_utilities.types.GameLevel, 0)        """Test setting funds for invalid difficulty (defaults to easy)."""

        ui_utilities.set_game_level_funds(99)

    @patch('src.micropolis.ui_utilities.types.SetFunds')

    def test_set_game_level_funds_easy(self, mock_SetFunds):        mock_types.SetFunds.assert_called_once_with(20000)

        """Test setting funds for easy difficulty."""

        ui_utilities.set_game_level_funds(0)    @patch('src.micropolis.ui_utilities.types')

    def test_set_game_level(self, mock_types):

        mock_SetFunds.assert_called_once_with(20000)        """Test setting game level."""

        self.assertEqual(ui_utilities.types.GameLevel, 0)        ui_utilities.set_game_level(1)



    @patch('src.micropolis.ui_utilities.types.SetFunds')        self.assertEqual(mock_types.GameLevel, 1)

    def test_set_game_level_funds_medium(self, mock_SetFunds):

        """Test setting funds for medium difficulty."""    def test_update_game_level(self):

        ui_utilities.set_game_level_funds(1)        """Test updating game level display (no-op in pygame version)."""

        # This function is currently a no-op

        mock_SetFunds.assert_called_once_with(10000)        ui_utilities.update_game_level()

        self.assertEqual(ui_utilities.types.GameLevel, 1)



    @patch('src.micropolis.ui_utilities.types.SetFunds')class TestCityNameManagement(unittest.TestCase):

    def test_set_game_level_funds_hard(self, mock_SetFunds):    """Test city name management functions."""

        """Test setting funds for hard difficulty."""

        ui_utilities.set_game_level_funds(2)    @patch('src.micropolis.ui_utilities.types')

    def test_set_city_name_sanitized(self, mock_types):

        mock_SetFunds.assert_called_once_with(5000)        """Test setting city name with sanitization."""

        self.assertEqual(ui_utilities.types.GameLevel, 2)        ui_utilities.set_city_name("Test City!")



    def test_set_game_level(self):        # Should sanitize non-alphanumeric characters

        """Test setting game level."""        mock_types.__setattr__.assert_called_once_with('CityName', 'Test_City_')

        ui_utilities.set_game_level(1)

    @patch('src.micropolis.ui_utilities.types')

        self.assertEqual(ui_utilities.types.GameLevel, 1)    def test_set_city_name_alphanumeric_only(self, mock_types):

        """Test setting city name with only alphanumeric characters."""

    def test_update_game_level(self):        ui_utilities.set_city_name("TestCity123")

        """Test updating game level display."""

        # This is a no-op function, just ensure it doesn't crash        mock_types.__setattr__.assert_called_once_with('CityName', 'TestCity123')

        ui_utilities.update_game_level()

    @patch('src.micropolis.ui_utilities.types')

    def test_set_any_city_name(self, mock_types):

class TestCityNameManagement(unittest.TestCase):        """Test setting city name without sanitization."""

    """Test city name management functions."""        ui_utilities.set_any_city_name("Test City!")



    def test_set_city_name_alphanumeric_only(self):        mock_types.__setattr__.assert_called_once_with('CityName', 'Test City!')

        """Test setting city name with only alphanumeric characters."""

        ui_utilities.set_city_name("TestCity123")

class TestTimeManagement(unittest.TestCase):

        self.assertEqual(ui_utilities.types.CityName, "TestCity123")    """Test time management functions."""



    def test_set_city_name_sanitized(self):    @patch('src.micropolis.ui_utilities.types')

        """Test setting city name with sanitization."""    def test_set_year_valid(self, mock_types):

        ui_utilities.set_city_name("Test City!")        """Test setting year to valid value."""

        mock_types.StartingYear = 1900

        # Should sanitize non-alphanumeric characters        mock_types.CityTime = 480  # 10 years * 48 = 480

        self.assertEqual(ui_utilities.types.CityName, "Test_City_")

        ui_utilities.set_year(1910)

    def test_set_any_city_name(self):

        """Test setting city name without sanitization."""        # Year offset = 1910 - 1900 - (480 // 48) = 10 - 10 = 0

        ui_utilities.set_any_city_name("Test City!")        # CityTime should increase by 0 * 48 = 0

        self.assertEqual(mock_types.CityTime, 480)

        self.assertEqual(ui_utilities.types.CityName, "Test City!")

    @patch('src.micropolis.ui_utilities.types')

    def test_set_year_below_minimum(self, mock_types):

class TestTimeManagement(unittest.TestCase):        """Test setting year below StartingYear."""

    """Test time management functions."""        mock_types.StartingYear = 1900

        mock_types.CityTime = 480

    def test_current_year(self):

        """Test getting current year."""        ui_utilities.set_year(1800)

        # Set up test values

        original_city_time = ui_utilities.types.CityTime        # Should be clamped to StartingYear

        original_starting_year = ui_utilities.types.StartingYear        # Year offset = 1900 - 1900 - (480 // 48) = 0 - 10 = -10

        # CityTime should increase by -10 * 48 = -480

        ui_utilities.types.CityTime = 480  # 10 years        self.assertEqual(mock_types.CityTime, 0)

        ui_utilities.types.StartingYear = 1900

    @patch('src.micropolis.ui_utilities.types')

        result = ui_utilities.current_year()    def test_current_year(self, mock_types):

        """Test getting current year."""

        # 480 CityTime / 48 = 10 years + 1900 = 1910        mock_types.CityTime = 480  # 10 years

        self.assertEqual(result, 1910)        mock_types.StartingYear = 1900



        # Restore original values        result = ui_utilities.current_year()

        ui_utilities.types.CityTime = original_city_time

        ui_utilities.types.StartingYear = original_starting_year        self.assertEqual(result, 1910)



    def test_set_year_below_minimum(self):

        """Test setting year below StartingYear."""class TestMapViewManagement(unittest.TestCase):

        # Set up test values    """Test map view management functions."""

        original_starting_year = ui_utilities.types.StartingYear

        original_city_time = ui_utilities.types.CityTime    def test_do_set_map_state(self):

        """Test setting map view state."""

        ui_utilities.types.StartingYear = 1900        mock_view = Mock()

        ui_utilities.types.CityTime = 480

        ui_utilities.do_set_map_state(mock_view, 5)

        ui_utilities.set_year(1800)

        self.assertEqual(mock_view.map_state, 5)

        # Should be clamped to StartingYear        self.assertTrue(mock_view.invalid)

        # Year offset = 1900 - 1900 - (480 // 48) = 0 - 10 = -10

        # CityTime should increase by -10 * 48 = -480

        self.assertEqual(ui_utilities.types.CityTime, 0)class TestGameManagement(unittest.TestCase):

    """Test game management functions."""

        # Restore original values

        ui_utilities.types.StartingYear = original_starting_year    @patch('src.micropolis.ui_utilities.initialization')

        ui_utilities.types.CityTime = original_city_time    def test_do_new_game(self, mock_initialization):

        """Test starting a new game."""

    def test_set_year_valid(self):        ui_utilities.do_new_game()

        """Test setting year above StartingYear."""

        # Set up test values        mock_initialization.InitializeSimulation.assert_called_once()

        original_starting_year = ui_utilities.types.StartingYear

        original_city_time = ui_utilities.types.CityTime

class TestStubFunctions(unittest.TestCase):

        ui_utilities.types.StartingYear = 1900    """Test stub functions."""

        ui_utilities.types.CityTime = 0

    def test_do_generated_city_image(self):

        ui_utilities.set_year(1910)        """Test city image generation stub."""

        # Should not raise any exceptions

        # Year offset = 1910 - 1900 - (0 // 48) = 10 - 0 = 10        ui_utilities.do_generated_city_image("TestCity", 100, 1000, "A", 500)

        # CityTime should increase by 10 * 48 = 480

        self.assertEqual(ui_utilities.types.CityTime, 480)    def test_do_start_elmd(self):

        """Test ELM daemon start stub."""

        # Restore original values        # Should not raise any exceptions

        ui_utilities.types.StartingYear = original_starting_year        ui_utilities.do_start_elmd()

        ui_utilities.types.CityTime = original_city_time

    @patch('builtins.print')

    def test_do_pop_up_message(self, mock_print):

class TestMapViewManagement(unittest.TestCase):        """Test popup message display."""

    """Test map view management functions."""        ui_utilities.do_pop_up_message("Test message")



    def test_do_set_map_state(self):        mock_print.assert_called_once_with("Popup message: Test message")

        """Test setting map view state."""

        # Create a mock view object

        mock_view = MagicMock()class TestUIUtilitiesCommand(unittest.TestCase):

        mock_view.map_state = 0    """Test TCL command interface."""

        mock_view.invalid = False

    def setUp(self):

        ui_utilities.do_set_map_state(mock_view, 5)        """Set up test fixtures."""

        self.cmd = ui_utilities.UIUtilitiesCommand()

        self.assertEqual(mock_view.map_state, 5)

        self.assertTrue(mock_view.invalid)    @patch('src.micropolis.ui_utilities.pause')

    def test_handle_command_pause(self, mock_pause):

        """Test pause command."""

class TestGameManagement(unittest.TestCase):        result = self.cmd.handle_command("pause")

    """Test game management functions."""

        mock_pause.assert_called_once()

    @patch('src.micropolis.ui_utilities.initialization.InitializeSimulation')        self.assertEqual(result, "")

    def test_do_new_game(self, mock_InitializeSimulation):

        """Test starting a new game."""    @patch('src.micropolis.ui_utilities.resume')

        ui_utilities.do_new_game()    def test_handle_command_resume(self, mock_resume):

        """Test resume command."""

        mock_InitializeSimulation.assert_called_once()        result = self.cmd.handle_command("resume")



        mock_resume.assert_called_once()

class TestStubFunctions(unittest.TestCase):        self.assertEqual(result, "")

    """Test stub functions."""

    @patch('src.micropolis.ui_utilities.set_speed')

    def test_do_generated_city_image(self):    def test_handle_command_setspeed(self, mock_set_speed):

        """Test generated city image stub."""        """Test setspeed command."""

        # This is a stub function, just ensure it doesn't crash        result = self.cmd.handle_command("setspeed", "2")

        ui_utilities.do_generated_city_image("TestCity", 100, 50000, "VILLAGE", 85)

        mock_set_speed.assert_called_once_with(2)

    def test_do_pop_up_message(self):        self.assertEqual(result, "")

        """Test popup message stub."""

        # This should print to console, but we can't easily test that    def test_handle_command_setspeed_invalid_args(self):

        # Just ensure it doesn't crash        """Test setspeed command with invalid arguments."""

        ui_utilities.do_pop_up_message("Test message")        with self.assertRaises(ValueError) as cm:

            self.cmd.handle_command("setspeed")

    def test_do_start_elmd(self):

        """Test start ELM daemon stub."""        self.assertIn("Usage: setspeed <speed>", str(cm.exception))

        # This is a stub function, just ensure it doesn't crash

        ui_utilities.do_start_elmd()    @patch('src.micropolis.ui_utilities.set_skips')

    def test_handle_command_setskips(self, mock_set_skips):

        """Test setskips command."""

class TestUIUtilitiesCommand(unittest.TestCase):        result = self.cmd.handle_command("setskips", "5")

    """Test TCL command interface."""

        mock_set_skips.assert_called_once_with(5)

    def setUp(self):        self.assertEqual(result, "")

        """Set up test fixtures."""

        self.cmd = ui_utilities.UIUtilitiesCommand()    @patch('src.micropolis.ui_utilities.set_game_level_funds')

    def test_handle_command_setgamelevelfunds(self, mock_set_game_level_funds):

    @patch('src.micropolis.ui_utilities.pause')        """Test setgamelevelfunds command."""

    def test_handle_command_pause(self, mock_pause):        result = self.cmd.handle_command("setgamelevelfunds", "1")

        """Test pause command."""

        result = self.cmd.handle_command("pause")        mock_set_game_level_funds.assert_called_once_with(1)

        self.assertEqual(result, "")

        self.assertEqual(result, "")

        mock_pause.assert_called_once()    @patch('src.micropolis.ui_utilities.set_game_level')

    def test_handle_command_setgamelevel(self, mock_set_game_level):

    @patch('src.micropolis.ui_utilities.resume')        """Test setgamelevel command."""

    def test_handle_command_resume(self, mock_resume):        result = self.cmd.handle_command("setgamelevel", "2")

        """Test resume command."""

        result = self.cmd.handle_command("resume")        mock_set_game_level.assert_called_once_with(2)

        self.assertEqual(result, "")

        self.assertEqual(result, "")

        mock_resume.assert_called_once()    @patch('src.micropolis.ui_utilities.set_city_name')

    def test_handle_command_setcityname(self, mock_set_city_name):

    @patch('src.micropolis.ui_utilities.set_speed')        """Test setcityname command."""

    def test_handle_command_setspeed(self, mock_set_speed):        result = self.cmd.handle_command("setcityname", "TestCity")

        """Test setspeed command."""

        result = self.cmd.handle_command("setspeed", "2")        mock_set_city_name.assert_called_once_with("TestCity")

        self.assertEqual(result, "")

        self.assertEqual(result, "")

        mock_set_speed.assert_called_once_with(2)    @patch('src.micropolis.ui_utilities.set_any_city_name')

    def test_handle_command_setanycityname(self, mock_set_any_city_name):

    def test_handle_command_setspeed_invalid_args(self):        """Test setanycityname command."""

        """Test setspeed command with invalid arguments."""        result = self.cmd.handle_command("setanycityname", "Test City!")

        with self.assertRaises(ValueError):

            self.cmd.handle_command("setspeed")        mock_set_any_city_name.assert_called_once_with("Test City!")

        self.assertEqual(result, "")

    def test_handle_command_setspeed_wrong_arg_count(self):

        """Test setspeed command with wrong argument count."""    @patch('src.micropolis.ui_utilities.set_year')

        with self.assertRaises(ValueError):    def test_handle_command_setyear(self, mock_set_year):

            self.cmd.handle_command("setspeed", "1", "2")        """Test setyear command."""

        result = self.cmd.handle_command("setyear", "1950")

    @patch('src.micropolis.ui_utilities.set_skips')

    def test_handle_command_setskips(self, mock_set_skips):        mock_set_year.assert_called_once_with(1950)

        """Test setskips command."""        self.assertEqual(result, "")

        result = self.cmd.handle_command("setskips", "5")

    @patch('src.micropolis.ui_utilities.current_year')

        self.assertEqual(result, "")    def test_handle_command_currentyear(self, mock_current_year):

        mock_set_skips.assert_called_once_with(5)        """Test currentyear command."""

        mock_current_year.return_value = 1960

    @patch('src.micropolis.ui_utilities.set_game_level_funds')

    def test_handle_command_setgamelevelfunds(self, mock_set_game_level_funds):        result = self.cmd.handle_command("currentyear")

        """Test setgamelevelfunds command."""

        result = self.cmd.handle_command("setgamelevelfunds", "1")        mock_current_year.assert_called_once()

        self.assertEqual(result, "1960")

        self.assertEqual(result, "")

        mock_set_game_level_funds.assert_called_once_with(1)    @patch('src.micropolis.ui_utilities.do_pop_up_message')

    def test_handle_command_popupmessage(self, mock_do_pop_up_message):

    @patch('src.micropolis.ui_utilities.set_game_level')        """Test popupmessage command."""

    def test_handle_command_setgamelevel(self, mock_set_game_level):        result = self.cmd.handle_command("popupmessage", "Test message")

        """Test setgamelevel command."""

        result = self.cmd.handle_command("setgamelevel", "2")        mock_do_pop_up_message.assert_called_once_with("Test message")

        self.assertEqual(result, "")

        self.assertEqual(result, "")

        mock_set_game_level.assert_called_once_with(2)    def test_handle_command_unknown(self):

        """Test unknown command."""

    @patch('src.micropolis.ui_utilities.set_city_name')        with self.assertRaises(ValueError) as cm:

    def test_handle_command_setcityname(self, mock_set_city_name):            self.cmd.handle_command("unknown")

        """Test setcityname command."""

        result = self.cmd.handle_command("setcityname", "TestCity")        self.assertIn("Unknown UI utility command: unknown", str(cm.exception))



        self.assertEqual(result, "")    def test_handle_command_setspeed_wrong_arg_count(self):

        mock_set_city_name.assert_called_once_with("TestCity")        """Test setspeed command with wrong number of arguments."""

        with self.assertRaises(ValueError) as cm:

    @patch('src.micropolis.ui_utilities.set_any_city_name')            self.cmd.handle_command("setspeed", "1", "2")

    def test_handle_command_setanycityname(self, mock_set_any_city_name):

        """Test setanycityname command."""        self.assertIn("Usage: setspeed <speed>", str(cm.exception))

        result = self.cmd.handle_command("setanycityname", "Test City!")



        self.assertEqual(result, "")if __name__ == '__main__':

        mock_set_any_city_name.assert_called_once_with("Test City!")    unittest.main()

    @patch('src.micropolis.ui_utilities.set_year')
    def test_handle_command_setyear(self, mock_set_year):
        """Test setyear command."""
        result = self.cmd.handle_command("setyear", "1950")

        self.assertEqual(result, "")
        mock_set_year.assert_called_once_with(1950)

    @patch('src.micropolis.ui_utilities.current_year')
    def test_handle_command_currentyear(self, mock_current_year):
        """Test currentyear command."""
        mock_current_year.return_value = 1960

        result = self.cmd.handle_command("currentyear")

        self.assertEqual(result, "1960")
        mock_current_year.assert_called_once()

    @patch('src.micropolis.ui_utilities.do_pop_up_message')
    def test_handle_command_popupmessage(self, mock_do_pop_up_message):
        """Test popupmessage command."""
        result = self.cmd.handle_command("popupmessage", "Test message")

        self.assertEqual(result, "")
        mock_do_pop_up_message.assert_called_once_with("Test message")

    def test_handle_command_unknown(self):
        """Test unknown command."""
        with self.assertRaises(ValueError):
            self.cmd.handle_command("unknown_command")


if __name__ == '__main__':
    unittest.main()