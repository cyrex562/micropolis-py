"""
test_teardown.py - Tests for DoStopMicropolis() teardown functionality

Tests the complete shutdown sequence including:
- Pygame loop exit
- Timer cleanup
- Audio system shutdown
- Graphics cleanup
- Event bus cleanup
- State reset
"""

from unittest.mock import Mock, patch

import pygame
import pytest

from micropolis.app_config import AppConfig
from micropolis.context import AppContext
from micropolis.engine import DoStopMicropolis


class TestDoStopMicropolis:
    """Test suite for DoStopMicropolis teardown function."""

    def setup_method(self):
        """Set up test environment."""
        if not pygame.get_init():
            pygame.init()

    def teardown_method(self):
        """Clean up after tests."""
        if pygame.get_init():
            pygame.quit()

    def test_sets_exit_flags(self):
        """Test that DoStopMicropolis sets exit flags."""
        app_config = AppConfig()
        context = AppContext(config=app_config)
        context.tk_must_exit = False
        context.running = True

        DoStopMicropolis(context)

        assert context.tk_must_exit is True
        assert context.running is False

    @patch("micropolis.engine.pygame.time.set_timer")
    def test_stops_all_timers(self, mock_set_timer):
        """Test that all pygame timers are stopped."""
        app_config = AppConfig()
        context = AppContext(config=app_config)

        DoStopMicropolis(context)

        # Verify set_timer was called with 0 for each timer
        assert mock_set_timer.call_count >= 3
        # Check that timers were stopped (interval set to 0)
        for call in mock_set_timer.call_args_list:
            args = call[0]
            assert args[1] == 0  # Second argument should be 0 (stop timer)

    @patch("micropolis.audio.shutdown_sound")
    def test_shuts_down_audio(self, mock_shutdown):
        """Test that audio system is shut down."""
        app_config = AppConfig()
        context = AppContext(config=app_config)

        DoStopMicropolis(context)

        mock_shutdown.assert_called_once_with(context)

    @patch("micropolis.graphics_setup.cleanup_graphics")
    def test_cleans_up_graphics(self, mock_cleanup):
        """Test that graphics resources are cleaned up."""
        app_config = AppConfig()
        context = AppContext(config=app_config)

        DoStopMicropolis(context)

        mock_cleanup.assert_called_once()

    @patch("micropolis.tkinter_bridge.tk_main_cleanup")
    def test_cleans_up_tkinter_bridge(self, mock_cleanup):
        """Test that tkinter bridge is cleaned up."""
        app_config = AppConfig()
        context = AppContext(config=app_config)

        DoStopMicropolis(context)

        mock_cleanup.assert_called_once_with(context)

    @patch("micropolis.ui.event_bus.get_default_event_bus")
    def test_clears_event_bus(self, mock_get_bus):
        """Test that event bus is cleared."""
        app_config = AppConfig()
        context = AppContext(config=app_config)
        mock_bus = Mock()
        mock_get_bus.return_value = mock_bus

        DoStopMicropolis(context)

        mock_bus.clear.assert_called_once()

    def test_resets_simulation_state(self):
        """Test that simulation state flags are reset."""
        app_config = AppConfig()
        context = AppContext(config=app_config)
        context.sim_paused = 1
        context.sim_paused_speed = 5

        DoStopMicropolis(context)

        assert context.sim_paused == 0
        assert context.sim_paused_speed == 3

    @patch("micropolis.audio.shutdown_sound", side_effect=Exception("Audio error"))
    def test_handles_audio_shutdown_error_gracefully(self, mock_shutdown):
        """Test that audio shutdown errors don't crash the teardown."""
        app_config = AppConfig()
        context = AppContext(config=app_config)

        # Should not raise exception
        DoStopMicropolis(context)

        # Exit flags should still be set even if audio fails
        assert context.tk_must_exit is True

    @patch(
        "micropolis.engine.graphics_setup.cleanup_graphics",
        side_effect=Exception("Graphics error"),
    )
    def test_handles_graphics_cleanup_error_gracefully(self, mock_cleanup):
        """Test that graphics cleanup errors don't crash the teardown."""
        app_config = AppConfig()
        context = AppContext(config=app_config)

        # Should not raise exception
        DoStopMicropolis(context)

        # Exit flags should still be set even if graphics cleanup fails
        assert context.tk_must_exit is True

    @patch(
        "micropolis.engine.pygame.time.set_timer", side_effect=Exception("Timer error")
    )
    def test_handles_timer_stop_error_gracefully(self, mock_set_timer):
        """Test that timer stop errors don't crash the teardown."""
        app_config = AppConfig()
        context = AppContext(config=app_config)

        # Should not raise exception
        DoStopMicropolis(context)

        # Exit flags should still be set even if timer stop fails
        assert context.tk_must_exit is True

    @patch("micropolis.audio.shutdown_sound")
    @patch("micropolis.graphics_setup.cleanup_graphics")
    @patch("micropolis.tkinter_bridge.tk_main_cleanup")
    @patch("micropolis.ui.event_bus.get_default_event_bus")
    @patch("micropolis.engine.pygame.time.set_timer")
    def test_full_teardown_sequence(
        self, mock_set_timer, mock_get_bus, mock_bridge, mock_graphics, mock_audio
    ):
        """Test complete teardown sequence with all components."""
        app_config = AppConfig()
        context = AppContext(config=app_config)
        mock_bus = Mock()
        mock_get_bus.return_value = mock_bus

        # Initial state
        context.tk_must_exit = False
        context.running = True
        context.sim_paused = 1

        DoStopMicropolis(context)

        # Verify all cleanup steps were called
        assert mock_set_timer.call_count >= 3
        mock_audio.assert_called_once()
        mock_graphics.assert_called_once()
        mock_bridge.assert_called_once()
        mock_bus.clear.assert_called_once()

        # Verify state was reset
        assert context.tk_must_exit is True
        assert context.running is False
        assert context.sim_paused == 0

    def test_idempotent_multiple_calls(self):
        """Test that calling DoStopMicropolis multiple times is safe."""
        app_config = AppConfig()
        context = AppContext(config=app_config)

        # First call
        DoStopMicropolis(context)
        assert context.tk_must_exit is True

        # Second call should not crash
        DoStopMicropolis(context)
        assert context.tk_must_exit is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
