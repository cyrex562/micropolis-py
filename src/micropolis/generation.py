#!/usr/bin/env python3
"""
generation.py - City map generation algorithms for Micropolis Python port

This module implements the city generation system ported from s_gen.c,
responsible for creating new city maps with rivers, lakes, trees, and terrain
features using procedural generation algorithms.
"""

import micropolis.constants
import micropolis.utilities
from . import types, macros


# ============================================================================
# Generation Control Variables
# ============================================================================

XStart: int = 0
YStart: int = 0
MapX: int = 0
MapY: int = 0
Dir: int = 0
LastDir: int = 0

# Generation parameters (can be set externally)
TreeLevel: int = -1  # Level for tree creation (-1 = random, 0 = none, >0 = amount)
LakeLevel: int = -1  # Level for lake creation (-1 = random, 0 = none, >0 = amount)
CurveLevel: int = -1  # Level for river curviness (-1 = random, 0 = none, >0 = amount)
CreateIsland: int = -1  # Island creation (-1 = 10% chance, 0 = never, 1 = always)

# ============================================================================
# Terrain Constants
# ============================================================================

WATER_LOW = types.RIVER  # 2
WATER_HIGH = types.LASTRIVEDGE  # 20
WOODS_LOW = types.TREEBASE  # 21
WOODS_HIGH = 39  # UNUSED_TRASH2 (woods tile range end)

# ============================================================================
# Main Generation Functions
# ============================================================================


def GenerateNewCity() -> None:
    """
    Generate a new random city.

    Ported from GenerateNewCity() in s_gen.c.
    Main entry point for city generation.
    """
    GenerateSomeCity(micropolis.utilities.rand16())


def GenerateSomeCity(r: int) -> None:
    """
    Generate a city with a specific random seed.

    Ported from GenerateSomeCity(int r) in s_gen.c.
    Called from GenerateNewCity and scenario loading.

    Args:
        r: Random seed for reproducible generation
    """
    # Clear any existing city file reference
    types.city_file_name = ""

    # Record start time (placeholder for timing)
    # gettimeofday(&start_time, NULL);

    # Generate the map
    GenerateMap(r)

    # Reset simulation state
    types.scenario_id = 0
    types.city_time = 0
    types.init_sim_load = 2
    types.do_initial_eval = 0

    # Initialize simulation components (placeholders for now)
    # types.InitWillStuff()
    # types.ResetMapState()
    # types.ResetEditorState()
    # types.InvalidateEditors()
    # types.InvalidateMaps()
    types.UpdateFunds()
    # types.DoSimInit()

    # UI callback (placeholder)
    # Eval("UIDidGenerateNewCity");

    types.Kick()


def ERand(limit: int) -> int:
    """
    Generate a random number with extra randomness.

    Ported from ERand(short limit) in s_gen.c.
    Uses two random calls and returns the smaller one.

    Args:
        limit: Upper bound for random number

    Returns:
        Random number between 0 and limit-1
    """
    z = micropolis.utilities.rand(limit)
    x = micropolis.utilities.rand(limit)
    return z if z < x else x


def GenerateMap(r: int) -> None:
    """
    Core map generation algorithm.

    Ported from GenerateMap(int r) in s_gen.c.
    Generates terrain features in sequence: island/base, rivers, lakes, smoothing, trees.

    Args:
        r: Random seed
    """
    # Seed the random number generator
    import random as python_random

    python_random.seed(r)

    # Island generation logic
    if CreateIsland < 0:
        if micropolis.utilities.rand(100) < 10:  # 10% chance for island
            MakeIsland()
            return
    elif CreateIsland == 1:
        MakeNakedIsland()
    else:
        ClearMap()

    # Generate terrain features
    GetRandStart()

    if CurveLevel != 0:
        DoRivers()

    if LakeLevel != 0:
        MakeLakes()

    SmoothRiver()

    if TreeLevel != 0:
        DoTrees()

    # Randomize the seed again for additional randomness
    import random as python_random

    python_random.seed()


# ============================================================================
# Map Clearing Functions
# ============================================================================


def ClearMap() -> None:
    """
    Initialize the entire map to dirt tiles.

    Ported from ClearMap() in s_gen.c.
    Sets all map cells to DIRT.
    """
    for x in range(micropolis.constants.WORLD_X):
        for y in range(micropolis.constants.WORLD_Y):
            types.map_data[x][y] = types.DIRT


def ClearUnnatural() -> None:
    """
    Clear all man-made structures, leaving only natural terrain.

    Ported from ClearUnnatural() in s_gen.c.
    Removes any tiles above WOODS (buildings, roads, etc.).
    """
    for x in range(micropolis.constants.WORLD_X):
        for y in range(micropolis.constants.WORLD_Y):
            if types.map_data[x][y] > types.WOODS:
                types.map_data[x][y] = types.DIRT


# ============================================================================
# Island Generation
# ============================================================================

RADIUS = 18


def MakeNakedIsland() -> None:
    """
    Create a basic island surrounded by water.

    Ported from MakeNakedIsland() in s_gen.c.
    Creates a land mass in the center surrounded by rivers, with some
    river branches extending toward the edges.
    """
    # Fill entire map with river
    for x in range(micropolis.constants.WORLD_X):
        for y in range(micropolis.constants.WORLD_Y):
            types.map_data[x][y] = types.RIVER

    # Create central land area
    for x in range(5, micropolis.constants.WORLD_X - 5):
        for y in range(5, micropolis.constants.WORLD_Y - 5):
            types.map_data[x][y] = types.DIRT

    # Add river branches horizontally
    for x in range(0, micropolis.constants.WORLD_X - 5, 2):
        global MapX, MapY
        MapX = x
        MapY = ERand(RADIUS)
        BRivPlop()
        MapY = (micropolis.constants.WORLD_Y - 10) - ERand(RADIUS)
        BRivPlop()
        MapY = 0
        SRivPlop()
        MapY = micropolis.constants.WORLD_Y - 6
        SRivPlop()

    # Add river branches vertically
    for y in range(0, micropolis.constants.WORLD_Y - 5, 2):
        MapY = y
        MapX = ERand(RADIUS)
        BRivPlop()
        MapX = (micropolis.constants.WORLD_X - 10) - ERand(RADIUS)
        BRivPlop()
        MapX = 0
        SRivPlop()
        MapX = micropolis.constants.WORLD_X - 6
        SRivPlop()


def MakeIsland() -> None:
    """
    Create a complete island with smoothed rivers and trees.

    Ported from MakeIsland() in s_gen.c.
    Calls MakeNakedIsland then adds smoothing and trees.
    """
    MakeNakedIsland()
    SmoothRiver()
    DoTrees()


# ============================================================================
# Lake Generation
# ============================================================================


def MakeLakes() -> None:
    """
    Generate lakes on the map.

    Ported from MakeLakes() in s_gen.c.
    Places multiple lake clusters using river placement functions.
    """
    if LakeLevel < 0:
        Lim1 = micropolis.utilities.rand(10)
    else:
        Lim1 = LakeLevel // 2

    for t in range(Lim1):
        x = micropolis.utilities.rand(micropolis.constants.WORLD_X - 21) + 10
        y = micropolis.utilities.rand(micropolis.constants.WORLD_Y - 20) + 10
        Lim2 = micropolis.utilities.rand(12) + 2

        for z in range(Lim2):
            global MapX, MapY
            MapX = x - 6 + micropolis.utilities.rand(12)
            MapY = y - 6 + micropolis.utilities.rand(12)
            if micropolis.utilities.rand(4):
                SRivPlop()
            else:
                BRivPlop()


# ============================================================================
# River Generation
# ============================================================================


def GetRandStart() -> None:
    """
    Choose a random starting position for river generation.

    Ported from GetRandStart() in s_gen.c.
    Sets XStart, YStart, MapX, MapY to a random position in the central area.
    """
    global XStart, YStart, MapX, MapY
    XStart = 40 + micropolis.utilities.rand(micropolis.constants.WORLD_X - 80)
    YStart = 33 + micropolis.utilities.rand(micropolis.constants.WORLD_Y - 67)
    MapX = XStart
    MapY = YStart


def MoveMap(dir: int) -> None:
    """
    Move the current map position in a specified direction.

    Ported from MoveMap(short dir) in s_gen.c.
    Updates MapX and MapY based on direction (0-7).

    Args:
        dir: Direction to move (0-7, where 0=north, 2=east, 4=south, 6=west)
    """
    global MapX, MapY
    DirTab = [[0, 1, 1, 1, 0, -1, -1, -1], [-1, -1, 0, 1, 1, 1, 0, -1]]
    dir = dir & 7
    MapX += DirTab[0][dir]
    MapY += DirTab[1][dir]


def DoRivers() -> None:
    """
    Generate the main river system.

    Ported from DoRivers() in s_gen.c.
    Creates rivers starting from the center and extending in different directions.
    """
    global LastDir, Dir, MapX, MapY
    LastDir = micropolis.utilities.rand(3)
    Dir = LastDir
    DoBRiv()

    MapX = XStart
    MapY = YStart
    LastDir = LastDir ^ 4
    Dir = LastDir
    DoBRiv()

    MapX = XStart
    MapY = YStart
    LastDir = micropolis.utilities.rand(3)
    DoSRiv()


def DoBRiv() -> None:
    """
    Generate a big river branch.

    Ported from DoBRiv() in s_gen.c.
    Creates a wide river path with some curvature.
    """
    global Dir, LastDir, MapX, MapY

    if CurveLevel < 0:
        r1 = 100
        r2 = 200
    else:
        r1 = CurveLevel + 10
        r2 = CurveLevel + 100

    while macros.TestBounds(MapX + 4, MapY + 4):
        BRivPlop()
        if micropolis.utilities.rand(r1) < 10:
            Dir = LastDir
        else:
            if micropolis.utilities.rand(r2) > 90:
                Dir += 1
            if micropolis.utilities.rand(r2) > 90:
                Dir -= 1
        MoveMap(Dir)


def DoSRiv() -> None:
    """
    Generate a small river branch.

    Ported from DoSRiv() in s_gen.c.
    Creates a narrow river path with some curvature.
    """
    global Dir, LastDir, MapX, MapY

    if CurveLevel < 0:
        r1 = 100
        r2 = 200
    else:
        r1 = CurveLevel + 10
        r2 = CurveLevel + 100

    while macros.TestBounds(MapX + 3, MapY + 3):
        SRivPlop()
        if micropolis.utilities.rand(r1) < 10:
            Dir = LastDir
        else:
            if micropolis.utilities.rand(r2) > 90:
                Dir += 1
            if micropolis.utilities.rand(r2) > 90:
                Dir -= 1
        MoveMap(Dir)


def PutOnMap(Mchar: int, Xoff: int, Yoff: int) -> None:
    """
    Place a terrain tile on the map at an offset from current position.

    Ported from PutOnMap(short Mchar, short Xoff, short Yoff) in s_gen.c.
    Only places the tile if the position is valid and doesn't conflict with existing terrain.

    Args:
        Mchar: Tile type to place (0 = no tile)
        Xoff: X offset from MapX
        Yoff: Y offset from MapY
    """
    if Mchar == 0:
        return

    Xloc = MapX + Xoff
    Yloc = MapY + Yoff

    if not macros.TestBounds(Xloc, Yloc):
        return

    temp = types.map_data[Xloc][Yloc]
    if temp:
        temp = temp & types.LOMASK
        if temp == types.RIVER:
            if Mchar != types.CHANNEL:
                return
        if temp == types.CHANNEL:
            return

    types.map_data[Xloc][Yloc] = Mchar


def BRivPlop() -> None:
    """
    Place a big river segment (9x9 area).

    Ported from BRivPlop() in s_gen.c.
    Uses a predefined matrix to place river tiles in a 9x9 pattern.
    """
    BRMatrix = [
        [0, 0, 0, 3, 3, 3, 0, 0, 0],
        [0, 0, 3, 2, 2, 2, 3, 0, 0],
        [0, 3, 2, 2, 2, 2, 2, 3, 0],
        [3, 2, 2, 2, 2, 2, 2, 2, 3],
        [3, 2, 2, 2, 4, 2, 2, 2, 3],
        [3, 2, 2, 2, 2, 2, 2, 2, 3],
        [0, 3, 2, 2, 2, 2, 2, 3, 0],
        [0, 0, 3, 2, 2, 2, 3, 0, 0],
        [0, 0, 0, 3, 3, 3, 0, 0, 0],
    ]

    for x in range(9):
        for y in range(9):
            PutOnMap(BRMatrix[y][x], x, y)


def SRivPlop() -> None:
    """
    Place a small river segment (6x6 area).

    Ported from SRivPlop() in s_gen.c.
    Uses a predefined matrix to place river tiles in a 6x6 pattern.
    """
    SRMatrix = [
        [0, 0, 3, 3, 0, 0],
        [0, 3, 2, 2, 3, 0],
        [3, 2, 2, 2, 2, 3],
        [3, 2, 2, 2, 2, 3],
        [0, 3, 2, 2, 3, 0],
        [0, 0, 3, 3, 0, 0],
    ]

    for x in range(6):
        for y in range(6):
            PutOnMap(SRMatrix[y][x], x, y)


# ============================================================================
# Tree Generation
# ============================================================================


def TreeSplash(xloc: int, yloc: int) -> None:
    """
    Create a cluster of trees starting from a location.

    Ported from TreeSplash(short xloc, short yloc) in s_gen.c.
    Grows trees outward from the starting point in random directions.

    Args:
        xloc: Starting X coordinate
        yloc: Starting Y coordinate
    """
    global MapX, MapY

    if TreeLevel < 0:
        dis = micropolis.utilities.rand(150) + 50
    else:
        dis = micropolis.utilities.rand(100 + (TreeLevel * 2)) + 50

    MapX = xloc
    MapY = yloc

    for z in range(dis):
        dir = micropolis.utilities.rand(7)
        MoveMap(dir)
        if not macros.TestBounds(MapX, MapY):
            return
        if (types.map_data[MapX][MapY] & types.LOMASK) == types.DIRT:
            types.map_data[MapX][MapY] = types.WOODS + types.BLBNBIT


def DoTrees() -> None:
    """
    Generate trees across the map.

    Ported from DoTrees() in s_gen.c.
    Creates multiple tree clusters at random locations.
    """
    if TreeLevel < 0:
        Amount = micropolis.utilities.rand(100) + 50
    else:
        Amount = TreeLevel + 3

    for x in range(Amount):
        xloc = micropolis.utilities.rand(micropolis.constants.WORLD_X - 1)
        yloc = micropolis.utilities.rand(micropolis.constants.WORLD_Y - 1)
        TreeSplash(xloc, yloc)

    SmoothTrees()
    SmoothTrees()


# ============================================================================
# Terrain Smoothing Functions
# ============================================================================


def SmoothRiver() -> None:
    """
    Smooth river edges to create more natural transitions.

    Ported from SmoothRiver() in s_gen.c.
    Converts REDGE tiles to appropriate river edge tiles based on neighboring terrain.
    """
    DX = [-1, 0, 1, 0]
    DY = [0, 1, 0, -1]
    REdTab = [
        13 + types.BULLBIT,
        13 + types.BULLBIT,
        17 + types.BULLBIT,
        15 + types.BULLBIT,
        5 + types.BULLBIT,
        2,
        19 + types.BULLBIT,
        17 + types.BULLBIT,
        9 + types.BULLBIT,
        11 + types.BULLBIT,
        2,
        13 + types.BULLBIT,
        7 + types.BULLBIT,
        9 + types.BULLBIT,
        5 + types.BULLBIT,
        2,
    ]

    for MapX in range(micropolis.constants.WORLD_X):
        for MapY in range(micropolis.constants.WORLD_Y):
            if types.map_data[MapX][MapY] == types.REDGE:
                bitindex = 0
                for z in range(4):
                    bitindex = bitindex << 1
                    Xtem = MapX + DX[z]
                    Ytem = MapY + DY[z]
                    if (
                        macros.TestBounds(Xtem, Ytem)
                        and ((types.map_data[Xtem][Ytem] & types.LOMASK) != types.DIRT)
                        and (
                            ((types.map_data[Xtem][Ytem] & types.LOMASK) < WOODS_LOW)
                            or (
                                (types.map_data[Xtem][Ytem] & types.LOMASK) > WOODS_HIGH
                            )
                        )
                    ):
                        bitindex += 1

                temp = REdTab[bitindex & 15]
                if (temp != types.RIVER) and micropolis.utilities.rand(1):
                    temp += 1
                types.map_data[MapX][MapY] = temp


def IsTree(cell: int) -> bool:
    """
    Check if a cell contains a tree tile.

    Ported from IsTree(int cell) in s_gen.c.

    Args:
        cell: Map cell value

    Returns:
        True if the cell contains a tree
    """
    cell_type = cell & types.LOMASK
    return WOODS_LOW <= cell_type <= WOODS_HIGH


def SmoothTrees() -> None:
    """
    Smooth tree edges to create more natural forest boundaries.

    Ported from SmoothTrees() in s_gen.c.
    Converts tree tiles to appropriate forest edge tiles based on neighboring trees.
    """
    DX = [-1, 0, 1, 0]
    DY = [0, 1, 0, -1]
    TEdTab = [0, 0, 0, 34, 0, 0, 36, 35, 0, 32, 0, 33, 30, 31, 29, 37]

    for MapX in range(micropolis.constants.WORLD_X):
        for MapY in range(micropolis.constants.WORLD_Y):
            if IsTree(types.map_data[MapX][MapY]):
                bitindex = 0
                for z in range(4):
                    bitindex = bitindex << 1
                    Xtem = MapX + DX[z]
                    Ytem = MapY + DY[z]
                    if macros.TestBounds(Xtem, Ytem) and IsTree(
                        types.map_data[Xtem][Ytem]
                    ):
                        bitindex += 1

                temp = TEdTab[bitindex & 15]
                if temp:
                    if temp != types.WOODS:
                        if (MapX + MapY) & 1:
                            temp = temp - 8
                    types.map_data[MapX][MapY] = temp + types.BLBNBIT
                else:
                    types.map_data[MapX][MapY] = temp


def SmoothWater() -> None:
    """
    Smooth water edges and transitions.

    Ported from SmoothWater() in s_gen.c.
    Complex algorithm that adjusts water tiles based on neighboring terrain.
    """
    # First pass: Mark river edges
    for x in range(micropolis.constants.WORLD_X):
        for y in range(micropolis.constants.WORLD_Y):
            # If water:
            if WATER_LOW <= (types.map_data[x][y] & types.LOMASK) <= WATER_HIGH:
                # Check neighbors for non-water
                if x > 0:
                    if not (
                        WATER_LOW
                        <= (types.map_data[x - 1][y] & types.LOMASK)
                        <= WATER_HIGH
                    ):
                        types.map_data[x][y] = types.REDGE
                        continue
                if x < (micropolis.constants.WORLD_X - 1):
                    if not (
                        WATER_LOW
                        <= (types.map_data[x + 1][y] & types.LOMASK)
                        <= WATER_HIGH
                    ):
                        types.map_data[x][y] = types.REDGE
                        continue
                if y > 0:
                    if not (
                        WATER_LOW
                        <= (types.map_data[x][y - 1] & types.LOMASK)
                        <= WATER_HIGH
                    ):
                        types.map_data[x][y] = types.REDGE
                        continue
                if y < (micropolis.constants.WORLD_Y - 1):
                    if not (
                        WATER_LOW
                        <= (types.map_data[x][y + 1] & types.LOMASK)
                        <= WATER_HIGH
                    ):
                        types.map_data[x][y] = types.REDGE
                        continue

    # Second pass: Convert isolated water to river
    for x in range(micropolis.constants.WORLD_X):
        for y in range(micropolis.constants.WORLD_Y):
            # If water which is not a channel:
            if (types.map_data[x][y] & types.LOMASK) != types.CHANNEL and WATER_LOW <= (
                types.map_data[x][y] & types.LOMASK
            ) <= WATER_HIGH:
                # Check if all neighbors are water
                is_isolated = True
                if x > 0:
                    if not (
                        WATER_LOW
                        <= (types.map_data[x - 1][y] & types.LOMASK)
                        <= WATER_HIGH
                    ):
                        is_isolated = False
                if x < (micropolis.constants.WORLD_X - 1):
                    if not (
                        WATER_LOW
                        <= (types.map_data[x + 1][y] & types.LOMASK)
                        <= WATER_HIGH
                    ):
                        is_isolated = False
                if y > 0:
                    if not (
                        WATER_LOW
                        <= (types.map_data[x][y - 1] & types.LOMASK)
                        <= WATER_HIGH
                    ):
                        is_isolated = False
                if y < (micropolis.constants.WORLD_Y - 1):
                    if not (
                        WATER_LOW
                        <= (types.map_data[x][y + 1] & types.LOMASK)
                        <= WATER_HIGH
                    ):
                        is_isolated = False

                if is_isolated:
                    types.map_data[x][y] = types.RIVER

    # Third pass: Adjust woods near water
    for x in range(micropolis.constants.WORLD_X):
        for y in range(micropolis.constants.WORLD_Y):
            # If woods:
            if WOODS_LOW <= (types.map_data[x][y] & types.LOMASK) <= WOODS_HIGH:
                # Check if adjacent to water
                if x > 0:
                    if types.map_data[x - 1][y] in (types.RIVER, types.CHANNEL):
                        types.map_data[x][y] = types.REDGE
                        continue
                if x < (micropolis.constants.WORLD_X - 1):
                    if types.map_data[x + 1][y] in (types.RIVER, types.CHANNEL):
                        types.map_data[x][y] = types.REDGE
                        continue
                if y > 0:
                    if types.map_data[x][y - 1] in (types.RIVER, types.CHANNEL):
                        types.map_data[x][y] = types.REDGE
                        continue
                if y < (micropolis.constants.WORLD_Y - 1):
                    if types.map_data[x][y + 1] in (types.RIVER, types.CHANNEL):
                        types.map_data[x][y] = types.REDGE
                        continue
