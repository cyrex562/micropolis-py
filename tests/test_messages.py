"""
test_messages.py - Unit tests for the messages system

Tests the message system functions including message sending,
scenario scoring, and message string loading.
"""

from unittest.mock import MagicMock, patch

from src.micropolis import messages
from src.micropolis.context import AppContext
from tests.assertions import Assertions

context: AppContext | None = None


class TestMessages(Assertions):
    """Test cases for the messages system."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset message state
        context.message_port = 0
        context.mes_x = 0
        context.mes_y = 0
        context.mes_num = 0
        context.last_mes_time = 0
        context.last_city_pop = 0
        context.last_category = 0
        context.last_pic_num = 0
        context.last_message = ""
        context.have_last_message = False
        context.sound = 1
        context.auto_go = False

        # Reset city state for testing
        context.total_z_pop = 0
        context.res_z_pop = 0
        context.com_z_pop = 0
        context.ind_z_pop = 0
        context.nuclear_pop = 0
        context.coal_pop = 0
        context.road_total = 0
        context.rail_total = 0
        context.res_pop = 0
        context.com_pop = 0
        context.ind_pop = 0
        context.stadium_pop = 0
        context.port_pop = 0
        context.airport_pop = 0
        context.total_pop = 0
        context.fire_st_pop = 0
        context.police_pop = 0
        context.city_tax = 0
        context.road_effect = 0
        context.fire_effect = 0
        context.police_effect = 0
        context.pollute_average = 0
        context.crime_average = 0
        context.traffic_average = 0
        context.un_pwrd_z_cnt = 0
        context.pwrd_z_cnt = 0
        context.scenario_id = 0
        context.score_type = 0
        context.score_wait = 0
        context.city_class = 0
        context.city_score = 0

    def test_load_message_strings(self):
        """Test loading message strings from file."""
        messages.load_message_strings()
        # Should have loaded strings (may be empty if file not found)
        self.assertIsInstance(messages.MESSAGE_STRINGS, list)

    def test_get_message_string(self):
        """Test getting message strings by number."""
        messages.load_message_strings()

        # Test valid message numbers
        msg = messages.get_message_string(context, 1)
        self.assertIsInstance(msg, str)

        # Test invalid message numbers
        msg = messages.get_message_string(context, 999)
        self.assertEqual(msg, "")

    def test_tick_count(self):
        """Test tick count function."""
        count1 = messages.tick_count()
        count2 = messages.tick_count()
        # Should be monotonically increasing
        self.assertGreaterEqual(count2, count1)
        self.assertIsInstance(count1, int)

    @patch("src.micropolis.messages.types")
    def test_make_sound(self, mock_types):
        """Test sound playing function."""
        mock_types.Sound = 1
        # Should not raise an exception
        messages.make_sound(context, "city", "test")
        mock_types.Sound = 0
        messages.make_sound(context, "city", "test")

    def test_clear_mes(self):
        """Test clearing message state."""
        context.message_port = 5
        context.mes_x = 10
        context.mes_y = 20
        context.last_pic_num = 3

        messages.clear_mes(context)

        self.assertEqual(context.message_port, 0)
        self.assertEqual(context.mes_x, 0)
        self.assertEqual(context.mes_y, 0)
        self.assertEqual(context.last_pic_num, 0)

    def test_send_mes(self):
        """Test sending messages."""
        # Clear message port first
        context.message_port = 0

        # Should send positive message
        result = messages.send_mes(context, 1)
        self.assertEqual(result, 1)
        self.assertEqual(context.message_port, 1)
        self.assertEqual(context.mes_x, 0)
        self.assertEqual(context.mes_y, 0)

        # Should not send duplicate positive message
        result = messages.send_mes(context, 1)
        self.assertEqual(result, 0)

        # Clear and test negative message
        context.message_port = 0
        context.last_pic_num = 0
        result = messages.send_mes(context, -10)
        self.assertEqual(result, 1)
        self.assertEqual(context.message_port, -10)
        self.assertEqual(context.last_pic_num, -10)

        # Should not send duplicate negative message
        result = messages.send_mes(context, -10)
        self.assertEqual(result, 0)

    def test_send_mes_at(self):
        """Test sending messages at specific locations."""
        context.message_port = 0

        messages.send_mes_at(context, 5, 100, 200)

        self.assertEqual(context.message_port, 5)
        self.assertEqual(context.mes_x, 100)
        self.assertEqual(context.mes_y, 200)

    def test_check_growth(self):
        """Test population growth milestone checking."""
        # Test initial state
        context.last_city_pop = 0
        context.last_category = 0

        # Set up city with small population
        context.res_pop = 10
        context.com_pop = 0
        context.ind_pop = 0
        context.city_time = 4  # Multiple of 4 to trigger check

        messages.check_growth(context)

        # Should not trigger any messages yet
        self.assertEqual(context.last_city_pop, 200)  # (10+0+0)*20 = 200
        # Actually: ((ResPop) + (ComPop * 8L) + (IndPop * 8L)) * 20L
        # = (10 + 0 + 0) * 20 = 200

        # Test town milestone
        context.last_city_pop = 1999
        context.res_pop = 100  # Should give population of 2000
        messages.check_growth(context)

        # Should have sent message -35 (town)
        self.assertEqual(context.message_port, -35)
        self.assertEqual(context.last_category, 35)

    @patch("src.micropolis.messages.do_lose_game")
    def test_do_scenario_score_lose(self, mock_lose_game):
        """Test scenario scoring for loss conditions."""
        context.score_type = 1  # Dullsville
        context.city_class = 3  # Less than required 4

        messages.do_scenario_score(context, 1)

        # Should call lose game
        mock_lose_game.assert_called_once()

    @patch("src.micropolis.messages.do_lose_game")
    def test_do_scenario_score_win(self, mock_lose_game):
        """Test scenario scoring for win conditions."""
        context.score_type = 1  # Dullsville
        context.city_class = 4  # Meets requirement

        messages.do_scenario_score(context, 1)

        # Should send win message (-100)
        self.assertEqual(context.message_port, -100)
        # Should not call lose game
        mock_lose_game.assert_not_called()

    @patch("src.micropolis.messages.types")
    def test_set_message_field(self, mock_types):
        """Test setting message field in UI."""
        mock_types.HaveLastMessage = 0
        mock_types.LastMessage = ""
        mock_types.Eval = MagicMock()

        messages.set_message_field(context, "Test message")

        mock_types.Eval.assert_called_with("UISetMessage {Test message}")
        self.assertEqual(mock_types.LastMessage, "Test message")
        self.assertEqual(mock_types.HaveLastMessage, 1)

        # Test duplicate message (should not call Eval again)
        mock_types.Eval.reset_mock()
        messages.set_message_field(context, "Test message")
        mock_types.Eval.assert_not_called()

    @patch("src.micropolis.messages.types")
    def test_do_auto_goto(self, mock_types):
        """Test auto-goto functionality."""
        mock_types.Eval = MagicMock()

        messages.do_auto_goto(context, 50, 75, "Test message")

        mock_types.Eval.assert_any_call("UISetMessage {Test message}")
        mock_types.Eval.assert_any_call("UIAutoGoto 50 75")

    @patch("src.micropolis.messages.types")
    def test_do_show_picture(self, mock_types):
        """Test showing pictures."""
        mock_types.Eval = MagicMock()

        messages.do_show_picture(context, 42)

        mock_types.Eval.assert_called_with("UIShowPicture 42")

    @patch("src.micropolis.messages.types")
    def test_do_lose_game(self, mock_types):
        """Test game loss handling."""
        mock_types.Eval = MagicMock()

        messages.do_lose_game(context)

        mock_types.Eval.assert_called_with("UILoseGame")

    @patch("src.micropolis.messages.types")
    def test_do_win_game(self, mock_types):
        """Test game win handling."""
        mock_types.Eval = MagicMock()

        messages.do_win_game(context)

        mock_types.Eval.assert_called_with("UIWinGame")

    def test_monster_speed(self):
        """Test monster speed calculation."""
        # Test multiple calls to ensure valid range
        for _ in range(10):
            speed = messages.monster_speed()
            self.assertGreaterEqual(speed, 70)
            self.assertLessEqual(speed, 110)  # 40 + 70
