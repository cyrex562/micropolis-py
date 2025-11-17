"""Asset conversion and manifest generation utility.

This script converts legacy Micropolis assets (XPM sprites, font aliases,
legacy Tcl sound definitions) into pygame-friendly formats and emits
`assets/asset_manifest.json` so the runtime can load resources without
hard-coded paths.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from PIL import Image, ImageColor

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = PROJECT_ROOT / "assets"
IMAGES_ROOT = ASSET_ROOT / "images"
SOUNDS_ROOT = ASSET_ROOT / "sounds"
FONTS_ROOT = ASSET_ROOT / "dejavu-lgc"
MANIFEST_PATH = ASSET_ROOT / "asset_manifest.json"
SOUND_TCL = ASSET_ROOT / "sound.tcl"

SOUND_REGEX = re.compile(
    r"^sound\s+file\s+([A-Za-z0-9\-]+)\s+\$ResourceDir/([A-Za-z0-9_.\-]+)"
)


@dataclass
class BuildStats:
    converted_images: int = 0
    skipped_images: int = 0
    failed_images: list[str] = field(default_factory=list)


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _convert_16bit_to_8bit(value: int) -> int:
    return max(0, min(255, (value + 128) // 257))


def parse_color_token(color_value: str) -> tuple[int, int, int, int]:
    if color_value.lower() == "none":
        return (0, 0, 0, 0)

    lowered = color_value.lower()
    for prefix in ("gray", "grey"):
        if lowered.startswith(prefix) and lowered[len(prefix) :].isdigit():
            pct = int(lowered[len(prefix) :])
            pct = max(0, min(100, pct))
            channel = round(pct * 255 / 100)
            return (channel, channel, channel, 255)

    try:
        return cast(
            tuple[int, int, int, int],
            ImageColor.getcolor(color_value, "RGBA"),
        )
    except ValueError:
        pass

    if color_value.startswith("#"):
        hex_body = color_value[1:]
        if len(hex_body) == 12:  # #RRRRGGGGBBBB format
            r = int(hex_body[0:4], 16)
            g = int(hex_body[4:8], 16)
            b = int(hex_body[8:12], 16)
            return (
                _convert_16bit_to_8bit(r),
                _convert_16bit_to_8bit(g),
                _convert_16bit_to_8bit(b),
                255,
            )

    raise ValueError(f"unknown color specifier: '{color_value}'")


def extract_xpm_strings(path: Path) -> list[str]:
    strings: list[str] = []
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("/*") or line.startswith("//"):
                continue
            if '"' not in line:
                continue
            start = line.find('"') + 1
            end = line.rfind('"')
            if end <= start:
                continue
            strings.append(line[start:end])
    if not strings:
        raise ValueError(f"No XPM data found in {path}")
    return strings


def render_xpm(path: Path) -> Image.Image:
    strings = extract_xpm_strings(path)
    try:
        width, height, ncolors, cpp = map(int, strings[0].split())
    except ValueError as exc:  # pragma: no cover - invalid XPM
        raise ValueError(f"Invalid XPM header in {path}") from exc

    if len(strings) < 1 + ncolors + height:
        raise ValueError(f"Truncated XPM file: {path}")

    palette: dict[str, tuple[int, int, int, int]] = {}
    for line in strings[1 : 1 + ncolors]:
        key = line[:cpp]
        spec = line[cpp:].strip()
        tokens = spec.split()
        color_value = None
        for idx, token in enumerate(tokens):
            if token == "c" and idx + 1 < len(tokens):
                color_value = tokens[idx + 1]
                break
        if color_value is None:
            raise ValueError(f"Missing color spec in {path} line: {line}")
        palette[key] = parse_color_token(color_value)

    pixel_data: list[tuple[int, int, int, int]] = []
    for line in strings[1 + ncolors : 1 + ncolors + height]:
        if len(line) < width * cpp:
            raise ValueError(f"Incomplete pixel row in {path}")
        for col in range(width):
            key = line[col * cpp : (col + 1) * cpp]
            try:
                pixel_data.append(palette[key])
            except KeyError as exc:
                raise ValueError(f"Unknown color key '{key}' in {path}") from exc

    image = Image.new("RGBA", (width, height))
    image.putdata(pixel_data)
    return image


def convert_images(force: bool, stats: BuildStats) -> None:
    if not IMAGES_ROOT.exists():
        return

    for xpm_path in sorted(IMAGES_ROOT.rglob("*.xpm")):
        png_path = xpm_path.with_suffix(".png")
        if (
            not force
            and png_path.exists()
            and png_path.stat().st_mtime >= xpm_path.stat().st_mtime
        ):
            stats.skipped_images += 1
            continue

        png_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if xpm_path.stat().st_size == 0:
                Image.new("RGBA", (1, 1)).save(png_path)
            else:
                render_xpm(xpm_path).save(png_path)
            stats.converted_images += 1
        except Exception as exc:  # pragma: no cover - diagnostic path
            stats.failed_images.append(f"{xpm_path.relative_to(ASSET_ROOT)}: {exc}")
            continue


def build_image_records() -> list[dict]:
    records: list[dict] = []
    if not IMAGES_ROOT.exists():
        return records

    for png_path in sorted(IMAGES_ROOT.rglob("*.png")):
        rel = png_path.relative_to(ASSET_ROOT).as_posix()
        with Image.open(png_path) as img:
            width, height = img.size
        record = {
            "name": png_path.name,
            "logical_name": png_path.stem.lower(),
            "path": rel,
            "category": "images",
            "size": png_path.stat().st_size,
            "width": width,
            "height": height,
        }
        source = png_path.with_suffix(".xpm")
        if source.exists():
            record["legacy_source"] = source.relative_to(ASSET_ROOT).as_posix()
        records.append(record)
    return records


def parse_font_descriptors(descriptor_file: Path) -> dict[str, Path]:
    desc_map: dict[str, Path] = {}
    if not descriptor_file.exists():
        return desc_map

    with descriptor_file.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()

    for line in lines[1:]:  # skip count header
        line = line.strip()
        if not line:
            continue
        try:
            file_name, descriptor = line.split(" ", 1)
        except ValueError:
            continue
        desc_map[descriptor.strip()] = FONTS_ROOT / file_name
    return desc_map


def parse_font_aliases(descriptor_map: dict[str, Path]) -> dict[Path, list[str]]:
    alias_map: dict[Path, list[str]] = defaultdict(list)
    alias_file = FONTS_ROOT / "fonts.alias"
    if not alias_file.exists():
        return alias_map

    with alias_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("!"):
                continue
            parts = shlex.split(line)
            if len(parts) != 2:
                continue
            alias, target = parts
            target_path = descriptor_map.get(target)
            if not target_path:
                continue
            alias_map[target_path].append(alias)
    return alias_map


def build_font_records() -> list[dict]:
    records: list[dict] = []
    if not FONTS_ROOT.exists():
        return records

    descriptor_map = parse_font_descriptors(FONTS_ROOT / "fonts.dir")
    alias_map = parse_font_aliases(descriptor_map)

    for font_path in sorted(FONTS_ROOT.glob("*.ttf")):
        rel = font_path.relative_to(ASSET_ROOT).as_posix()
        descriptor = next(
            (desc for desc, path in descriptor_map.items() if path == font_path),
            None,
        )
        record: dict[str, object] = {
            "name": font_path.name,
            "logical_name": font_path.stem.lower(),
            "path": rel,
            "category": "fonts",
            "size": font_path.stat().st_size,
        }
        if descriptor:
            record["x11_descriptor"] = descriptor
        aliases = alias_map.get(font_path)
        if aliases:
            record["aliases"] = sorted(aliases)
        records.append(record)
    return records


def parse_sound_definitions() -> dict[str, str]:
    mapping: dict[str, str] = {}
    if not SOUND_TCL.exists():
        return mapping

    with SOUND_TCL.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            match = SOUND_REGEX.match(line)
            if not match:
                continue
            legacy_name, legacy_path = match.groups()
            mapping[legacy_name] = legacy_path
    return mapping


def build_sound_records() -> list[dict]:
    records: list[dict] = []
    if not SOUNDS_ROOT.exists():
        return records

    legacy = parse_sound_definitions()
    audio_lookup = {
        slugify(audio.stem): audio for audio in sorted(SOUNDS_ROOT.glob("*.wav"))
    }

    for name, legacy_path in legacy.items():
        slug = slugify(name)
        actual_path = audio_lookup.get(slug)
        if not actual_path:
            continue
        rel = actual_path.relative_to(ASSET_ROOT).as_posix()
        record = {
            "name": actual_path.name,
            "logical_name": slug,
            "legacy_name": name,
            "path": rel,
            "category": "sounds",
            "size": actual_path.stat().st_size,
            "legacy_source": legacy_path,
        }
        records.append(record)

    known_sound_paths = {record["path"] for record in records}
    for audio_path in sorted(SOUNDS_ROOT.glob("*.wav")):
        rel = audio_path.relative_to(ASSET_ROOT).as_posix()
        if rel in known_sound_paths:
            continue
        records.append(
            {
                "name": audio_path.name,
                "logical_name": slugify(audio_path.stem),
                "path": rel,
                "category": "sounds",
                "size": audio_path.stat().st_size,
            }
        )

    return records


def build_raw_records(known_paths: set[str]) -> list[dict]:
    records: list[dict] = []
    for file_path in sorted(ASSET_ROOT.rglob("*")):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(ASSET_ROOT).as_posix()
        if rel in known_paths or file_path.name == MANIFEST_PATH.name:
            continue
        records.append(
            {
                "name": file_path.name,
                "path": rel,
                "category": "raw",
                "size": file_path.stat().st_size,
            }
        )
    return records


def generate_manifest(
    force_images: bool, *, run_conversions: bool = True
) -> tuple[dict, BuildStats]:
    stats = BuildStats()
    if run_conversions:
        convert_images(force_images, stats)

    image_records = build_image_records()
    font_records = build_font_records()
    sound_records = build_sound_records()

    known_paths = {
        record["path"] for record in (*image_records, *font_records, *sound_records)
    }
    raw_records = build_raw_records(known_paths)

    manifest = {
        "version": 1,
        "generated": datetime.now(UTC).isoformat(),
        "assets": {
            "images": image_records,
            "fonts": font_records,
            "sounds": sound_records,
            "raw": raw_records,
        },
        "stats": {
            "images": len(image_records),
            "fonts": len(font_records),
            "sounds": len(sound_records),
            "raw": len(raw_records),
            "converted_images": stats.converted_images,
            "skipped_images": stats.skipped_images,
            "failed_images": len(stats.failed_images),
        },
    }
    return manifest, stats


def write_manifest(manifest: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force-images",
        action="store_true",
        help="Rebuild PNGs even if they appear up-to-date",
    )
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help=(
            "Skip image conversion (assumes PNGs already exist) "
            "and only rebuild manifest"
        ),
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    force_images = args.force_images and not args.manifest_only

    manifest, stats = generate_manifest(
        force_images=force_images, run_conversions=not args.manifest_only
    )

    if stats.failed_images:
        for failure in stats.failed_images:
            print(f"[ERROR] {failure}")
        raise SystemExit(
            "One or more XPM files could not be converted; see errors above."
        )

    if args.manifest_only:
        print(
            "Generated manifest with"
            f" {manifest['stats']['images']} images (PNG conversion skipped)"
        )
    else:
        print(
            "Converted"
            f" {manifest['stats']['converted_images']} images,"
            f" skipped {manifest['stats']['skipped_images']} up-to-date conversions."
        )

    write_manifest(manifest)
    print(f"Wrote manifest to {MANIFEST_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
