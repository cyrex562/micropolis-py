"""Asset discovery and lookup utilities for the Micropolis pygame port."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event, RLock, Thread
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
ASSET_ROOT = (PROJECT_ROOT / "assets").resolve()
MANIFEST_PATH = ASSET_ROOT / "asset_manifest.json"

HotReloadCallback = Callable[[set[Path]], None]


def _normalize_key(name: str) -> str:
    return name.replace("\\", "/").lower()


class AssetManifestError(RuntimeError):
    """Base exception for manifest-related failures."""


class AssetManifestMissingError(AssetManifestError):
    """Raised when the generated manifest file cannot be found."""

    def __init__(self, manifest_path: Path) -> None:
        super().__init__(
            "Asset manifest not found. Run `uv run python scripts/build_assets.py` "
            "to generate assets/asset_manifest.json before starting the UI."
        )
        self.manifest_path = manifest_path


@dataclass(frozen=True)
class AssetRecord:
    """Metadata describing a single asset entry."""

    name: str
    relative_path: str
    category: str
    size: int
    logical_name: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_path(self, asset_root: Path = ASSET_ROOT) -> Path:
        return (asset_root / self.relative_path).resolve()

    def keys(self) -> set[str]:
        keys = {
            _normalize_key(self.name),
            _normalize_key(self.relative_path),
        }

        if self.logical_name:
            keys.add(_normalize_key(self.logical_name))

        legacy_source = self.metadata.get("legacy_source")
        if isinstance(legacy_source, str):
            keys.add(_normalize_key(legacy_source))
            keys.add(_normalize_key(Path(legacy_source).name))

        legacy_name = self.metadata.get("legacy_name")
        if isinstance(legacy_name, str):
            keys.add(_normalize_key(legacy_name))

        aliases = self.metadata.get("aliases")
        if isinstance(aliases, Iterable):
            for alias in aliases:
                if isinstance(alias, str):
                    keys.add(_normalize_key(alias))

        extra_logical = self.metadata.get("logical_name")
        if isinstance(extra_logical, str):
            keys.add(_normalize_key(extra_logical))

        return {key for key in keys if key}


class AssetManager:
    """Loads `assets/asset_manifest.json` and resolves asset paths by name."""

    def __init__(
        self,
        manifest_path: Path = MANIFEST_PATH,
        *,
        asset_root: Path = ASSET_ROOT,
    ) -> None:
        self._manifest_path = manifest_path
        self._asset_root = asset_root
        self._lock = RLock()
        self._manifest: dict[str, Any] = {}
        self._index: dict[str, list[AssetRecord]] = {}
        self._records_by_category: dict[str, list[AssetRecord]] = {}
        self._records: list[AssetRecord] = []
        self._manifest_mtime: int | None = None
        self.refresh()

    def _load_manifest(self) -> dict:
        if not self._manifest_path.exists():
            raise AssetManifestMissingError(self._manifest_path)
        with self._manifest_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if "assets" not in data:
            raise AssetManifestError(
                f"Manifest {self._manifest_path} is missing the 'assets' key."
            )
        return data

    @staticmethod
    def _record_from_raw(category: str, raw: dict) -> AssetRecord:
        metadata = {
            key: value
            for key, value in raw.items()
            if key not in {"name", "logical_name", "path", "category", "size"}
        }
        return AssetRecord(
            name=raw["name"],
            logical_name=raw.get("logical_name"),
            relative_path=raw["path"],
            category=category.lower(),
            size=raw.get("size", 0),
            metadata=metadata,
        )

    def _build_index(
        self, manifest: dict
    ) -> tuple[
        dict[str, list[AssetRecord]],
        dict[str, list[AssetRecord]],
        list[AssetRecord],
    ]:
        index: dict[str, list[AssetRecord]] = {}
        by_category: dict[str, list[AssetRecord]] = {}
        records: list[AssetRecord] = []

        assets = manifest.get("assets", {})
        for category, raw_records in assets.items():
            for raw in raw_records:
                record = self._record_from_raw(category, raw)
                records.append(record)
                by_category.setdefault(record.category, []).append(record)
                for key in record.keys():
                    index.setdefault(key, []).append(record)

        return index, by_category, records

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """Reload the asset manifest from disk."""

        manifest = self._load_manifest()
        (
            index,
            records_by_category,
            records,
        ) = self._build_index(manifest)
        with self._lock:
            self._manifest = manifest
            self._index = index
            self._records_by_category = records_by_category
            self._records = records
            self._manifest_mtime = self._stat_path(self._manifest_path)

    def get_path(self, name: str, *, category: str | None = None) -> Path | None:
        """Resolve a logical asset name to an on-disk path."""

        key = _normalize_key(name)
        with self._lock:
            candidates = list(self._index.get(key, ()))
        if not candidates:
            return None

        if category is None:
            return candidates[0].to_path(self._asset_root)

        category = category.lower()
        for record in candidates:
            if record.category == category:
                return record.to_path(self._asset_root)
        return None

    def list(self, category: str | None = None) -> Iterable[AssetRecord]:
        """Iterate over manifest records, optionally filtered by category."""

        with self._lock:
            if category is None:
                records = list(self._records)
            else:
                category = category.lower()
                records = list(self._records_by_category.get(category, ()))
        yield from records

    def get_record(
        self, name: str, *, category: str | None = None
    ) -> AssetRecord | None:
        """Return the manifest entry for the provided logical name."""

        key = _normalize_key(name)
        with self._lock:
            candidates = list(self._index.get(key, ()))
        if not candidates:
            return None
        if category is None:
            return candidates[0]
        category = category.lower()
        for record in candidates:
            if record.category == category:
                return record
        return None

    @property
    def manifest_path(self) -> Path:
        return self._manifest_path

    @property
    def asset_root(self) -> Path:
        return self._asset_root

    def snapshot_files(self) -> dict[Path, int | None]:
        """Return a mapping of asset paths to their last modification times."""

        snapshot: dict[Path, int | None] = {
            self._manifest_path: self._stat_path(self._manifest_path)
        }
        with self._lock:
            records = list(self._records)
            asset_root = self._asset_root
        for record in records:
            path = record.to_path(asset_root)
            snapshot[path] = self._stat_path(path)
        return snapshot

    def refresh_if_manifest_changed(self) -> bool:
        """Refresh the manifest if its timestamp differs from the cached copy."""

        current = self._stat_path(self._manifest_path)
        with self._lock:
            previous = self._manifest_mtime
        if current == previous:
            return False
        self.refresh()
        return True

    def create_hot_reload_controller(
        self,
        *,
        poll_interval: float = 0.5,
        auto_start: bool = True,
        logger: Callable[[str], None] | None = None,
    ) -> AssetHotReloadController:
        return AssetHotReloadController(
            self,
            poll_interval=poll_interval,
            auto_start=auto_start,
            logger=logger,
        )

    @staticmethod
    def _stat_path(path: Path) -> int | None:
        try:
            return path.stat().st_mtime_ns
        except FileNotFoundError:
            return None


class AssetHotReloadController:
    """Poll-based watcher that notifies listeners when assets change."""

    def __init__(
        self,
        asset_manager: AssetManager,
        *,
        poll_interval: float = 0.5,
        auto_start: bool = True,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        self._asset_manager = asset_manager
        self._poll_interval = max(0.1, poll_interval)
        self._logger = logger
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._lock = RLock()
        self._listeners: dict[int, HotReloadCallback] = {}
        self._next_token = 0
        self._snapshot = asset_manager.snapshot_files()
        if auto_start:
            self.start()

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = Thread(
                target=self._run,
                name="AssetHotReload",
                daemon=True,
            )
            self._thread.start()

    def stop(self, *, wait: bool = True, timeout: float | None = None) -> None:
        self._stop_event.set()
        thread = self._thread
        if wait and thread and thread.is_alive():
            thread.join(timeout)
        self._thread = None

    def is_running(self) -> bool:
        thread = self._thread
        return bool(thread and thread.is_alive())

    def add_listener(self, callback: HotReloadCallback) -> Callable[[], None]:
        with self._lock:
            token = self._next_token
            self._next_token += 1
            self._listeners[token] = callback

        def _unsubscribe() -> None:
            with self._lock:
                self._listeners.pop(token, None)

        return _unsubscribe

    def check_now(self) -> set[Path]:
        """Run a single change-detection pass, notifying listeners if needed."""

        try:
            self._asset_manager.refresh_if_manifest_changed()
        except AssetManifestError as exc:  # pragma: no cover - diagnostic path
            self._log(f"Asset hot-reload refresh failed: {exc}")
            return set()

        snapshot = self._asset_manager.snapshot_files()
        changed = self._diff_snapshot(snapshot)
        if changed:
            self._notify(changed)
        return changed

    def _run(self) -> None:
        while not self._stop_event.wait(self._poll_interval):
            try:
                self.check_now()
            except Exception as exc:  # pragma: no cover - defensive
                self._log(f"Asset hot-reload loop error: {exc}")

    def _diff_snapshot(self, new_snapshot: dict[Path, int | None]) -> set[Path]:
        with self._lock:
            previous = self._snapshot
            changed: set[Path] = {
                path
                for path, mtime in new_snapshot.items()
                if previous.get(path) != mtime
            }
            removed = set(previous.keys()) - set(new_snapshot.keys())
            changed.update(removed)
            self._snapshot = new_snapshot
        return changed

    def _notify(self, changed: set[Path]) -> None:
        with self._lock:
            listeners = list(self._listeners.values())
        for callback in listeners:
            try:
                callback(set(changed))
            except Exception as exc:  # pragma: no cover - defensive
                self._log(f"Asset hot-reload listener error: {exc}")

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger(message)


# Shared singleton used throughout the codebase.
asset_manager = AssetManager()


def get_asset_path(name: str, *, category: str | None = None) -> Path | None:
    """Convenience wrapper mirroring the legacy `get_resource_path` helper."""

    return asset_manager.get_path(name, category=category)
