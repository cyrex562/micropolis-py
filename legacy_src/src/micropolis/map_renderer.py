from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from math import ceil

import pygame

from .constants import CONDBIT, PWRBIT, WORLD_X, WORLD_Y, ZONEBIT
from .context import AppContext
from .sim_view import SimView

Color = tuple[int, int, int, int]


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def _clamp_float(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


@dataclass(frozen=True)
class ScalarOverlay:
    """Describes overlays backed by down-sampled scalar fields."""

    attr_name: str
    scale: tuple[int, int]
    value_range: tuple[float, float]
    ramp: tuple[tuple[float, Color], ...]

    def color_for(self, context: AppContext, tile_x: int, tile_y: int) -> Color | None:
        data = getattr(context, self.attr_name, None)
        if not data:
            return None

        grid_x = tile_x // self.scale[0]
        grid_y = tile_y // self.scale[1]
        if grid_x < 0 or grid_y < 0:
            return None

        max_x = len(data) - 1
        if max_x < 0:
            return None
        grid_x = min(max_x, grid_x)
        column = data[grid_x]
        if not column:
            return None
        grid_y = min(len(column) - 1, grid_y)

        try:
            raw_value = column[grid_y]
        except (IndexError, TypeError):
            return None

        min_val, max_val = self.value_range
        if max_val == min_val:
            normalized = 0.0
        else:
            normalized = (float(raw_value) - min_val) / (max_val - min_val)
        normalized = _clamp_float(normalized)
        return _color_from_ramp(normalized, self.ramp)


def _color_from_ramp(
    value: float, ramp: tuple[tuple[float, Color], ...]
) -> Color | None:
    clamped = _clamp_float(value)
    for threshold, color in ramp:
        if clamped <= threshold:
            return color
    return ramp[-1][1] if ramp else None


_POPULATION_OVERLAY = ScalarOverlay(
    attr_name="pop_density",
    scale=(2, 2),
    value_range=(0.0, 255.0),
    ramp=(
        (0.2, (0, 96, 255, 90)),
        (0.4, (0, 190, 255, 110)),
        (0.6, (255, 220, 0, 140)),
        (0.8, (255, 140, 0, 160)),
        (1.0, (255, 60, 0, 180)),
    ),
)

_TRAFFIC_OVERLAY = ScalarOverlay(
    attr_name="trf_density",
    scale=(2, 2),
    value_range=(0.0, 255.0),
    ramp=(
        (0.2, (0, 180, 120, 90)),
        (0.4, (240, 220, 0, 120)),
        (0.6, (255, 165, 0, 150)),
        (0.8, (220, 80, 0, 170)),
        (1.0, (200, 20, 20, 190)),
    ),
)

_POLLUTION_OVERLAY = ScalarOverlay(
    attr_name="pollution_mem",
    scale=(2, 2),
    value_range=(0.0, 255.0),
    ramp=(
        (0.2, (0, 160, 0, 80)),
        (0.4, (150, 200, 0, 110)),
        (0.6, (220, 180, 0, 140)),
        (0.8, (220, 100, 0, 165)),
        (1.0, (200, 30, 0, 190)),
    ),
)

_CRIME_OVERLAY = ScalarOverlay(
    attr_name="crime_mem",
    scale=(2, 2),
    value_range=(0.0, 255.0),
    ramp=(
        (0.2, (0, 140, 200, 90)),
        (0.4, (60, 90, 200, 120)),
        (0.6, (140, 60, 200, 150)),
        (0.8, (190, 30, 180, 170)),
        (1.0, (230, 0, 140, 190)),
    ),
)

_LAND_VALUE_OVERLAY = ScalarOverlay(
    attr_name="land_value_mem",
    scale=(2, 2),
    value_range=(0.0, 255.0),
    ramp=(
        (0.2, (200, 30, 30, 90)),
        (0.4, (220, 140, 20, 120)),
        (0.6, (210, 200, 40, 140)),
        (0.8, (90, 200, 80, 160)),
        (1.0, (40, 180, 120, 190)),
    ),
)

_SCALAR_OVERLAYS: dict[str, ScalarOverlay] = {
    "population": _POPULATION_OVERLAY,
    "traffic": _TRAFFIC_OVERLAY,
    "pollution": _POLLUTION_OVERLAY,
    "crime": _CRIME_OVERLAY,
    "land_value": _LAND_VALUE_OVERLAY,
}


def _power_overlay(context: AppContext, tile_x: int, tile_y: int) -> Color | None:
    if not (0 <= tile_x < WORLD_X and 0 <= tile_y < WORLD_Y):
        return None
    tile_value = context.map_data[tile_x][tile_y]
    if tile_value & ZONEBIT:
        return (255, 215, 0, 170) if (tile_value & PWRBIT) else (60, 80, 110, 190)
    if tile_value & CONDBIT:
        return (200, 200, 200, 120)
    return None


_OVERLAY_SAMPLERS: dict[str, Callable[[AppContext, int, int], Color | None]] = {
    "power": _power_overlay,
}

for _name, _spec in _SCALAR_OVERLAYS.items():
    _OVERLAY_SAMPLERS[_name] = _spec.color_for


_ENSURE_VIEW_SURFACE: Callable[[SimView], pygame.Surface] | None = None
_MEM_DRAW_BEEG_MAP_RECT: (
    Callable[[AppContext, SimView, int, int, int, int], None] | None
) = None


def _get_editor_view_helpers() -> tuple[
    Callable[[SimView], pygame.Surface],
    Callable[[AppContext, SimView, int, int, int, int], None],
]:
    global _ENSURE_VIEW_SURFACE, _MEM_DRAW_BEEG_MAP_RECT
    if _ENSURE_VIEW_SURFACE is None or _MEM_DRAW_BEEG_MAP_RECT is None:
        from .editor_view import ensure_view_surface, mem_draw_beeg_map_rect

        _ENSURE_VIEW_SURFACE = ensure_view_surface
        _MEM_DRAW_BEEG_MAP_RECT = mem_draw_beeg_map_rect
    return _ENSURE_VIEW_SURFACE, _MEM_DRAW_BEEG_MAP_RECT


def get_overlay_color(
    context: AppContext, overlay_name: str, tile_x: int, tile_y: int
) -> Color | None:
    """Return the overlay color for a specific tile.

    Args:
        context: Micropolis context containing overlay data.
        overlay_name: One of the registered overlay keys ("power", "population", etc.).
        tile_x: World X coordinate (0-119).
        tile_y: World Y coordinate (0-99).
    """

    sampler = _OVERLAY_SAMPLERS.get(overlay_name)
    if sampler is None:
        raise ValueError(f"Unknown overlay '{overlay_name}'")
    return sampler(context, tile_x, tile_y)


class MapRenderer:
    """Viewport renderer for the pygame editor panel."""

    def __init__(
        self,
        context: AppContext,
        view: SimView,
        *,
        viewport_size: tuple[int, int] | None = None,
        tile_size: int = 16,
    ) -> None:
        self.context = context
        self.view = view
        self.tile_size = tile_size
        ensure_surface, _ = _get_editor_view_helpers()
        ensure_surface(self.view)

        default_width = WORLD_X * tile_size
        default_height = WORLD_Y * tile_size
        if viewport_size is None or viewport_size == (0, 0):
            viewport_size = context.editor_viewport_size
        if not viewport_size or viewport_size == (0, 0):
            viewport_size = (default_width, default_height)

        self._viewport_tile_rect = pygame.Rect(0, 0, 1, 1)
        self._viewport_px_size = (tile_size, tile_size)
        self._pixel_origin = [
            int(getattr(view, "pan_x", 0)),
            int(getattr(view, "pan_y", 0)),
        ]
        self._surface = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        self._overlay_surface = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        self._overlay_mode: str | None = None
        self._last_overlay_mode: str | None = None

        self.set_viewport_pixels(*viewport_size)

    # ------------------------------------------------------------------
    @property
    def viewport_tiles(self) -> pygame.Rect:
        return self._viewport_tile_rect.copy()

    @property
    def viewport_size_px(self) -> tuple[int, int]:
        return self._viewport_px_size

    @property
    def pixel_origin(self) -> tuple[int, int]:
        return tuple(self._pixel_origin)

    # ------------------------------------------------------------------
    def set_viewport_pixels(self, width_px: int, height_px: int) -> None:
        width_px = _clamp(width_px, self.tile_size, WORLD_X * self.tile_size)
        height_px = _clamp(height_px, self.tile_size, WORLD_Y * self.tile_size)

        width_tiles = _clamp(ceil(width_px / self.tile_size), 1, WORLD_X)
        height_tiles = _clamp(ceil(height_px / self.tile_size), 1, WORLD_Y)

        self._viewport_tile_rect.width = width_tiles
        self._viewport_tile_rect.height = height_tiles
        new_size = (width_tiles * self.tile_size, height_tiles * self.tile_size)
        if new_size != self._surface.get_size():
            self._surface = pygame.Surface(new_size, pygame.SRCALPHA)
            self._overlay_surface = pygame.Surface(new_size, pygame.SRCALPHA)
        self._viewport_px_size = new_size
        self.context.editor_viewport_size = new_size
        self._clamp_pixel_origin()
        self._sync_view_pan()

    def set_overlay_mode(self, mode: str | None) -> None:
        normalized = mode.lower() if isinstance(mode, str) else None
        if normalized and normalized not in _OVERLAY_SAMPLERS:
            raise ValueError(f"Unknown overlay '{mode}'")
        self._overlay_mode = normalized

    def scroll_pixels(self, dx: int, dy: int) -> tuple[int, int]:
        self._sync_from_view_pan()
        new_x = _clamp(self._pixel_origin[0] + dx, 0, self._max_pixel_origin_x())
        new_y = _clamp(self._pixel_origin[1] + dy, 0, self._max_pixel_origin_y())
        moved = (new_x - self._pixel_origin[0], new_y - self._pixel_origin[1])
        if moved != (0, 0):
            self._pixel_origin[0], self._pixel_origin[1] = new_x, new_y
            self._sync_view_pan()
        return moved

    def scroll_tiles(self, dx: int, dy: int) -> tuple[int, int]:
        return self.scroll_pixels(dx * self.tile_size, dy * self.tile_size)

    def center_on(self, tile_x: int, tile_y: int) -> None:
        px = tile_x * self.tile_size - (self._viewport_px_size[0] // 2)
        py = tile_y * self.tile_size - (self._viewport_px_size[1] // 2)
        self._pixel_origin[0] = _clamp(px, 0, self._max_pixel_origin_x())
        self._pixel_origin[1] = _clamp(py, 0, self._max_pixel_origin_y())
        self._sync_view_pan()

    # ------------------------------------------------------------------
    def render(
        self,
        *,
        blink_override: bool | None = None,
        overlay_mode: str | None = None,
        dest_surface: pygame.Surface | None = None,
        dest_rect: pygame.Rect | tuple[int, int, int, int] | None = None,
    ) -> pygame.Surface:
        ensure_surface, draw_rect = _get_editor_view_helpers()
        if self.view.surface is None:
            ensure_surface(self.view)
        self._sync_from_view_pan()

        (
            start_x,
            start_y,
            span_x,
            span_y,
            offset_x,
            offset_y,
        ) = self._compute_tile_region()
        draw_rect(self.context, self.view, start_x, start_y, span_x, span_y)
        self._copy_view_region()

        overlay_target = overlay_mode or self._overlay_mode
        if overlay_target:
            self._apply_overlay(
                overlay_target,
                start_x,
                start_y,
                span_x,
                span_y,
                offset_x,
                offset_y,
            )
            self._last_overlay_mode = overlay_target
        else:
            self._last_overlay_mode = None

        if dest_surface is not None:
            target_rect = (
                pygame.Rect(dest_rect)
                if dest_rect
                else pygame.Rect(0, 0, *self._viewport_px_size)
            )
            if target_rect.size == self._viewport_px_size:
                dest_surface.blit(self._surface, target_rect.topleft)
            else:
                scaled = pygame.transform.smoothscale(self._surface, target_rect.size)
                dest_surface.blit(scaled, target_rect.topleft)
        return self._surface

    # ------------------------------------------------------------------
    def _compute_tile_region(self) -> tuple[int, int, int, int, int, int]:
        start_x = self._pixel_origin[0] // self.tile_size
        start_y = self._pixel_origin[1] // self.tile_size
        offset_x = self._pixel_origin[0] % self.tile_size
        offset_y = self._pixel_origin[1] % self.tile_size

        span_x = self._viewport_tile_rect.width
        span_y = self._viewport_tile_rect.height
        if offset_x and start_x + span_x < WORLD_X:
            span_x += 1
        if offset_y and start_y + span_y < WORLD_Y:
            span_y += 1
        return start_x, start_y, span_x, span_y, offset_x, offset_y

    def _copy_view_region(self) -> None:
        src_rect = pygame.Rect(
            self._pixel_origin[0],
            self._pixel_origin[1],
            self._viewport_px_size[0],
            self._viewport_px_size[1],
        )
        self._surface.blit(self.view.surface, (0, 0), src_rect)

    def _apply_overlay(
        self,
        overlay_mode: str,
        start_x: int,
        start_y: int,
        span_x: int,
        span_y: int,
        offset_x: int,
        offset_y: int,
    ) -> None:
        sampler = _OVERLAY_SAMPLERS.get(overlay_mode)
        if sampler is None:
            return

        self._overlay_surface.fill((0, 0, 0, 0))
        viewport_rect = pygame.Rect(0, 0, *self._viewport_px_size)
        for dx in range(span_x):
            world_x = start_x + dx
            if world_x >= WORLD_X:
                break
            for dy in range(span_y):
                world_y = start_y + dy
                if world_y >= WORLD_Y:
                    break
                color = sampler(self.context, world_x, world_y)
                if color is None:
                    continue
                rect = pygame.Rect(
                    dx * self.tile_size - offset_x,
                    dy * self.tile_size - offset_y,
                    self.tile_size,
                    self.tile_size,
                )
                clipped = rect.clip(viewport_rect)
                if clipped.width and clipped.height:
                    self._overlay_surface.fill(color, clipped)
        self._surface.blit(self._overlay_surface, (0, 0))

    def _sync_from_view_pan(self) -> None:
        max_x = self._max_pixel_origin_x()
        max_y = self._max_pixel_origin_y()
        px = _clamp(int(getattr(self.view, "pan_x", 0)), 0, max_x)
        py = _clamp(int(getattr(self.view, "pan_y", 0)), 0, max_y)
        self._pixel_origin[0], self._pixel_origin[1] = px, py

    def _sync_view_pan(self) -> None:
        self.view.pan_x = self._pixel_origin[0]
        self.view.pan_y = self._pixel_origin[1]

    def _clamp_pixel_origin(self) -> None:
        self._pixel_origin[0] = _clamp(
            self._pixel_origin[0],
            0,
            self._max_pixel_origin_x(),
        )
        self._pixel_origin[1] = _clamp(
            self._pixel_origin[1],
            0,
            self._max_pixel_origin_y(),
        )

    def _max_pixel_origin_x(self) -> int:
        return max(0, WORLD_X * self.tile_size - self._viewport_px_size[0])

    def _max_pixel_origin_y(self) -> int:
        return max(0, WORLD_Y * self.tile_size - self._viewport_px_size[1])


_CONTEXT_RENDERERS: dict[int, MapRenderer] = {}


def get_or_create_map_renderer(
    context: AppContext, *, viewport_size: tuple[int, int] | None = None
) -> MapRenderer:
    """Return the shared MapRenderer, creating it if necessary."""

    sim = getattr(context, "sim", None)
    view = getattr(sim, "editor", None)
    if view is None:
        raise RuntimeError("No editor view is available for rendering")

    key = id(context)
    renderer = _CONTEXT_RENDERERS.get(key)
    if not isinstance(renderer, MapRenderer) or renderer.view is not view:
        renderer = MapRenderer(context, view, viewport_size=viewport_size)
        _CONTEXT_RENDERERS[key] = renderer
    elif viewport_size:
        renderer.set_viewport_pixels(*viewport_size)
    return renderer


def available_overlays() -> Iterable[str]:
    return tuple(sorted(_OVERLAY_SAMPLERS.keys()))


__all__ = [
    "MapRenderer",
    "available_overlays",
    "get_overlay_color",
    "get_or_create_map_renderer",
]
