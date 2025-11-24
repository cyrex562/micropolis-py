"""
test_evaluation_ui.py - Unit tests for the evaluation_ui.py module

This module contains comprehensive tests for the city evaluation display system.
"""

from unittest.mock import patch, MagicMock
import sys
import os

from tests.assertions import Assertions

# Add the src directory to the path

from micropolis import evaluation_ui
from micropolis.context import AppContext
from micropolis.app_config import AppConfig

# Create a test context
context = AppContext(config=AppConfig())


class TestEvaluationUIConstants(Assertions):
    """Test evaluation UI constants and string mappings"""

    def test_city_class_strings(self):
        """Test city class string mappings"""
        self.assertEqual(evaluation_ui.get_city_class_string(0), "VILLAGE")
        self.assertEqual(evaluation_ui.get_city_class_string(1), "TOWN")
        self.assertEqual(evaluation_ui.get_city_class_string(2), "CITY")
        self.assertEqual(evaluation_ui.get_city_class_string(3), "CAPITAL")
        self.assertEqual(evaluation_ui.get_city_class_string(4), "METROPOLIS")
        self.assertEqual(evaluation_ui.get_city_class_string(5), "MEGALOPOLIS")

        # Test bounds checking
        self.assertEqual(evaluation_ui.get_city_class_string(-1), "UNKNOWN")
        self.assertEqual(evaluation_ui.get_city_class_string(6), "UNKNOWN")

    def test_city_level_strings(self):
        """Test city level string mappings"""
        self.assertEqual(evaluation_ui.get_city_level_string(0), "Easy")
        self.assertEqual(evaluation_ui.get_city_level_string(1), "Medium")
        self.assertEqual(evaluation_ui.get_city_level_string(2), "Hard")

        # Test bounds checking
        self.assertEqual(evaluation_ui.get_city_level_string(-1), "UNKNOWN")
        self.assertEqual(evaluation_ui.get_city_level_string(3), "UNKNOWN")

    def test_problem_strings(self):
        """Test problem string mappings"""
        self.assertEqual(evaluation_ui.get_problem_string(0), "CRIME")
        self.assertEqual(evaluation_ui.get_problem_string(1), "POLLUTION")
        self.assertEqual(evaluation_ui.get_problem_string(2), "HOUSING COSTS")
        self.assertEqual(evaluation_ui.get_problem_string(3), "TAXES")
        self.assertEqual(evaluation_ui.get_problem_string(4), "TRAFFIC")
        self.assertEqual(evaluation_ui.get_problem_string(5), "UNEMPLOYMENT")
        self.assertEqual(evaluation_ui.get_problem_string(6), "FIRES")

        # Test bounds checking
        self.assertEqual(evaluation_ui.get_problem_string(-1), "UNKNOWN")
        self.assertEqual(evaluation_ui.get_problem_string(7), "UNKNOWN")


class TestDollarFormatting(Assertions):
    """Test dollar amount formatting"""

    def test_make_dollar_decimal_str_single_digit(self):
        """Test formatting single digit numbers"""
        result = evaluation_ui.make_dollar_decimal_str("5", "")
        self.assertEqual(result, "$5")

    def test_make_dollar_decimal_str_two_digits(self):
        """Test formatting two digit numbers"""
        result = evaluation_ui.make_dollar_decimal_str("42", "")
        self.assertEqual(result, "$42")

    def test_make_dollar_decimal_str_three_digits(self):
        """Test formatting three digit numbers"""
        result = evaluation_ui.make_dollar_decimal_str("123", "")
        self.assertEqual(result, "$123")

    def test_make_dollar_decimal_str_four_digits(self):
        """Test formatting four digit numbers with comma"""
        result = evaluation_ui.make_dollar_decimal_str("1234", "")
        self.assertEqual(result, "$1,234")

    def test_make_dollar_decimal_str_large_number(self):
        """Test formatting large numbers with multiple commas"""
        result = evaluation_ui.make_dollar_decimal_str("1234567", "")
        self.assertEqual(result, "$1,234,567")

    def test_make_dollar_decimal_str_edge_cases(self):
        """Test edge cases"""
        # Empty string
        result = evaluation_ui.make_dollar_decimal_str("", "")
        self.assertEqual(result, "$")

        # Very large number
        result = evaluation_ui.make_dollar_decimal_str("123456789", "")
        self.assertEqual(result, "$123,456,789")


class TestCurrentYear(Assertions):
    """Test current year calculation"""

    def test_current_year_calculation(self):
        """Test current year calculation"""
        # CityTime = 48 * years_elapsed + remainder
        # CurrentYear = (CityTime // 48) + StartingYear

        context.starting_year = 1900

        context.city_time = 0
        self.assertEqual(evaluation_ui.current_year(context), 1900)

        context.city_time = 48  # 1 year
        self.assertEqual(evaluation_ui.current_year(context), 1901)

        context.city_time = 480  # 10 years
        self.assertEqual(evaluation_ui.current_year(context), 1910)

        context.city_time = 47  # Less than 1 year (47/48)
        self.assertEqual(evaluation_ui.current_year(context), 1900)


class TestEvaluationDisplay(Assertions):
    """Test evaluation display functions"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock evaluation module
        self.eval_patcher = patch("micropolis.evaluation_ui.evaluation")
        self.mock_eval = self.eval_patcher.start()

        # Set up mock data
        self.mock_eval.CityYes = 75
        self.mock_eval.CityNo = 25
        self.mock_eval.ProblemVotes = [10, 20, 5, 15, 8, 12, 3]
        self.mock_eval.ProblemOrder = [
            1,
            3,
            0,
            5,
        ]  # Pollution, Taxes, Crime, Unemployment
        self.mock_eval.CityPop = 50000
        self.mock_eval.deltaCityPop = 2500
        self.mock_eval.CityAssValue = 1000000
        self.mock_eval.CityScore = 750
        self.mock_eval.deltaCityScore = 25
        self.mock_eval.CityClass = 2  # CITY

        # Set game level on context (legacy GameLevel attribute)
        context.game_level = 1  # Medium

    def tearDown(self):
        """Clean up patches"""
        self.eval_patcher.stop()

    @patch("micropolis.evaluation_ui.current_year")
    @patch("micropolis.evaluation_ui.set_evaluation")
    def test_do_score_card(self, mock_set_eval, mock_current_year):
        """Test score card generation"""
        mock_current_year.return_value = 1950

        evaluation_ui.do_score_card(context)

        # Check that set_evaluation was called with correct data
        mock_set_eval.assert_called_once()

        # Get the call arguments
        args = mock_set_eval.call_args[0]

        # Check title
        self.assertEqual(args[17], "City Evaluation  1950")  # title

        # Check score and change
        self.assertEqual(args[0], "25")  # changed
        self.assertEqual(args[1], "750")  # score

        # Check problem names (should be in order: Pollution, Taxes, Crime, Unemployment)
        self.assertEqual(args[2], "**POLLUTION**")  # ps0 - marked as bold
        self.assertEqual(args[3], "TAXES")  # ps1
        self.assertEqual(args[4], "CRIME")  # ps2
        self.assertEqual(args[5], "UNEMPLOYMENT")  # ps3

        # Check problem votes
        self.assertEqual(args[6], "20%")  # pv0 - Pollution
        self.assertEqual(args[7], "15%")  # pv1 - Taxes
        self.assertEqual(args[8], "10%")  # pv2 - Crime
        self.assertEqual(args[9], "12%")  # pv3 - Unemployment

        # Check population stats
        self.assertEqual(args[10], "50000")  # pop
        self.assertEqual(args[11], "2500")  # delta

        # Check assessed value (formatted)
        self.assertEqual(args[12], "$1,000,000")  # assessed_dollars

        # Check city class and level
        self.assertEqual(args[13], "CITY")  # cityclass
        self.assertEqual(args[14], "Medium")  # citylevel

        # Check approval ratings
        self.assertEqual(args[15], "75%")  # goodyes
        self.assertEqual(args[16], "25%")  # goodno

    @patch("micropolis.evaluation_ui.draw_evaluation")
    def test_set_evaluation(self, mock_draw_eval):
        """Test set_evaluation function"""
        evaluation_ui.set_evaluation(
            "25",
            "750",
            "POLLUTION",
            "TAXES",
            "CRIME",
            "UNEMPLOYMENT",
            "20%",
            "15%",
            "10%",
            "12%",
            "50000",
            "2500",
            "$1,000,000",
            "CITY",
            "Medium",
            "75%",
            "25%",
            "City Evaluation  1950",
        )

        # Check that evaluation data was stored
        data = evaluation_ui.get_evaluation_data()
        self.assertIsNotNone(data)
        self.assertEqual(data["title"], "City Evaluation  1950")
        self.assertEqual(data["score"], "750")
        self.assertEqual(data["changed"], "25")
        self.assertEqual(
            data["problems"], ["POLLUTION", "TAXES", "CRIME", "UNEMPLOYMENT"]
        )
        self.assertEqual(data["problem_votes"], ["20%", "15%", "10%", "12%"])
        self.assertEqual(data["population"], "50000")
        self.assertEqual(data["population_delta"], "2500")
        self.assertEqual(data["assessed_value"], "$1,000,000")
        self.assertEqual(data["city_class"], "CITY")
        self.assertEqual(data["city_level"], "Medium")
        self.assertEqual(data["approval_rating"], "75%")
        self.assertEqual(data["disapproval_rating"], "25%")

        # Check that draw_evaluation was called
        mock_draw_eval.assert_called_once()


class TestEvaluationUIState(Assertions):
    """Test evaluation UI state management"""

    def test_change_eval(self):
        """Test change_eval function"""
        # Reset eval_changed on context
        context.eval_changed = 0

        evaluation_ui.change_eval(context)

        self.assertEqual(context.eval_changed, 1)

    @patch("micropolis.evaluation_ui.do_score_card")
    def test_score_doer_with_change(self, mock_do_score):
        """Test score_doer when evaluation has changed"""
        context.eval_changed = 1

        evaluation_ui.score_doer(context)

        mock_do_score.assert_called_once()
        self.assertEqual(context.eval_changed, 0)

    @patch("micropolis.evaluation_ui.do_score_card")
    def test_score_doer_without_change(self, mock_do_score):
        """Test score_doer when evaluation has not changed"""
        context.eval_changed = 0

        evaluation_ui.score_doer(context)

        mock_do_score.assert_not_called()


class TestDrawingFunctions(Assertions):
    """Test UI drawing functions"""

    def test_draw_evaluation(self):
        """Test draw_evaluation flag setting"""
        # Reset flag
        evaluation_ui.must_draw_evaluation = False

        evaluation_ui.draw_evaluation()

        self.assertTrue(evaluation_ui.must_draw_evaluation)

    def test_really_draw_evaluation(self):
        """Test really_draw_evaluation flag clearing"""
        evaluation_ui.must_draw_evaluation = True

        evaluation_ui.really_draw_evaluation()

        self.assertFalse(evaluation_ui.must_draw_evaluation)

    def test_update_evaluation_with_flag(self):
        """Test update_evaluation when flag is set"""
        evaluation_ui.must_draw_evaluation = True

        evaluation_ui.update_evaluation()

        self.assertFalse(evaluation_ui.must_draw_evaluation)

    def test_update_evaluation_without_flag(self):
        """Test update_evaluation when flag is not set"""
        evaluation_ui.must_draw_evaluation = False

        # This should not crash
        evaluation_ui.update_evaluation()

        self.assertFalse(evaluation_ui.must_draw_evaluation)


class TestCommandInterface(Assertions):
    """Test TCL command interface functions"""

    @patch("micropolis.evaluation_ui.do_score_card")
    @patch("micropolis.sim_control.kick")
    def test_do_score_card_command(self, mock_kick, mock_do_score):
        """Test do_score_card_command"""
        evaluation_ui.do_score_card_command(context)

        mock_do_score.assert_called_once()
        mock_kick.assert_called_once()

    @patch("micropolis.sim_control.kick")
    def test_change_eval_command(self, mock_kick):
        """Test change_eval_command"""
        context.eval_changed = 0
        evaluation_ui.change_eval_command(context)

        self.assertEqual(context.eval_changed, 1)
        mock_kick.assert_called_once()

    @patch("micropolis.evaluation_ui.update_evaluation")
    @patch("micropolis.sim_control.kick")
    def test_update_evaluation_command(self, mock_kick, mock_update_eval):
        """Test update_evaluation_command"""
        evaluation_ui.update_evaluation_command(context)

        mock_update_eval.assert_called_once()
        mock_kick.assert_called_once()


class TestEvaluationDataAccess(Assertions):
    """Test evaluation data access functions"""

    def test_get_evaluation_data_initially_none(self):
        """Test that evaluation data is initially None"""
        # Reset global data
        evaluation_ui._evaluation_data = None

        data = evaluation_ui.get_evaluation_data()
        self.assertIsNone(data)

    def test_get_evaluation_data_after_setting(self):
        """Test getting evaluation data after it has been set"""
        test_data = {"title": "Test", "score": "100"}
        evaluation_ui._evaluation_data = test_data

        data = evaluation_ui.get_evaluation_data()
        self.assertEqual(data, test_data)


class TestEvaluationPanel(Assertions):
    """Tests for pygame evaluation overlay state."""

    def teardown_method(self):
        evaluation_ui.set_evaluation_panel_visible(False)

    def test_visibility_toggle(self):
        evaluation_ui.set_evaluation_panel_visible(False)
        self.assertFalse(evaluation_ui.is_evaluation_panel_visible())
        evaluation_ui.set_evaluation_panel_visible(True)
        self.assertTrue(evaluation_ui.is_evaluation_panel_visible())

    def test_get_surface_without_pygame(self):
        with patch.object(evaluation_ui, "PYGAME_AVAILABLE", False):
            evaluation_ui.set_evaluation_panel_visible(True)
            evaluation_ui.draw_evaluation()
            self.assertIsNone(evaluation_ui.get_evaluation_surface())

    def test_get_surface_with_pygame(self):
        with (
            patch.object(evaluation_ui, "PYGAME_AVAILABLE", True),
            patch.object(evaluation_ui, "pygame") as mock_pygame,
        ):
            mock_pygame.SRCALPHA = 0
            mock_surface = MagicMock()
            mock_pygame.Surface.return_value = mock_surface
            mock_surface.get_size.return_value = (250, 150)
            mock_surface.fill = MagicMock()
            mock_font = MagicMock()
            mock_render = MagicMock()
            mock_render.get_height.return_value = 12
            mock_font.render.return_value = mock_render
            mock_pygame.font.get_init.return_value = True
            mock_pygame.font.SysFont.return_value = mock_font
            mock_pygame.draw.rect = MagicMock()

            evaluation_ui._evaluation_data = {
                "title": "Test",
                "score": "100",
                "changed": "5",
                "population": "1000",
                "population_delta": "50",
                "approval_rating": "60%",
                "disapproval_rating": "40%",
            }

            evaluation_ui.set_evaluation_panel_visible(True)
            evaluation_ui.set_evaluation_panel_size(context, 250, 150)
            evaluation_ui.draw_evaluation()

            surface = evaluation_ui.get_evaluation_surface()
            self.assertIs(surface, mock_surface)
