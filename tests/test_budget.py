"""
test_budget.py - Unit tests for the budget.py module

This module contains comprehensive tests for the budget and finance management system.
"""

import unittest
from unittest.mock import patch
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from micropolis import budget


class TestBudgetGlobals(unittest.TestCase):
    """Test budget global variables and initialization"""

    def setUp(self):
        """Reset budget state before each test"""
        budget.init_funding_level()

    def test_initial_funding_levels(self):
        """Test that funding levels are initialized correctly"""
        # Note: init_funding_level() sets drawing flags to True
        self.assertEqual(budget.get_road_percent(), 1.0)
        self.assertEqual(budget.get_police_percent(), 1.0)
        self.assertEqual(budget.get_fire_percent(), 1.0)

        self.assertEqual(budget.get_road_value(), 0)
        self.assertEqual(budget.get_police_value(), 0)
        self.assertEqual(budget.get_fire_value(), 0)

    def test_budget_percent_setters(self):
        """Test budget percentage setters with bounds checking"""
        # Test valid values
        budget.set_road_percent(0.5)
        self.assertEqual(budget.get_road_percent(), 0.5)

        budget.set_police_percent(0.75)
        self.assertEqual(budget.get_police_percent(), 0.75)

        budget.set_fire_percent(0.25)
        self.assertEqual(budget.get_fire_percent(), 0.25)

        # Test bounds checking
        budget.set_road_percent(-0.1)
        self.assertEqual(budget.get_road_percent(), 0.0)

        budget.set_road_percent(1.5)
        self.assertEqual(budget.get_road_percent(), 1.0)


class TestBudgetCalculation(unittest.TestCase):
    """Test budget calculation logic"""

    def setUp(self):
        """Set up test fixtures with mock types"""
        budget.init_funding_level()

        # Mock types module
        self.types_patcher = patch('micropolis.budget.types')
        self.mock_types = self.types_patcher.start()

        # Set up mock values
        self.mock_types.FireFund = 100
        self.mock_types.PoliceFund = 100
        self.mock_types.RoadFund = 100
        self.mock_types.TaxFund = 200
        self.mock_types.TotalFunds = 1000
        self.mock_types.autoBudget = 0
        self.mock_types.FireSpend = 0
        self.mock_types.PoliceSpend = 0
        self.mock_types.RoadSpend = 0
        self.mock_types.MustUpdateFunds = 0

    def tearDown(self):
        """Clean up patches"""
        self.types_patcher.stop()

    @patch('micropolis.budget.spend')
    @patch('micropolis.budget.show_budget_window_and_start_waiting')
    def test_do_budget_now_manual_enough_funds(self, mock_show_window, mock_spend):
        """Test manual budget with enough funds"""
        # Set up: enough funds for all requests
        self.mock_types.TaxFund = 350  # More than 100+100+100=300

        budget.do_budget_now(from_menu=False)

        # Should allocate full requested amounts
        self.assertEqual(budget.get_fire_value(), 100)
        self.assertEqual(budget.get_police_value(), 100)
        self.assertEqual(budget.get_road_value(), 100)

        # Should call spend with remaining funds
        mock_spend.assert_called_once_with(-50)  # 350 - 300 = 50

        # Should show budget window
        mock_show_window.assert_called_once()

    @patch('micropolis.budget.spend')
    @patch('micropolis.budget.show_budget_window_and_start_waiting')
    def test_do_budget_now_manual_insufficient_funds(self, mock_show_window, mock_spend):
        """Test manual budget with insufficient funds"""
        # Set up: not enough funds
        self.mock_types.TaxFund = 50  # 50 + 100 = 150 total funds, but 300 needed

        budget.do_budget_now(from_menu=False)

        # Should allocate proportionally with priority: road > fire > police
        # Road gets full allocation (100), fire gets remaining (50), police gets 0
        self.assertEqual(budget.get_road_value(), 100)  # Full road allocation
        self.assertEqual(budget.get_fire_value(), 50)   # Remaining funds
        self.assertEqual(budget.get_police_value(), 0)  # Police gets nothing

        # Should adjust fire percentage
        self.assertEqual(budget.get_fire_percent(), 0.5)
        self.assertEqual(budget.get_police_percent(), 0.0)

        mock_show_window.assert_called_once()

    @patch('micropolis.budget.update_heads')
    def test_do_budget_now_auto_enough_funds(self, mock_update_heads):
        """Test auto-budget with enough funds"""
        # Set up auto-budget mode
        self.mock_types.autoBudget = 1
        self.mock_types.TaxFund = 350

        budget.do_budget_now(from_menu=False)

        # Should allocate full amounts
        self.assertEqual(budget.get_fire_value(), 100)
        self.assertEqual(budget.get_police_value(), 100)
        self.assertEqual(budget.get_road_value(), 100)

        # Should set spending values
        self.assertEqual(self.mock_types.FireSpend, 100)
        self.assertEqual(self.mock_types.PoliceSpend, 100)
        self.assertEqual(self.mock_types.RoadSpend, 100)

        mock_update_heads.assert_called_once()

    @patch('micropolis.budget.messages')
    def test_do_budget_now_auto_insufficient_funds(self, mock_messages):
        """Test auto-budget with insufficient funds disables auto-budget"""
        # Set up auto-budget mode but insufficient funds
        self.mock_types.autoBudget = 1
        self.mock_types.TaxFund = 150  # 150 + 100 = 250 total funds, but 300 needed

        budget.do_budget_now(from_menu=False)

        # Should send message about insufficient funds
        mock_messages.clear_mes.assert_called_once()
        mock_messages.send_mes.assert_called_once_with(29)

        # Should set MustUpdateOptions
        self.assertEqual(self.mock_types.MustUpdateOptions, 1)


class TestBudgetUI(unittest.TestCase):
    """Test budget UI functions"""

    def setUp(self):
        """Set up test fixtures"""
        budget.init_funding_level()

    def test_draw_flags(self):
        """Test drawing flags are set correctly"""
        # Reset flags first
        budget.must_draw_curr_percents = False
        budget.must_draw_budget_window = False

        # Initially false
        self.assertFalse(budget.must_draw_curr_percents)
        self.assertFalse(budget.must_draw_budget_window)

        # Set flags
        budget.draw_curr_percents()
        budget.draw_budget_window()

        self.assertTrue(budget.must_draw_curr_percents)
        self.assertTrue(budget.must_draw_budget_window)

    @patch('micropolis.budget.really_draw_curr_percents')
    @patch('micropolis.budget.really_draw_budget_window')
    def test_update_budget_window(self, mock_draw_window, mock_draw_percents):
        """Test budget window updates"""
        # Set flags
        budget.draw_curr_percents()
        budget.draw_budget_window()

        # Update should call drawing functions and clear flags
        budget.update_budget_window()

        mock_draw_percents.assert_called_once()
        mock_draw_window.assert_called_once()

        # Flags should be cleared
        self.assertFalse(budget.must_draw_curr_percents)
        self.assertFalse(budget.must_draw_budget_window)


class TestBudgetCommands(unittest.TestCase):
    """Test TCL command interfaces"""

    def setUp(self):
        """Set up test fixtures"""
        budget.init_funding_level()

        self.types_patcher = patch('micropolis.budget.types')
        self.mock_types = self.types_patcher.start()
        self.mock_types.autoBudget = 0
        self.mock_types.MustUpdateOptions = 0

    def tearDown(self):
        """Clean up patches"""
        self.types_patcher.stop()

    @patch('micropolis.budget.kick')
    @patch('micropolis.budget.update_budget')
    def test_auto_budget_command(self, mock_update_budget, mock_kick):
        """Test auto_budget command interface"""
        # Test getter
        result = budget.auto_budget()
        self.assertEqual(result, 0)

        # Test setter
        result = budget.auto_budget(True)
        self.assertEqual(result, 1)  # Returns new value (True converted to 1)

        self.assertEqual(self.mock_types.autoBudget, 1)
        self.assertEqual(self.mock_types.MustUpdateOptions, 1)
        mock_kick.assert_called_once()
        mock_update_budget.assert_called_once()

    @patch('micropolis.budget.do_budget')
    @patch('micropolis.budget.kick')
    def test_do_budget_command(self, mock_kick, mock_do_budget):
        """Test do_budget command"""
        budget.do_budget_command()
        mock_do_budget.assert_called_once()
        mock_kick.assert_called_once()

    @patch('micropolis.budget.do_budget_from_menu')
    @patch('micropolis.budget.kick')
    def test_do_budget_from_menu_command(self, mock_kick, mock_do_budget_from_menu):
        """Test do_budget_from_menu command"""
        budget.do_budget_from_menu_command()
        mock_do_budget_from_menu.assert_called_once()
        mock_kick.assert_called_once()

    @patch('micropolis.budget.update_budget')
    @patch('micropolis.budget.kick')
    def test_update_budget_command(self, mock_kick, mock_update_budget):
        """Test update_budget command"""
        budget.update_budget_command()
        mock_update_budget.assert_called_once()
        mock_kick.assert_called_once()

    @patch('micropolis.budget.update_budget_window')
    @patch('micropolis.budget.kick')
    def test_update_budget_window_command(self, mock_kick, mock_update_budget_window):
        """Test update_budget_window command"""
        budget.update_budget_window_command()
        mock_update_budget_window.assert_called_once()
        mock_kick.assert_called_once()


class TestBudgetIntegration(unittest.TestCase):
    """Integration tests for budget system"""

    def setUp(self):
        """Set up integration test fixtures"""
        budget.init_funding_level()

        self.types_patcher = patch('micropolis.budget.types')
        self.mock_types = self.types_patcher.start()

        # Set up realistic values
        self.mock_types.FireFund = 500
        self.mock_types.PoliceFund = 400
        self.mock_types.RoadFund = 600
        self.mock_types.TaxFund = 1000
        self.mock_types.TotalFunds = 5000
        self.mock_types.autoBudget = 0

    def tearDown(self):
        """Clean up patches"""
        self.types_patcher.stop()

    def test_budget_allocation_priority(self):
        """Test that budget allocation follows correct priority"""
        # Set different percentages
        budget.set_fire_percent(0.8)    # 500 * 0.8 = 400
        budget.set_police_percent(0.6)  # 400 * 0.6 = 240
        budget.set_road_percent(0.9)    # 600 * 0.9 = 540
        # Total requested: 400 + 240 + 540 = 1180

        # TaxFund = 1000, TotalFunds = 5000, so plenty of funds
        self.mock_types.TaxFund = 1000

        budget.do_budget_now(from_menu=False)

        # Enough funds for all requests
        self.assertEqual(budget.get_road_value(), 540)
        self.assertEqual(budget.get_fire_value(), 400)
        self.assertEqual(budget.get_police_value(), 240)

    def test_budget_max_values(self):
        """Test that max values are set correctly"""
        budget.do_budget_now(from_menu=False)

        self.assertEqual(budget.get_fire_max_value(), 500)
        self.assertEqual(budget.get_police_max_value(), 400)
        self.assertEqual(budget.get_road_max_value(), 600)


class TestSpendFunction(unittest.TestCase):
    """Test the spend utility function"""

    def setUp(self):
        """Set up test fixtures"""
        self.types_patcher = patch('micropolis.budget.types')
        self.mock_types = self.types_patcher.start()
        self.mock_types.TotalFunds = 1000
        self.mock_types.MustUpdateFunds = 0

    def tearDown(self):
        """Clean up patches"""
        self.types_patcher.stop()

    @patch('micropolis.budget.kick')
    def test_spend_positive_amount(self, mock_kick):
        """Test spending positive amount"""
        budget.spend(200)

        self.assertEqual(self.mock_types.TotalFunds, 800)
        self.assertEqual(self.mock_types.MustUpdateFunds, 1)
        mock_kick.assert_called_once()

    @patch('micropolis.budget.kick')
    def test_spend_negative_amount(self, mock_kick):
        """Test spending negative amount (refund)"""
        budget.spend(-100)

        self.assertEqual(self.mock_types.TotalFunds, 1100)
        self.assertEqual(self.mock_types.MustUpdateFunds, 1)
        mock_kick.assert_called_once()


if __name__ == '__main__':
    unittest.main()