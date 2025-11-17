"""Tests for the tool palette panel."""

import pytest

from micropolis.constants import (
    DOZE_STATE,
    airportState,
    commercialState,
    residentialState,
)
from micropolis.context import AppContext
from micropolis.ui.panels.tool_palette_panel import ToolPalettePanel


@pytest.fixture
def mock_panel_manager():
    """Create a mock panel manager."""

    class MockPanelManager:
        pass

    return MockPanelManager()


@pytest.fixture
def app_context():
    """Create an application context."""
    from micropolis.app_config import AppConfig

    config = AppConfig()
    context = AppContext(config=config)
    context.total_funds = 10000
    return context


@pytest.fixture
def tool_palette_panel(mock_panel_manager, app_context):
    """Create a tool palette panel."""
    return ToolPalettePanel(mock_panel_manager, app_context)


def test_tool_palette_panel_initialization(tool_palette_panel):
    """Test that the tool palette panel initializes correctly."""
    assert tool_palette_panel.panel_id == "tool_palette"
    assert tool_palette_panel.legacy_name == "ToolPalette"
    assert tool_palette_panel.visible is True
    assert tool_palette_panel.enabled is True


def test_tool_palette_panel_has_19_tools(tool_palette_panel):
    """Test that the tool palette has 19 tools."""
    # We have 19 tools (0-18 states)
    assert len(tool_palette_panel._palette_items) == 19


def test_tool_palette_items_have_metadata(tool_palette_panel):
    """Test that each tool has proper metadata."""
    for item in tool_palette_panel._palette_items:
        assert item.item_id.startswith("tool_")
        assert item.label  # Has a label
        assert item.tooltip  # Has a tooltip
        # Icon may be None for some tools
        assert item.enabled is True  # All tools enabled by default


def test_tool_palette_costs_match_constants(tool_palette_panel):
    """Test that tool costs match the CostOf constants."""
    from micropolis.constants import CostOf

    for item in tool_palette_panel._palette_items:
        tool_state = int(item.item_id.split("_")[1])
        cost = CostOf[tool_state] if tool_state < len(CostOf) else 0
        # Check that the label includes the cost
        if cost > 0:
            assert f"${cost}" in item.label
        else:
            assert "Free" in item.label


def test_set_tool_updates_selection(tool_palette_panel):
    """Test that setting a tool updates the selection."""
    tool_palette_panel.did_mount()

    # Set residential tool
    tool_palette_panel.set_tool(residentialState)
    assert tool_palette_panel.get_current_tool() == residentialState

    # Set commercial tool
    tool_palette_panel.set_tool(commercialState)
    assert tool_palette_panel.get_current_tool() == commercialState


def test_funds_update_disables_expensive_tools(tool_palette_panel, app_context):
    """Test that low funds disable expensive tools."""
    tool_palette_panel.did_mount()

    # Set low funds
    app_context.total_funds = 100

    # Trigger funds update event
    from micropolis.ui.event_bus import get_default_event_bus

    event_bus = get_default_event_bus()
    event_bus.publish("funds.updated", {"total_funds": 100})

    # Check that expensive tools (like airport) are disabled
    airport_item = None
    for item in tool_palette_panel._palette_items:
        if item.item_id == f"tool_{airportState}":
            airport_item = item
            break

    assert airport_item is not None
    # Airport costs 10000, so it should be disabled with 100 funds
    assert airport_item.enabled is False


def test_tool_palette_panel_unmount_cleans_up(tool_palette_panel):
    """Test that unmounting cleans up subscriptions."""
    tool_palette_panel.did_mount()
    assert len(tool_palette_panel._subscriptions) > 0

    tool_palette_panel.did_unmount()
    assert len(tool_palette_panel._subscriptions) == 0
    assert tool_palette_panel._palette_grid is None


def test_tool_state_ids_are_correct(tool_palette_panel):
    """Test that tool state IDs match expected constants."""
    tool_ids = [
        int(item.item_id.split("_")[1]) for item in tool_palette_panel._palette_items
    ]

    # Check that some expected tools are present
    for expected in [residentialState, commercialState, DOZE_STATE, airportState]:
        assert expected in tool_ids


def test_palette_grid_selection_callback(tool_palette_panel, app_context):
    """Test that palette grid selection triggers tool change."""
    tool_palette_panel.did_mount()

    # Get the residential tool item
    res_item = tool_palette_panel._palette_items[residentialState]

    # Simulate selection
    tool_palette_panel._on_tool_selected(res_item)

    # Check that the tool was set
    assert tool_palette_panel.get_current_tool() == residentialState


def test_insufficient_funds_prevents_tool_selection(tool_palette_panel, app_context):
    """Test that insufficient funds prevents expensive tool selection."""
    tool_palette_panel.did_mount()

    # Set very low funds
    app_context.total_funds = 10

    # Try to select airport (costs 10000)
    airport_item = None
    for item in tool_palette_panel._palette_items:
        if item.item_id == f"tool_{airportState}":
            airport_item = item
            break

    assert airport_item is not None

    # Get current tool before selection
    current_tool = tool_palette_panel.get_current_tool()

    # Try to select the expensive tool
    tool_palette_panel._on_tool_selected(airport_item)

    # Tool should not have changed (due to insufficient funds)
    assert tool_palette_panel.get_current_tool() == current_tool
