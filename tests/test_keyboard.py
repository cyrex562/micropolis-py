"""
test_keyboard.py - Test suite for keyboard.py
"""

from unittest.mock import Mock, patch
import sys
import os

from tests.assertions import Assertions

# Add the src directory to the path

from src.micropolis import keyboard, types, tools


class TestKeyboard(Assertions):
    """Test cases for keyboard input handling"""

    def setUp(self):
        """Set up test fixtures"""
        # Reset global state
        keyboard.last_keys = "    "
        types.punish_cnt = 0

        # Create a mock view
        self.mock_view = Mock()
        self.mock_view.tool_state = tools.roadState
        self.mock_view.tool_state_save = -1

    def test_reset_last_keys(self):
        """Test reset_last_keys function"""
        # Set some keys
        keyboard.last_keys = "test"
        types.punish_cnt = 5

        # Reset
        keyboard.reset_last_keys(context)

        self.assertEqual(keyboard.last_keys, "    ")
        self.assertEqual(types.punish_cnt, 0)

    def test_get_last_keys(self):
        """Test get_last_keys function"""
        keyboard.last_keys = "test"
        self.assertEqual(keyboard.get_last_keys(context), "test")

        keyboard.last_keys = "  ab"
        self.assertEqual(keyboard.get_last_keys(context), "ab")

    @patch("src.micropolis.tools.Spend")
    def test_cheat_code_fund(self, mock_spend):
        """Test 'fund' cheat code"""
        # Set up initial state
        types.punish_cnt = 0

        # Simulate typing 'fund'
        keyboard.do_key_down(context, self.mock_view, "f")
        keyboard.do_key_down(context, self.mock_view, "u")
        keyboard.do_key_down(context, self.mock_view, "n")
        keyboard.do_key_down(context, self.mock_view, "d")

        # Check that Spend was called with -10000
        mock_spend.assert_called_with(-10000)
        self.assertEqual(types.punish_cnt, 1)

    @patch("src.micropolis.disasters.MakeEarthquake")
    @patch("src.micropolis.tools.Spend")
    def test_cheat_code_fund_fifth_time(self, mock_spend, mock_earthquake):
        """Test 'fund' cheat code triggers earthquake on 5th use"""
        types.punish_cnt = 4  # One less than trigger

        keyboard.do_key_down(context, self.mock_view, "f")
        keyboard.do_key_down(context, self.mock_view, "u")
        keyboard.do_key_down(context, self.mock_view, "n")
        keyboard.do_key_down(context, self.mock_view, "d")

        mock_earthquake.assert_called_once()
        self.assertEqual(types.punish_cnt, 0)  # Reset to 0

    @patch("src.micropolis.disasters.MakeMonster")
    @patch("src.micropolis.disasters.MakeEarthquake")
    @patch("src.micropolis.disasters.MakeTornado")
    @patch("src.micropolis.disasters.MakeFlood")
    @patch("src.micropolis.disasters.MakeFire")
    @patch("src.micropolis.messages.make_sound")
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

    @patch("src.micropolis.types.Kick")
    @patch("src.micropolis.sim_control.set_heat_steps")
    def test_cheat_code_stop(self, mock_set_heat_steps, mock_kick):
        """Test 'stop' cheat code"""
        keyboard.do_key_down(context, self.mock_view, "s")
        keyboard.do_key_down(context, self.mock_view, "t")
        keyboard.do_key_down(context, self.mock_view, "o")
        keyboard.do_key_down(context, self.mock_view, "p")

        mock_set_heat_steps.assert_called_with(0)
        mock_kick.assert_called_once()

    @patch("src.micropolis.types.Kick")
    def test_cheat_code_will(self, mock_kick):
        """Test 'will' cheat code scrambles map"""
        # Mock the map and Rand function
        original_map = [[i * 100 + j for j in range(10)] for i in range(10)]
        types.map_data = original_map.copy()

        with patch("src.micropolis.types.Rand") as mock_rand:
            # Set up Rand to return predictable values
            mock_rand.side_effect = [0, 0, 1, 1, 2, 2]  # First 3 pairs

            keyboard.do_key_down(context, self.mock_view, "w")
            keyboard.do_key_down(context, self.mock_view, "i")
            keyboard.do_key_down(context, self.mock_view, "l")
            keyboard.do_key_down(context, self.mock_view, "l")

            # Check that map was modified (tiles swapped)
            self.assertNotEqual(types.map_data, original_map)
            mock_kick.assert_called_once()

    @patch("src.micropolis.tools.setWandState")
    def test_tool_switching_x_key(self, mock_set_wand_state):
        """Test X key cycles to next tool"""
        self.mock_view.tool_state = tools.roadState  # 9

        keyboard.do_key_down(context, self.mock_view, "X")

        # Should cycle to next tool (roadState + 1)
        mock_set_wand_state.assert_called_with(self.mock_view, tools.roadState + 1)

    @patch("src.micropolis.tools.setWandState")
    def test_tool_switching_z_key(self, mock_set_wand_state):
        """Test Z key cycles to previous tool"""
        self.mock_view.tool_state = tools.wireState  # 6

        keyboard.do_key_down(context, self.mock_view, "Z")

        # Should cycle to previous tool (wireState - 1)
        mock_set_wand_state.assert_called_with(self.mock_view, tools.wireState - 1)

    @patch("src.micropolis.tools.setWandState")
    def test_tool_switching_b_key(self, mock_set_wand_state):
        """Test B key switches to bulldozer"""
        keyboard.do_key_down(context, self.mock_view, "B")

        # Should save current tool and switch to bulldozer
        self.assertEqual(self.mock_view.tool_state_save, tools.roadState)
        mock_set_wand_state.assert_called_with(self.mock_view, tools.dozeState)

    @patch("src.micropolis.tools.setWandState")
    def test_key_up_restores_tool(self, mock_set_wand_state):
        """Test key up restores previous tool state"""
        # First press B to save current tool
        keyboard.do_key_down(context, self.mock_view, "B")
        self.assertEqual(self.mock_view.tool_state_save, tools.roadState)

        # Then release B
        keyboard.do_key_up(self.mock_view, "B")

        # Should restore saved tool
        mock_set_wand_state.assert_called_with(self.mock_view, tools.roadState)
        self.assertEqual(self.mock_view.tool_state_save, -1)

    @patch("src.micropolis.types.Eval")
    def test_escape_key(self, mock_eval):
        """Test ESC key turns off sound"""
        keyboard.do_key_down(context, self.mock_view, chr(27))

        mock_eval.assert_called_with("UISoundOff")
        self.assertEqual(types.dozing, 0)

    def test_keyboard_command_resetlastkeys(self):
        """Test TCL command resetlastkeys"""
        keyboard.last_keys = "test"
        types.punish_cnt = 5

        result = keyboard.KeyboardCommand.handle_command(context, "resetlastkeys")

        self.assertEqual(result, "")
        self.assertEqual(keyboard.last_keys, "    ")
        self.assertEqual(types.punish_cnt, 0)

    def test_keyboard_command_getlastkeys(self):
        """Test TCL command getlastkeys"""
        keyboard.last_keys = "test"

        result = keyboard.KeyboardCommand.handle_command(context, "getlastkeys")

        self.assertEqual(result, "test")

    def test_keyboard_command_invalid(self):
        """Test invalid TCL command raises ValueError"""
        with self.assertRaises(ValueError):
            keyboard.KeyboardCommand.handle_command(context, "invalid_command")
