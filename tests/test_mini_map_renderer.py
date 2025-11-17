from __future__ import annotations

from pathlib import Path

import pygame
import pytest

from src.micropolis import map_renderer as map_renderer_module
from src.micropolis import sim_view as sim_view_module
from micropolis.app_config import AppConfig
from micropolis.constants import (
    EDITOR_H,
    EDITOR_W,
    MAP_H,
    MAP_W,
    PWRBIT,
    TILE_COUNT,
    WORLD_X,
    WORLD_Y,
    ZONEBIT,
)
from micropolis.context import AppContext
from micropolis.map_renderer import get_or_create_map_renderer, get_overlay_color
from micropolis.mini_map_renderer import get_or_create_minimap_renderer
from micropolis.sim_view import SimView


@pytest.fixture(scope="module", autouse=True)
def init_pygame() -> None:
    pygame.display.init()
    yield
    pygame.display.quit()


@pytest.fixture(autouse=True)
def stub_engine_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide lightweight stand-ins to avoid pulling heavy engine modules."""

    def fake_populate(
        context: AppContext,
        view: SimView,
        width: int,
        height: int,
        class_id: int,
    ) -> None:
        view.class_id = class_id
        view.width = width
        view.height = height
        view.m_width = width
        view.m_height = height
        view.w_width = width
        view.w_height = height
        view.i_width = width
        view.i_height = height
        view.screen_width = width
        view.screen_height = height
        view.tile_x = 0
        view.tile_y = 0
        view.tile_width = WORLD_X
        view.tile_height = WORLD_Y
        view.pixel_bytes = 4
        view.line_bytes = width * view.pixel_bytes
        view.visible = True
        view.invalid = True
        if view.surface is None:
            view.surface = pygame.Surface((width or 1, height or 1))

    def ensure_surface(view: SimView) -> pygame.Surface:
        if view.surface is None:
            view.surface = pygame.Surface((view.width or 1, view.height or 1))
        return view.surface

    def noop_draw(*_args, **_kwargs) -> None:
        return None

    monkeypatch.setattr(
        sim_view_module,
        "populate_common_view_fields",
        fake_populate,
        raising=False,
    )
    monkeypatch.setattr(
        map_renderer_module,
        "_ENSURE_VIEW_SURFACE",
        ensure_surface,
        raising=False,
    )
    monkeypatch.setattr(
        map_renderer_module,
        "_MEM_DRAW_BEEG_MAP_RECT",
        noop_draw,
        raising=False,
    )


def make_context() -> AppContext:
    config = AppConfig(home=Path.cwd(), resource_dir=Path.cwd())
    return AppContext(config=config)


def _color_for_tile(tile_index: int) -> tuple[int, int, int, int]:
    return (
        (tile_index * 13) % 256,
        (tile_index * 7) % 256,
        (tile_index * 3) % 256,
        255,
    )


def _seed_small_tile_sheet(view) -> None:
    sheet = pygame.Surface((4, 4 * TILE_COUNT), pygame.SRCALPHA)
    for index in range(TILE_COUNT):
        color = _color_for_tile(index)
        sheet.fill(color, pygame.Rect(0, index * 4, 4, 4))
    view._small_tile_sheet = sheet


def _make_simulation(context: AppContext) -> None:
    class SimStub:
        pass

    sim = SimStub()
    sim.editor = SimView(
        width=EDITOR_W,
        height=EDITOR_H,
        tile_width=WORLD_X,
        tile_height=WORLD_Y,
        tile_x=0,
        tile_y=0,
        pixel_bytes=4,
        line_bytes=EDITOR_W * 4,
        surface=pygame.Surface((EDITOR_W, EDITOR_H)),
    )
    sim.map = SimView(
        width=MAP_W,
        height=MAP_H,
        tile_width=WORLD_X,
        tile_height=WORLD_Y,
        tile_x=0,
        tile_y=0,
        pixel_bytes=4,
        line_bytes=MAP_W * 4,
        surface=pygame.Surface((MAP_W, MAP_H)),
    )
    context.sim = sim
    _seed_small_tile_sheet(sim.map)
    context.dynamic_data = [0, 255] * 8


def _cleanup_renderer_cache(context: AppContext) -> None:
    from src.micropolis import mini_map_renderer as mmr

    mmr._MINIMAP_RENDERERS.pop((id(context), mmr._MINIMAP_TILE_SIZE), None)


@pytest.fixture
def seeded_context() -> AppContext:
    context = make_context()
    _make_simulation(context)
    yield context
    _cleanup_renderer_cache(context)


def test_minimap_render_matches_small_tiles(seeded_context: AppContext) -> None:
    renderer = get_or_create_minimap_renderer(seeded_context)
    seeded_context.map_data[2][3] = 7

    surface = renderer.render(show_viewport=False)
    expected_color = _color_for_tile(7)
    pixel = surface.get_at((2 * renderer.tile_size + 1, 3 * renderer.tile_size + 1))
    assert tuple(pixel) == expected_color


def test_minimap_overlay_sampling_uses_overlay_colors(
    seeded_context: AppContext,
) -> None:
    renderer = get_or_create_minimap_renderer(seeded_context)
    seeded_context.map_data[0][0] = ZONEBIT | PWRBIT

    overlay_surface = renderer.sample_density_overlay("power", force=True)
    color = overlay_surface.get_at((1, 1))
    expected = get_overlay_color(seeded_context, "power", 0, 0)
    assert expected is not None
    assert tuple(color) == expected


def test_quick_jump_updates_map_renderer_center(seeded_context: AppContext) -> None:
    map_renderer = get_or_create_map_renderer(seeded_context)
    map_renderer.set_viewport_pixels(160, 160)
    renderer = get_or_create_minimap_renderer(seeded_context)

    target_tile = (30, 20)
    click_point = (
        int(target_tile[0] * renderer.tile_size + renderer.tile_size / 2),
        int(target_tile[1] * renderer.tile_size + renderer.tile_size / 2),
    )
    renderer.quick_jump_to(click_point)

    viewport_width, viewport_height = map_renderer.viewport_size_px
    max_origin_x = max(0, WORLD_X * map_renderer.tile_size - viewport_width)
    max_origin_y = max(0, WORLD_Y * map_renderer.tile_size - viewport_height)
    expected_origin = (
        max(
            0,
            min(
                max_origin_x,
                target_tile[0] * map_renderer.tile_size - viewport_width // 2,
            ),
        ),
        max(
            0,
            min(
                max_origin_y,
                target_tile[1] * map_renderer.tile_size - viewport_height // 2,
            ),
        ),
    )
    assert map_renderer.pixel_origin == expected_origin


def test_dynamic_filter_overlay_changes_pixels(seeded_context: AppContext) -> None:
    renderer = get_or_create_minimap_renderer(seeded_context)
    base_surface = renderer.render(show_viewport=False)
    renderer.set_dynamic_filter(True)
    overlay_surface = renderer.render(show_viewport=False)

    base_color = base_surface.get_at((1, 1))
    overlay_color = overlay_surface.get_at((1, 1))
    assert tuple(overlay_color) != tuple(base_color)
