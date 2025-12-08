"""
graphics_setup.py - Graphics initialization for Micropolis Python port

This module handles loading of graphics assets and initialization of display
structures, adapted from g_setup.c for pygame instead of X11/TCL-Tk.
"""

from collections import OrderedDict
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import pygame

from micropolis.asset_manager import get_asset_path
from micropolis.constants import (
    AIR,
    BUS,
    COP,
    DIAG_BITS,
    EXP,
    GOD,
    GRAY25_BITS,
    GRAY50_BITS,
    GRAY75_BITS,
    HORIZ_BITS,
    LIGHTNINGBOLT,
    LOMASK,
    OBJN,
    PWRBIT,
    SHI,
    SIM_GSMTILE,
    STIPPLE_HEIGHT,
    STIPPLE_WIDTH,
    TILE_COUNT,
    TOR,
    TRA,
    VERT_BITS,
    ZONEBIT,
)
from micropolis.context import AppContext
from micropolis.view_types import (
    IsEditorView,
    IsMapView,
    MakeNewXDisplay,
    X_Mem_View,
    X_Wire_View,
    XDisplay,
)

OverlayFilter = Callable[[AppContext, int, int], bool]
ColorLike = tuple[int, int, int] | tuple[int, int, int, int]
ColorStop = tuple[int, tuple[int, int, int, int]]
ColorRamp = tuple[ColorStop, ...]
ColorRampInput = Sequence[tuple[int, ColorLike]]

_TILE_VARIANT_CACHE: OrderedDict[
    tuple[int, tuple[int, int, int, int], str], pygame.Surface
] = OrderedDict()
_VARIANT_CACHE_LIMIT = 256


# ============================================================================
# Graphics Constants (from g_setup.c)
# ============================================================================


# ============================================================================
# Graphics Loading Functions
# ============================================================================


def get_resource_path(filename: str, *, category: str | None = None) -> str:
    """Resolve legacy asset names through the generated manifest."""
    import logging

    logger = logging.getLogger(__name__)

    normalized = filename.lstrip("@")
    logger.debug(
        f"[get_resource_path] Looking for asset: "
        f"filename='{filename}', category={category}, "
        f"normalized='{normalized}'"
    )

    potential = [normalized]
    if category == "images" and not normalized.startswith("images/"):
        potential.append(f"images/{normalized}")
        logger.debug(f"[get_resource_path] Added image path variant: {potential[-1]}")

    candidate_path = Path(normalized)
    if candidate_path.is_absolute():
        logger.debug(f"[get_resource_path] Using absolute path: {candidate_path}")
        return str(candidate_path)

    for candidate in potential:
        logger.debug(f"[get_resource_path] Trying candidate: '{candidate}'")
        resolved = get_asset_path(candidate, category=category)
        if resolved is not None:
            logger.info(f"[get_resource_path] ✓ Resolved '{filename}' → '{resolved}'")
            return str(resolved)
        else:
            logger.debug(
                f"[get_resource_path] ✗ Candidate '{candidate}' not found in manifest"
            )

    error_msg = (
        f"Asset '{filename}' (category={category}) was not found in asset_manifest.json"
    )
    logger.error(f"[get_resource_path] {error_msg}")
    raise FileNotFoundError(error_msg)


def load_xpm_surface(filename: str) -> Any | None:
    """
    Load an XPM file as a pygame surface.

    Args:
        filename: Name of the XPM file to load

    Returns:
        pygame Surface if successful, None if failed
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.debug(f"[load_xpm_surface] Attempting to load: {filename}")
        filepath = get_resource_path(filename, category="images")
        logger.debug(f"[load_xpm_surface] Resolved path: {filepath}")

        # Verify file exists before loading
        if not Path(filepath).exists():
            logger.error(f"[load_xpm_surface] ✗ File not found: {filepath}")
            return None

        surface = pygame.image.load(filepath)
        logger.info(
            f"[load_xpm_surface] ✓ Successfully loaded {filename} "
            f"({surface.get_width()}x{surface.get_height()})"
        )
        return surface
    except (pygame.error, FileNotFoundError) as e:
        logger.error(f"[load_xpm_surface] ✗ Failed to load XPM file {filename}: {e}")
        return None


def load_hexa_resource(resource_id: int) -> bytes | None:
    """
    Load a hexa resource file.

    Ported from MickGetHexa() in g_setup.c.

    Args:
        resource_id: The resource ID (e.g., SIM_GSMTILE = 388)

    Returns:
        Raw bytes from the hexa file, or None if failed
    """
    filename = f"hexa.{resource_id}"
    filepath = get_resource_path(filename, category="raw")

    try:
        with open(filepath, "rb") as f:
            return f.read()
    except OSError as e:
        print(f"Warning: Failed to load hexa resource {resource_id}: {e}")
        return None


def create_small_tiles_surface() -> Any | None:
    """
    Create a pygame surface for small tiles (map view) from hexa resource.

    Ported from the monochrome small tiles loading in GetViewTiles().

    Returns:
        pygame Surface containing small tile data, or None if failed
    """
    # Load the hexa resource for small tiles
    hexa_data = load_hexa_resource(SIM_GSMTILE)
    if hexa_data is None:
        return None

    # The hexa data is 4 pixels wide × 3 pixels high × TILE_COUNT tiles
    # We need to convert this to 4×4 pixels per tile with padding
    expected_size = 4 * 3 * TILE_COUNT  # 11520
    if len(hexa_data) < expected_size:
        print(
            "Warning: Hexa data too small "
            f"{len(hexa_data)}, expected at least {expected_size}"
        )
        return None

    # Use only the expected amount of data, ignore any extra
    actual_data = hexa_data[:expected_size]

    try:
        # Create surface for 4×4 tiles: TILE_COUNT tiles × 4×4 pixels × 4 bytes per
        # pixel (RGBA)
        surface_width = 4  # 4 pixels per tile
        surface_height = 4 * TILE_COUNT  # 4 pixels high per tile × TILE_COUNT tiles

        surface = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)

        # Process each tile
        data_index = 0
        for tile in range(TILE_COUNT):
            # Read 3 rows of 4 pixels each from hexa data
            for y in range(3):
                for x in range(4):
                    if data_index < len(actual_data):
                        pixel_value = actual_data[data_index]
                        # Convert grayscale to RGBA
                        color = (pixel_value, pixel_value, pixel_value, 255)
                        surface.set_at((x, tile * 4 + y), color)
                        data_index += 1

            # Add padding row (4th row is transparent)
            for x in range(4):
                surface.set_at((x, tile * 4 + 3), (0, 0, 0, 0))

        return surface

    except Exception as e:
        print(f"Error creating small tiles surface: {e}")
        return None


def load_big_tiles_surface(color: bool = True) -> Any | None:
    """
    Load big tiles surface for editor view.

    This would normally load from tiles.xpm or tilesbw.xpm, but since we don't have
    those files, we'll create a placeholder surface for now.

    Args:
        color: Whether to load color or monochrome tiles

    Returns:
        pygame Surface for big tiles, or None if failed
    """
    import logging

    logger = logging.getLogger(__name__)

    logger.debug(
        f"[load_big_tiles_surface] Creating placeholder surface, color={color}"
    )

    try:
        # For now, create a placeholder surface
        # Big tiles are 16×16 pixels per tile
        tiles_per_row = 16  # Assume tiles are arranged in a grid
        rows = (TILE_COUNT + tiles_per_row - 1) // tiles_per_row

        surface_width = tiles_per_row * 16
        surface_height = rows * 16

        logger.debug(
            f"[load_big_tiles_surface] Creating placeholder: "
            f"{surface_width}x{surface_height} "
            f"({tiles_per_row}x{rows} tiles)"
        )

        surface = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)

        # Fill with a placeholder pattern (checkerboard)
        for tile_y in range(rows):
            for tile_x in range(tiles_per_row):
                tile_index = tile_y * tiles_per_row + tile_x
                if tile_index >= TILE_COUNT:
                    break

                # Create a simple colored rectangle for each tile
                color_value = (tile_index * 7) % 256  # Vary color based on tile index
                tile_color = (
                    color_value,
                    (color_value + 85) % 256,
                    (color_value + 170) % 256,
                    255,
                )

                pygame.draw.rect(
                    surface, tile_color, (tile_x * 16, tile_y * 16, 16, 16)
                )

        logger.info(
            f"[load_big_tiles_surface] ✓ Created placeholder surface "
            f"with {TILE_COUNT} tiles"
        )
        return surface

    except Exception as e:
        logger.exception(
            f"[load_big_tiles_surface] ✗ Error creating big tiles surface: {e}"
        )
        return None


def create_stipple_surface(
    bits: bytes, width: int = STIPPLE_WIDTH, height: int = STIPPLE_HEIGHT
) -> Any | None:
    """
    Create a pygame surface from stipple pattern bits.

    Args:
        bits: Bitmap data as bytes
        width: Width of the stipple pattern
        height: Height of the stipple pattern

    Returns:
        pygame Surface with the stipple pattern
    """
    try:
        # Create a surface for the stipple pattern
        surface = pygame.Surface((width, height), pygame.SRCALPHA)

        # Convert bitmap data to surface pixels
        # Each byte represents 8 pixels (1 bit per pixel)
        for y in range(height):
            for x in range(0, width, 8):
                if y * (width // 8) + (x // 8) < len(bits):
                    byte_val = bits[y * (width // 8) + (x // 8)]
                    for bit in range(8):
                        if x + bit < width:
                            pixel_value = 255 if (byte_val & (1 << (7 - bit))) else 0
                            surface.set_at(
                                (x + bit, y),
                                (pixel_value, pixel_value, pixel_value, 255),
                            )

        return surface
    except Exception as e:
        print(f"Warning: Failed to create stipple surface: {e}")
        return None


def get_object_surfaces(object_id: int, frames: int) -> list[Any] | None:
    """
    Load object sprite surfaces for a given object type.

    Ported from GetObjectXpms() in g_setup.c.

    Args:
        object_id: Object type ID (TRA, COP, AIR, etc.)
        frames: Number of animation frames

    Returns:
        List of pygame surfaces for the object, or None if failed
    """
    surfaces = []

    # Map object IDs to filename patterns
    object_names = {
        TRA: "obj1",  # Train
        COP: "obj2",  # Police helicopter
        AIR: "obj3",  # Airplanes
        SHI: "obj4",  # Ships
        GOD: "obj5",  # God
        TOR: "obj6",  # Tornado
        EXP: "obj7",  # Explosion
        BUS: "obj8",  # Bus
    }

    if object_id not in object_names:
        print(f"Warning: Unknown object ID {object_id}")
        return None

    base_name = object_names[object_id]

    for frame in range(frames):
        filename = f"{base_name}-{frame}.xpm"
        surface = load_xpm_surface(filename)
        if surface is None:
            print(f"Warning: Failed to load object {base_name} frame {frame}")
            return None
        surfaces.append(surface)

    return surfaces


def get_pixmaps(display: XDisplay) -> None:
    """
    Initialize pixmaps and stipple patterns for the display.

    Ported from GetPixmaps() in g_setup.c.

    Args:
        display: XDisplay structure to initialize
    """

    # Create stipple patterns if not already created
    if display.gray25_stipple is None:
        display.gray25_stipple = create_stipple_surface(GRAY25_BITS)
        display.gray50_stipple = create_stipple_surface(GRAY50_BITS)
        display.gray75_stipple = create_stipple_surface(GRAY75_BITS)
        display.vert_stipple = create_stipple_surface(VERT_BITS)
        display.horiz_stipple = create_stipple_surface(HORIZ_BITS)
        display.diag_stipple = create_stipple_surface(DIAG_BITS)

    # Load object sprites if not already loaded
    if display.objects is None:
        display.objects = []  # Initialize as empty list
        for _ in range(OBJN):
            display.objects.append(None)  # Add None for each object slot

        # Load sprites for each object type with their frame counts
        object_frames = {
            TRA: 5,  # Train: 5 frames
            COP: 8,  # Police helicopter: 8 frames
            AIR: 11,  # Airplanes: 11 frames
            SHI: 8,  # Ships: 8 frames
            GOD: 16,  # God: 16 frames
            TOR: 3,  # Tornado: 3 frames
            EXP: 6,  # Explosion: 6 frames
            BUS: 4,  # Bus: 4 frames
        }

        for obj_id, frames in object_frames.items():
            surfaces = get_object_surfaces(obj_id, frames)
            if surfaces is not None:
                display.objects[obj_id] = surfaces
            else:
                print(f"Warning: Failed to load sprites for object {obj_id}")


def get_view_tiles(view: Any) -> None:
    """
    Load tile graphics for a view.

    Ported from GetViewTiles() in g_setup.c.

    Args:
        view: View structure to initialize with tiles
    """
    import logging

    logger = logging.getLogger(__name__)

    # Determine if this is an editor or map view by checking class_id directly
    # Editor_Class = 0, Map_Class = 1
    from .view_types import Editor_Class, Map_Class

    is_editor = view.class_id == Editor_Class
    is_map = view.class_id == Map_Class

    logger.info(
        f"[get_view_tiles] Loading tiles for view: "
        f"class_id={view.class_id}, is_editor={is_editor}, "
        f"is_map={is_map}, type={view.type}"
    )

    if is_editor:
        logger.debug("[get_view_tiles] Loading tiles for EDITOR view")
        # Load tiles for editor view (16x16 pixels per tile)
        if view.type == X_Mem_View:
            logger.debug("[get_view_tiles] Editor view type: X_Mem_View")
            if view.x.big_tile_image is None:
                # Try to load from XPM first, then fall back to generated surface
                tiles_filename = "tiles.png" if view.x.color else "tilesbw.png"
                logger.info(
                    f"[get_view_tiles] Loading big tile image: {tiles_filename}"
                )
                view.x.big_tile_image = load_xpm_surface(tiles_filename)

                if view.x.big_tile_image is None:
                    logger.warning(
                        "[get_view_tiles] Failed to load tiles.png, using placeholder"
                    )
                    # Fall back to generated placeholder surface
                    view.x.big_tile_image = load_big_tiles_surface(view.x.color)

                if view.x.big_tile_image is None:
                    logger.error("[get_view_tiles] ✗ Failed to load big tile image")
                    return
                else:
                    logger.info(
                        f"[get_view_tiles] ✓ Loaded big tile image: "
                        f"{view.x.big_tile_image.get_width()}x"
                        f"{view.x.big_tile_image.get_height()}"
                    )
            else:
                logger.debug("[get_view_tiles] Big tile image already loaded")

            # Extract tile data from the surface
            view.bigtiles = view.x.big_tile_image
            logger.debug("[get_view_tiles] Set view.bigtiles from big_tile_image")

        elif view.type == X_Wire_View:
            logger.debug("[get_view_tiles] Editor view type: X_Wire_View")
            if view.x.big_tile_pixmap is None:
                tiles_filename = "tiles.png" if view.x.color else "tilesbw.png"
                logger.info(
                    f"[get_view_tiles] Loading big tile pixmap: {tiles_filename}"
                )
                view.x.big_tile_pixmap = load_xpm_surface(tiles_filename)

                if view.x.big_tile_pixmap is None:
                    logger.warning(
                        "[get_view_tiles] Failed to load tiles.png, using placeholder"
                    )
                    # Fall back to generated placeholder surface
                    view.x.big_tile_pixmap = load_big_tiles_surface(view.x.color)

                if view.x.big_tile_pixmap is None:
                    logger.error("[get_view_tiles] ✗ Failed to load big tile pixmap")
                    return
                else:
                    logger.info(
                        f"[get_view_tiles] ✓ Loaded big tile pixmap: "
                        f"{view.x.big_tile_pixmap.get_width()}x"
                        f"{view.x.big_tile_pixmap.get_height()}"
                    )
            else:
                logger.debug("[get_view_tiles] Big tile pixmap already loaded")

    elif is_map:
        logger.debug("[get_view_tiles] Loading tiles for MAP view")
        # Load tiles for map view (3x3 pixels per tile, expanded to 4x4)
        if view.x.small_tile_image is None:
            if view.x.color:
                # Try to load color tiles from XPM
                tiles_filename = "tilessm.png"
                logger.info(
                    f"[get_view_tiles] Loading small tile image: {tiles_filename}"
                )
                view.x.small_tile_image = load_xpm_surface(tiles_filename)

                if view.x.small_tile_image is None:
                    logger.warning(
                        f"[get_view_tiles] Failed to load small tile image "
                        f"{tiles_filename}, using placeholder"
                    )
                    # For now, create a placeholder - the converted asset is not
                    # available yet.
                    view.x.small_tile_image = pygame.Surface(
                        (4, 3 * TILE_COUNT), pygame.SRCALPHA
                    )
                else:
                    logger.info(
                        f"[get_view_tiles] ✓ Loaded small tile image: "
                        f"{view.x.small_tile_image.get_width()}x"
                        f"{view.x.small_tile_image.get_height()}"
                    )

            else:
                # For monochrome, load from hexa resource
                logger.debug("[get_view_tiles] Loading monochrome tiles from hexa")
                hexa_data = load_hexa_resource(SIM_GSMTILE)
                if hexa_data is not None:
                    logger.info(
                        f"[get_view_tiles] ✓ Loaded hexa data: {len(hexa_data)} bytes"
                    )
                    # Create XImage-like structure from hexa data
                    # This mimics the XCreateImage call in the C code
                    view.x.small_tile_image = pygame.Surface(
                        (4, 3 * TILE_COUNT), pygame.SRCALPHA
                    )

                    # Fill surface with hexa data (grayscale)
                    for i, pixel_value in enumerate(hexa_data):
                        x = i % 4
                        y = i // 4
                        if y < 3 * TILE_COUNT:
                            color = (pixel_value, pixel_value, pixel_value, 255)
                            view.x.small_tile_image.set_at((x, y), color)
                    logger.debug(
                        "[get_view_tiles] Filled small_tile_image with hexa data"
                    )
                else:
                    logger.error(
                        "[get_view_tiles] ✗ Failed to load monochrome small tiles"
                    )
                    return
        else:
            logger.debug("[get_view_tiles] Small tile image already loaded")

        # Process the small tile data into 4x4 format
        if view.smalltiles is None:
            logger.debug("[get_view_tiles] Converting small tiles to 4x4 format")
            # Convert 4x3 tiles to 4x4 tiles with padding (matching C code logic)
            pixel_bytes = 4  # RGBA
            source_surface = view.x.small_tile_image

            # Allocate space for 4x4 tiles
            view.smalltiles = bytearray(4 * 4 * TILE_COUNT * pixel_bytes)

            to_index = 0
            for tile in range(TILE_COUNT):
                # Copy 3 rows of 4 pixels each
                for y in range(3):
                    for x in range(4):
                        if source_surface is not None:
                            color = source_surface.get_at((x, tile * 3 + y))
                            # Store as RGBA bytes
                            view.smalltiles[to_index] = color[0]  # R
                            view.smalltiles[to_index + 1] = color[1]  # G
                            view.smalltiles[to_index + 2] = color[2]  # B
                            view.smalltiles[to_index + 3] = color[3]  # A
                        to_index += pixel_bytes

                # Add padding row (4th row is transparent)
                for x in range(4):
                    view.smalltiles[to_index] = 0  # R
                    view.smalltiles[to_index + 1] = 0  # G
                    view.smalltiles[to_index + 2] = 0  # B
                    view.smalltiles[to_index + 3] = 0  # A
                    to_index += pixel_bytes

            logger.info(
                f"[get_view_tiles] ✓ Converted {TILE_COUNT} small tiles "
                f"to 4x4 format ({len(view.smalltiles)} bytes)"
            )
        else:
            logger.debug("[get_view_tiles] Small tiles already in 4x4 format")
    else:
        logger.warning(f"[get_view_tiles] Unknown view class_id: {view.class_id}")


# ============================================================================
# Initialization Functions
# ============================================================================


def init_graphics(context: AppContext) -> bool:
    """
    Initialize the graphics system.

    Returns:
        True if initialization successful, False otherwise
        :param context:
    """

    try:
        # Initialize pygame if not already done
        if not pygame.get_init():
            pygame.init()

        # Get the main display
        if not hasattr(context, "MainDisplay") or context.main_display is None:
            context.main_display = MakeNewXDisplay()

        # Initialize pixmaps for the main display
        get_pixmaps(context.main_display)

        return True

    except Exception as e:
        print(f"Error initializing graphics: {e}")
        return False


def init_view_graphics(view: Any) -> bool:
    """
    Initialize graphics for a specific view.

    Args:
        view: View to initialize graphics for

    Returns:
        True if successful, False otherwise
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info(
            f"[init_view_graphics] Initializing graphics for view: "
            f"class_id={getattr(view, 'class_id', 'unknown')}, "
            f"type={getattr(view, 'type', 'unknown')}"
        )

        # Ensure the view has a display
        if not hasattr(view, "x") or view.x is None:
            logger.error("[init_view_graphics] ✗ View has no display")
            return False

        logger.debug(
            f"[init_view_graphics] View display attributes: "
            f"color={getattr(view.x, 'color', 'unknown')}"
        )

        # Load tiles for this view
        logger.debug("[init_view_graphics] Calling get_view_tiles()...")
        get_view_tiles(view)

        # Verify tiles were loaded
        has_bigtiles = hasattr(view, "bigtiles") and view.bigtiles is not None
        has_smalltiles = hasattr(view, "smalltiles") and view.smalltiles is not None

        logger.info(
            f"[init_view_graphics] ✓ Graphics initialized: "
            f"bigtiles={has_bigtiles}, smalltiles={has_smalltiles}"
        )

        return True

    except Exception as e:
        logger.exception(
            f"[init_view_graphics] ✗ Error initializing view graphics: {e}"
        )
        return False


def cleanup_graphics() -> None:
    """
    Clean up graphics resources.
    """
    # This would free surfaces and other resources
    # For now, pygame cleanup is handled automatically
    pass


# ============================================================================
# Utility Functions
# ============================================================================


def resolve_tile_for_render(
    context: AppContext,
    tile_value: int,
    *,
    coords: tuple[int, int] | None = None,
    blink: bool | None = None,
    overlay_filter: OverlayFilter | None = None,
) -> int:
    """Normalize a raw tile value for rendering with lightning/overlay gating."""

    adjusted = tile_value
    if (adjusted & LOMASK) >= TILE_COUNT:
        adjusted -= TILE_COUNT

    tile_index = adjusted & LOMASK
    blink_state = context.flag_blink <= 0 if blink is None else blink

    if blink_state and (tile_value & ZONEBIT) and not (tile_value & PWRBIT):
        lightning_tile = getattr(context, "LIGHTNINGBOLT", LIGHTNINGBOLT)
        tile_index = lightning_tile

    if overlay_filter and coords and tile_index > 63:
        if not overlay_filter(context, coords[0], coords[1]):
            tile_index = 0

    return _normalize_tile_index(tile_index)


def get_tile_surface(
    tile_id: int,
    view: Any,
    *,
    context: AppContext | None = None,
    coords: tuple[int, int] | None = None,
    blink: bool | None = None,
    overlay_filter: OverlayFilter | None = None,
    treat_input_as_raw: bool = False,
    tint_color: tuple[int, int, int, int] | None = None,
    variant: str | None = None,
    return_tile_index: bool = False,
) -> Any | tuple[Any | None, int]:
    """Return a cached 16×16 tile surface for editor views."""

    if treat_input_as_raw:
        if context is None:
            raise ValueError("context is required when treat_input_as_raw=True")
        tile_index = resolve_tile_for_render(
            context,
            tile_id,
            coords=coords,
            blink=blink,
            overlay_filter=overlay_filter,
        )
    else:
        tile_index = _normalize_tile_index(tile_id)

    sheet = _get_big_tile_sheet(view)
    surface: pygame.Surface | None = None

    if sheet is not None:
        cache = _get_big_tile_cache(view)
        surface = cache.get(tile_index)
        if surface is None:
            tiles_per_row = getattr(view, "_tiles_per_row", None)
            if not tiles_per_row:
                tiles_per_row = max(1, sheet.get_width() // 16)
                setattr(view, "_tiles_per_row", tiles_per_row)

            tile_x = (tile_index % tiles_per_row) * 16
            tile_y = (tile_index // tiles_per_row) * 16
            rect = pygame.Rect(tile_x, tile_y, 16, 16)

            try:
                surface = sheet.subsurface(rect)
                cache[tile_index] = surface
            except ValueError:
                surface = None

    if surface is not None and tint_color and variant:
        surface = _get_tinted_variant_surface(surface, tint_color, variant)

    if return_tile_index:
        return surface, tile_index
    return surface


def get_small_tile_surface(
    tile_id: int,
    view: Any,
    *,
    context: AppContext | None = None,
    coords: tuple[int, int] | None = None,
    blink: bool | None = None,
    overlay_filter: OverlayFilter | None = None,
    treat_input_as_raw: bool = False,
    tint_color: tuple[int, int, int, int] | None = None,
    variant: str | None = None,
    return_tile_index: bool = False,
) -> Any | tuple[Any | None, int]:
    """Return a cached 4×4 tile surface for map/minimap views."""

    if treat_input_as_raw:
        if context is None:
            raise ValueError("context is required when treat_input_as_raw=True")
        tile_index = resolve_tile_for_render(
            context,
            tile_id,
            coords=coords,
            blink=blink,
            overlay_filter=overlay_filter,
        )
    else:
        tile_index = _normalize_tile_index(tile_id)

    sheet = _get_small_tile_sheet(view)
    surface: pygame.Surface | None = None

    if sheet is not None:
        cache = _get_small_tile_cache(view)
        surface = cache.get(tile_index)
        if surface is None:
            rect = pygame.Rect(0, tile_index * 4, 4, 4)
            try:
                surface = sheet.subsurface(rect)
                cache[tile_index] = surface
            except ValueError:
                surface = None

    if surface is not None and tint_color and variant:
        surface = _get_tinted_variant_surface(surface, tint_color, variant)

    if return_tile_index:
        return surface, tile_index
    return surface


def get_small_tile_overlay_surface(
    tile_id: int,
    view: Any,
    *,
    overlay_key: str,
    tint_color: tuple[int, int, int, int] | None = None,
    color_ramp: ColorRampInput | None = None,
    context: AppContext | None = None,
    coords: tuple[int, int] | None = None,
    blink: bool | None = None,
    overlay_filter: OverlayFilter | None = None,
    treat_input_as_raw: bool = False,
    return_tile_index: bool = False,
) -> Any | tuple[Any | None, int]:
    """Return a tinted 4×4 tile surface for a named minimap overlay."""

    if treat_input_as_raw:
        if context is None:
            raise ValueError("context is required when treat_input_as_raw=True")
        tile_index = resolve_tile_for_render(
            context,
            tile_id,
            coords=coords,
            blink=blink,
            overlay_filter=overlay_filter,
        )
    else:
        tile_index = _normalize_tile_index(tile_id)

    overlay_entry = _get_small_tile_overlay_sheet(
        view,
        overlay_key=overlay_key,
        tint_color=tint_color,
        color_ramp=color_ramp,
    )

    surface: pygame.Surface | None = None
    if overlay_entry is not None:
        sheet, cache = overlay_entry
        surface = cache.get(tile_index)
        if surface is None:
            rect = pygame.Rect(0, tile_index * 4, 4, 4)
            try:
                surface = sheet.subsurface(rect)
                cache[tile_index] = surface
            except ValueError:
                surface = None

    if return_tile_index:
        return surface, tile_index
    return surface


def _normalize_tile_index(tile_id: int) -> int:
    if tile_id < 0:
        return 0
    return tile_id % TILE_COUNT


def _get_big_tile_sheet(view: Any) -> pygame.Surface | None:
    sheet = getattr(view, "bigtiles", None)
    if isinstance(sheet, pygame.Surface):
        return sheet

    if hasattr(view, "x") and getattr(view.x, "big_tile_image", None):
        sheet = view.x.big_tile_image
        view.bigtiles = sheet
        return sheet

    return None


def _get_small_tile_sheet(view: Any) -> pygame.Surface | None:
    sheet = getattr(view, "_small_tile_sheet", None)
    if isinstance(sheet, pygame.Surface):
        return sheet

    raw_tiles = getattr(view, "smalltiles", None)
    if raw_tiles:
        buffer = (
            raw_tiles if isinstance(raw_tiles, (bytes, bytearray)) else bytes(raw_tiles)
        )
        sheet = pygame.image.frombuffer(buffer, (4, 4 * TILE_COUNT), "RGBA")
        sheet = sheet.convert_alpha()
        setattr(view, "_small_tile_sheet", sheet)
        return sheet

    image = None
    if hasattr(view, "x") and getattr(view.x, "small_tile_image", None):
        image = view.x.small_tile_image

    if isinstance(image, pygame.Surface):
        sheet = pygame.Surface((4, 4 * TILE_COUNT), pygame.SRCALPHA)
        for tile in range(TILE_COUNT):
            src_rect = pygame.Rect(0, tile * 3, 4, 3)
            dest_rect = pygame.Rect(0, tile * 4, 4, 3)
            sheet.blit(image, dest_rect, src_rect)
        setattr(view, "_small_tile_sheet", sheet)
        return sheet

    return None


def _get_big_tile_cache(view: Any) -> dict[int, pygame.Surface]:
    cache = getattr(view, "_tile_surface_cache", None)
    if cache is None:
        cache = {}
        setattr(view, "_tile_surface_cache", cache)
    return cache


def _get_small_tile_cache(view: Any) -> dict[int, pygame.Surface]:
    cache = getattr(view, "_small_tile_surface_cache", None)
    if cache is None:
        cache = {}
        setattr(view, "_small_tile_surface_cache", cache)
    return cache


def _get_small_tile_overlay_sheet(
    view: Any,
    *,
    overlay_key: str,
    tint_color: tuple[int, int, int, int] | None = None,
    color_ramp: ColorRampInput | None = None,
) -> tuple[pygame.Surface, dict[int, pygame.Surface]] | None:
    sheet = _get_small_tile_sheet(view)
    if sheet is None:
        return None

    overlay_cache = _get_small_tile_overlay_cache(view)
    normalized_ramp = _normalize_color_ramp(color_ramp) if color_ramp else None
    key = _build_overlay_cache_key(sheet, overlay_key, tint_color, normalized_ramp)
    cached = overlay_cache.get(key)
    if cached is not None:
        return cached

    tinted_sheet = sheet.copy()
    if normalized_ramp:
        _apply_color_ramp(tinted_sheet, normalized_ramp)
    elif tint_color:
        tinted_sheet.fill(
            _normalize_tint_color(tint_color), special_flags=pygame.BLEND_RGBA_MULT
        )

    cache_entry = (tinted_sheet, {})
    overlay_cache[key] = cache_entry
    return cache_entry


def _get_small_tile_overlay_cache(
    view: Any,
) -> dict[
    tuple[int, str, tuple[int, int, int, int] | None, ColorRamp | None],
    tuple[pygame.Surface, dict[int, pygame.Surface]],
]:
    cache = getattr(view, "_small_tile_overlay_cache", None)
    if cache is None:
        cache = {}
        setattr(view, "_small_tile_overlay_cache", cache)
    return cache


def _build_overlay_cache_key(
    sheet: pygame.Surface,
    overlay_key: str,
    tint_color: tuple[int, int, int, int] | None,
    color_ramp: ColorRamp | None,
) -> tuple[int, str, tuple[int, int, int, int] | None, ColorRamp | None]:
    normalized_tint = _normalize_tint_color(tint_color) if tint_color else None
    return (id(sheet), overlay_key, normalized_tint, color_ramp)


def _get_tinted_variant_surface(
    base_surface: pygame.Surface, tint_color: tuple[int, int, int, int], variant: str
) -> pygame.Surface:
    normalized = _normalize_tint_color(tint_color)
    key = (id(base_surface), normalized, variant)
    cached = _TILE_VARIANT_CACHE.get(key)
    if cached is not None:
        _TILE_VARIANT_CACHE.move_to_end(key)
        return cached

    tinted = base_surface.copy()
    tinted.fill(normalized, special_flags=pygame.BLEND_RGBA_MULT)
    _TILE_VARIANT_CACHE[key] = tinted
    if len(_TILE_VARIANT_CACHE) > _VARIANT_CACHE_LIMIT:
        _TILE_VARIANT_CACHE.popitem(last=False)

    return tinted


def _normalize_tint_color(color: ColorLike) -> tuple[int, int, int, int]:
    if len(color) == 4:
        return color
    if len(color) == 3:
        return (color[0], color[1], color[2], 255)
    raise ValueError("tint_color must have 3 or 4 components")


def _normalize_color_ramp(color_ramp: ColorRampInput | None) -> ColorRamp:
    if not color_ramp:
        raise ValueError("color_ramp must contain at least one stop")

    normalized: list[ColorStop] = []
    for stop, color in color_ramp:
        clamped_stop = max(0, min(255, int(stop)))
        normalized_color = _normalize_tint_color(color)
        normalized.append((clamped_stop, normalized_color))

    normalized.sort(key=lambda item: item[0])

    if normalized[0][0] != 0:
        normalized.insert(0, (0, normalized[0][1]))
    if normalized[-1][0] != 255:
        normalized.append((255, normalized[-1][1]))

    return tuple(normalized)


def _apply_color_ramp(surface: pygame.Surface, color_ramp: ColorRamp) -> None:
    width, height = surface.get_size()
    buffer = bytearray(pygame.image.tostring(surface, "RGBA"))

    for index in range(0, len(buffer), 4):
        alpha = buffer[index + 3]
        if alpha == 0:
            continue

        intensity = buffer[index]
        color = _sample_color_ramp(intensity, color_ramp)
        buffer[index] = color[0]
        buffer[index + 1] = color[1]
        buffer[index + 2] = color[2]
        buffer[index + 3] = min(255, (color[3] * alpha) // 255)

    recolored = pygame.image.frombuffer(buffer, (width, height), "RGBA")
    surface.blit(recolored, (0, 0))


def _sample_color_ramp(value: int, color_ramp: ColorRamp) -> tuple[int, int, int, int]:
    clamped_value = max(0, min(255, value))

    for index in range(1, len(color_ramp)):
        stop, color = color_ramp[index]
        prev_stop, prev_color = color_ramp[index - 1]
        if clamped_value <= stop:
            span = stop - prev_stop
            if span == 0:
                return color
            weight = clamped_value - prev_stop
            return tuple(
                prev_color[channel]
                + ((color[channel] - prev_color[channel]) * weight) // span
                for channel in range(4)
            )

    return color_ramp[-1][1]


def get_object_surface(
    context: AppContext, object_id: int, frame: int = 0, display: XDisplay | None = None
) -> Any | None:
    """
    Get the surface for a specific object sprite.

    Args:
        object_id: ID of the object
        frame: Animation frame number
        display: Display containing the object graphics

    Returns:
        pygame Surface for the object sprite, or None if not found
        :param context:
    """
    if display is None:
        display = context.main_display

    if display is None or display.objects is None:
        return None

    try:
        if (
            0 < object_id < len(display.objects)
            and display.objects[object_id] is not None
        ):
            frames = display.objects[object_id]
            if frames is not None and 0 <= frame < len(frames):
                return frames[frame]
    except (IndexError, TypeError):
        pass

    return None


# ============================================================================
# Validation Functions
# ============================================================================


def validate_graphics_setup(context: AppContext) -> bool:
    """
    Validate that graphics have been properly initialized.

    Returns:
        True if graphics are properly set up, False otherwise
        :param context:
    """

    try:
        # Check main display
        if not hasattr(context, "MainDisplay") or context.main_display is None:
            return False

        display = context.main_display

        # Check stipple patterns
        stipples = [
            display.gray25_stipple,
            display.gray50_stipple,
            display.gray75_stipple,
            display.vert_stipple,
            display.horiz_stipple,
            display.diag_stipple,
        ]

        for stipple in stipples:
            if stipple is None:
                return False

        # Check object sprites (at least some should be loaded)
        if display.objects is None:
            return False

        # Check that at least one object has sprites loaded
        has_objects = any(
            obj is not None for obj in display.objects[1:] if obj is not None
        )
        if not has_objects:
            return False

        return True

    except (AttributeError, TypeError):
        return False
