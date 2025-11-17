"""Tests for the manifest-backed asset manager."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from micropolis.asset_manager import (
    AssetManager,
    AssetManifestMissingError,
)


def _write_file(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"data")


def _write_manifest(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle)


def test_asset_manager_indexes_logical_and_legacy_names(tmp_path: Path) -> None:
    asset_root = tmp_path / "assets"
    _write_file(asset_root, "images/airport.png")
    _write_file(asset_root, "dejavu/DejaVu.ttf")
    _write_file(asset_root, "sounds/click.wav")
    _write_file(asset_root, "hexa.388")

    manifest = {
        "assets": {
            "images": [
                {
                    "name": "airport.png",
                    "logical_name": "airport",
                    "path": "images/airport.png",
                    "category": "images",
                    "size": 8,
                    "width": 16,
                    "height": 16,
                    "legacy_source": "images/airport.xpm",
                }
            ],
            "fonts": [
                {
                    "name": "DejaVu.ttf",
                    "logical_name": "dejavu",
                    "path": "dejavu/DejaVu.ttf",
                    "category": "fonts",
                    "size": 8,
                    "aliases": ["Dialog", "Micropolis"],
                    "x11_descriptor": "-misc-dejavu-regular-*",
                }
            ],
            "sounds": [
                {
                    "name": "click.wav",
                    "logical_name": "click",
                    "path": "sounds/click.wav",
                    "category": "sounds",
                    "size": 8,
                    "legacy_name": "Click",
                    "legacy_source": "click.aiff",
                }
            ],
            "raw": [
                {
                    "name": "hexa.388",
                    "path": "hexa.388",
                    "category": "raw",
                    "size": 4,
                }
            ],
        },
        "stats": {},
    }

    manifest_path = tmp_path / "manifest.json"
    _write_manifest(manifest_path, manifest)

    manager = AssetManager(manifest_path=manifest_path, asset_root=asset_root)

    assert manager.get_path("airport").name == "airport.png"
    assert manager.get_path("images/airport.xpm").name == "airport.png"
    assert manager.get_path("airport.xpm").name == "airport.png"

    font_path = manager.get_path("Dialog", category="fonts")
    assert font_path is not None
    assert font_path.name == "DejaVu.ttf"

    sound_path = manager.get_path("click")
    assert sound_path is not None
    assert sound_path.name == "click.wav"
    assert manager.get_path("Click").name == "click.wav"

    assert manager.get_path("hexa.388", category="raw").name == "hexa.388"

    record = manager.get_record("airport", category="images")
    assert record is not None
    assert record.metadata["width"] == 16


def test_missing_manifest_raises(tmp_path: Path) -> None:
    missing_manifest = tmp_path / "missing.json"
    with pytest.raises(AssetManifestMissingError):
        AssetManager(manifest_path=missing_manifest, asset_root=tmp_path)


def test_hot_reload_detects_asset_changes(tmp_path: Path) -> None:
    asset_root = tmp_path / "assets"
    _write_file(asset_root, "images/icon.png")
    manifest_path = tmp_path / "manifest.json"
    _write_manifest(
        manifest_path,
        {
            "assets": {
                "images": [
                    {
                        "name": "icon.png",
                        "logical_name": "icon",
                        "path": "images/icon.png",
                        "category": "images",
                        "size": 8,
                    }
                ]
            }
        },
    )

    manager = AssetManager(manifest_path=manifest_path, asset_root=asset_root)
    controller = manager.create_hot_reload_controller(auto_start=False)

    events: list[set[Path]] = []
    controller.add_listener(lambda paths: events.append(paths))
    changed_asset = asset_root / "images/icon.png"
    changes: set[Path] = set()
    try:
        controller.check_now()
        changed_asset.write_bytes(b"updated")
        changes = controller.check_now()
    finally:
        controller.stop()

    assert changed_asset in changes
    assert events and changed_asset in next(iter(events))


def test_hot_reload_refreshes_manifest_on_change(tmp_path: Path) -> None:
    asset_root = tmp_path / "assets"
    _write_file(asset_root, "images/old.png")
    manifest_path = tmp_path / "manifest.json"
    manifest = {
        "assets": {
            "images": [
                {
                    "name": "old.png",
                    "logical_name": "old",
                    "path": "images/old.png",
                    "category": "images",
                    "size": 4,
                }
            ]
        }
    }
    _write_manifest(manifest_path, manifest)

    manager = AssetManager(manifest_path=manifest_path, asset_root=asset_root)
    controller = manager.create_hot_reload_controller(auto_start=False)
    changes: set[Path] = set()
    try:
        controller.check_now()

        _write_file(asset_root, "images/new.png")
        manifest["assets"]["images"].append(
            {
                "name": "new.png",
                "logical_name": "new_icon",
                "path": "images/new.png",
                "category": "images",
                "size": 4,
            }
        )
        _write_manifest(manifest_path, manifest)

        changes = controller.check_now()
    finally:
        controller.stop()

    assert manifest_path in changes
    new_path = manager.get_path("new_icon", category="images")
    assert new_path is not None and new_path.name == "new.png"
