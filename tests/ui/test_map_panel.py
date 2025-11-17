"""Tests for the map/minimap panel implementation."""

from __future__ import annotations

import pytest

from micropolis.context import AppContext, AppConfig
from micropolis.ui.panels.map_panel import MapPanel, MapPanelState


@pytest.fixture
def test_context() -> AppContext:
    """Return a basic context for testing."""
    from micropolis.initialization import InitGame

    context = AppContext(config=AppConfig())
    InitGame(context)
    return context


@pytest.fixture
def map_panel(test_context: AppContext) -> MapPanel:
    """Create a MapPanel for testing."""
    # Create a minimal mock manager for testing
    from unittest.mock import MagicMock

    mock_manager = MagicMock()
    return MapPanel(mock_manager, test_context)


def test_map_panel_initialization(map_panel: MapPanel) -> None:
    """Test that MapPanel initializes correctly."""
    assert map_panel is not None
    assert map_panel.context is not None


def test_map_panel_render_with_null_renderer(map_panel: MapPanel) -> None:
    """Test that MapPanel can render without errors."""
    # UIPanel.draw() is called by UIPanel.render(surface)
    map_panel.draw(None)  # Should not raise


def test_map_panel_get_initial_state(map_panel: MapPanel) -> None:
    """Test that MapPanel returns correct initial state."""
    state = map_panel.get_state()
    assert isinstance(state, MapPanelState)
    assert state.overlay_mode is None  # Default to "None" overlay
    assert state.zoom_level == 1  # Default to "Overall" zoom
    assert state.viewport_visible is True


def test_map_panel_overlay_button_selection(map_panel: MapPanel) -> None:
    """Test that overlay buttons toggle correctly."""
    # Access internal view for testing
    view = map_panel._view
    assert len(view._overlay_buttons) > 0

    # Initially, first button (None) should be toggled
    assert view._overlay_buttons[0].toggled is True

    # Select a different overlay
    if len(view._overlay_buttons) > 1:
        view._on_overlay_selected("power")
        state = map_panel.get_state()
        assert state.overlay_mode == "power"

        # Check that only one button is toggled
        toggled_count = sum(1 for btn in view._overlay_buttons if btn.toggled)
        assert toggled_count == 1


def test_map_panel_zoom_button_selection(map_panel: MapPanel) -> None:
    """Test that zoom buttons toggle correctly."""
    view = map_panel._view
    assert len(view._zoom_buttons) > 0

    # Initially, first button (Overall/1x) should be toggled
    assert view._zoom_buttons[0].toggled is True

    # Select a different zoom level
    view._on_zoom_selected(2)
    state = map_panel.get_state()
    assert state.zoom_level == 2

    # Check that only one button is toggled
    toggled_count = sum(1 for btn in view._zoom_buttons if btn.toggled)
    assert toggled_count == 1


def test_map_panel_exclusive_overlay_selection(map_panel: MapPanel) -> None:
    """Test that overlay selection triggers callbacks correctly."""
    view = map_panel._view

    # Select multiple overlays in sequence
    overlays = [None, "power", "population"]
    for overlay_key in overlays:
        view._on_overlay_selected(overlay_key)
        # Verify the current overlay mode matches what was selected
        assert view._current_overlay == overlay_key
        assert view._minimap._overlay_mode == overlay_key


def test_map_panel_exclusive_zoom_selection(map_panel: MapPanel) -> None:
    """Test that only one zoom level can be selected at a time."""
    view = map_panel._view

    # Select multiple zoom levels in sequence
    for zoom_level in [1, 2, 3]:
        view._on_zoom_selected(zoom_level)

        # Verify exclusive selection
        toggled_buttons = [btn for btn in view._zoom_buttons if btn.toggled]
        assert len(toggled_buttons) == 1


def test_map_panel_minimap_overlay_sync(map_panel: MapPanel) -> None:
    """Test that minimap overlay updates when overlay button is selected."""
    view = map_panel._view
    minimap = view._minimap

    # Select an overlay
    view._on_overlay_selected("power")
    assert minimap._overlay_mode == "power"

    # Select None
    view._on_overlay_selected(None)
    assert minimap._overlay_mode is None


def test_map_panel_minimap_zoom_sync(map_panel: MapPanel) -> None:
    """Test that minimap zoom updates when zoom button is selected."""
    view = map_panel._view
    minimap = view._minimap

    # Select different zoom levels
    view._on_zoom_selected(2)
    assert minimap._zoom_level == 2

    view._on_zoom_selected(3)
    assert minimap._zoom_level == 3

    view._on_zoom_selected(1)
    assert minimap._zoom_level == 1


def test_map_panel_minimap_zoom_clamping(map_panel: MapPanel) -> None:
    """Test that minimap zoom level is clamped to valid range."""
    view = map_panel._view
    minimap = view._minimap

    # Try to set zoom beyond limits
    minimap.set_zoom_level(0)
    assert minimap._zoom_level == 1

    minimap.set_zoom_level(10)
    assert minimap._zoom_level == 3


def test_map_panel_cleanup(map_panel: MapPanel) -> None:
    """Test that MapPanel cleans up resources."""
    # Verify timer subscription exists
    assert map_panel._timer_subscription_id is not None

    # Cleanup
    map_panel.cleanup()

    # Verify subscription is removed
    assert map_panel._timer_subscription_id is None


def test_map_panel_update_called(map_panel: MapPanel) -> None:
    """Test that update method can be called without errors."""
    map_panel.update(0.016)  # Should not raise with delta time


def test_map_panel_render_with_recording_renderer(map_panel: MapPanel) -> None:
    """Test that MapPanel rendering is captured by RecordingRenderer."""
    from micropolis.ui.widgets import RecordingRenderer

    renderer = RecordingRenderer()
    map_panel._view.render(renderer)

    # Verify that some rendering operations occurred
    assert len(renderer.commands) > 0


def test_map_panel_widget_tree_structure(map_panel: MapPanel) -> None:
    """Test that MapPanel has correct widget tree structure."""
    view = map_panel._view
    assert view is not None
    assert view._minimap is not None
    assert len(view._overlay_buttons) > 0
    assert len(view._zoom_buttons) == 3  # Overall, City, District


def test_map_panel_overlay_button_labels(map_panel: MapPanel) -> None:
    """Test that overlay buttons have correct labels."""
    view = map_panel._view
    expected_labels = [
        "None",
        "Crime",
        "Land Value",
        "Pollution",
        "Population",
        "Power",
    ]

    button_labels = [btn.label for btn in view._overlay_buttons]
    # Check that expected labels are present (order may vary)
    for label in button_labels:
        assert label in expected_labels or label == "Traffic"


def test_map_panel_zoom_button_labels(map_panel: MapPanel) -> None:
    """Test that zoom buttons have correct labels."""
    view = map_panel._view
    expected_labels = ["Overall", "City", "District"]

    button_labels = [btn.label for btn in view._zoom_buttons]
    assert button_labels == expected_labels


def test_map_panel_minimap_invalidation_on_overlay_change(
    map_panel: MapPanel,
) -> None:
    """Test that minimap invalidates when overlay changes."""
    view = map_panel._view
    minimap = view._minimap

    # Change overlay
    view._on_overlay_selected("power")

    # Minimap should have dirty regions (invalidated)
    assert len(minimap._dirty_regions) > 0


def test_map_panel_minimap_invalidation_on_zoom_change(map_panel: MapPanel) -> None:
    """Test that minimap invalidates when zoom changes."""
    view = map_panel._view
    minimap = view._minimap

    # Clear dirty regions
    minimap.consume_dirty_regions()

    # Change zoom
    view._on_zoom_selected(2)

    # Minimap should have dirty regions (invalidated)
    assert len(minimap._dirty_regions) > 0


def test_map_panel_handle_event(map_panel: MapPanel) -> None:
    """Test that MapPanel forwards events to widget tree."""
    from unittest.mock import MagicMock

    event = MagicMock()
    result = map_panel.handle_panel_event(event)

    # Event should be handled (returns bool)
    assert isinstance(result, bool)
