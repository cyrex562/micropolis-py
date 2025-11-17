#!/usr/bin/env python3
"""
Test script to verify tile graphics loading functionality.

This script tests:
1. Asset path resolution for tiles.png
2. pygame.image.load() success
3. init_view_graphics() functionality
4. Comprehensive logging output
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)-8s [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def test_asset_path_resolution():
    """Test that tiles.png can be resolved through asset manifest."""
    logger.info("=" * 70)
    logger.info("TEST 1: Asset Path Resolution")
    logger.info("=" * 70)

    try:
        from micropolis.graphics_setup import get_resource_path

        # Test tiles.png resolution
        logger.info("Testing tiles.png resolution...")
        tiles_path = get_resource_path("tiles.png", category="images")
        logger.info(f"✓ tiles.png resolved to: {tiles_path}")

        # Verify file exists
        if Path(tiles_path).exists():
            logger.info(f"✓ tiles.png exists at: {tiles_path}")
            size = Path(tiles_path).stat().st_size
            logger.info(f"  File size: {size:,} bytes")
            return True
        else:
            logger.error(f"✗ tiles.png not found at: {tiles_path}")
            return False

    except Exception as e:
        logger.exception(f"✗ Asset path resolution failed: {e}")
        return False


def test_pygame_image_load():
    """Test that pygame.image.load() can load tiles.png."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: pygame.image.load()")
    logger.info("=" * 70)

    try:
        import pygame

        pygame.init()

        from micropolis.graphics_setup import get_resource_path

        logger.info("Loading tiles.png with pygame.image.load()...")
        tiles_path = get_resource_path("tiles.png", category="images")
        surface = pygame.image.load(tiles_path)

        logger.info(f"✓ Successfully loaded tiles.png")
        logger.info(f"  Dimensions: {surface.get_width()}x{surface.get_height()}")
        logger.info(f"  Pixel format: {surface.get_bitsize()} bits")
        logger.info(f"  Has alpha: {surface.get_flags() & pygame.SRCALPHA != 0}")

        return True

    except Exception as e:
        logger.exception(f"✗ pygame.image.load() failed: {e}")
        return False


def test_load_xpm_surface():
    """Test the load_xpm_surface() function."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: load_xpm_surface()")
    logger.info("=" * 70)

    try:
        import pygame

        pygame.init()

        from micropolis.graphics_setup import load_xpm_surface

        logger.info("Testing load_xpm_surface('tiles.png')...")
        surface = load_xpm_surface("tiles.png")

        if surface is None:
            logger.error("✗ load_xpm_surface() returned None")
            return False

        logger.info(f"✓ Successfully loaded with load_xpm_surface()")
        logger.info(f"  Dimensions: {surface.get_width()}x{surface.get_height()}")

        return True

    except Exception as e:
        logger.exception(f"✗ load_xpm_surface() failed: {e}")
        return False


def test_init_view_graphics():
    """Test init_view_graphics() for a mock view."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: init_view_graphics()")
    logger.info("=" * 70)

    try:
        import pygame

        pygame.init()

        from micropolis.graphics_setup import init_view_graphics
        from micropolis.view_types import (
            MakeNewXDisplay,
            Editor_Class,
            Map_Class,
            X_Mem_View,
        )

        # Create a mock editor view
        logger.info("Creating mock editor view...")

        class MockView:
            def __init__(self):
                self.class_id = Editor_Class
                self.type = X_Mem_View
                self.x = MakeNewXDisplay()
                self.x.color = True
                self.bigtiles = None
                self.smalltiles = None

        view = MockView()
        logger.info(f"Mock view created: class_id={view.class_id}, type={view.type}")

        logger.info("Calling init_view_graphics()...")
        success = init_view_graphics(view)

        if success:
            logger.info("✓ init_view_graphics() succeeded")
            logger.info(f"  view.bigtiles is None: {view.bigtiles is None}")
            if view.bigtiles is not None:
                logger.info(
                    f"  view.bigtiles dimensions: "
                    f"{view.bigtiles.get_width()}x{view.bigtiles.get_height()}"
                )
            return True
        else:
            logger.error("✗ init_view_graphics() returned False")
            return False

    except Exception as e:
        logger.exception(f"✗ init_view_graphics() failed: {e}")
        return False


def main():
    """Run all tile loading tests."""
    logger.info("\n" + "=" * 70)
    logger.info("TILE GRAPHICS LOADING VERIFICATION")
    logger.info("=" * 70)

    results = {}

    # Run all tests
    results["asset_path"] = test_asset_path_resolution()
    results["pygame_load"] = test_pygame_image_load()
    results["load_xpm"] = test_load_xpm_surface()
    results["init_view"] = test_init_view_graphics()

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status:8} {test_name}")

    all_passed = all(results.values())

    logger.info("=" * 70)
    if all_passed:
        logger.info("✓ ALL TESTS PASSED")
        return 0
    else:
        logger.error("✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
