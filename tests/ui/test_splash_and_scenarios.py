"""Test splash scene and scenario picker panels."""

from unittest.mock import Mock

import pygame
import pytest

from micropolis.context import AppContext
from micropolis.ui.panel_manager import PanelManager
from micropolis.ui.panels.scenario_picker import ScenarioPickerPanel
from micropolis.ui.panels.splash_scene import SplashScene


@pytest.fixture
def mock_context():
    """Create a mock AppContext."""
    context = Mock(spec=AppContext)
    context.resource_dir = "."
    context.game_level = 0
    return context


@pytest.fixture
def mock_panel_manager(mock_context):
    """Create a mock PanelManager."""
    pygame.init()
    manager = Mock(spec=PanelManager)
    manager.context = mock_context
    manager.timer_service = Mock()
    manager.timer_service.schedule = Mock(return_value="test-timer-id")
    manager.timer_service.cancel = Mock()
    manager._event_bus = Mock()
    manager._event_bus.publish = Mock()
    return manager


def test_splash_scene_init(mock_panel_manager, mock_context):
    """Test splash scene initialization."""
    splash = SplashScene(mock_panel_manager, mock_context)

    assert splash.panel_id == "splash"
    assert splash.legacy_name == "splash"
    assert splash.visible
    assert splash._hotspots == []


def test_splash_scene_mount(mock_panel_manager, mock_context):
    """Test splash scene mounting."""
    splash = SplashScene(mock_panel_manager, mock_context)
    splash.did_mount()

    # Should have created hotspots
    assert len(splash._hotspots) == 4  # Load, Generate, Quit, About


def test_splash_scene_keyboard_shortcuts(mock_panel_manager, mock_context):
    """Test splash scene keyboard shortcuts."""
    splash = SplashScene(mock_panel_manager, mock_context)
    splash.did_mount()

    # Test 'L' key for load
    event = Mock()
    event.type = pygame.KEYDOWN
    event.key = pygame.K_l

    result = splash.handle_panel_event(event)
    assert result  # Event was handled


def test_scenario_picker_init(mock_panel_manager, mock_context):
    """Test scenario picker initialization."""
    picker = ScenarioPickerPanel(mock_panel_manager, mock_context)

    assert picker.panel_id == "scenario_picker"
    assert picker.legacy_name == "scenario"
    assert picker.visible
    assert picker._selected_difficulty == 0  # Default to Easy


def test_scenario_picker_mount(mock_panel_manager, mock_context):
    """Test scenario picker mounting."""
    picker = ScenarioPickerPanel(mock_panel_manager, mock_context)
    picker.did_mount()

    # Should have created 8 scenario buttons
    assert len(picker._scenario_buttons) == 8

    # Should have created 3 difficulty checkboxes
    assert len(picker._difficulty_checkboxes) == 3


def test_scenario_picker_difficulty_selection(mock_panel_manager, mock_context):
    """Test difficulty selection."""
    picker = ScenarioPickerPanel(mock_panel_manager, mock_context)
    picker.did_mount()

    # Select medium difficulty
    picker._on_difficulty_selected(1)
    assert picker._selected_difficulty == 1

    # Select hard difficulty
    picker._on_difficulty_selected(2)
    assert picker._selected_difficulty == 2


def test_scenario_picker_keyboard_shortcuts(mock_panel_manager, mock_context):
    """Test scenario picker keyboard shortcuts."""
    picker = ScenarioPickerPanel(mock_panel_manager, mock_context)
    picker.did_mount()

    # Test number key for scenario selection
    event = Mock()
    event.type = pygame.KEYDOWN
    event.key = pygame.K_1

    # This will try to call _on_scenario_selected which will fail
    # due to missing file, but the event handling should work
    result = picker.handle_panel_event(event)
    assert result  # Event was handled


def test_splash_draw_no_crash(mock_panel_manager, mock_context):
    """Test splash scene draws without crashing."""
    pygame.init()
    surface = pygame.Surface((1200, 900))

    splash = SplashScene(mock_panel_manager, mock_context)
    splash.did_mount()

    # Should not crash
    splash.draw(surface)


def test_scenario_picker_draw_no_crash(mock_panel_manager, mock_context):
    """Test scenario picker draws without crashing."""
    pygame.init()
    surface = pygame.Surface((1200, 900))

    picker = ScenarioPickerPanel(mock_panel_manager, mock_context)
    picker.did_mount()

    # Should not crash
    picker.draw(surface)
