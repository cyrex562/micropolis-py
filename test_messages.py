"""
test_messages.py - Unit tests for the messages system

Tests the message system functions including message sending,
scenario scoring, and message string loading.
"""

import unittest
from unittest.mock import patch, MagicMock

from src.micropolis import messages, types


class TestMessages(unittest.TestCase):
    """Test cases for the messages system."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset message state
        types.MessagePort = 0
        types.MesX = 0
        types.MesY = 0
        types.MesNum = 0
        types.LastMesTime = 0
        types.LastCityPop = 0
        types.LastCategory = 0
        types.LastPicNum = 0
        types.LastMessage = ""
        types.HaveLastMessage = 0
        types.Sound = 1
        types.autoGo = 0

        # Reset city state for testing
        types.TotalZPop = 0
        types.ResZPop = 0
        types.ComZPop = 0
        types.IndZPop = 0
        types.NuclearPop = 0
        types.CoalPop = 0
        types.RoadTotal = 0
        types.RailTotal = 0
        types.ResPop = 0
        types.ComPop = 0
        types.IndPop = 0
        types.StadiumPop = 0
        types.PortPop = 0
        types.APortPop = 0
        types.TotalPop = 0
        types.FireStPop = 0
        types.PolicePop = 0
        types.CityTax = 0
        types.RoadEffect = 0
        types.FireEffect = 0
        types.PoliceEffect = 0
        types.PolluteAverage = 0
        types.CrimeAverage = 0
        types.TrafficAverage = 0
        types.unPwrdZCnt = 0
        types.PwrdZCnt = 0
        types.ScenarioID = 0
        types.ScoreType = 0
        types.ScoreWait = 0
        types.CityClass = 0
        types.CityScore = 0

    def test_load_message_strings(self):
        """Test loading message strings from file."""
        messages.load_message_strings()
        # Should have loaded strings (may be empty if file not found)
        self.assertIsInstance(messages.MESSAGE_STRINGS, list)

    def test_get_message_string(self):
        """Test getting message strings by number."""
        messages.load_message_strings()

        # Test valid message numbers
        msg = messages.get_message_string(1)
        self.assertIsInstance(msg, str)

        # Test invalid message numbers
        msg = messages.get_message_string(999)
        self.assertEqual(msg, "")

    def test_tick_count(self):
        """Test tick count function."""
        count1 = messages.tick_count()
        count2 = messages.tick_count()
        # Should be monotonically increasing
        self.assertGreaterEqual(count2, count1)
        self.assertIsInstance(count1, int)

    @patch('src.micropolis.messages.types')
    def test_make_sound(self, mock_types):
        """Test sound playing function."""
        mock_types.Sound = 1
        # Should not raise an exception
        messages.make_sound("city", "test")
        mock_types.Sound = 0
        messages.make_sound("city", "test")

    def test_clear_mes(self):
        """Test clearing message state."""
        types.MessagePort = 5
        types.MesX = 10
        types.MesY = 20
        types.LastPicNum = 3

        messages.clear_mes()

        self.assertEqual(types.MessagePort, 0)
        self.assertEqual(types.MesX, 0)
        self.assertEqual(types.MesY, 0)
        self.assertEqual(types.LastPicNum, 0)

    def test_send_mes(self):
        """Test sending messages."""
        # Clear message port first
        types.MessagePort = 0

        # Should send positive message
        result = messages.send_mes(1)
        self.assertEqual(result, 1)
        self.assertEqual(types.MessagePort, 1)
        self.assertEqual(types.MesX, 0)
        self.assertEqual(types.MesY, 0)

        # Should not send duplicate positive message
        result = messages.send_mes(1)
        self.assertEqual(result, 0)

        # Clear and test negative message
        types.MessagePort = 0
        types.LastPicNum = 0
        result = messages.send_mes(-10)
        self.assertEqual(result, 1)
        self.assertEqual(types.MessagePort, -10)
        self.assertEqual(types.LastPicNum, -10)

        # Should not send duplicate negative message
        result = messages.send_mes(-10)
        self.assertEqual(result, 0)

    def test_send_mes_at(self):
        """Test sending messages at specific locations."""
        types.MessagePort = 0

        messages.send_mes_at(5, 100, 200)

        self.assertEqual(types.MessagePort, 5)
        self.assertEqual(types.MesX, 100)
        self.assertEqual(types.MesY, 200)

    def test_check_growth(self):
        """Test population growth milestone checking."""
        # Test initial state
        types.LastCityPop = 0
        types.LastCategory = 0

        # Set up city with small population
        types.ResPop = 10
        types.ComPop = 0
        types.IndPop = 0
        types.CityTime = 4  # Multiple of 4 to trigger check

        messages.check_growth()

        # Should not trigger any messages yet
        self.assertEqual(types.LastCityPop, 200)  # (10+0+0)*20 = 200
        # Actually: ((ResPop) + (ComPop * 8L) + (IndPop * 8L)) * 20L
        # = (10 + 0 + 0) * 20 = 200

        # Test town milestone
        types.LastCityPop = 1999
        types.ResPop = 100  # Should give population of 2000
        messages.check_growth()

        # Should have sent message -35 (town)
        self.assertEqual(types.MessagePort, -35)
        self.assertEqual(types.LastCategory, 35)

    @patch('src.micropolis.messages.do_lose_game')
    def test_do_scenario_score_lose(self, mock_lose_game):
        """Test scenario scoring for loss conditions."""
        types.ScoreType = 1  # Dullsville
        types.CityClass = 3  # Less than required 4

        messages.do_scenario_score(1)

        # Should call lose game
        mock_lose_game.assert_called_once()

    @patch('src.micropolis.messages.do_lose_game')
    def test_do_scenario_score_win(self, mock_lose_game):
        """Test scenario scoring for win conditions."""
        types.ScoreType = 1  # Dullsville
        types.CityClass = 4  # Meets requirement

        messages.do_scenario_score(1)

        # Should send win message (-100)
        self.assertEqual(types.MessagePort, -100)
        # Should not call lose game
        mock_lose_game.assert_not_called()

    @patch('src.micropolis.messages.types')
    def test_set_message_field(self, mock_types):
        """Test setting message field in UI."""
        mock_types.HaveLastMessage = 0
        mock_types.LastMessage = ""
        mock_types.Eval = MagicMock()

        messages.set_message_field("Test message")

        mock_types.Eval.assert_called_with("UISetMessage {Test message}")
        self.assertEqual(mock_types.LastMessage, "Test message")
        self.assertEqual(mock_types.HaveLastMessage, 1)

        # Test duplicate message (should not call Eval again)
        mock_types.Eval.reset_mock()
        messages.set_message_field("Test message")
        mock_types.Eval.assert_not_called()

    @patch('src.micropolis.messages.types')
    def test_do_auto_goto(self, mock_types):
        """Test auto-goto functionality."""
        mock_types.Eval = MagicMock()

        messages.do_auto_goto(50, 75, "Test message")

        mock_types.Eval.assert_any_call("UISetMessage {Test message}")
        mock_types.Eval.assert_any_call("UIAutoGoto 50 75")

    @patch('src.micropolis.messages.types')
    def test_do_show_picture(self, mock_types):
        """Test showing pictures."""
        mock_types.Eval = MagicMock()

        messages.do_show_picture(42)

        mock_types.Eval.assert_called_with("UIShowPicture 42")

    @patch('src.micropolis.messages.types')
    def test_do_lose_game(self, mock_types):
        """Test game loss handling."""
        mock_types.Eval = MagicMock()

        messages.do_lose_game()

        mock_types.Eval.assert_called_with("UILoseGame")

    @patch('src.micropolis.messages.types')
    def test_do_win_game(self, mock_types):
        """Test game win handling."""
        mock_types.Eval = MagicMock()

        messages.do_win_game()

        mock_types.Eval.assert_called_with("UIWinGame")

    def test_monster_speed(self):
        """Test monster speed calculation."""
        # Test multiple calls to ensure valid range
        for _ in range(10):
            speed = messages.monster_speed()
            self.assertGreaterEqual(speed, 70)
            self.assertLessEqual(speed, 110)  # 40 + 70


if __name__ == '__main__':
    unittest.main()