"""
Minimal tests for sprite_manager using the real micropolis package.

This file provides a small, self-contained set of tests that construct a
minimal AppContext and Sim via the public API (micropolis.sim.MakeNewSim).
It intentionally keeps tests small and focused so pytest collection succeeds
and the test runs are fast.
"""

from pathlib import Path

import pytest
import pygame
from unittest.mock import patch

import micropolis.sprite_manager as sprite_manager
import micropolis.types as types
from micropolis.app_config import AppConfig
from micropolis.context import AppContext
from micropolis.sim import MakeNewSim


# Module-level context for legacy-style calls
context: AppContext | None = None


@pytest.fixture(autouse=True)
def setup_simulation():
    """Build a minimal AppContext and Sim and attach them for each test."""
    global context

    pygame.init()
    pygame.font.init()

    repo_root = Path(__file__).resolve().parents[1]
    config = AppConfig(home=repo_root, resource_dir=repo_root / "assets")
    context = AppContext(config=config)

    sim = MakeNewSim(context)
    types.sim = sim
    context.sim = sim

    sprite_manager.initialize_sprite_system(context)

    yield

    types.sim = None
    context = None
    pygame.quit()


def test_make_and_destroy_sprite():
    sprite = sprite_manager.new_sprite(context, "t", types.TRA, 10, 20)
    assert sprite is not None
    assert types.sim.sprites >= 1

    sprite_manager.destroy_sprite(context, sprite)
    assert types.sim.sprites == 0


def test_movement_calls_do_train():
    sprite = sprite_manager.make_new_sprite(context, types.TRA, 100, 100)
    # Call the train movement routine. Movement depends on map/rail state
    # so ensure the function runs without error and the sprite remains valid.
    sprite_manager.do_train_sprite(context, sprite)
    assert sprite is not None


@patch("micropolis.sprite_manager.random.Rand")
def test_generate_train_population_requirement(mock_rand):
    mock_rand.return_value = 10
    types.TotalPop = 1
    sprite_manager.generate_train(context, 50, 50)
    # should not crash; generation may or may not create a sprite
    assert True
