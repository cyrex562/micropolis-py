from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pygame

from ..asset_manager import AssetHotReloadController, AssetManager
from ..asset_manager import asset_manager as _default_asset_manager
from ..constants import MAX_CHANNELS, SOUND_CHANNELS
from .widgets.theme import (
    THEME_MANAGER,
    Theme,
    ThemeManager,
    ThemeMetrics,
    ThemePalette,
)

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_PROJECT_ROOT = _PACKAGE_ROOT.parents[1]
_DEFAULT_THEME_CONFIG = _PROJECT_ROOT / "config" / "themes.json"
_ASSET_HOT_RELOAD_ENV = "MICROPOLIS_ASSET_HOT_RELOAD"

ColorValue = tuple[int, int, int, int]
ImageLoader = Callable[[str], pygame.Surface]
FontLoader = Callable[[str, int], Any]
SoundLoader = Callable[[str], Any]


def _normalize_key(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


@dataclass(frozen=True)
class SpriteSheetSpec:
    """Describe how a sprite sheet should be sliced into frames."""

    frame_width: int
    frame_height: int
    columns: int | None = None
    rows: int | None = None
    margin: int = 0
    spacing: int = 0

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        if self.frame_width <= 0 or self.frame_height <= 0:
            raise ValueError("Sprite frame dimensions must be positive")
        if self.margin < 0 or self.spacing < 0:
            raise ValueError("margin and spacing must be non-negative")

    def key(self) -> tuple[int, ...]:
        return (
            self.frame_width,
            self.frame_height,
            self.columns or -1,
            self.rows or -1,
            self.margin,
            self.spacing,
        )


@dataclass(slots=True)
class SpriteSheet:
    name: str
    spec: SpriteSheetSpec
    frames: list[pygame.Surface]

    def frame(self, index: int) -> pygame.Surface:
        try:
            return self.frames[index]
        except IndexError as exc:  # pragma: no cover - defensive
            raise IndexError(
                f"Sprite index {index} out of range for '{self.name}'"
            ) from exc


class SoundRouter:
    """Centralizes pygame mixer channel management."""

    def __init__(
        self,
        *,
        mixer_module: Any | None = None,
        channels: Mapping[str, int] | None = None,
        max_channels: int = MAX_CHANNELS,
    ) -> None:
        self._mixer = mixer_module or pygame.mixer
        self._channel_map = dict(channels or SOUND_CHANNELS)
        self._max_channels = max_channels

    def _ensure_ready(self) -> None:
        if not self._mixer.get_init():
            raise RuntimeError("pygame.mixer is not initialized")
        current = self._mixer.get_num_channels()
        if current < self._max_channels:
            self._mixer.set_num_channels(self._max_channels)

    def play(
        self,
        channel_name: str,
        sound: Any,
        *,
        loops: int = 0,
        maxtime: int = 0,
        fade_ms: int = 0,
    ) -> None:
        self._ensure_ready()
        try:
            channel_index = self._channel_map[channel_name]
        except KeyError as exc:
            raise KeyError(f"Unknown sound channel '{channel_name}'") from exc
        channel = self._mixer.Channel(channel_index)
        channel.play(sound, loops=loops, maxtime=maxtime, fade_ms=fade_ms)

    def stop(self, channel_name: str) -> None:
        if not self._mixer.get_init():
            return
        channel_index = self._channel_map.get(channel_name)
        if channel_index is None:
            return
        self._mixer.Channel(channel_index).stop()

    def set_volume(self, channel_name: str, volume: float) -> None:
        if not self._mixer.get_init():
            return
        channel_index = self._channel_map.get(channel_name)
        if channel_index is None:
            raise KeyError(f"Unknown sound channel '{channel_name}'")
        volume = max(0.0, min(1.0, volume))
        self._mixer.Channel(channel_index).set_volume(volume)

    def register_channel(self, name: str, index: int) -> None:
        self._channel_map[name] = index

    def channels(self) -> Mapping[str, int]:
        return dict(self._channel_map)


class AssetService:
    """Runtime asset loader that wraps the manifest-driven AssetManager."""

    def __init__(
        self,
        asset_manager: AssetManager | None = None,
        *,
        image_loader: ImageLoader | None = None,
        font_loader: FontLoader | None = None,
        sound_loader: SoundLoader | None = None,
        mixer_module: Any | None = None,
        sound_router: SoundRouter | None = None,
        enable_hot_reload: bool | None = None,
        hot_reload_controller: AssetHotReloadController | None = None,
        hot_reload_poll_interval: float = 0.5,
    ) -> None:
        self.asset_manager = asset_manager or _default_asset_manager
        self._image_loader = image_loader or pygame.image.load
        self._font_loader = font_loader or (
            lambda path, size: pygame.font.Font(path, size)
        )
        self._sound_loader = sound_loader or pygame.mixer.Sound
        self._sound_router = sound_router or SoundRouter(mixer_module=mixer_module)
        self._hot_reload_controller = hot_reload_controller
        self._hot_reload_unsubscribe: Callable[[], None] | None = None
        self._owns_hot_reload_controller = False

        self._image_cache: dict[str, pygame.Surface] = {}
        self._sprite_cache: dict[tuple[str, tuple[int, ...]], SpriteSheet] = {}
        self._font_cache: dict[tuple[str, int], Any] = {}
        self._sound_cache: dict[str, Any] = {}
        self._font_aliases = self._build_font_aliases()
        self._configure_hot_reload(
            enable_hot_reload=enable_hot_reload,
            poll_interval=hot_reload_poll_interval,
        )

    # ------------------------------------------------------------------
    # Image helpers
    # ------------------------------------------------------------------
    def load_image(
        self,
        name: str,
        *,
        cache: bool = True,
        convert_alpha: bool = False,
    ) -> pygame.Surface:
        key = _normalize_key(name)
        if cache and key in self._image_cache:
            return self._image_cache[key]

        path = self._require_path(name, category="images")
        surface = self._image_loader(str(path))
        if convert_alpha and pygame.display.get_init() and pygame.display.get_surface():
            try:
                surface = surface.convert_alpha()
            except pygame.error:
                pass  # Headless test environments may not have a display

        if cache:
            self._image_cache[key] = surface
        return surface

    def load_sprite_sheet(
        self,
        name: str,
        spec: SpriteSheetSpec,
        *,
        cache: bool = True,
    ) -> SpriteSheet:
        cache_key = (_normalize_key(name), spec.key())
        if cache and cache_key in self._sprite_cache:
            return self._sprite_cache[cache_key]

        surface = self.load_image(name)
        frames = self._slice_sheet(surface, spec)
        sheet = SpriteSheet(name=name, spec=spec, frames=frames)

        if cache:
            self._sprite_cache[cache_key] = sheet
        return sheet

    def get_sprite(
        self, name: str, spec: SpriteSheetSpec, index: int
    ) -> pygame.Surface:
        sheet = self.load_sprite_sheet(name, spec)
        return sheet.frame(index)

    def _slice_sheet(
        self, surface: pygame.Surface, spec: SpriteSheetSpec
    ) -> list[pygame.Surface]:
        width, height = surface.get_size()
        columns = spec.columns or max(
            1,
            (width - spec.margin * 2 + spec.spacing)
            // (spec.frame_width + spec.spacing),
        )
        rows = spec.rows or max(
            1,
            (height - spec.margin * 2 + spec.spacing)
            // (spec.frame_height + spec.spacing),
        )
        frames: list[pygame.Surface] = []

        for row in range(rows):
            top = spec.margin + row * (spec.frame_height + spec.spacing)
            if top + spec.frame_height > height:
                break
            for column in range(columns):
                left = spec.margin + column * (spec.frame_width + spec.spacing)
                if left + spec.frame_width > width:
                    break
                frame = pygame.Surface(
                    (spec.frame_width, spec.frame_height), pygame.SRCALPHA
                )
                frame.blit(
                    surface,
                    (0, 0),
                    (left, top, spec.frame_width, spec.frame_height),
                )
                frames.append(frame)
        return frames

    # ------------------------------------------------------------------
    # Font helpers
    # ------------------------------------------------------------------
    def register_font_alias(self, alias: str, logical_name: str) -> None:
        if not alias:
            return
        self._font_aliases[_normalize_key(alias)] = logical_name

    def has_font(self, alias: str) -> bool:
        return self._resolve_font_name(alias, strict=False) is not None

    def get_font(self, alias: str, *, size: int | None = None) -> Any:
        canonical = self._resolve_font_name(alias)
        font_size = size or 16
        cache_key = (canonical, font_size)
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        path = self._require_path(canonical, category="fonts")
        if not pygame.font.get_init():
            pygame.font.init()
        font = self._font_loader(str(path), font_size)
        self._font_cache[cache_key] = font
        return font

    def font_aliases(self) -> Mapping[str, str]:
        return dict(self._font_aliases)

    def _resolve_font_name(self, name: str, *, strict: bool = True) -> str:
        key = _normalize_key(name)
        canonical = self._font_aliases.get(key)
        if canonical:
            return canonical
        record = self.asset_manager.get_record(name, category="fonts")
        if record and record.logical_name:
            canonical = record.logical_name
            self._font_aliases[key] = canonical
            return canonical
        if strict:
            raise KeyError(f"Unknown font alias '{name}'")
        return ""

    def _build_font_aliases(self) -> dict[str, str]:
        aliases: dict[str, str] = {}
        for record in self.asset_manager.list("fonts"):
            canonical = record.logical_name or Path(record.relative_path).stem
            if not canonical:
                continue
            canonical_key = _normalize_key(canonical)
            aliases[canonical_key] = canonical
            names: Iterable[str] = {
                record.name,
                Path(record.name).stem,
                canonical,
            }
            metadata = record.metadata.get("aliases")
            if isinstance(metadata, Iterable):
                names = set(names) | {str(alias) for alias in metadata}
            descriptor = record.metadata.get("x11_descriptor")
            if isinstance(descriptor, str):
                names = set(names) | {descriptor}
            for name in names:
                aliases[_normalize_key(name)] = canonical
        return aliases

    # ------------------------------------------------------------------
    # Sound helpers
    # ------------------------------------------------------------------
    def load_sound(self, name: str, *, cache: bool = True) -> Any:
        key = _normalize_key(name)
        if cache and key in self._sound_cache:
            return self._sound_cache[key]
        if not pygame.mixer.get_init():
            raise RuntimeError("pygame.mixer is not initialized")
        path = self._require_path(name, category="sounds")
        sound = self._sound_loader(str(path))
        if cache:
            self._sound_cache[key] = sound
        return sound

    def play_sound(
        self,
        channel: str,
        sound: str | Any,
        *,
        loops: int = 0,
        maxtime: int = 0,
        fade_ms: int = 0,
    ) -> None:
        sound_obj = self.load_sound(sound) if isinstance(sound, str) else sound
        self._sound_router.play(
            channel,
            sound_obj,
            loops=loops,
            maxtime=maxtime,
            fade_ms=fade_ms,
        )

    def stop_channel(self, channel: str) -> None:
        self._sound_router.stop(channel)

    def set_channel_volume(self, channel: str, volume: float) -> None:
        self._sound_router.set_volume(channel, volume)

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    def clear_cache(self) -> None:
        self._image_cache.clear()
        self._sprite_cache.clear()
        self._font_cache.clear()
        self._sound_cache.clear()

    def close(self) -> None:
        if self._hot_reload_unsubscribe:
            self._hot_reload_unsubscribe()
            self._hot_reload_unsubscribe = None
        if self._owns_hot_reload_controller and self._hot_reload_controller:
            self._hot_reload_controller.stop()
            self._owns_hot_reload_controller = False

    def __del__(self) -> None:  # pragma: no cover - best-effort cleanup
        try:
            self.close()
        except Exception:
            pass

    def _configure_hot_reload(
        self,
        *,
        enable_hot_reload: bool | None,
        poll_interval: float,
    ) -> None:
        if self._hot_reload_controller is None:
            if enable_hot_reload is None:
                env_value = os.getenv(_ASSET_HOT_RELOAD_ENV, "")
                enable_hot_reload = env_value.strip().lower() in (
                    "1",
                    "true",
                    "yes",
                    "on",
                )
            if enable_hot_reload:
                self._hot_reload_controller = (
                    self.asset_manager.create_hot_reload_controller(
                        poll_interval=poll_interval
                    )
                )
                self._owns_hot_reload_controller = True

        if self._hot_reload_controller is not None:
            self._hot_reload_unsubscribe = self._hot_reload_controller.add_listener(
                self._handle_hot_reload
            )

    def _handle_hot_reload(self, changed_paths: set[Path]) -> None:
        _ = changed_paths  # For future logging hooks
        self.clear_cache()

    def _require_path(self, name: str, *, category: str | None = None) -> Path:
        path = self.asset_manager.get_path(name, category=category)
        if path is None:
            raise FileNotFoundError(
                f"Asset '{name}' (category={category}) not found in manifest"
            )
        return path


class ThemeService:
    """Synchronize ThemeManager definitions with disk configuration and assets."""

    def __init__(
        self,
        asset_service: AssetService,
        *,
        theme_manager: ThemeManager | None = None,
        config_path: Path | None = None,
    ) -> None:
        self.asset_service = asset_service
        self._manager = theme_manager or THEME_MANAGER
        self._config_path = config_path or _DEFAULT_THEME_CONFIG
        self.reload()

    def reload(self) -> None:
        if self._config_path and self._config_path.exists():
            data = json.loads(self._config_path.read_text(encoding="utf-8"))
            self._apply_theme_data(data)
        else:
            self._ensure_theme_fonts(self._manager.current)

    def _apply_theme_data(self, data: Mapping[str, Any]) -> None:
        for alias, logical in data.get("font_aliases", {}).items():
            self.asset_service.register_font_alias(alias, logical)

        themes = data.get("themes", {})
        for name, spec in themes.items():
            theme = self._build_theme(name, spec)
            self._manager.register_theme(theme)

        active = data.get("active")
        if active:
            self._manager.set_active(active)
        self._ensure_theme_fonts(self._manager.current)

    def _build_theme(self, name: str, spec: Mapping[str, Any]) -> Theme:
        base = (
            self._manager.get(name)
            if name in self._manager._themes
            else Theme(name=name)
        )
        palette = self._merge_palette(base.palette, spec.get("palette", {}))
        metrics = self._merge_metrics(base.metrics, spec.get("metrics", {}))
        return Theme(name=name, palette=palette, metrics=metrics)

    def _merge_palette(
        self, palette: ThemePalette, overrides: Mapping[str, Any]
    ) -> ThemePalette:
        if not overrides:
            return palette
        palette_kwargs = {}
        for key, value in overrides.items():
            if isinstance(value, (list, tuple)) and len(value) == 4:
                palette_kwargs[key] = tuple(int(component) for component in value)
            else:
                palette_kwargs[key] = value
        return replace(palette, **palette_kwargs)

    def _merge_metrics(
        self, metrics: ThemeMetrics, overrides: Mapping[str, Any]
    ) -> ThemeMetrics:
        if not overrides:
            return metrics
        return replace(metrics, **overrides)

    def _ensure_theme_fonts(self, theme: Theme) -> None:
        font_name = theme.metrics.font_name
        if font_name and not self.asset_service.has_font(font_name):
            record = self.asset_service.asset_manager.get_record(
                font_name, category="fonts"
            )
            if record and record.logical_name:
                self.asset_service.register_font_alias(font_name, record.logical_name)

    def get_theme(self, name: str | None = None) -> Theme:
        return self._manager.get(name) if name else self._manager.current

    def set_active(self, name: str) -> Theme:
        theme = self._manager.set_active(name)
        self._ensure_theme_fonts(theme)
        return theme

    def font(self, name: str | None = None, *, size: int | None = None) -> Any:
        theme = self.get_theme(name)
        requested_size = size or theme.metrics.font_size
        return self.asset_service.get_font(theme.metrics.font_name, size=requested_size)

    @property
    def manager(self) -> ThemeManager:
        return self._manager


_DEFAULT_ASSET_SERVICE: AssetService | None = None
_DEFAULT_THEME_SERVICE: ThemeService | None = None


def get_default_asset_service() -> AssetService:
    global _DEFAULT_ASSET_SERVICE
    if _DEFAULT_ASSET_SERVICE is None:
        _DEFAULT_ASSET_SERVICE = AssetService()
    return _DEFAULT_ASSET_SERVICE


def set_default_asset_service(service: AssetService | None) -> None:
    global _DEFAULT_ASSET_SERVICE
    _DEFAULT_ASSET_SERVICE = service


def get_default_theme_service(
    asset_service: AssetService | None = None,
) -> ThemeService:
    global _DEFAULT_THEME_SERVICE
    if _DEFAULT_THEME_SERVICE is None:
        asset_service = asset_service or get_default_asset_service()
        _DEFAULT_THEME_SERVICE = ThemeService(asset_service)
    return _DEFAULT_THEME_SERVICE


def set_default_theme_service(service: ThemeService | None) -> None:
    global _DEFAULT_THEME_SERVICE
    _DEFAULT_THEME_SERVICE = service


__all__ = [
    "AssetService",
    "ThemeService",
    "SpriteSheet",
    "SpriteSheetSpec",
    "SoundRouter",
    "get_default_asset_service",
    "set_default_asset_service",
    "get_default_theme_service",
    "set_default_theme_service",
]
