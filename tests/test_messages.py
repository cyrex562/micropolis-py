"""
test_messages.py - Unit tests for the messages system

Tests the message system functions including message sending,
scenario scoring, and message string loading.
"""

from unittest.mock import patch, MagicMock

from src.micropolis import messages, types


from tests.assertions import Assertions


class TestMessages(Assertions):
    """Test cases for the messages system."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset message state
        types.message_port = 0
        types.mes_x = 0
        types.mes_y = 0
        types.mes_num = 0
        types.last_mes_time = 0
        types.last_city_pop = 0
        types.last_category = 0
        types.last_pic_num = 0
        types.last_message = ""
        types.have_last_message = 0
        types.sound = 1
        types.auto_go = 0

        # Reset city state for testing
        types.TotalZPop = 0
        types.res_z_pop = 0
        types.ComZPop = 0
        types.IndZPop = 0
        types.nuclear_pop = 0
        types.coal_pop = 0
        types.road_total = 0
        types.rail_total = 0
        types.res_pop = 0
        types.com_pop = 0
        types.ind_pop = 0
        types.stadium_pop = 0
        types.port_pop = 0
        types.airport_pop = 0
        types.total_pop = 0
        types.fire_st_pop = 0
        types.police_pop = 0
        types.city_tax = 0
        types.road_effect = 0
        types.fire_effect = 0
        types.police_effect = 0
        types.pollute_average = 0
        types.crime_average = 0
        types.traffic_average = 0
        types.un_pwrd_z_cnt = 0
        types.pwrd_z_cnt = 0
        types.scenario_id = 0
        types.score_type = 0
        types.score_wait = 0
        types.city_class = 0
        types.city_score = 0

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

    @patch("src.micropolis.messages.types")
    def test_make_sound(self, mock_types):
        """Test sound playing function."""
        mock_types.Sound = 1
        # Should not raise an exception
        messages.make_sound("city", "test")
        mock_types.Sound = 0
        messages.make_sound("city", "test")

    def test_clear_mes(self):
        """Test clearing message state."""
        types.message_port = 5
        types.mes_x = 10
        types.mes_y = 20
        types.last_pic_num = 3

        messages.clear_mes()

        self.assertEqual(types.message_port, 0)
        self.assertEqual(types.mes_x, 0)
        self.assertEqual(types.mes_y, 0)
        self.assertEqual(types.last_pic_num, 0)

    def test_send_mes(self):
        """Test sending messages."""
        # Clear message port first
        types.message_port = 0

        # Should send positive message
        result = messages.send_mes(1)
        self.assertEqual(result, 1)
        self.assertEqual(types.message_port, 1)
        self.assertEqual(types.mes_x, 0)
        self.assertEqual(types.mes_y, 0)

        # Should not send duplicate positive message
        result = messages.send_mes(1)
        self.assertEqual(result, 0)

        # Clear and test negative message
        types.message_port = 0
        types.last_pic_num = 0
        result = messages.send_mes(-10)
        self.assertEqual(result, 1)
        self.assertEqual(types.message_port, -10)
        self.assertEqual(types.last_pic_num, -10)

        # Should not send duplicate negative message
        result = messages.send_mes(-10)
        self.assertEqual(result, 0)

    def test_send_mes_at(self):
        """Test sending messages at specific locations."""
        types.message_port = 0

        messages.send_mes_at(5, 100, 200)

        self.assertEqual(types.message_port, 5)
        self.assertEqual(types.mes_x, 100)
        self.assertEqual(types.mes_y, 200)

    def test_check_growth(self):
        """Test population growth milestone checking."""
        # Test initial state
        types.last_city_pop = 0
        types.last_category = 0

        # Set up city with small population
        types.res_pop = 10
        types.com_pop = 0
        types.ind_pop = 0
        types.city_time = 4  # Multiple of 4 to trigger check

        messages.check_growth()

        # Should not trigger any messages yet
        self.assertEqual(types.last_city_pop, 200)  # (10+0+0)*20 = 200
        # Actually: ((ResPop) + (ComPop * 8L) + (IndPop * 8L)) * 20L
        # = (10 + 0 + 0) * 20 = 200

        # Test town milestone
        types.last_city_pop = 1999
        types.res_pop = 100  # Should give population of 2000
        messages.check_growth()

        # Should have sent message -35 (town)
        self.assertEqual(types.message_port, -35)
        self.assertEqual(types.last_category, 35)

    @patch("src.micropolis.messages.do_lose_game")
    def test_do_scenario_score_lose(self, mock_lose_game):
        """Test scenario scoring for loss conditions."""
        types.score_type = 1  # Dullsville
        types.city_class = 3  # Less than required 4

        messages.do_scenario_score(1)

        # Should call lose game
        mock_lose_game.assert_called_once()

    @patch("src.micropolis.messages.do_lose_game")
    def test_do_scenario_score_win(self, mock_lose_game):
        """Test scenario scoring for win conditions."""
        types.score_type = 1  # Dullsville
        types.city_class = 4  # Meets requirement

        messages.do_scenario_score(1)

        # Should send win message (-100)
        self.assertEqual(types.message_port, -100)
        # Should not call lose game
        mock_lose_game.assert_not_called()

    @patch("src.micropolis.messages.types")
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

    @patch("src.micropolis.messages.types")
    def test_do_auto_goto(self, mock_types):
        """Test auto-goto functionality."""
        mock_types.Eval = MagicMock()

        messages.do_auto_goto(50, 75, "Test message")

        mock_types.Eval.assert_any_call("UISetMessage {Test message}")
        mock_types.Eval.assert_any_call("UIAutoGoto 50 75")

    @patch("src.micropolis.messages.types")
    def test_do_show_picture(self, mock_types):
        """Test showing pictures."""
        mock_types.Eval = MagicMock()

        messages.do_show_picture(42)

        mock_types.Eval.assert_called_with("UIShowPicture 42")

    @patch("src.micropolis.messages.types")
    def test_do_lose_game(self, mock_types):
        """Test game loss handling."""
        mock_types.Eval = MagicMock()

        messages.do_lose_game()

        mock_types.Eval.assert_called_with("UILoseGame")

    @patch("src.micropolis.messages.types")
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
