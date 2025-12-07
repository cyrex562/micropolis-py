import pygame
import pytest
from citysim.core.engine import Engine
from citysim.core.config import GameConfig

# Mock OpenGL to avoid window creation issues if possible,
# but Engine init calls real pygame.display.set_mode.
# We will just rely on the fact that we can init it in this environment.


def test_ui_initialization():
    # Setup
    config = GameConfig.default()
    # Use small window for test
    config.window_width = 100
    config.window_height = 100

    try:
        engine = Engine(config)
    except Exception as e:
        pytest.skip(f"Skipping UI test due to display init failure: {e}")
        return

    # Verify Top Bar
    assert engine.top_bar is not None
    assert engine.lbl_pop is not None
    assert engine.lbl_date is not None

    # Verify Labels Initial Text
    assert "Population: 0" in engine.lbl_pop.text
    assert "Day: 0" in engine.lbl_date.text

    # Verify Inspector
    assert engine.inspector_window is not None
    assert engine.lbl_inspector_info is not None
    assert engine.inspector_window.visible == 0  # Should be hidden

    engine.quit()
