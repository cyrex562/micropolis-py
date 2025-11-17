"""test_keyboard.py - Test suite for keyboard.py"""

from unittest.mock import Mock, patch

from tests.assertions import Assertions

# Import the modules under test from the source package layout used in tests
from src.micropolis import keyboard, tools, constants as const


class TestKeyboard(Assertions):
    """Test cases for keyboard input handling"""

    def setUp(self):
        """Set up test fixtures"""
        # Reset global-ish state
        context.last_keys = "    "
        context.punish_cnt = 0

        # Create a mock view
        self.mock_view = Mock()
        self.mock_view.tool_state = const.roadState
        self.mock_view.tool_state_save = -1

    def test_reset_last_keys(self):
        """Test reset_last_keys function"""
        # Set some keys
        context.last_keys = "test"
        context.punish_cnt = 5

        # Reset
        keyboard.reset_last_keys(context)

        self.assertEqual(context.last_keys, "    ")
        self.assertEqual(context.punish_cnt, 0)

    def test_get_last_keys(self):
        """Test get_last_keys function"""
        context.last_keys = "test"
        self.assertEqual(keyboard.get_last_keys(context), "test")

        context.last_keys = "  ab"
        self.assertEqual(keyboard.get_last_keys(context), "ab")

    @patch("src.micropolis.keyboard.Spend")
    def test_cheat_code_fund(self, mock_spend):
        """Test 'fund' cheat code"""
        # Set up initial state
        context.punish_cnt = 0

        # Simulate typing 'fund'
        keyboard.do_key_down(context, self.mock_view, "f")
        keyboard.do_key_down(context, self.mock_view, "u")
        keyboard.do_key_down(context, self.mock_view, "n")
        keyboard.do_key_down(context, self.mock_view, "d")

        # Check that Spend was called with -10000
        mock_spend.assert_called_with(-10000)
        self.assertEqual(context.punish_cnt, 1)

    @patch("src.micropolis.keyboard.trigger_earthquake_disaster")
    @patch("src.micropolis.keyboard.Spend")
    def test_cheat_code_fund_fifth_time(self, mock_spend, mock_earthquake):
        """Test 'fund' cheat code triggers earthquake on 5th use"""
        # One less than trigger
        context.punish_cnt = 4

        keyboard.do_key_down(context, self.mock_view, "f")
        keyboard.do_key_down(context, self.mock_view, "u")
        keyboard.do_key_down(context, self.mock_view, "n")
        keyboard.do_key_down(context, self.mock_view, "d")

        mock_earthquake.assert_called_once()
        self.assertEqual(context.punish_cnt, 0)  # Reset to 0

    @patch("src.micropolis.keyboard.spawn_monster_disaster")
    @patch("src.micropolis.keyboard.trigger_earthquake_disaster")
    @patch("src.micropolis.keyboard.spawn_tornado_disaster")
    @patch("src.micropolis.keyboard.start_flood_disaster")
    @patch("src.micropolis.keyboard.create_fire_disaster")
    @patch("src.micropolis.keyboard.make_sound")
    def test_cheat_code_fart(
        self,
        mock_make_sound,
        mock_fire,
        mock_flood,
        mock_tornado,
        mock_earthquake,
        mock_monster,
    ):
        """Test 'fart' cheat code triggers all disasters"""
        keyboard.do_key_down(context, self.mock_view, "f")
        keyboard.do_key_down(context, self.mock_view, "a")
        keyboard.do_key_down(context, self.mock_view, "r")
        keyboard.do_key_down(context, self.mock_view, "t")

        # Check all disasters were triggered
        mock_fire.assert_called_once()
        mock_flood.assert_called_once()
        mock_tornado.assert_called_once()
        mock_earthquake.assert_called_once()
        mock_monster.assert_called_once()

        # Check sound effects
        self.assertEqual(mock_make_sound.call_count, 2)

    @patch("src.micropolis.keyboard.kick")
    @patch("src.micropolis.keyboard.set_heat_steps")
    def test_cheat_code_stop(self, mock_set_heat_steps, mock_kick):
        """Test 'stop' cheat code"""
        keyboard.do_key_down(context, self.mock_view, "s")
        keyboard.do_key_down(context, self.mock_view, "t")
        keyboard.do_key_down(context, self.mock_view, "o")
        keyboard.do_key_down(context, self.mock_view, "p")

        mock_set_heat_steps.assert_called_with(0)
        mock_kick.assert_called_once()

    @patch("src.micropolis.keyboard.kick")
    def test_cheat_code_will(self, mock_kick):
        """Test 'will' cheat code scrambles map"""
        # Create a small test map and place it on the context
        original_map = [[i * 100 + j for j in range(10)] for i in range(10)]
        context.map_data = [row[:] for row in original_map]

        # Patch the keyboard's rand function to produce deterministic swaps
        with patch("src.micropolis.keyboard.rand") as mock_rand:
            mock_rand.side_effect = [0, 0, 1, 1, 2, 2]

            keyboard.do_key_down(context, self.mock_view, "w")
            keyboard.do_key_down(context, self.mock_view, "i")
            keyboard.do_key_down(context, self.mock_view, "l")
            keyboard.do_key_down(context, self.mock_view, "l")

            # Check that map was modified (tiles swapped)
            self.assertNotEqual(context.map_data, original_map)
            mock_kick.assert_called_once()

    @patch("src.micropolis.keyboard.setWandState")
    def test_tool_switching_x_key(self, mock_set_wand_state):
        """Test X key cycles to next tool"""
        self.mock_view.tool_state = const.roadState  # 9

        keyboard.do_key_down(context, self.mock_view, "X")

        # Should cycle to next tool (roadState + 1)
        mock_set_wand_state.assert_called_with(self.mock_view, const.roadState + 1)

    @patch("src.micropolis.keyboard.setWandState")
    def test_tool_switching_z_key(self, mock_set_wand_state):
        """Test Z key cycles to previous tool"""
        self.mock_view.tool_state = const.wireState  # 6

        keyboard.do_key_down(context, self.mock_view, "Z")

        # Should cycle to previous tool (wireState - 1)
        mock_set_wand_state.assert_called_with(self.mock_view, const.wireState - 1)

    @patch("src.micropolis.keyboard.setWandState")
    def test_tool_switching_b_key(self, mock_set_wand_state):
        """Test B key switches to bulldozer"""
        keyboard.do_key_down(context, self.mock_view, "B")

        # Should save current tool and switch to bulldozer
        self.assertEqual(self.mock_view.tool_state_save, const.roadState)
        mock_set_wand_state.assert_called_with(self.mock_view, const.DOZE_STATE)

    @patch("src.micropolis.keyboard.setWandState")
    def test_key_up_restores_tool(self, mock_set_wand_state):
        """Test key up restores previous tool state"""
        # First press B to save current tool
        keyboard.do_key_down(context, self.mock_view, "B")
        self.assertEqual(self.mock_view.tool_state_save, const.roadState)

        # Then release B
        keyboard.do_key_up(self.mock_view, "B")

        # Should restore saved tool
        mock_set_wand_state.assert_called_with(self.mock_view, const.roadState)
        self.assertEqual(self.mock_view.tool_state_save, -1)

    @patch("src.micropolis.keyboard.eval_cmd_str")
    def test_escape_key(self, mock_eval):
        """Test ESC key turns off sound"""
        keyboard.do_key_down(context, self.mock_view, chr(27))

        # eval_cmd_str is called with (context, "UISoundOff")
        mock_eval.assert_called_with(context, "UISoundOff")
        self.assertEqual(context.dozing, 0)

    def test_keyboard_command_resetlastkeys(self):
        """Test TCL command resetlastkeys"""
        context.last_keys = "test"
        context.punish_cnt = 5

        result = keyboard.KeyboardCommand.handle_command(context, "resetlastkeys")

        self.assertEqual(result, "")
        self.assertEqual(context.last_keys, "    ")
        self.assertEqual(context.punish_cnt, 0)

    def test_keyboard_command_getlastkeys(self):
        """Test TCL command getlastkeys"""
        context.last_keys = "test"

        result = keyboard.KeyboardCommand.handle_command(context, "getlastkeys")

        self.assertEqual(result, "test")

    def test_keyboard_command_invalid(self):
        """Test invalid TCL command raises ValueError"""
        with self.assertRaises(ValueError):
            keyboard.KeyboardCommand.handle_command(context, "invalid_command")
