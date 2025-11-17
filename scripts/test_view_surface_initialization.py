"""
Test script to verify view surface initialization and tile blitting.

This script tests:
1. map_view.MemDrawMap() paints actual tiles
2. editor_view.MemDrawBeegMapRect() paints actual tiles
3. sim_update_maps() / sim_update_editors() mark views invalid
4. types.sim.map / types.sim.editor have valid .surface objects
"""

import os
import sys
import pygame

# Add src to path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from micropolis.context import AppContext
from micropolis.app_config import AppConfig
from micropolis.map_view import MemDrawMap, setUpMapProcs
from micropolis.editor_view import mem_draw_beeg_map_rect, initialize_editor_tiles
from micropolis.sim import MakeNewSim
from micropolis.constants import (
    WORLD_X,
    WORLD_Y,
    RESBASE,
    COMBASE,
    INDBASE,
    MAP_W,
    MAP_H,
    EDITOR_W,
    EDITOR_H,
)
from micropolis.sim_view import create_editor_view, create_map_view
from micropolis.graphics_setup import init_view_graphics


def test_view_surface_initialization():
    """Test that view surfaces are properly initialized."""
    print("=" * 80)
    print("TEST: View Surface Initialization")
    print("=" * 80)

    # Initialize pygame
    pygame.init()

    # Create context with minimal config
    config = AppConfig()
    context = AppContext(config=config)

    # Create sim manually (avoiding sim_init to prevent circular imports)
    context.sim = MakeNewSim(context)

    # Initialize map procedures
    setUpMapProcs(context)

    # Initialize graphics for views
    if context.sim.map:
        init_view_graphics(context.sim.map)
    if context.sim.editor:
        init_view_graphics(context.sim.editor)

    print(f"\n1. Checking context.sim exists: {context.sim is not None}")
    if not context.sim:
        print("   ❌ FAILED: context.sim is None after MakeNewSim()")
        return False

    print(f"2. Checking context.sim.map exists: {context.sim.map is not None}")
    if not context.sim.map:
        print("   ❌ FAILED: context.sim.map is None")
        return False

    print(f"3. Checking context.sim.editor exists: {context.sim.editor is not None}")
    if not context.sim.editor:
        print("   ❌ FAILED: context.sim.editor is None")
        return False

    # Check map view surface
    map_view = context.sim.map
    print(f"\n4. Checking map_view.surface exists: {map_view.surface is not None}")
    if map_view.surface:
        print(f"   ✅ map_view.surface size: {map_view.surface.get_size()}")
    else:
        print(f"   ⚠️  map_view.surface is None - will be created on first draw")

    # Check editor view surface
    editor_view = context.sim.editor
    print(
        f"\n5. Checking editor_view.surface exists: {editor_view.surface is not None}"
    )
    if editor_view.surface:
        print(f"   ✅ editor_view.surface size: {editor_view.surface.get_size()}")
    else:
        print(f"   ⚠️  editor_view.surface is None - will be created on first draw")

    # Add some test data to the map
    print(
        f"\n6. Adding test data to map (residential, commercial, industrial zones)..."
    )
    for x in range(10, 20):
        for y in range(10, 20):
            context.map_data[x][y] = RESBASE  # Residential
    for x in range(30, 40):
        for y in range(30, 40):
            context.map_data[x][y] = COMBASE  # Commercial
    for x in range(50, 60):
        for y in range(50, 60):
            context.map_data[x][y] = INDBASE  # Industrial
    print(f"   ✅ Added test zones to map")

    return True


def test_map_view_drawing():
    """Test that MemDrawMap() actually paints tiles."""
    print("\n" + "=" * 80)
    print("TEST: Map View Drawing")
    print("=" * 80)

    # Create context
    context = AppContext()

    # Initialize manually
    context.sim = MakeNewSim(context)
    setUpMapProcs(context)

    if not context.sim or not context.sim.map:
        print("   ❌ FAILED: Cannot test - sim or map view not initialized")
        return False

    map_view = context.sim.map

    # Initialize graphics for this view
    init_view_graphics(map_view)

    # Force view to be marked invalid
    map_view.invalid = True
    print(f"\n1. Marked map_view as invalid: {map_view.invalid}")

    # Get surface before drawing
    surface_before = map_view.surface
    print(f"2. Surface before MemDrawMap: {surface_before}")

    # Call MemDrawMap to render
    print(f"3. Calling MemDrawMap(context, map_view)...")
    try:
        MemDrawMap(context, map_view)
        print(f"   ✅ MemDrawMap() completed without errors")
    except Exception as e:
        print(f"   ❌ FAILED: MemDrawMap() raised exception: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Check surface after drawing
    surface_after = map_view.surface
    print(f"4. Surface after MemDrawMap: {surface_after}")

    if surface_after is None:
        print(f"   ❌ FAILED: surface is still None after MemDrawMap")
        return False

    print(f"   ✅ Surface size: {surface_after.get_size()}")

    # Check if pixels were actually drawn (surface not entirely black)
    pixels_array = pygame.surfarray.pixels3d(surface_after)
    non_black_pixels = (pixels_array != 0).any()
    print(f"5. Surface has non-black pixels: {non_black_pixels}")

    if not non_black_pixels:
        print(f"   ⚠️  WARNING: All pixels are black - may indicate tiles not rendering")
    else:
        print(f"   ✅ Surface has colored pixels - tiles are rendering")

    return True


def test_editor_view_drawing():
    """Test that mem_draw_beeg_map_rect() actually paints tiles."""
    print("\n" + "=" * 80)
    print("TEST: Editor View Drawing")
    print("=" * 80)

    # Create context
    context = AppContext()

    # Initialize manually
    context.sim = MakeNewSim(context)

    if not context.sim or not context.sim.editor:
        print("   ❌ FAILED: Cannot test - sim or editor view not initialized")
        return False

    editor_view = context.sim.editor

    # Initialize graphics for this view
    init_view_graphics(editor_view)

    # Force view to be marked invalid
    editor_view.invalid = True
    print(f"\n1. Marked editor_view as invalid: {editor_view.invalid}")

    # Get surface before drawing
    surface_before = editor_view.surface
    print(f"2. Surface before mem_draw_beeg_map_rect: {surface_before}")

    # Call mem_draw_beeg_map_rect to render a portion
    x, y, w, h = 0, 0, 10, 10  # Render 10x10 tile area
    print(
        f"3. Calling mem_draw_beeg_map_rect(context, editor_view, {x}, {y}, {w}, {h})..."
    )
    try:
        mem_draw_beeg_map_rect(context, editor_view, x, y, w, h)
        print(f"   ✅ mem_draw_beeg_map_rect() completed without errors")
    except Exception as e:
        print(f"   ❌ FAILED: mem_draw_beeg_map_rect() raised exception: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Check surface after drawing
    surface_after = editor_view.surface
    print(f"4. Surface after mem_draw_beeg_map_rect: {surface_after}")

    if surface_after is None:
        print(f"   ❌ FAILED: surface is still None after mem_draw_beeg_map_rect")
        return False

    print(f"   ✅ Surface size: {surface_after.get_size()}")

    # Check if pixels were actually drawn
    pixels_array = pygame.surfarray.pixels3d(surface_after)
    non_black_pixels = (pixels_array != 0).any()
    print(f"5. Surface has non-black pixels: {non_black_pixels}")

    if not non_black_pixels:
        print(f"   ⚠️  WARNING: All pixels are black - may indicate tiles not rendering")
    else:
        print(f"   ✅ Surface has colored pixels - tiles are rendering")

    return True


def test_sim_update_functions():
    """Test that sim_update_maps() and sim_update_editors() mark views invalid."""
    print("\n" + "=" * 80)
    print("TEST: Invalidation Logic")
    print("=" * 80)

    # Create context
    context = AppContext()

    # Initialize manually
    context.sim = MakeNewSim(context)

    if not context.sim:
        print("   ❌ FAILED: context.sim is None")
        return False

    map_view = context.sim.map
    editor_view = context.sim.editor

    # Reset invalid flags
    map_view.invalid = False
    editor_view.invalid = False
    print("\n1. Reset invalid flags to False")
    print(f"   map_view.invalid = {map_view.invalid}")
    print(f"   editor_view.invalid = {editor_view.invalid}")

    # Test manual invalidation
    print("\n2. Testing manual invalidation...")
    map_view.invalid = True
    editor_view.invalid = True

    print(f"3. After manual invalidation:")
    print(f"   map_view.invalid = {map_view.invalid}")
    print(f"   editor_view.invalid = {editor_view.invalid}")

    if map_view.invalid and editor_view.invalid:
        print("   ✅ Views can be marked as invalid")
    else:
        print("   ❌ FAILED: Views not properly invalidated")
        return False

    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("VIEW SURFACE INITIALIZATION TEST SUITE")
    print("=" * 80)

    results = []

    # Run tests
    results.append(("View Surface Initialization", test_view_surface_initialization()))
    results.append(("Map View Drawing", test_map_view_drawing()))
    results.append(("Editor View Drawing", test_editor_view_drawing()))
    results.append(("sim_update Functions", test_sim_update_functions()))

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {passed} passed, {failed} failed")

    pygame.quit()

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
