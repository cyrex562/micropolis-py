"""Test suite for EditorPanel."""

import unittest
from unittest.mock import Mock, patch

from micropolis.app_config import AppConfig
from micropolis.context import AppContext
from micropolis.ui.panels.editor_panel import EditorPanel


class TestEditorPanel(unittest.TestCase):
    """Tests for the EditorPanel class."""

    def setUp(self):
        """Set up test fixtures."""
        self.context = AppContext(config=AppConfig())
        self.context.sim = Mock()
        self.context.sim.editor = Mock()
        self.context.editor_viewport_size = (800, 600)

        self.manager = Mock()
        self.panel = EditorPanel(self.manager, self.context)

    def test_initialization(self):
        """Test panel initialization."""
        self.assertEqual(self.panel.panel_id, "editor")
        self.assertEqual(self.panel.legacy_name, "EditorWindow")
        self.assertFalse(self.panel._mouse_down)
        self.assertIsNone(self.panel._drag_start)
        self.assertEqual(len(self.panel._pan_keys_pressed), 0)

    def test_viewport_size_default(self):
        """Test default viewport size."""
        self.assertEqual(self.panel._viewport_size, (800, 600))

    def test_mouse_state_initialization(self):
        """Test mouse state starts in correct state."""
        self.assertFalse(self.panel._mouse_down)
        self.assertIsNone(self.panel._drag_start)
        self.assertIsNone(self.panel._last_mouse_pos)

    def test_keyboard_state_initialization(self):
        """Test keyboard state starts empty."""
        self.assertEqual(len(self.panel._pan_keys_pressed), 0)

    @patch("micropolis.ui.panels.editor_panel._HAVE_PYGAME", False)
    def test_draw_without_pygame(self):
        """Test draw does nothing when pygame is unavailable."""
        surface = Mock()
        self.panel.draw(surface)
        # Should not crash, just return early
        surface.blit.assert_not_called()

    def test_did_mount_subscribes_to_events(self):
        """Test that mounting subscribes to event bus."""
        with patch(
            "micropolis.ui.panels.editor_panel.get_default_event_bus"
        ) as mock_bus:
            mock_event_bus = Mock()
            mock_bus.return_value = mock_event_bus

            panel = EditorPanel(self.manager, self.context)
            panel.did_mount()

            # Should have subscribed to events
            self.assertGreater(mock_event_bus.subscribe.call_count, 0)

    def test_did_unmount_unsubscribes(self):
        """Test that unmounting cleans up subscriptions."""
        self.panel._subscriptions = [Mock(), Mock()]
        self.panel._event_bus = Mock()

        self.panel.did_unmount()

        # Should have unsubscribed
        self.assertEqual(self.panel._event_bus.unsubscribe.call_count, 2)
        self.assertEqual(len(self.panel._subscriptions), 0)

    def test_did_resize_updates_viewport(self):
        """Test resize updates viewport size."""
        self.panel._renderer = Mock()

        self.panel.did_resize((1024, 768))

        self.assertEqual(self.panel._viewport_size, (1024, 768))
        self.panel._renderer.set_viewport_pixels.assert_called_once_with(1024, 768)

    def test_set_overlay_mode(self):
        """Test overlay mode can be set."""
        self.panel._renderer = Mock()

        self.panel.set_overlay_mode("power")

        self.panel._renderer.set_overlay_mode.assert_called_once_with("power")

    def test_center_on_tile(self):
        """Test centering on a tile."""
        self.panel._renderer = Mock()

        self.panel.center_on_tile(50, 50)

        self.panel._renderer.center_on.assert_called_once_with(50, 50)

    def test_get_viewport_rect_without_renderer(self):
        """Test getting viewport rect when renderer is None."""
        self.panel._renderer = None

        rect = self.panel.get_viewport_rect()

        self.assertEqual(rect, (0, 0, 0, 0))

    def test_get_viewport_rect_with_renderer(self):
        """Test getting viewport rect with valid renderer."""
        mock_rect = Mock()
        mock_rect.x = 10
        mock_rect.y = 20
        mock_rect.width = 30
        mock_rect.height = 40

        self.panel._renderer = Mock()
        self.panel._renderer.viewport_tiles = mock_rect

        rect = self.panel.get_viewport_rect()

        self.assertEqual(rect, (10, 20, 30, 40))

    def test_handle_event_when_disabled(self):
        """Test events are not handled when panel is disabled."""
        self.panel.enabled = False
        event = Mock()

        result = self.panel.handle_panel_event(event)

        self.assertFalse(result)

    def test_handle_event_when_not_visible(self):
        """Test events are not handled when panel is not visible."""
        self.panel.visible = False
        event = Mock()

        result = self.panel.handle_panel_event(event)

        self.assertFalse(result)

    def test_on_update_skips_when_not_visible(self):
        """Test update does nothing when not visible."""
        self.panel.visible = False
        self.panel._renderer = Mock()

        # Should not crash
        self.panel.on_update(16.0)

    def test_on_update_skips_without_renderer(self):
        """Test update does nothing without renderer."""
        self.panel.visible = True
        self.panel._renderer = None

        # Should not crash
        self.panel.on_update(16.0)


if __name__ == "__main__":
    unittest.main()
