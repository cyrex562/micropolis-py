"""
test_editor.py - Unit tests for the editor.py module

This module contains comprehensive tests for the map editor interface functionality.
"""

from unittest.mock import Mock, patch

import micropolis
import micropolis.editor as editor
from micropolis.sim_view import SimView
import micropolis.view_types as view_types
from micropolis.context import AppContext
from micropolis.app_config import AppConfig

from tests.assertions import Assertions

# Module-level context for tests
context = AppContext(config=AppConfig())


class TestEditor(Assertions):
    """Test cases for the editor module"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a mock view
        self.mock_view = Mock()
        self.mock_view.w_width = 800
        self.mock_view.w_height = 600
        self.mock_view.pan_x = 400
        self.mock_view.pan_y = 300
        self.mock_view.tool_x = 100
        self.mock_view.tool_y = 100
        self.mock_view.tool_state = 0
        self.mock_view.tool_mode = 0
        self.mock_view.visible = True
        self.mock_view.invalid = False
        self.mock_view.update = False
        self.mock_view.skips = 0
        self.mock_view.skip = 0
        self.mock_view.updates = 0
        self.mock_view.auto_goto = False
        self.mock_view.auto_going = False
        self.mock_view.show_overlay = False
        self.mock_view.overlay_mode = 0
        self.mock_view.overlay_time = 0.0
        self.mock_view.i_width = 1920  # WORLD_X * 16
        self.mock_view.i_height = 1600  # WORLD_Y * 16
        self.mock_view.follow = None

        # Mock the display
        self.mock_display = Mock()
        self.mock_display.color = True
        self.mock_display.gray50_stipple = None
        self.mock_view.x = self.mock_display

        # Mock pygame
        self.pygame_mock = Mock()
        self.surface_mock = Mock()
        self.pygame_mock.Surface.return_value = self.surface_mock

    def test_view_to_tile_coords(self):
        """Test coordinate conversion from screen to tile coordinates"""
        # Test center of screen (should map to pan position)
        tile_x = [0]
        tile_y = [0]
        editor.view_to_tile_coords(self.mock_view, 400, 300, tile_x, tile_y)

        # Center should map to pan position
        self.assertEqual(tile_x[0], 400 // 16)  # 25
        self.assertEqual(tile_y[0], 300 // 16)  # 18

    def test_tile_to_view_coords(self):
        """Test coordinate conversion from tile to view coordinates"""
        view_x, view_y = editor.tile_to_view_coords(self.mock_view, 25, 18)

        # Center tile (25, 18) should map to (400, 288) because:
        # tile_y = 18 * 16 = 288 pixels from origin
        # view_y = 288 - pan_y(300) + center_y(300) = 288
        self.assertEqual(view_x, 400)
        self.assertEqual(view_y, 288)

    def test_do_pan_to(self):
        """Test panning to a specific location"""
        editor.do_pan_to(context, self.mock_view, 500, 400)

        self.assertEqual(self.mock_view.pan_x, 500)
        self.assertEqual(self.mock_view.pan_y, 400)
        self.assertTrue(self.mock_view.invalid)
        # Should check that NewMap is set to 1

    def test_do_pan_by(self):
        """Test panning by a delta"""
        original_pan_x = self.mock_view.pan_x
        original_pan_y = self.mock_view.pan_y

        editor.do_pan_by(context, self.mock_view, 50, -25)

        self.assertEqual(self.mock_view.pan_x, original_pan_x + 50)
        self.assertEqual(self.mock_view.pan_y, original_pan_y - 25)
        self.assertTrue(self.mock_view.invalid)

    @patch("micropolis.editor.tools")
    def test_do_tool(self, mock_tools):
        """Test applying a tool"""
        mock_tools.do_tool.return_value = 0

        editor.do_tool(self.mock_view, 1, 400, 300)

        # Should call tools.do_tool with converted coordinates
        mock_tools.do_tool.assert_called_once()
        args = mock_tools.do_tool.call_args[0]
        self.assertEqual(args[0], self.mock_view)  # view
        self.assertEqual(args[1], 1)  # tool
        # Coordinates should be converted from screen to tile

    @patch("micropolis.editor.tools")
    def test_tool_down(self, mock_tools):
        """Test tool down event"""
        mock_tools.tool_down.return_value = None

        editor.tool_down(self.mock_view, 400, 300)

        mock_tools.tool_down.assert_called_once_with(
            self.mock_view, 25, 18
        )  # Converted coordinates

    @patch("micropolis.editor.tools")
    def test_tool_drag(self, mock_tools):
        """Test tool drag event"""
        mock_tools.tool_drag.return_value = 1

        editor.tool_drag(self.mock_view, 400, 300)

        mock_tools.tool_drag.assert_called_once_with(
            self.mock_view, 25, 18
        )  # Converted coordinates

    @patch("micropolis.editor.tools")
    def test_tool_up(self, mock_tools):
        """Test tool up event"""
        mock_tools.tool_up.return_value = 1

        editor.tool_up(self.mock_view, 400, 300)

        mock_tools.tool_up.assert_called_once_with(
            self.mock_view, 25, 18
        )  # Converted coordinates

    @patch("micropolis.editor.PYGAME_AVAILABLE", True)
    @patch("micropolis.editor.pygame")
    def test_draw_outside(self, mock_pygame):
        """Test drawing borders outside the map area"""
        mock_pygame.Surface.return_value = self.surface_mock

        # Should not raise an exception
        editor.draw_outside(self.mock_view)

    def test_do_new_editor(self):
        """Test initializing a new editor view"""
        # Mock sim on the context
        mock_sim = Mock()
        mock_sim.editors = 0
        mock_sim.editor = None
        context.sim = mock_sim

        editor.do_new_editor(context, self.mock_view)

        self.assertEqual(mock_sim.editors, 1)
        self.assertEqual(mock_sim.editor, self.mock_view)
        self.assertTrue(self.mock_view.invalid)

    def test_do_update_editor_invisible(self):
        """Test updating an invisible editor view"""
        self.mock_view.visible = False

        editor.do_update_editor(context, self.mock_view)

        # Should return early without doing anything
        self.assertEqual(self.mock_view.updates, 0)

    @patch("micropolis.editor.HandleAutoGoto")
    @patch("micropolis.editor.pygame")
    def test_do_update_editor_visible(
        self, mock_pygame, mock_handle_autogoto
    ):
        """Test updating a visible editor view"""
        self.mock_view.visible = True
        self.mock_view.invalid = True

        # Mock pygame surface
        mock_surface = Mock()
        mock_pygame.Surface.return_value = mock_surface
        setattr(self.mock_view, "surface", mock_surface)

        # Set context values instead of types module
        context.shake_now = 0
        context.sim_skips = 0
        context.do_animation = False
        context.tiles_animated = 0
        context.pending_tool = -1  # No pending tool

        editor.do_update_editor(context, self.mock_view)

        self.assertEqual(self.mock_view.updates, 1)
        self.assertFalse(self.mock_view.invalid)
        mock_handle_autogoto.assert_called_once_with(self.mock_view)

    def test_handle_auto_goto_no_follow(self):
        """Test auto-goto when not following anything"""
        self.mock_view.follow = None
        self.mock_view.auto_goto = False

        editor.handle_auto_goto(context, self.mock_view)

        # Should not change pan position
        self.assertEqual(self.mock_view.pan_x, 400)
        self.assertEqual(self.mock_view.pan_y, 300)

    def test_handle_auto_goto_with_follow(self):
        """Test auto-goto when following a sprite"""
        mock_sprite = Mock()
        mock_sprite.x = 500
        mock_sprite.y = 400
        mock_sprite.x_hot = 8
        mock_sprite.y_hot = 8

        self.mock_view.follow = mock_sprite

        editor.handle_auto_goto(context, self.mock_view)

        # Should pan to sprite position
        self.assertEqual(self.mock_view.pan_x, 508)  # x + x_hot
        self.assertEqual(self.mock_view.pan_y, 408)  # y + y_hot

    @patch("micropolis.editor.tools")
    def test_chalk_start(self, mock_tools):
        """Test starting chalk drawing"""
        mock_tools.chalk_start.return_value = None

        editor.chalk_start(self.mock_view, 400, 300, 1)

        mock_tools.chalk_start.assert_called_once()
        args = mock_tools.chalk_start.call_args[0]
        self.assertEqual(args[0], self.mock_view)
        # Coordinates should be converted

    @patch("micropolis.editor.tools")
    def test_chalk_to(self, mock_tools):
        """Test continuing chalk drawing"""
        mock_tools.chalk_to.return_value = None

        editor.chalk_to(self.mock_view, 400, 300)

        mock_tools.chalk_to.assert_called_once()
        args = mock_tools.chalk_to.call_args[0]
        self.assertEqual(args[0], self.mock_view)
        # Coordinates should be converted

    def test_set_wand_state(self):
        """Test setting the tool state"""
        editor.set_wand_state(self.mock_view, 5)

        self.assertEqual(self.mock_view.tool_state, 5)
        self.assertEqual(self.mock_view.tool_state_save, 5)

    def test_constants(self):
        """Test that constants are properly defined"""
        self.assertEqual(editor.OVERLAY_INVALID, 0)
        self.assertEqual(editor.OVERLAY_STABLE, 1)
        self.assertEqual(editor.OVERLAY_OPTIMIZE, 2)
        self.assertEqual(editor.OVERLAY_FAST_LINES, 3)
        self.assertEqual(editor.OVERLAY_FAST_CLIP, 4)
        self.assertEqual(editor.CURSOR_DASHES, [4, 4])
        self.assertEqual(editor.BOB_HEIGHT, 8)


class TestEditorIntegration(Assertions):
    """Integration tests for editor functionality"""

    def setUp(self):
        """Set up integration test fixtures"""
        # Create a more complete mock setup
        self.view = Mock(spec=SimView)
        self.view.w_width = 800
        self.view.w_height = 600
        self.view.pan_x = 400
        self.view.pan_y = 300
        self.view.tool_x = 100
        self.view.tool_y = 100
        self.view.tool_state = 0
        self.view.tool_mode = 0
        self.view.visible = True
        self.view.invalid = True
        self.view.update = False
        self.view.skips = 0
        self.view.skip = 0
        self.view.updates = 0
        self.view.auto_goto = False
        self.view.auto_going = False
        self.view.show_overlay = True
        self.view.overlay_mode = 0
        self.view.overlay_time = 0.0
        self.view.i_width = 1920
        self.view.i_height = 1600
        self.view.type = view_types.X_Mem_View
        self.view.follow = None

        # Mock display
        self.display = Mock()
        self.display.color = True
        self.view.x = self.display

    def test_full_update_cycle(self):
        """Test a full editor update cycle"""
        # Set context state instead of mocking types
        context.shake_now = 0
        context.sim_skips = 0
        context.do_animation = False
        context.tiles_animated = 0
        mock_sim = Mock()
        mock_sim.editors = 1
        mock_sim.editor = self.view
        context.sim = mock_sim

        with (
            patch("micropolis.editor.HandleAutoGoto") as mock_autogoto,
            patch("micropolis.editor.DrawOutside") as mock_draw_outside,
            patch("micropolis.editor.DrawPending") as mock_draw_pending,
            patch("micropolis.editor.DrawOverlay") as mock_draw_overlay,
        ):
            editor.do_update_editor(context, self.view)

            # Should call all the drawing functions
            mock_autogoto.assert_called_once_with(self.view)
            mock_draw_outside.assert_called_once_with(self.view)
            mock_draw_pending.assert_called_once_with(self.view)
            mock_draw_overlay.assert_called_once_with(self.view)

            self.assertFalse(self.view.invalid)
