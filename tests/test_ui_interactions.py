import pytest
from unittest.mock import MagicMock
from micropolis.context import AppContext
from micropolis.ui.panels.head_panel import HeadPanel
from micropolis.ui.widgets import UIEvent


from micropolis.app_config import AppConfig


class TestHeadPanelInteractions:
    @pytest.fixture
    def context(self):
        config = AppConfig()
        ctx = AppContext(config=config)
        # Mock sim_control functions if they are called directly
        # But HeadPanel imports them inside functions to avoid circular imports.
        # We might need to mock them in sys.modules or patch them.
        # However, HeadPanel uses _get_ui_utilities which returns a module.
        # We can probably rely on default context behavior or mock the utility module.
        return ctx

    @pytest.fixture
    def head_panel(self, context):
        # We need a mock manager
        manager = MagicMock()
        manager.timer_service = MagicMock()

        panel = HeadPanel(manager, context)
        # Simulate mounting and resizing
        panel.did_mount()
        panel.set_rect((0, 0, 1024, 150))
        panel.did_resize()  # This triggers inner view layout and rect sync
        return panel

    def test_pause_button_interaction(self, head_panel, context):
        # Verify initial state
        assert not context.sim_paused

        # Pause button layout: (x + padding, y + 48, button_width, 28)
        # default padding 8. x=0, y=0.
        # Button Rect: (8, 48, 110, 28)
        # Click at (10, 50) should be inside.

        # Verify button is untoggled initially
        assert not head_panel._view.pause_button.toggled

        # Send Mouse Down
        event_down = UIEvent(type="mouse_down", position=(10, 50), button=1)
        handled = head_panel.handle_panel_event(event_down)
        assert handled, "Mouse down should be handled by Pause button"

        # Send Mouse Up (triggers click)
        event_up = UIEvent(type="mouse_up", position=(10, 50), button=1)
        handled = head_panel.handle_panel_event(event_up)
        assert handled, "Mouse up should be handled by Pause button"

        # Verify button state toggled
        # Note: UI logic might send an event to change state, which updates context,
        # which then updates UI via listener.
        # HeadPanel._handle_pause_request calls _get_ui_utilities().pause(context)

        # We check if context.sim_paused changed (assuming ui_utilities.pause works on context)
        # If ui_utilities imports are real, it should update context.
        # If it's mocked, we might need to verify the call.

        # Actually, HeadPanel._handle_pause_request implementation:
        # _get_ui_utilities().pause(self.context)
        # micropolis.ui_utilities.pause sets context.sim_paused = True

        assert context.sim_paused, (
            "Context should be paused after clicking Pause button"
        )

        # Click again to resume
        head_panel.handle_panel_event(event_down)
        head_panel.handle_panel_event(event_up)

        assert not context.sim_paused, (
            "Context should be resumed after clicking Pause button again"
        )

    def test_speed_button_interaction(self, head_panel, context):
        # Speed buttons are next to pause button.
        # Pause: x=8, w=110. Next starts at x + padding + (idx+1)*(110+6)
        # idx 0 (Slow): 8 + 1*(116) = 124. Rect: (124, 48, 110, 28)
        # idx 1 (Normal): 8 + 2*(116) = 240. Rect: (240, 48, 110, 28)
        # idx 2 (Fast): 8 + 3*(116) = 356. Rect: (356, 48, 110, 28)

        # Click Fast button (idx 2)
        click_x = 360
        click_y = 50

        event_down = UIEvent(type="mouse_down", position=(click_x, click_y), button=1)
        event_up = UIEvent(type="mouse_up", position=(click_x, click_y), button=1)

        head_panel.handle_panel_event(event_down)
        head_panel.handle_panel_event(event_up)

        # Default speed is 1 (Slow) ? Or context default.
        # If we clicked Fast (speed 3), context should update.
        assert context.sim_speed == 3, (
            "Context speed should be 3 after clicking Fast button"
        )
