from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import Any

import pygame
import pytest

from micropolis.asset_manager import AssetManager
from micropolis.ui.asset_service import (
    AssetService,
    SoundRouter,
    SpriteSheetSpec,
    ThemeService,
)
from micropolis.ui.widgets.theme import ThemeManager

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


@pytest.fixture(scope="module", autouse=True)
def _init_pygame() -> Iterator[None]:
    pygame.init()
    yield
    pygame.quit()


class ImageLoaderSpy:
    def __init__(self) -> None:
        self.paths: list[str] = []
        self.calls = 0

    def __call__(self, path: str) -> pygame.Surface:
        self.paths.append(path)
        self.calls += 1
        surface = pygame.Surface((16, 8), pygame.SRCALPHA)
        surface.fill((self.calls * 20 % 255, 40, 90, 255))
        return surface


class SoundLoaderSpy:
    def __init__(self) -> None:
        self.paths: list[str] = []

    def __call__(self, path: str) -> Any:
        self.paths.append(path)
        return {"path": path}


class DummyRouter:
    def __init__(self) -> None:
        self.play_calls: list[tuple[str, Any, int, int, int]] = []
        self.stop_calls: list[str] = []
        self.volume_calls: list[tuple[str, float]] = []

    def play(
        self,
        channel: str,
        sound: Any,
        *,
        loops: int = 0,
        maxtime: int = 0,
        fade_ms: int = 0,
    ) -> None:
        self.play_calls.append((channel, sound, loops, maxtime, fade_ms))

    def stop(self, channel: str) -> None:
        self.stop_calls.append(channel)

    def set_volume(self, channel: str, volume: float) -> None:
        self.volume_calls.append((channel, volume))


class HotReloadControllerDouble:
    def __init__(self) -> None:
        self.listeners: list[Callable[[set[Path]], None]] = []

    def add_listener(self, callback: Callable[[set[Path]], None]) -> Callable[[], None]:
        self.listeners.append(callback)

        def _unsubscribe() -> None:
            try:
                self.listeners.remove(callback)
            except ValueError:
                pass

        return _unsubscribe

    def trigger(self, paths: Iterable[Path] | None = None) -> None:
        payload = set(paths) if paths is not None else set()
        for listener in list(self.listeners):
            listener(set(payload))

    def stop(self) -> None:
        self.listeners.clear()


class AssetTestEnv:
    def __init__(self, root: Path) -> None:
        self.asset_root = root / "assets"
        self.asset_root.mkdir(parents=True, exist_ok=True)
        self.image_path = self._write_placeholder("images/ui-buttons.png")
        self.font_path = self._write_placeholder("fonts/TestFont.ttf")
        self.sound_path = self._write_placeholder("sounds/click.wav")

        manifest = {
            "assets": {
                "images": [
                    {
                        "name": "ui-buttons.png",
                        "logical_name": "ui.buttons",
                        "path": "images/ui-buttons.png",
                        "category": "images",
                        "size": 128,
                        "width": 16,
                        "height": 8,
                    }
                ],
                "fonts": [
                    {
                        "name": "TestFont.ttf",
                        "logical_name": "MicropolisSans",
                        "path": "fonts/TestFont.ttf",
                        "category": "fonts",
                        "size": 1024,
                        "aliases": ["MicropolisBody"],
                    }
                ],
                "sounds": [
                    {
                        "name": "click.wav",
                        "logical_name": "ui.click",
                        "path": "sounds/click.wav",
                        "category": "sounds",
                        "size": 512,
                        "legacy_name": "Click",
                    }
                ],
            },
            "stats": {},
        }

        self.manifest_path = root / "manifest.json"
        self.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.manager = AssetManager(
            manifest_path=self.manifest_path, asset_root=self.asset_root
        )
        self.image_loader = ImageLoaderSpy()
        self.sound_loader = SoundLoaderSpy()
        self.font_loader = lambda path, size: (path, size)
        self.router = DummyRouter()
        self.service = AssetService(
            asset_manager=self.manager,
            image_loader=self.image_loader,
            font_loader=self.font_loader,
            sound_loader=self.sound_loader,
            sound_router=self.router,  # type: ignore[arg-type]
        )

    def _write_placeholder(self, relative_path: str) -> Path:
        path = self.asset_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"placeholder")
        return path


@pytest.fixture
def asset_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[AssetTestEnv]:
    env = AssetTestEnv(tmp_path)
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: True)
    try:
        yield env
    finally:
        env.service.close()


def test_load_image_caches_and_slices(asset_env: AssetTestEnv) -> None:
    spec = SpriteSheetSpec(frame_width=8, frame_height=4, columns=2, rows=2)
    sheet = asset_env.service.load_sprite_sheet("ui.buttons", spec)
    assert len(sheet.frames) == 4
    assert asset_env.image_loader.calls == 1

    # Cache hit returns the same SpriteSheet instance
    cached = asset_env.service.load_sprite_sheet("ui.buttons", spec)
    assert cached is sheet

    sprite = asset_env.service.get_sprite("ui.buttons", spec, 1)
    assert sprite.get_size() == (8, 4)


def test_theme_service_loads_config_and_fonts(
    asset_env: AssetTestEnv, tmp_path: Path
) -> None:
    config_path = tmp_path / "themes.json"
    config = {
        "font_aliases": {"Body": "MicropolisSans"},
        "themes": {
            "MicropolisDark": {
                "palette": {"background": [10, 20, 30, 255]},
                "metrics": {"font_name": "Body", "font_size": 19},
            }
        },
        "active": "MicropolisDark",
    }
    config_path.write_text(json.dumps(config), encoding="utf-8")

    manager = ThemeManager()
    theme_service = ThemeService(
        asset_env.service, theme_manager=manager, config_path=config_path
    )

    theme = theme_service.get_theme("MicropolisDark")
    assert theme.palette.background == (10, 20, 30, 255)

    font_instance = theme_service.font(size=24)
    assert font_instance == (str(asset_env.font_path), 24)
    assert "body" in asset_env.service.font_aliases()


def test_asset_service_play_sound_uses_router(asset_env: AssetTestEnv) -> None:
    asset_env.service.play_sound("mode", "ui.click", loops=2)
    assert asset_env.sound_loader.paths == [str(asset_env.sound_path)]
    assert asset_env.router.play_calls == [
        ("mode", {"path": str(asset_env.sound_path)}, 2, 0, 0)
    ]


def test_sound_router_maps_named_channels() -> None:
    class DummyChannel:
        def __init__(self) -> None:
            self.play_args: list[tuple[Any, int, int, int]] = []
            self.stopped = False
            self.volumes: list[float] = []

        def play(
            self,
            sound: Any,
            loops: int = 0,
            maxtime: int = 0,
            fade_ms: int = 0,
        ) -> None:
            self.play_args.append((sound, loops, maxtime, fade_ms))

        def stop(self) -> None:
            self.stopped = True

        def set_volume(self, volume: float) -> None:
            self.volumes.append(volume)

    class DummyMixer:
        def __init__(self) -> None:
            self._channels: dict[int, DummyChannel] = {}
            self._channel_count = 0

        def get_init(self) -> bool:
            return True

        def get_num_channels(self) -> int:
            return self._channel_count

        def set_num_channels(self, count: int) -> None:
            self._channel_count = count

        def Channel(self, index: int) -> DummyChannel:  # noqa: N802 (matching pygame API)
            return self._channels.setdefault(index, DummyChannel())

    mixer = DummyMixer()
    router = SoundRouter(mixer_module=mixer, channels={"city": 3}, max_channels=4)
    sound = object()

    router.play("city", sound, loops=1, maxtime=500, fade_ms=10)
    channel = mixer._channels[3]
    assert channel.play_args == [(sound, 1, 500, 10)]

    router.set_volume("city", 0.25)
    assert channel.volumes[-1] == 0.25

    router.stop("city")
    assert channel.stopped


def test_asset_service_hot_reload_clears_cache(asset_env: AssetTestEnv) -> None:
    controller = HotReloadControllerDouble()
    service = AssetService(
        asset_manager=asset_env.manager,
        image_loader=asset_env.image_loader,
        font_loader=asset_env.font_loader,
        sound_loader=asset_env.sound_loader,
        sound_router=asset_env.router,  # type: ignore[arg-type]
        hot_reload_controller=controller,
    )
    try:
        service.load_image("ui.buttons")
        assert asset_env.image_loader.calls == 1

        controller.trigger({asset_env.image_path})
        service.load_image("ui.buttons")
        assert asset_env.image_loader.calls == 2
    finally:
        service.close()


def test_asset_service_env_flag_enables_hot_reload(
    asset_env: AssetTestEnv, monkeypatch: pytest.MonkeyPatch
) -> None:
    controller = HotReloadControllerDouble()
    captured: dict[str, tuple[float, bool]] = {}

    def fake_create_hot_reload_controller(
        *,
        poll_interval: float = 0.5,
        auto_start: bool = True,
        logger: Any | None = None,
    ) -> HotReloadControllerDouble:
        captured["args"] = (poll_interval, auto_start)
        return controller

    monkeypatch.setenv("MICROPOLIS_ASSET_HOT_RELOAD", "yes")
    monkeypatch.setattr(
        asset_env.manager,
        "create_hot_reload_controller",
        fake_create_hot_reload_controller,
    )

    service = AssetService(
        asset_manager=asset_env.manager,
        image_loader=asset_env.image_loader,
        font_loader=asset_env.font_loader,
        sound_loader=asset_env.sound_loader,
        sound_router=asset_env.router,  # type: ignore[arg-type]
    )
    try:
        assert captured["args"] == (0.5, True)
        assert controller.listeners, (
            "listener should be registered when hot reload is enabled"
        )
    finally:
        service.close()
        monkeypatch.delenv("MICROPOLIS_ASSET_HOT_RELOAD", raising=False)
