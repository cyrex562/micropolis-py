"""
test_tkinter_bridge.py - Tests for tkinter_bridge module

Tests the pygame-based TK integration replacement functionality.
"""

import pygame
from unittest.mock import Mock, patch
from queue import Queue

from src.micropolis import tkinter_bridge
from src.micropolis import types


class TestTkinterBridge:
    """Test cases for tkinter_bridge module."""

    def setup_method(self):
        """Set up test environment."""
        # Reset global state
        tkinter_bridge.running = False
        tkinter_bridge.sim_timer_token = None
        tkinter_bridge.sim_timer_idle = False
        tkinter_bridge.sim_timer_set = False
        tkinter_bridge.earthquake_timer_token = None
        tkinter_bridge.earthquake_timer_set = False
        tkinter_bridge.update_delayed = False
        tkinter_bridge.stdin_queue = Queue()

        # Initialize pygame for testing
        if not pygame.get_init():
            pygame.init()
            pygame.display.set_mode((800, 600))

    def teardown_method(self):
        """Clean up test environment."""
        tkinter_bridge.tk_main_cleanup()
        if pygame.get_init():
            pygame.quit()

    @patch('src.micropolis.tkinter_bridge.make_sound')
    def test_do_earthquake(self, mock_make_sound):
        """Test earthquake triggering."""
        # Reset global state
        types.ShakeNow = 0

        tkinter_bridge.do_earthquake()

        # Check that sound was played
        mock_make_sound.assert_called_once_with("city", "Explosion-Low")

        # Check that ShakeNow was set
        assert types.ShakeNow == 1

    def test_stop_earthquake(self):
        """Test earthquake stopping."""
        # Set up earthquake state
        types.ShakeNow = 1
        tkinter_bridge.earthquake_timer_set = True

        tkinter_bridge.stop_earthquake()

        # Check that ShakeNow was reset
        assert types.ShakeNow == 0
        assert not tkinter_bridge.earthquake_timer_set

    def test_eval_command_registered(self):
        """Test evaluating a registered command."""
        callback_mock = Mock()
        tkinter_bridge.register_command("test_command", callback_mock)

        result = tkinter_bridge.eval_command("test_command arg1 arg2")

        assert result == 0
        callback_mock.assert_called_once_with("arg1", "arg2")

    def test_eval_command_unregistered(self):
        """Test evaluating an unregistered command."""
        result = tkinter_bridge.eval_command("unknown_command")

        assert result == 1

    def test_eval_command_no_args(self):
        """Test evaluating a command with no arguments."""
        callback_mock = Mock()
        tkinter_bridge.register_command("test_cmd", callback_mock)

        result = tkinter_bridge.eval_command("test_cmd")

        assert result == 0
        callback_mock.assert_called_once_with()

    def test_register_command(self):
        """Test command registration."""
        def test_callback():
            pass

        tkinter_bridge.register_command("test_cmd", test_callback)

        assert "test_cmd" in tkinter_bridge.command_callbacks
        assert tkinter_bridge.command_callbacks["test_cmd"] == test_callback

    @patch('src.micropolis.tkinter_bridge.sim_loop')
    @patch('src.micropolis.tkinter_bridge.start_micropolis_timer')
    def test_sim_timer_callback_with_speed(self, mock_start_timer, mock_sim_loop):
        """Test simulation timer callback when speed is set."""
        types.SimSpeed = 1
        types.NeedRest = 0

        tkinter_bridge._sim_timer_callback()

        mock_sim_loop.assert_called_once_with(True)
        mock_start_timer.assert_called_once()

    @patch('src.micropolis.tkinter_bridge.stop_micropolis_timer')
    def test_sim_timer_callback_no_speed(self, mock_stop_timer):
        """Test simulation timer callback when speed is zero."""
        types.SimSpeed = 0

        tkinter_bridge._sim_timer_callback()

        mock_stop_timer.assert_called_once()

    def test_start_micropolis_timer(self):
        """Test starting the simulation timer."""
        tkinter_bridge.sim_timer_idle = True

        tkinter_bridge.start_micropolis_timer()

        assert not tkinter_bridge.sim_timer_idle

    def test_stop_micropolis_timer(self):
        """Test stopping the simulation timer."""
        tkinter_bridge.sim_timer_set = True
        tkinter_bridge.sim_timer_token = pygame.USEREVENT + 2

        tkinter_bridge.stop_micropolis_timer()

        assert not tkinter_bridge.sim_timer_set
        assert tkinter_bridge.sim_timer_token is None

    def test_kick(self):
        """Test kick function."""
        tkinter_bridge.update_delayed = False

        tkinter_bridge.kick()

        assert tkinter_bridge.update_delayed

    def test_invalidate_maps(self):
        """Test invalidating map views."""
        # Create a mock Sim with map views
        mock_view = Mock()
        mock_view.next = None

        mock_sim = Mock()
        mock_sim.map = mock_view

        with patch('src.micropolis.tkinter_bridge.Sim', mock_sim):
            tkinter_bridge.invalidate_maps()

        assert mock_view.invalid
        assert mock_view.skip == 0

    def test_invalidate_editors(self):
        """Test invalidating editor views."""
        # Create a mock Sim with editor views
        mock_view = Mock()
        mock_view.next = None

        mock_sim = Mock()
        mock_sim.editor = mock_view

        with patch('src.micropolis.tkinter_bridge.Sim', mock_sim):
            tkinter_bridge.invalidate_editors()

        assert mock_view.invalid
        assert mock_view.skip == 0

    def test_redraw_maps(self):
        """Test redrawing map views."""
        # Create a mock Sim with map views
        mock_view = Mock()
        mock_view.next = None

        mock_sim = Mock()
        mock_sim.map = mock_view

        with patch('src.micropolis.tkinter_bridge.Sim', mock_sim):
            tkinter_bridge.redraw_maps()

        assert mock_view.skip == 0

    def test_redraw_editors(self):
        """Test redrawing editor views."""
        # Create a mock Sim with editor views
        mock_view = Mock()
        mock_view.next = None

        mock_sim = Mock()
        mock_sim.editor = mock_view

        with patch('src.micropolis.tkinter_bridge.Sim', mock_sim):
            tkinter_bridge.redraw_editors()

        assert mock_view.skip == 0

    def test_start_auto_scroll_tool_mode_zero(self):
        """Test auto-scroll with tool_mode = 0 (should do nothing)."""
        mock_view = Mock()
        mock_view.tool_mode = 0

        tkinter_bridge.start_auto_scroll(mock_view, 100, 100)

        # Should not modify view since tool_mode is 0
        assert mock_view.tool_mode == 0

    def test_start_auto_scroll_edge_triggered(self):
        """Test auto-scroll when cursor is near edge."""
        mock_view = Mock()
        mock_view.tool_mode = 1
        mock_view.w_width = 800
        mock_view.w_height = 600

        # Cursor at left edge
        tkinter_bridge.start_auto_scroll(mock_view, 5, 300)

        # Should trigger auto-scroll (implementation is simplified)

    def test_stop_auto_scroll(self):
        """Test stopping auto-scroll."""
        mock_view = Mock()

        # Should not raise any exceptions
        tkinter_bridge.stop_auto_scroll(mock_view)

    @patch('src.micropolis.tkinter_bridge.threading.Thread')
    def test_start_stdin_processing(self, mock_thread):
        """Test starting stdin processing."""
        tkinter_bridge.stdin_thread = None

        tkinter_bridge.start_stdin_processing()

        mock_thread.assert_called_once()
        assert tkinter_bridge.stdin_thread is not None

    def test_stop_stdin_processing(self):
        """Test stopping stdin processing."""
        mock_thread = Mock()
        tkinter_bridge.stdin_thread = mock_thread

        tkinter_bridge.stop_stdin_processing()

        mock_thread.join.assert_called_once_with(timeout=1.0)
        assert tkinter_bridge.stdin_thread is None

    def test_process_stdin_commands_empty(self):
        """Test processing empty stdin queue."""
        tkinter_bridge._process_stdin_commands()

        # Should not raise any exceptions

    def test_process_stdin_commands_with_command(self):
        """Test processing stdin commands."""
        callback_mock = Mock()
        tkinter_bridge.register_command("test_cmd", callback_mock)
        tkinter_bridge.stdin_queue.put("test_cmd arg")

        tkinter_bridge._process_stdin_commands()

        callback_mock.assert_called_once_with("arg")

    def test_tk_main_cleanup(self):
        """Test main cleanup function."""
        tkinter_bridge.running = True
        tkinter_bridge.sim_timer_token = pygame.USEREVENT + 2
        tkinter_bridge.earthquake_timer_token = pygame.USEREVENT + 3

        tkinter_bridge.tk_main_cleanup()

        assert not tkinter_bridge.running
        assert tkinter_bridge.sim_timer_token is None
        assert tkinter_bridge.earthquake_timer_token is None

    def test_tk_timer_start_stop(self):
        """Test TkTimer start and stop functionality."""
        callback_mock = Mock()
        timer = tkinter_bridge.TkTimer(100, callback_mock)

        timer.start()
        assert timer.active
        assert timer.timer_id is not None

        timer.stop()
        assert not timer.active
        assert timer.timer_id is None

    def test_tk_timer_trigger(self):
        """Test TkTimer manual trigger."""
        callback_mock = Mock()
        data = "test_data"
        timer = tkinter_bridge.TkTimer(100, callback_mock, data)

        timer.trigger()

        callback_mock.assert_called_once_with(data)

    @patch('src.micropolis.tkinter_bridge.pygame.time.set_timer')
    def test_really_start_micropolis_timer(self, mock_set_timer):
        """Test actually starting the simulation timer."""
        tkinter_bridge.sim_timer_idle = True

        tkinter_bridge.really_start_micropolis_timer()

        assert not tkinter_bridge.sim_timer_idle
        assert tkinter_bridge.sim_timer_set
        mock_set_timer.assert_called()

    def test_fix_micropolis_timer(self):
        """Test fixing the simulation timer."""
        tkinter_bridge.sim_timer_set = True

        with patch('src.micropolis.tkinter_bridge.start_micropolis_timer') as mock_start:
            tkinter_bridge.fix_micropolis_timer()

            mock_start.assert_called_once()

    def test_do_delayed_update(self):
        """Test performing delayed update."""
        tkinter_bridge.update_delayed = True

        with patch('src.micropolis.tkinter_bridge.sim_update') as mock_update:
            tkinter_bridge._do_delayed_update()

            assert not tkinter_bridge.update_delayed
            mock_update.assert_called_once()


class TestTkinterBridgeIntegration:
    """Integration tests for tkinter_bridge module."""

    def setup_method(self):
        """Set up integration test environment."""
        if not pygame.get_init():
            pygame.init()
            pygame.display.set_mode((800, 600))

    def teardown_method(self):
        """Clean up integration test environment."""
        tkinter_bridge.tk_main_cleanup()
        if pygame.get_init():
            pygame.quit()

    @patch('src.micropolis.tkinter_bridge.pygame.time.set_timer')
    def test_tk_main_init(self, mock_set_timer):
        """Test TK main initialization."""
        screen = pygame.display.set_mode((800, 600))

        tkinter_bridge.tk_main_init(screen)

        assert tkinter_bridge.main_window == screen
        assert tkinter_bridge.running
        assert "UIEarthQuake" in tkinter_bridge.command_callbacks

    def test_event_loop_initialization(self):
        """Test that event loop can be initialized."""
        screen = pygame.display.set_mode((800, 600))

        tkinter_bridge.tk_main_init(screen)

        # Should not raise any exceptions
        assert tkinter_bridge.running
        assert tkinter_bridge.main_window == screen

        tkinter_bridge.tk_main_cleanup()