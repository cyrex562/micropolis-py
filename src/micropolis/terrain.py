"""
terrain.py - Terrain generation and management for Micropolis

This module implements procedural terrain generation algorithms including:
- River systems with curvature control
- Lake placement
- Tree distribution and clustering
- Island generation
- Terrain smoothing and edge detection
- Configurable generation parameters

Based on the original C code from mapgener.c, terragen.c, and terra.c
"""

import random

from src.micropolis.constants import (
    WORLD_X,
    WORLD_Y,
    DIR_TAB_X,
    DIR_TAB_Y,
    RIVER,
    CHANNEL,
    BR_MATRIX,
    SR_MATRIX,
    WOODS,
    BLN,
    REDGE,
    RED_TAB,
    BN,
    TED_TAB,
    BURNBIT,
)
from typing import TYPE_CHECKING, Any

# Avoid importing AppContext at module import time to prevent circular
# imports with context.py. Use TYPE_CHECKING for type hints and Any at
# runtime for function signatures.
if TYPE_CHECKING:
    from src.micropolis.context import AppContext


def _init_random_state(seed: int) -> list[int]:
    """Initialize the GRand random number generator state."""
    # Based on original GRanArray initialization
    state = [1018, 4521, 202, 419, 3]
    state[0] = seed  # Use seed instead of TickCount()
    return state


def test_bounds(x: int, y: int) -> bool:
    """
    Test if coordinates are within world bounds.

    Args:
        x, y: Coordinates to test

    Returns:
        True if coordinates are valid
    """
    return 0 <= x < WORLD_X and 0 <= y < WORLD_Y


def clear_map(map_data: list[list[int]]) -> None:
    """
    Clear the entire map to zeros.

    Args:
        map_data: The map to clear
    """
    for x in range(WORLD_X):
        for y in range(WORLD_Y):
            map_data[x][y] = 0


def smooth_trees(map_data: list[list[int]]) -> None:
    """
    Smooth tree edges using lookup table.

    Args:
        map_data: The map to modify
    """
    dx = [-1, 0, 1, 0]
    dy = [0, 1, 0, -1]

    for x in range(WORLD_X):
        for y in range(WORLD_Y):
            if (map_data[x][y] & BLN) == BLN:
                bitindex = 0
                for z in range(4):
                    bitindex <<= 1
                    xtem = x + dx[z]
                    ytem = y + dy[z]
                    if test_bounds(xtem, ytem) and (map_data[xtem][ytem] & BN):
                        bitindex += 1

                temp = TED_TAB[bitindex & 15]
                if temp:
                    if temp != 37 and (x + y) & 1:
                        temp -= 8
                    map_data[x][y] = temp + BLN
                else:
                    # Preserve tree bit when lookup produces no replacement.
                    map_data[x][y] = WOODS + BLN


class TerrainGenerator:
    """
    Procedural terrain generation system for Micropolis.

    Implements the core algorithms from the original C codebase:
    - River generation with curvature control
    - Lake placement algorithms
    - Tree distribution and clustering
    - Island generation
    - Terrain smoothing and edge detection
    """

    def __init__(self, seed: int | None = None):
        """
        Initialize terrain generator with random seed.

        Args:
            seed: Random seed for reproducible generation (uses system time if None)
        """
        self.seed = seed if seed is not None else random.randint(0, 2**31 - 1)
        self.random_state = _init_random_state(self.seed)

        # Current position for terrain operations
        self.map_x = 0
        self.map_y = 0

        # River generation state
        self.x_start = 0
        self.y_start = 0
        self.dir = 0
        self.last_dir = 0

    def grand(self, range_val: int) -> int:
        """
        Generate random number using the original GRand algorithm.

        Args:
            range_val: Upper bound (exclusive)

        Returns:
            Random integer from 0 to range_val-1
        """
        RANMASK = 32767
        divisor = RANMASK // (range_val + 1)

        # Update random state
        newv = 0
        for x in range(4, 0, -1):
            self.random_state[x] = self.random_state[x - 1]
            newv += self.random_state[x]
        self.random_state[0] = newv

        x = (newv & RANMASK) // divisor
        return min(x, range_val)

    def egrand(self, limit: int) -> int:
        """
        Enhanced random - returns minimum of two random values.

        Args:
            limit: Upper bound (exclusive)

        Returns:
            Random integer from 0 to limit-1 (biased toward lower values)
        """
        z = self.grand(limit)
        x = self.grand(limit)
        return min(z, x)

    def move_map(self, direction: int) -> None:
        """
        Move current position based on direction.

        Args:
            direction: Direction (0-7, where 0=north, 2=east, 4=south, 6=west)
        """
        direction &= 7
        self.map_x += DIR_TAB_X[direction]
        self.map_y += DIR_TAB_Y[direction]

    def put_on_map(
        self, tile: int, x_off: int, y_off: int, map_data: list[list[int]]
    ) -> bool:
        """
        Place a tile on the map with collision detection.

        Args:
            tile: Tile value to place
            x_off, y_off: Offset from current position
            map_data: The map to modify

        Returns:
            True if tile was placed successfully
        """
        if tile == 0:
            return True

        x_loc = self.map_x + x_off
        y_loc = self.map_y + y_off

        if not test_bounds(x_loc, y_loc):
            return False

        existing = map_data[x_loc][y_loc]
        if existing:
            existing &= 1023  # Mask to lower 10 bits
            if existing == RIVER and tile != CHANNEL:
                return False
            if existing == CHANNEL:
                return False

        map_data[x_loc][y_loc] = tile
        return True

    def make_island(self, map_data: list[list[int]]) -> None:
        """
        Generate an island terrain by clearing the center and adding water edges.

        Args:
            map_data: The map to modify
        """
        RADIUS = 18

        # Fill entire map with river (water)
        for x in range(WORLD_X):
            for y in range(WORLD_Y):
                map_data[x][y] = RIVER

        # Clear center area
        for x in range(5, WORLD_X - 5):
            for y in range(5, WORLD_Y - 5):
                map_data[x][y] = 0

        # Add water edges around the perimeter
        for x in range(0, WORLD_X - 5, 2):
            self.map_x = x

            self.map_y = self.egrand(RADIUS)
            self._briv_plop(map_data)

            self.map_y = 90 - self.egrand(RADIUS)
            self._briv_plop(map_data)

            self.map_y = 0
            self._sriv_plop(map_data)

            self.map_y = 94
            self._sriv_plop(map_data)

        for y in range(0, WORLD_Y - 5, 2):
            self.map_y = y

            self.map_x = self.egrand(RADIUS)
            self._briv_plop(map_data)

            self.map_x = 110 - self.egrand(RADIUS)
            self._briv_plop(map_data)

            self.map_x = 0
            self._sriv_plop(map_data)

            self.map_x = 114
            self._sriv_plop(map_data)

        self.smooth_river(map_data)
        self.do_trees(map_data)

    def get_rand_start(self) -> None:
        """Get random starting position for river generation."""
        self.x_start = 40 + self.grand(40)
        self.y_start = 33 + self.grand(33)
        self.map_x = self.x_start
        self.map_y = self.y_start

    def do_rivers(self, map_data: list[list[int]]) -> None:
        """
        Generate river systems on the map.

        Args:
            map_data: The map to modify
        """
        self.last_dir = self.grand(3)
        self.dir = self.last_dir
        self._do_briv(map_data)

        self.map_x = self.x_start
        self.map_y = self.y_start
        self.last_dir = self.last_dir ^ 4
        self.dir = self.last_dir
        self._do_briv(map_data)

        self.map_x = self.x_start
        self.map_y = self.y_start
        self.last_dir = self.grand(3)
        self._do_sriv(map_data)

    def _do_briv(self, map_data: list[list[int]]) -> None:
        """Generate a big river branch."""
        while test_bounds(self.map_x + 4, self.map_y + 4):
            self._briv_plop(map_data)
            if self.grand(10) > 4:
                self.dir += 1
            if self.grand(10) > 4:
                self.dir -= 1
            if not self.grand(10):
                self.dir = self.last_dir
            self.move_map(self.dir)

    def _do_sriv(self, map_data: list[list[int]]) -> None:
        """Generate a small river branch."""
        while test_bounds(self.map_x + 3, self.map_y + 3):
            self._sriv_plop(map_data)
            if self.grand(10) > 5:
                self.dir += 1
            if self.grand(10) > 5:
                self.dir -= 1
            if not self.grand(12):
                self.dir = self.last_dir
            self.move_map(self.dir)

    def _briv_plop(self, map_data: list[list[int]]) -> None:
        """Place a big river tile pattern."""
        for x in range(9):
            for y in range(9):
                self.put_on_map(BR_MATRIX[y][x], x - 4, y - 4, map_data)

    def _sriv_plop(self, map_data: list[list[int]]) -> None:
        """Place a small river tile pattern."""
        for x in range(6):
            for y in range(6):
                self.put_on_map(SR_MATRIX[y][x], x - 3, y - 3, map_data)

    def make_lakes(self, map_data: list[list[int]]) -> None:
        """
        Add lakes randomly to the map.

        Args:
            map_data: The map to modify
        """
        lim1 = self.grand(10)
        for _ in range(lim1):
            x = self.grand(99) + 10
            y = self.grand(80) + 10
            lim2 = self.grand(12) + 2
            for _ in range(lim2):
                self.map_x = x - 6 + self.grand(12)
                self.map_y = y - 6 + self.grand(12)
                if self.grand(4):
                    self._sriv_plop(map_data)
                else:
                    self._briv_plop(map_data)

    def do_trees(self, map_data: list[list[int]]) -> None:
        """
        Place trees randomly on the map and smooth them.

        Args:
            map_data: The map to modify
        """
        amount = self.grand(100) + 50
        for _ in range(amount):
            xloc = self.grand(119)
            yloc = self.grand(99)
            self._tree_splash(xloc, yloc, map_data)

        smooth_trees(map_data)
        smooth_trees(map_data)

    def _tree_splash(self, xloc: int, yloc: int, map_data: list[list[int]]) -> None:
        """
        Create a tree cluster starting from a location.

        Args:
            xloc, yloc: Starting coordinates
            map_data: The map to modify
        """
        dis = self.grand(150) + 50
        self.map_x = xloc
        self.map_y = yloc

        for _ in range(dis):
            dir_val = self.grand(7)
            self.move_map(dir_val)
            if not test_bounds(self.map_x, self.map_y):
                return
            if map_data[self.map_x][self.map_y] == 0:
                map_data[self.map_x][self.map_y] = WOODS + BLN

    def smooth_river(self, map_data: list[list[int]]) -> None:
        """
        Smooth river edges using lookup table.

        Args:
            map_data: The map to modify
        """
        dx = [-1, 0, 1, 0]
        dy = [0, 1, 0, -1]

        for x in range(WORLD_X):
            for y in range(WORLD_Y):
                if map_data[x][y] == REDGE:
                    bitindex = 0
                    for z in range(4):
                        bitindex <<= 1
                        xtem = x + dx[z]
                        ytem = y + dy[z]
                        if test_bounds(xtem, ytem) and map_data[xtem][ytem]:
                            bitindex += 1

                    temp = RED_TAB[bitindex & 15]
                    if temp != 2 and self.grand(1):
                        temp += 1
                    map_data[x][y] = temp

    def generate_map(self, map_data: list[list[int]]) -> None:
        """
        Main terrain generation entry point.

        Decides between island or river-based terrain generation.

        Args:
            map_data: The map to generate terrain on
        """
        # Reset random state for this generation
        self.random_state = _init_random_state(self.seed)

        if not self.grand(10):  # 1 in 10 chance for island
            self.make_island(map_data)
            return

        # Generate river-based terrain
        clear_map(map_data)
        self.get_rand_start()
        self.do_rivers(map_data)
        self.make_lakes(map_data)
        self.smooth_river(map_data)
        self.do_trees(map_data)


# Convenience functions for external use
def generate_terrain(map_data: list[list[int]], seed: int | None = None) -> None:
    """
    Generate procedural terrain on a map.

    Args:
        map_data: 120x100 tile map to generate terrain on
        seed: Random seed for reproducible generation
    """
    generator = TerrainGenerator(seed)
    generator.generate_map(map_data)


def clear_terrain(context: Any, map_data: list[list[int]]) -> None:
    """
    Clear all terrain from a map.

    Args:
        map_data: 120x100 tile map to clear
    """
    context.generator = TerrainGenerator()
    clear_map(map_data)


def _get_generator(context: Any) -> TerrainGenerator:
    """Return a cached generator for quick utility calls."""
    # global _GLOBAL_GENERATOR
    if context.global_generator is None:
        context.global_generator = TerrainGenerator()
    return context.global_generator


def ClearMap(context: Any) -> None:
    """Legacy interface: clear the simulation map to bare terrain.
    :param context:
    """
    context.generator = _get_generator(context)
    clear_map(context.map_data)
    context.new_map = 1


def ClearUnnatural(context: Any) -> None:
    """Remove burned/unnatural tiles (placeholder implementation)."""
    for x in range(WORLD_X):
        for y in range(WORLD_Y):
            tile = context.map_data[x][y]
            if tile & BURNBIT:
                context.map_data[x][y] = tile & ~BURNBIT
    context.new_map = 1


def SmoothTrees(context: Any) -> None:
    """Placeholder for tree smoothing to keep legacy APIs available."""
    context.new_map = 1


def SmoothWater(context: Any) -> None:
    """Placeholder for water smoothing."""
    context.new_map = 1


def SmoothRiver(context: Any) -> None:
    """Placeholder for river smoothing."""
    context.new_map = 1
