from __future__ import annotations

from pathlib import Path

import pygame
import pytest

from micropolis.app_config import AppConfig
from micropolis.constants import LIGHTNINGBOLT, TILE_COUNT, ZONEBIT
from micropolis.context import AppContext
from micropolis.graphics_setup import (
    get_small_tile_overlay_surface,
    get_small_tile_surface,
    get_tile_surface,
    resolve_tile_for_render,
)
from micropolis.sim_view import SimView


@pytest.fixture(scope="module", autouse=True)
def init_pygame() -> None:
    pygame.display.init()
    yield
    pygame.display.quit()


def make_context() -> AppContext:
    config = AppConfig(
        home=Path.cwd(),
        resource_dir=Path.cwd(),
    )
    return AppContext(config=config)


def make_editor_view(width_tiles: int = 4, height_tiles: int = 4) -> SimView:
    view = SimView()
    view.tile_width = width_tiles
    view.tile_height = height_tiles
    view.tile_x = 0
    view.tile_y = 0
    view.surface = pygame.Surface(
        (width_tiles * 16, height_tiles * 16),
        pygame.SRCALPHA,
    )
    atlas_width = 32 * 16
    atlas_height = 32 * 16
    view.bigtiles = pygame.Surface((atlas_width, atlas_height), pygame.SRCALPHA)
    view.tiles = [[-1 for _ in range(view.tile_height)] for _ in range(view.tile_width)]
    return view


def make_small_tile_sheet() -> pygame.Surface:
    sheet = pygame.Surface((4, 4 * TILE_COUNT), pygame.SRCALPHA)
    sheet.fill((64, 64, 64, 255), pygame.Rect(0, 0, 4, 4))
    sheet.fill((192, 192, 192, 255), pygame.Rect(0, 4, 4, 4))
    return sheet


def test_resolve_tile_for_render_blinks_unpowered_zone() -> None:
    context = make_context()
    raw_tile = 42 | ZONEBIT
    resolved = resolve_tile_for_render(context, raw_tile, blink=True)
    assert resolved == getattr(context, "LIGHTNINGBOLT", LIGHTNINGBOLT)


def test_resolve_tile_for_render_applies_overlay_filter() -> None:
    context = make_context()

    def deny_filter(_ctx: AppContext, _x: int, _y: int) -> bool:
        return False

    tile_value = 128 | ZONEBIT
    resolved = resolve_tile_for_render(
        context,
        tile_value,
        coords=(10, 20),
        blink=False,
        overlay_filter=deny_filter,
    )
    assert resolved == 0


def test_get_tile_surface_caches_surfaces() -> None:
    view = make_editor_view()
    first, second = get_tile_surface(0, view), get_tile_surface(0, view)
    assert first is not None
    assert first is second


def test_get_tile_surface_accepts_raw_values_with_blink() -> None:
    context = make_context()
    view = make_editor_view()
    tile = 17 | ZONEBIT
    surface, resolved = get_tile_surface(
        tile,
        view,
        context=context,
        blink=True,
        treat_input_as_raw=True,
        return_tile_index=True,
    )
    assert surface is not None
    assert resolved == getattr(context, "LIGHTNINGBOLT", LIGHTNINGBOLT)


def test_get_small_tile_surface_caches_and_tints() -> None:
    view = make_editor_view()
    setattr(view, "_small_tile_sheet", make_small_tile_sheet())
    base_one = get_small_tile_surface(0, view)
    base_two = get_small_tile_surface(0, view)
    assert base_one is not None
    assert base_one is base_two

    tint_color = (255, 0, 0, 128)
    tinted_one = get_small_tile_surface(0, view, tint_color=tint_color, variant="power")
    tinted_two = get_small_tile_surface(0, view, tint_color=tint_color, variant="power")
    assert tinted_one is not None
    assert tinted_one is tinted_two
    assert tinted_one is not base_one


def test_get_small_tile_overlay_surface_uses_overlay_cache() -> None:
    view = make_editor_view()
    setattr(view, "_small_tile_sheet", make_small_tile_sheet())

    overlay_surface = get_small_tile_overlay_surface(
        0,
        view,
        overlay_key="power",
        tint_color=(255, 0, 0, 255),
    )
    assert overlay_surface is not None

    overlay_surface_repeat = get_small_tile_overlay_surface(
        0,
        view,
        overlay_key="power",
        tint_color=(255, 0, 0, 255),
    )
    assert overlay_surface is overlay_surface_repeat


def test_small_tile_overlay_color_ramp_applies_gradient() -> None:
    view = make_editor_view()
    setattr(view, "_small_tile_sheet", make_small_tile_sheet())

    ramp = ((0, (0, 0, 0, 0)), (255, (0, 0, 255, 255)))
    overlay_surface = get_small_tile_overlay_surface(
        1,
        view,
        overlay_key="water",
        color_ramp=ramp,
    )
    assert overlay_surface is not None
    pixel = overlay_surface.get_at((0, 0))
    assert pixel[2] > pixel[0]
    assert pixel[3] > 0
