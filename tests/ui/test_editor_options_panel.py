"""Tests for the editor options panel."""

import pytest

from micropolis.app_config import AppConfig
from micropolis.context import AppContext
from micropolis.sim_control import get_auto_goto, get_sim_skips
from micropolis.ui.panels.editor_options_panel import EditorOptionsPanel


class MockPanelManager:
    """Mock panel manager for testing."""

    def __init__(self):
        self.panels = {}

    def register_panel(self, panel_id, panel):
        self.panels[panel_id] = panel


@pytest.fixture
def context():
    """Create a test context."""
    config = AppConfig()
    ctx = AppContext(config=config)
    ctx.auto_goto = True
    ctx.chalk_overlay = True
    ctx.dynamic_filter = False
    ctx.sim_skips = 0
    return ctx


@pytest.fixture
def panel_manager():
    """Create a mock panel manager."""
    return MockPanelManager()


@pytest.fixture
def panel(context, panel_manager):
    """Create an editor options panel."""
    panel = EditorOptionsPanel(panel_manager, context)
    panel._rect = (10, 10, 300, 300)  # Set internal rect
    return panel


def test_panel_initialization(panel):
    """Test that panel initializes correctly."""
    assert panel.panel_id == "editor_options"
    assert panel.legacy_name == "EditorOptionsWindow"
    assert panel.context is not None


def test_panel_mount_creates_widgets(panel):
    """Test that mounting creates widgets."""
    panel.did_mount()

    # Should have created widgets
    assert len(panel._widgets) > 0
    assert panel._auto_goto_checkbox is not None
    assert panel._chalk_overlay_checkbox is not None
    assert panel._dynamic_filter_checkbox is not None
    assert panel._skip_frequency_slider is not None


def test_panel_loads_context_values(panel, context):
    """Test that panel loads values from context."""
    context.auto_goto = False
    context.chalk_overlay = False
    context.dynamic_filter = True
    context.sim_skips = 5

    panel.did_mount()

    # Widgets should reflect context values
    assert panel._auto_goto_checkbox.toggled is False
    assert panel._chalk_overlay_checkbox.toggled is False
    assert panel._dynamic_filter_checkbox.toggled is True
    assert panel._skip_frequency_slider.value == 5.0


def test_auto_goto_toggle_updates_context(panel, context):
    """Test that toggling auto_goto updates context."""
    panel.did_mount()

    # Initial state
    assert get_auto_goto(context) is True

    # Toggle off
    panel._on_auto_goto_toggle(panel._auto_goto_checkbox, False)
    assert get_auto_goto(context) is False

    # Toggle on
    panel._on_auto_goto_toggle(panel._auto_goto_checkbox, True)
    assert get_auto_goto(context) is True


def test_chalk_overlay_toggle_updates_context(panel, context):
    """Test that toggling chalk_overlay updates context."""
    panel.did_mount()

    # Initial state
    assert context.chalk_overlay is True

    # Toggle off
    panel._on_chalk_overlay_toggle(panel._chalk_overlay_checkbox, False)
    assert context.chalk_overlay is False

    # Toggle on
    panel._on_chalk_overlay_toggle(panel._chalk_overlay_checkbox, True)
    assert context.chalk_overlay is True


def test_dynamic_filter_toggle_updates_context(panel, context):
    """Test that toggling dynamic_filter updates context."""
    panel.did_mount()

    # Initial state
    assert context.dynamic_filter is False

    # Toggle on
    panel._on_dynamic_filter_toggle(panel._dynamic_filter_checkbox, True)
    assert context.dynamic_filter is True

    # Toggle off
    panel._on_dynamic_filter_toggle(panel._dynamic_filter_checkbox, False)
    assert context.dynamic_filter is False


def test_skip_frequency_slider_updates_context(panel, context):
    """Test that changing skip frequency updates context."""
    panel.did_mount()

    # Initial state
    assert get_sim_skips(context) == 0

    # Change to 5
    panel._on_skip_frequency_change(panel._skip_frequency_slider, 5.0)
    assert get_sim_skips(context) == 5

    # Change to 10
    panel._on_skip_frequency_change(panel._skip_frequency_slider, 10.0)
    assert get_sim_skips(context) == 10

    # Change to 0
    panel._on_skip_frequency_change(panel._skip_frequency_slider, 0.0)
    assert get_sim_skips(context) == 0


def test_panel_refresh_values(panel, context):
    """Test that refresh_values loads current context state."""
    panel.did_mount()

    # Change context values externally using the sim_control functions
    from micropolis.sim_control import (
        set_auto_goto,
        set_sim_skips,
    )

    set_auto_goto(context, False)
    context.chalk_overlay = False
    context.dynamic_filter = True
    set_sim_skips(context, 7)

    # Refresh panel
    panel._refresh_values()

    # Widgets should reflect updated values
    assert panel._auto_goto_checkbox.toggled is False
    assert panel._chalk_overlay_checkbox.toggled is False
    assert panel._dynamic_filter_checkbox.toggled is True
    assert panel._skip_frequency_slider.value == 7.0


def test_panel_show_and_hide(panel):
    """Test show and hide functionality."""
    panel.did_mount()

    # Initially not visible
    assert panel.visible is True  # Default is True

    # Hide
    panel.hide()
    assert panel.visible is False

    # Show
    panel.show()
    assert panel.visible is True


def test_panel_unmount_cleanup(panel):
    """Test that unmounting cleans up resources."""
    panel.did_mount()

    # Should have subscriptions and widgets
    assert len(panel._subscriptions) > 0
    assert len(panel._widgets) > 0

    # Unmount
    panel.did_unmount()

    # Should be cleaned up
    assert len(panel._subscriptions) == 0
    assert len(panel._widgets) == 0
