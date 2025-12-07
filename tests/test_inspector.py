import pygame
import pytest
from citysim.core.engine import Engine
from citysim.core.config import GameConfig
from citysim.simulation.tile import TileType


def test_show_inspector_no_crash():
    # Setup
    config = GameConfig.default()
    config.window_width = 100
    config.window_height = 100

    try:
        engine = Engine(config)
    except Exception as e:
        pytest.skip(f"Skipping UI test due to display init failure: {e}")
        return

    # Trigger show_inspector on a valid tile
    # (32, 20 is likely empty/dirt)
    try:
        engine.show_inspector(0, 0)
    except AttributeError as e:
        pytest.fail(f"show_inspector raised AttributeError: {e}")
    except Exception as e:
        pytest.fail(f"show_inspector raised Exception: {e}")

    # Verify label text updated (no crash means we got past the formatting line)
    assert "Pos: (0, 0)" in engine.lbl_inspector_info.html_text

    # Test a non-empty tile
    engine.world.set_tile(1, 1, TileType.ROAD)
    engine.show_inspector(1, 1)
    assert "Road" in engine.lbl_inspector_info.html_text
    assert "Cost: $10" in engine.lbl_inspector_info.html_text

    engine.quit()
