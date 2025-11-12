#!/usr/bin/env python3
"""
generation.py - City map generation algorithms for Micropolis Python port

This module implements the city generation system ported from s_gen.c,
responsible for creating new city maps with rivers, lakes, trees, and terrain
features using procedural generation algorithms.
"""
from src.micropolis.constants import RIVER, WORLD_X, WORLD_Y, DIRT, WOODS, LOMASK, CHANNEL, \
    BLBNBIT, BULLBIT, REDGE, WOODS_LOW, WOODS_HIGH, WATER_LOW, WATER_HIGH
from src.micropolis.context import AppContext
from src.micropolis.macros import TestBounds
from src.micropolis.simulation import rand16, rand
from src.micropolis.ui_utilities import update_funds, kick


# ============================================================================
# Generation Control Variables
# ============================================================================


# ============================================================================
# Terrain Constants
# ============================================================================


# ============================================================================
# Main Generation Functions
# ============================================================================


def GenerateNewCity(context: AppContext) -> None:
    """
    Generate a new random city.

    Ported from GenerateNewCity() in s_gen.c.
    Main entry point for city generation.
    :param context: 
    """
    GenerateSomeCity(context, rand16())


def GenerateSomeCity(context: AppContext, r: int) -> None:
    """
    Generate a city with a specific random seed.

    Ported from GenerateSomeCity(int r) in s_gen.c.
    Called from GenerateNewCity and scenario loading.

    Args:
        r: Random seed for reproducible generation
        :param context: 
    """
    # Clear any existing city file reference
    context.city_file_name = ""

    # Record start time (placeholder for timing)
    # gettimeofday(&start_time, NULL);

    # Generate the map
    GenerateMap(context, r)

    # Reset simulation state
    context.scenario_id = 0
    context.city_time = 0
    context.init_sim_load = 2
    context.do_initial_eval = 0

    # Initialize simulation components (placeholders for now)
    # types.InitWillStuff()
    # types.ResetMapState()
    # types.ResetEditorState()
    # types.InvalidateEditors()
    # types.InvalidateMaps()
    update_funds(context)
    # types.DoSimInit()

    # UI callback (placeholder)
    # Eval("UIDidGenerateNewCity");

    kick(context)


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
    z = rand(context, limit)
    x = rand(context, limit)
    return z if z < x else x


def GenerateMap(context: AppContext, r: int) -> None:
    """
    Core map generation algorithm.

    Ported from GenerateMap(int r) in s_gen.c.
    Generates terrain features in sequence: island/base, rivers, lakes, smoothing, trees.

    Args:
        r: Random seed
        :param context: 
    """
    # Seed the random number generator
    import random as python_random

    python_random.seed(r)

    # Island generation logic
    if context.create_island < 0:
        if rand(context, 100) < 10:  # 10% chance for island
            MakeIsland(context)
            return
    elif context.create_island == 1:
        MakeNakedIsland(context)
    else:
        ClearMap(context)

    # Generate terrain features
    GetRandStart(context)

    if context.curve_level != 0:
        DoRivers(context)

    if context.lake_level != 0:
        MakeLakes(context)

    SmoothRiver(context)

    if context.tree_level != 0:
        DoTrees(context)

    # Randomize the seed again for additional randomness
    import random as python_random

    python_random.seed()


# ============================================================================
# Map Clearing Functions
# ============================================================================


def ClearMap(context: AppContext) -> None:
    """
    Initialize the entire map to dirt tiles.

    Ported from ClearMap() in s_gen.c.
    Sets all map cells to DIRT.
    :param context: 
    """
    for x in range(WORLD_X):
        for y in range(WORLD_Y):
            context.map_data[x][y] = DIRT


def ClearUnnatural(context: AppContext) -> None:
    """
    Clear all man-made structures, leaving only natural terrain.

    Ported from ClearUnnatural() in s_gen.c.
    Removes any tiles above WOODS (buildings, roads, etc.).
    :param context: 
    """
    for x in range(WORLD_X):
        for y in range(WORLD_Y):
            if context.map_data[x][y] > WOODS:
                context.map_data[x][y] = DIRT


# ============================================================================
# Island Generation
# ============================================================================

RADIUS = 18


def MakeNakedIsland(context: AppContext) -> None:
    """
    Create a basic island surrounded by water.

    Ported from MakeNakedIsland() in s_gen.c.
    Creates a land mass in the center surrounded by rivers, with some
    river branches extending toward the edges.
    :param context: 
    """
    # Fill entire map with river
    for x in range(WORLD_X):
        for y in range(WORLD_Y):
            context.map_data[x][y] = RIVER

    # Create central land area
    for x in range(5, WORLD_X - 5):
        for y in range(5, WORLD_Y - 5):
            context.map_data[x][y] = DIRT

    # Add river branches horizontally
    for x in range(0, WORLD_X - 5, 2):
        # global map_x, map_y
        context.map_x = x
        context.map_y = ERand(RADIUS)
        BRivPlop(context)
        context.map_y = (WORLD_Y - 10) - ERand(RADIUS)
        BRivPlop(context)
        context.map_y = 0
        SRivPlop(context)
        context.map_y = WORLD_Y - 6
        SRivPlop(context)

    # Add river branches vertically
    for y in range(0, WORLD_Y - 5, 2):
        context.map_y = y
        context.map_x = ERand(RADIUS)
        BRivPlop(context)
        context.map_x = (WORLD_X - 10) - ERand(RADIUS)
        BRivPlop(context)
        context.map_x = 0
        SRivPlop(context)
        context.map_x = WORLD_X - 6
        SRivPlop(context)


def MakeIsland(context: AppContext) -> None:
    """
    Create a complete island with smoothed rivers and trees.

    Ported from MakeIsland() in s_gen.c.
    Calls MakeNakedIsland then adds smoothing and trees.
    :param context: 
    """
    MakeNakedIsland(context)
    SmoothRiver(context)
    DoTrees(context)


# ============================================================================
# Lake Generation
# ============================================================================


def MakeLakes(context: AppContext) -> None:
    """
    Generate lakes on the map.

    Ported from MakeLakes() in s_gen.c.
    Places multiple lake clusters using river placement functions.
    :param context:
    """
    if context.lake_level < 0:
        Lim1 = rand(context, 10)
    else:
        Lim1 = context.lake_level // 2

    for t in range(Lim1):
        x = rand(context, WORLD_X - 21) + 10
        y = rand(context, WORLD_Y - 20) + 10
        Lim2 = rand(context, 12) + 2

        for z in range(Lim2):
            # global map_x, map_y
            context.map_x = x - 6 + rand(context, 12)
            context.map_y = y - 6 + rand(context, 12)
            if rand(context, 4):
                SRivPlop(context)
            else:
                BRivPlop(context)


# ============================================================================
# River Generation
# ============================================================================


def GetRandStart(context: AppContext) -> None:
    """
    Choose a random starting position for river generation.

    Ported from GetRandStart() in s_gen.c.
    Sets XStart, YStart, MapX, MapY to a random position in the central area.
    :param context:
    """
    # global x_start, y_start, map_x, map_y
    context.x_start = 40 + rand(context, WORLD_X - 80)
    context.y_start = 33 + rand(context, WORLD_Y - 67)
    context.map_x = context.x_start
    context.map_y = context.y_start


def MoveMap(context: AppContext, direction: int) -> None:
    """
    Move the current map position in a specified direction.

    Ported from MoveMap(short dir) in s_gen.c.
    Updates MapX and MapY based on direction (0-7).

    Args:
        direction: Direction to move (0-7, where 0=north, 2=east, 4=south, 6=west)
        :param context:
    """
    # global map_x, map_y
    DirTab = [[0, 1, 1, 1, 0, -1, -1, -1], [-1, -1, 0, 1, 1, 1, 0, -1]]
    direction = direction & 7
    context.map_x += DirTab[0][direction]
    context.map_y += DirTab[1][direction]


def DoRivers(context: AppContext) -> None:
    """
    Generate the main river system.

    Ported from DoRivers() in s_gen.c.
    Creates rivers starting from the center and extending in different directions.
    :param context:
    """
    # global last_dir, dir, map_x, map_y
    context.last_dir = rand(context, 3)
    context.dir = context.last_dir
    DoBRiv(context)

    context.map_x = context.x_start
    context.map_y = context.y_start
    context.last_dir = context.last_dir ^ 4
    context.dir = context.last_dir
    DoBRiv(context)

    context.map_x = context.x_start
    context.map_y = context.y_start
    context.last_dir = rand(context, 3)
    DoSRiv(context)


def DoBRiv(context: AppContext) -> None:
    """
    Generate a big river branch.

    Ported from DoBRiv() in s_gen.c.
    Creates a wide river path with some curvature.
    :param context:
    """
    # global dir, last_dir, map_x, map_y

    if context.curve_level < 0:
        r1 = 100
        r2 = 200
    else:
        r1 = context.curve_level + 10
        r2 = context.curve_level + 100

    while TestBounds(context.map_x + 4, context.map_y + 4):
        BRivPlop(context)
        if rand(context, r1) < 10:
            context.dir = context.last_dir
        else:
            if rand(context, r2) > 90:
                context.dir += 1
            if rand(context, r2) > 90:
                context.dir -= 1
        MoveMap(context, context.dir)


def DoSRiv(context: AppContext) -> None:
    """
    Generate a small river branch.

    Ported from DoSRiv() in s_gen.c.
    Creates a narrow river path with some curvature.
    :param context:
    """
    # global dir, last_dir, map_x, map_y

    if context.curve_level < 0:
        r1 = 100
        r2 = 200
    else:
        r1 = context.curve_level + 10
        r2 = context.curve_level + 100

    while TestBounds(context.map_x + 3, context.map_y + 3):
        SRivPlop(context)
        if rand(context, r1) < 10:
            context.dir = context.last_dir
        else:
            if rand(context, r2) > 90:
                context.dir += 1
            if rand(context, r2) > 90:
                context.dir -= 1
        MoveMap(context, context.dir)


def PutOnMap(context: AppContext, Mchar: int, Xoff: int, Yoff: int) -> None:
    """
    Place a terrain tile on the map at an offset from current position.

    Ported from PutOnMap(short Mchar, short Xoff, short Yoff) in s_gen.c.
    Only places the tile if the position is valid and doesn't conflict with existing terrain.

    Args:
        Mchar: Tile type to place (0 = no tile)
        Xoff: X offset from MapX
        Yoff: Y offset from MapY
        :param context:
    """
    if Mchar == 0:
        return

    Xloc = context.map_x + Xoff
    Yloc = context.map_y + Yoff

    if not TestBounds(Xloc, Yloc):
        return

    temp = context.map_data[Xloc][Yloc]
    if temp:
        temp = temp & LOMASK
        if temp == RIVER:
            if Mchar != CHANNEL:
                return
        if temp == CHANNEL:
            return

    context.map_data[Xloc][Yloc] = Mchar


def BRivPlop(context: AppContext) -> None:
    """
    Place a big river segment (9x9 area).

    Ported from BRivPlop() in s_gen.c.
    Uses a predefined matrix to place river tiles in a 9x9 pattern.
    :param context:
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
            PutOnMap(context, BRMatrix[y][x], x, y)


def SRivPlop(context: AppContext) -> None:
    """
    Place a small river segment (6x6 area).

    Ported from SRivPlop() in s_gen.c.
    Uses a predefined matrix to place river tiles in a 6x6 pattern.
    :param context:
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
            PutOnMap(context, SRMatrix[y][x], x, y)


# ============================================================================
# Tree Generation
# ============================================================================


def TreeSplash(context: AppContext, xloc: int, yloc: int) -> None:
    """
    Create a cluster of trees starting from a location.

    Ported from TreeSplash(short xloc, short yloc) in s_gen.c.
    Grows trees outward from the starting point in random directions.

    Args:
        xloc: Starting X coordinate
        yloc: Starting Y coordinate
        :param context:
    """
    # global map_x, map_y

    if context.tree_level < 0:
        dis = rand(context, 150) + 50
    else:
        dis = rand(context, 100 + (context.tree_level * 2)) + 50

    context.map_x = xloc
    context.map_y = yloc

    for z in range(dis):
        direction = rand(context, 7)
        MoveMap(context, direction)
        if not TestBounds(context.map_x, context.map_y):
            return
        if (context.map_data[context.map_x][context.map_y] & LOMASK) == DIRT:
            context.map_data[context.map_x][context.map_y] = WOODS + BLBNBIT


def DoTrees(context: AppContext) -> None:
    """
    Generate trees across the map.

    Ported from DoTrees() in s_gen.c.
    Creates multiple tree clusters at random locations.
    :param context:
    """
    if context.tree_level < 0:
        Amount = rand(context, 100) + 50
    else:
        Amount = context.tree_level + 3

    for x in range(Amount):
        xloc = rand(context, WORLD_X - 1)
        yloc = rand(context, WORLD_Y - 1)
        TreeSplash(context, xloc, yloc)

    SmoothTrees(context)
    SmoothTrees(context)


# ============================================================================
# Terrain Smoothing Functions
# ============================================================================


def SmoothRiver(context: AppContext) -> None:
    """
    Smooth river edges to create more natural transitions.

    Ported from SmoothRiver() in s_gen.c.
    Converts REDGE tiles to appropriate river edge tiles based on neighboring terrain.
    :param context:
    """
    DX = [-1, 0, 1, 0]
    DY = [0, 1, 0, -1]
    REdTab = [
        13 + BULLBIT,
        13 + BULLBIT,
        17 + BULLBIT,
        15 + BULLBIT,
        5 + BULLBIT,
        2,
        19 + BULLBIT,
        17 + BULLBIT,
        9 + BULLBIT,
        11 + BULLBIT,
        2,
        13 + BULLBIT,
        7 + BULLBIT,
        9 + BULLBIT,
        5 + BULLBIT,
        2,
    ]

    for MapX in range(WORLD_X):
        for MapY in range(WORLD_Y):
            if context.map_data[MapX][MapY] == REDGE:
                bitindex = 0
                for z in range(4):
                    bitindex = bitindex << 1
                    Xtem = MapX + DX[z]
                    Ytem = MapY + DY[z]
                    if (
                            TestBounds(Xtem, Ytem)
                            and ((context.map_data[Xtem][Ytem] & LOMASK) != DIRT)
                            and (
                            ((context.map_data[Xtem][Ytem] & LOMASK) < WOODS_LOW)
                            or (
                                    (context.map_data[Xtem][Ytem] & LOMASK) > WOODS_HIGH
                            )
                    )
                    ):
                        bitindex += 1

                temp = REdTab[bitindex & 15]
                if (temp != RIVER) and rand(context, 1):
                    temp += 1
                context.map_data[MapX][MapY] = temp


def IsTree(cell: int) -> bool:
    """
    Check if a cell contains a tree tile.

    Ported from IsTree(int cell) in s_gen.c.

    Args:
        cell: Map cell value

    Returns:
        True if the cell contains a tree
    """
    cell_type = cell & LOMASK
    return WOODS_LOW <= cell_type <= WOODS_HIGH


def SmoothTrees(context: AppContext) -> None:
    """
    Smooth tree edges to create more natural forest boundaries.

    Ported from SmoothTrees() in s_gen.c.
    Converts tree tiles to appropriate forest edge tiles based on neighboring trees.
    :param context:
    """
    DX = [-1, 0, 1, 0]
    DY = [0, 1, 0, -1]
    TEdTab = [0, 0, 0, 34, 0, 0, 36, 35, 0, 32, 0, 33, 30, 31, 29, 37]

    for MapX in range(WORLD_X):
        for MapY in range(WORLD_Y):
            if IsTree(context.map_data[MapX][MapY]):
                bitindex = 0
                for z in range(4):
                    bitindex = bitindex << 1
                    Xtem = MapX + DX[z]
                    Ytem = MapY + DY[z]
                    if TestBounds(Xtem, Ytem) and IsTree(
                            context.map_data[Xtem][Ytem]
                    ):
                        bitindex += 1

                temp = TEdTab[bitindex & 15]
                if temp:
                    if temp != WOODS:
                        if (MapX + MapY) & 1:
                            temp = temp - 8
                    context.map_data[MapX][MapY] = temp + BLBNBIT
                else:
                    context.map_data[MapX][MapY] = temp


def SmoothWater(context: AppContext) -> None:
    """
    Smooth water edges and transitions.

    Ported from SmoothWater() in s_gen.c.
    Complex algorithm that adjusts water tiles based on neighboring terrain.
    :param context:
    """
    # First pass: Mark river edges
    for x in range(WORLD_X):
        for y in range(WORLD_Y):
            # If water:
            if WATER_LOW <= (context.map_data[x][y] & LOMASK) <= WATER_HIGH:
                # Check neighbors for non-water
                if x > 0:
                    if not (
                            WATER_LOW
                            <= (context.map_data[x - 1][y] & LOMASK)
                            <= WATER_HIGH
                    ):
                        context.map_data[x][y] = REDGE
                        continue
                if x < (WORLD_X - 1):
                    if not (
                            WATER_LOW
                            <= (context.map_data[x + 1][y] & LOMASK)
                            <= WATER_HIGH
                    ):
                        context.map_data[x][y] = REDGE
                        continue
                if y > 0:
                    if not (
                            WATER_LOW
                            <= (context.map_data[x][y - 1] & LOMASK)
                            <= WATER_HIGH
                    ):
                        context.map_data[x][y] = REDGE
                        continue
                if y < (WORLD_Y - 1):
                    if not (
                            WATER_LOW
                            <= (context.map_data[x][y + 1] & LOMASK)
                            <= WATER_HIGH
                    ):
                        context.map_data[x][y] = REDGE
                        continue

    # Second pass: Convert isolated water to river
    for x in range(WORLD_X):
        for y in range(WORLD_Y):
            # If water which is not a channel:
            if (context.map_data[x][y] & LOMASK) != CHANNEL and WATER_LOW <= (
                    context.map_data[x][y] & LOMASK
            ) <= WATER_HIGH:
                # Check if all neighbors are water
                is_isolated = True
                if x > 0:
                    if not (
                            WATER_LOW
                            <= (context.map_data[x - 1][y] & LOMASK)
                            <= WATER_HIGH
                    ):
                        is_isolated = False
                if x < (WORLD_X - 1):
                    if not (
                            WATER_LOW
                            <= (context.map_data[x + 1][y] & LOMASK)
                            <= WATER_HIGH
                    ):
                        is_isolated = False
                if y > 0:
                    if not (
                            WATER_LOW
                            <= (context.map_data[x][y - 1] & LOMASK)
                            <= WATER_HIGH
                    ):
                        is_isolated = False
                if y < (WORLD_Y - 1):
                    if not (
                            WATER_LOW
                            <= (context.map_data[x][y + 1] & LOMASK)
                            <= WATER_HIGH
                    ):
                        is_isolated = False

                if is_isolated:
                    context.map_data[x][y] = RIVER

    # Third pass: Adjust woods near water
    for x in range(WORLD_X):
        for y in range(WORLD_Y):
            # If woods:
            if WOODS_LOW <= (context.map_data[x][y] & LOMASK) <= WOODS_HIGH:
                # Check if adjacent to water
                if x > 0:
                    if context.map_data[x - 1][y] in (RIVER, CHANNEL):
                        context.map_data[x][y] = REDGE
                        continue
                if x < (WORLD_X - 1):
                    if context.map_data[x + 1][y] in (RIVER, CHANNEL):
                        context.map_data[x][y] = REDGE
                        continue
                if y > 0:
                    if context.map_data[x][y - 1] in (RIVER, CHANNEL):
                        context.map_data[x][y] = REDGE
                        continue
                if y < (WORLD_Y - 1):
                    if context.map_data[x][y + 1] in (RIVER, CHANNEL):
                        context.map_data[x][y] = REDGE
                        continue
