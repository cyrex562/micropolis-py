from __future__ import annotations

from collections.abc import Iterable

import pygame

from .context import AppContext
from .constants import WORLD_X, WORLD_Y
from .graphics_setup import get_small_tile_surface
from .map_renderer import (
    available_overlays as _available_map_overlays,
    get_or_create_map_renderer,
    get_overlay_color,
)
from .mini_maps import dynamicFilter
from .sim_view import SimView

Color = tuple[int, int, int, int]

_MINIMAP_TILE_SIZE = 4
_VIEWPORT_COLOR: Color = (255, 255, 255, 220)
_DYNAMIC_FILTER_COLOR: Color = (0, 200, 255, 140)

_AVAILABLE_OVERLAYS: tuple[str, ...] = _available_map_overlays()
_AVAILABLE_OVERLAY_SET = set(_AVAILABLE_OVERLAYS)


class MiniMapRenderer:
    """Renders the 4×4 tile minimap surface with overlays and viewport overlays."""

    def __init__(
        self,
        context: AppContext,
        view: SimView,
        *,
        tile_size: int = _MINIMAP_TILE_SIZE,
    ) -> None:
        if tile_size <= 0:
            raise ValueError("tile_size must be positive")

        self.context = context
        self.view = view
        self.tile_size = tile_size
        self._base_surface = pygame.Surface(
            (WORLD_X * tile_size, WORLD_Y * tile_size), pygame.SRCALPHA
        )
        self._overlay_mode: str | None = None
        self._dynamic_filter_enabled = False
        self._overlay_cache: dict[str, pygame.Surface] = {}
        self._overlay_tokens: dict[str, int] = {}

    # ------------------------------------------------------------------
    def set_overlay_mode(self, mode: str | None) -> None:
        normalized = mode.lower() if isinstance(mode, str) else None
        if normalized and normalized not in _AVAILABLE_OVERLAY_SET:
            raise ValueError(f"Unknown overlay '{mode}'")
        self._overlay_mode = normalized

    def set_dynamic_filter(self, enabled: bool) -> None:
        self._dynamic_filter_enabled = bool(enabled)

    def invalidate_overlays(self, overlay_name: str | None = None) -> None:
        if overlay_name is None:
            self._overlay_cache.clear()
            self._overlay_tokens.clear()
            return

        normalized = overlay_name.lower()
        self._overlay_cache.pop(normalized, None)
        self._overlay_tokens.pop(normalized, None)

    # ------------------------------------------------------------------
    def render(
        self,
        *,
        blink_override: bool | None = None,
        overlay_mode: str | None = None,
        show_viewport: bool = True,
        dest_surface: pygame.Surface | None = None,
        dest_rect: pygame.Rect | tuple[int, int, int, int] | None = None,
    ) -> pygame.Surface:
        blink = (
            blink_override
            if blink_override is not None
            else self.context.flag_blink <= 0
        )
        self._draw_base_map(blink)
        result = self._base_surface.copy()

        overlay_target = overlay_mode or self._overlay_mode
        if overlay_target:
            overlay_surface = self.sample_density_overlay(overlay_target)
            result.blit(overlay_surface, (0, 0))

        if self._dynamic_filter_enabled:
            dynamic_surface = self._build_dynamic_filter_overlay()
            if dynamic_surface:
                result.blit(dynamic_surface, (0, 0))

        if show_viewport:
            self._draw_viewport_rect(result)

        if dest_surface is not None:
            target_rect = pygame.Rect(dest_rect) if dest_rect else result.get_rect()
            if target_rect.width <= 0 or target_rect.height <= 0:
                raise ValueError("Destination rectangle must have positive size")

            if target_rect.size == result.get_size():
                dest_surface.blit(result, target_rect.topleft)
            else:
                scaled = pygame.transform.smoothscale(result, target_rect.size)
                dest_surface.blit(scaled, target_rect.topleft)

        return result

    def sample_density_overlay(
        self, mode: str, *, force: bool = False
    ) -> pygame.Surface:
        normalized = mode.lower()
        if normalized not in _AVAILABLE_OVERLAY_SET:
            raise ValueError(f"Unknown overlay '{mode}'")

        current_cycle = getattr(self.context, "cycle", 0)
        cached = self._overlay_cache.get(normalized)
        cached_cycle = self._overlay_tokens.get(normalized)
        if cached is not None and cached_cycle == current_cycle and not force:
            return cached

        surface = pygame.Surface(self._base_surface.get_size(), pygame.SRCALPHA)
        for tile_x in range(WORLD_X):
            for tile_y in range(WORLD_Y):
                color = get_overlay_color(self.context, normalized, tile_x, tile_y)
                if color is None:
                    continue
                rect = pygame.Rect(
                    tile_x * self.tile_size,
                    tile_y * self.tile_size,
                    self.tile_size,
                    self.tile_size,
                )
                surface.fill(color, rect)

        self._overlay_cache[normalized] = surface
        self._overlay_tokens[normalized] = current_cycle
        return surface

    def world_coords_from_point(
        self,
        point: tuple[int, int],
        *,
        dest_rect: pygame.Rect | tuple[int, int, int, int] | None = None,
    ) -> tuple[int, int]:
        if dest_rect is not None:
            rect = pygame.Rect(dest_rect)
            if rect.width <= 0 or rect.height <= 0:
                raise ValueError("Destination rectangle must have positive dimensions")
            normalized_x = (point[0] - rect.left) / rect.width
            normalized_y = (point[1] - rect.top) / rect.height
        else:
            rect = self._base_surface.get_rect()
            normalized_x = point[0] / rect.width
            normalized_y = point[1] / rect.height

        tile_x = max(0, min(WORLD_X - 1, int(normalized_x * WORLD_X)))
        tile_y = max(0, min(WORLD_Y - 1, int(normalized_y * WORLD_Y)))
        return tile_x, tile_y

    def quick_jump_to(
        self,
        point: tuple[int, int],
        *,
        dest_rect: pygame.Rect | tuple[int, int, int, int] | None = None,
    ) -> tuple[int, int]:
        tile_x, tile_y = self.world_coords_from_point(point, dest_rect=dest_rect)
        map_renderer = get_or_create_map_renderer(self.context)
        map_renderer.center_on(tile_x, tile_y)
        return tile_x, tile_y

    # ------------------------------------------------------------------
    def _draw_base_map(self, blink: bool) -> None:
        self._base_surface.fill((0, 0, 0, 0))
        for tile_x in range(WORLD_X):
            for tile_y in range(WORLD_Y):
                tile_value = self.context.map_data[tile_x][tile_y]
                tile_surface = get_small_tile_surface(
                    tile_value,
                    self.view,
                    context=self.context,
                    coords=(tile_x, tile_y),
                    blink=blink,
                    treat_input_as_raw=True,
                )
                if tile_surface is None:
                    continue

                dest = (tile_x * self.tile_size, tile_y * self.tile_size)
                if (
                    tile_surface.get_width() == self.tile_size
                    and tile_surface.get_height() == self.tile_size
                ):
                    self._base_surface.blit(tile_surface, dest)
                else:
                    scaled = pygame.transform.smoothscale(
                        tile_surface, (self.tile_size, self.tile_size)
                    )
                    self._base_surface.blit(scaled, dest)

    def _build_dynamic_filter_overlay(self) -> pygame.Surface | None:
        if len(self.context.dynamic_data) < 16:
            return None

        surface = pygame.Surface(self._base_surface.get_size(), pygame.SRCALPHA)
        has_data = False
        for tile_x in range(WORLD_X):
            for tile_y in range(WORLD_Y):
                if not dynamicFilter(self.context, tile_x, tile_y):
                    continue
                has_data = True
                rect = pygame.Rect(
                    tile_x * self.tile_size,
                    tile_y * self.tile_size,
                    self.tile_size,
                    self.tile_size,
                )
                surface.fill(_DYNAMIC_FILTER_COLOR, rect)
        return surface if has_data else None

    def _draw_viewport_rect(self, result_surface: pygame.Surface) -> None:
        try:
            map_renderer = get_or_create_map_renderer(self.context)
        except RuntimeError:
            return

        viewport_px = map_renderer.viewport_size_px
        if viewport_px[0] <= 0 or viewport_px[1] <= 0:
            return

        origin_px = map_renderer.pixel_origin
        scale = self.tile_size / map_renderer.tile_size
        rect = pygame.Rect(
            int(round(origin_px[0] * scale)),
            int(round(origin_px[1] * scale)),
            max(1, int(round(viewport_px[0] * scale))),
            max(1, int(round(viewport_px[1] * scale))),
        )
        pygame.draw.rect(result_surface, _VIEWPORT_COLOR, rect, width=1)


_MINIMAP_RENDERERS: dict[tuple[int, int], MiniMapRenderer] = {}


def get_or_create_minimap_renderer(
    context: AppContext,
    *,
    tile_size: int = _MINIMAP_TILE_SIZE,
) -> MiniMapRenderer:
    sim = getattr(context, "sim", None)
    view = getattr(sim, "map", None)
    if view is None:
        raise RuntimeError("No map view is available for the minimap renderer")

    key = (id(context), tile_size)
    renderer = _MINIMAP_RENDERERS.get(key)
    if not isinstance(renderer, MiniMapRenderer) or renderer.view is not view:
        renderer = MiniMapRenderer(context, view, tile_size=tile_size)
        _MINIMAP_RENDERERS[key] = renderer
    return renderer


def available_minimap_overlays() -> Iterable[str]:
    return _AVAILABLE_OVERLAYS


__all__ = [
    "MiniMapRenderer",
    "available_minimap_overlays",
    "get_or_create_minimap_renderer",
]
