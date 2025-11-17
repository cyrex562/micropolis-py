# traffic.py: Traffic simulation and pathfinding for Micropolis Python port
#
# This module implements the traffic generation and pathfinding system
# that simulates how residential, commercial, and industrial zones generate
# traffic and attempt to reach destinations via road networks.
#
# Original C file: s_traf.c
# Ported to maintain algorithmic fidelity with the original Micropolis simulation
from micropolis.constants import MAXDIS, LOMASK, ROADBASE, POWERBASE, TELEBASE, TELELAST, WORLD_X, WORLD_Y, COMBASE, \
    LHTHR, NUCLEAR, PORT, LASTRAIL, RAILHPOWERV
from micropolis.context import AppContext
from micropolis.macros import TestBounds
from micropolis.random import sim_rand
from micropolis.simulation import rand
from micropolis.sprite_manager import GetSprite


# ============================================================================
# Traffic Generation Constants
# ============================================================================




# ============================================================================
# Traffic Generation Functions
# ============================================================================


def MakeTraf(context: AppContext, Zt: int) -> int:
    """
    Generate traffic from a zone.

    Attempts to find a road on the zone perimeter and drive to a destination.
    If successful, updates traffic density.

    Args:
        Zt: Zone type (0=Residential, 1=Commercial, 2=Industrial)

    Returns:
        1 if traffic passed, 0 if failed, -1 if no road found
        :param context: 
    """
    # Save current position
    xtem = context.s_map_x
    ytem = context.s_map_y

    # Set zone source type
    context.z_source = Zt
    context.pos_stack_num = 0

    # Check for telecommuting (currently disabled in original)
    # if (not random.Rand(2)) and FindPTele():
    #     return True

    # Look for road on zone perimeter
    if FindPRoad(context):
        # Attempt to drive somewhere
        if TryDrive(context):
            # If successful, increment traffic density
            SetTrafMem(context)
            context.s_map_x = xtem
            context.s_map_y = ytem
            return 1  # traffic passed
        else:
            context.s_map_x = xtem
            context.s_map_y = ytem
            return 0  # traffic failed
    else:
        return -1  # no road found


def SetTrafMem(context: AppContext) -> None:
    """
    Update traffic density memory along the driven path.

    Increments traffic density for road tiles along the path taken.
    Occasionally spawns police cars for high traffic areas.
    :param context: 
    """

    for x in range(context.pos_stack_num, 0, -1):
        PullPos(context)
        if TestBounds(context.s_map_x, context.s_map_y):
            z = context.map_data[context.s_map_x][context.s_map_y] & LOMASK
            if (z >= ROADBASE) and (z < POWERBASE):
                # Update traffic density (downsampled to 60x50 grid)
                density_x = context.s_map_x >> 1
                density_y = context.s_map_y >> 1
                z = context.trf_density[density_x][density_y]
                z += 50
                if (z > 240) and (not rand(context, 5)):
                    z = 240
                    # Set police car destination
                    context.traf_max_x = context.s_map_x << 4
                    context.traf_max_y = context.s_map_y << 4
                    # Try to assign police car sprite
                    sprite = GetSprite(context, 0)
                    if sprite and (sprite.control == -1):
                        sprite.dest_x = context.traf_max_x
                        sprite.dest_y = context.traf_max_y
                context.trf_density[density_x][density_y] = z


def PushPos(context: AppContext) -> None:
    """
    Push current position onto the position stack.
    :param context:
    """
    context.pos_stack_num += 1
    # Ensure stacks are large enough
    while len(context.s_map_x_stack) <= context.pos_stack_num:
        context.s_map_x_stack.append(0)
    while len(context.s_map_y_stack) <= context.pos_stack_num:
        context.s_map_y_stack.append(0)
    context.s_map_x_stack[context.pos_stack_num] = context.s_map_x
    context.s_map_y_stack[context.pos_stack_num] = context.s_map_y


def PullPos(context: AppContext) -> None:
    """
    Pull position from the position stack.
    :param context:
    """
    context.s_map_x = context.s_map_x_stack[context.pos_stack_num]
    context.s_map_y = context.s_map_y_stack[context.pos_stack_num]
    context.pos_stack_num -= 1


def FindPRoad(context: AppContext) -> bool:
    """
    Look for road on zone edges (perimeter).

    Checks 12 perimeter positions around the current zone for road tiles.

    Returns:
        True if road found, False otherwise
        :param context:
    """
    # Perimeter offsets: 12 positions around zone
    PerimX = [-1, 0, 1, 2, 2, 2, 1, 0, -1, -2, -2, -2]
    PerimY = [-2, -2, -2, -1, 0, 1, 2, 2, 2, 1, 0, -1]

    for z in range(12):
        tx = context.s_map_x + PerimX[z]
        ty = context.s_map_y + PerimY[z]
        if TestBounds(tx, ty):
            if RoadTest(context.map_data[tx][ty]):
                context.s_map_x = tx
                context.s_map_y = ty
                return True
    return False


def FindPTele(context: AppContext) -> bool:
    """
    Look for telecommunication on zone edges.

    Checks perimeter positions for telecommunication tiles.

    Returns:
        True if telecommunication found, False otherwise
        :param context:
    """
    # Perimeter offsets: same as FindPRoad
    PerimX = [-1, 0, 1, 2, 2, 2, 1, 0, -1, -2, -2, -2]
    PerimY = [-2, -2, -2, -1, 0, 1, 2, 2, 2, 1, 0, -1]

    for z in range(12):
        tx = context.s_map_x + PerimX[z]
        ty = context.s_map_y + PerimY[z]
        if TestBounds(tx, ty):
            tile = context.map_data[tx][ty] & LOMASK
            if (tile >= TELEBASE) and (tile <= TELELAST):
                return True
    return False


def TryDrive(context: AppContext) -> bool:
    """
    Attempt to drive to a destination.

    Uses pathfinding to try to reach a destination within MAXDIS steps.

    Returns:
        True if destination reached, False if failed
        :param context:
    """
    context.l_dir = 5  # Reset last direction

    for z in range(MAXDIS):
        if TryGo(context, z):
            if DriveDone(context):
                return True  # Destination reached
        else:
            if context.pos_stack_num:  # Dead end, backup
                context.pos_stack_num -= 1
                z += 3  # Skip ahead
            else:
                return False  # Give up at start

    return False  # Gone max distance


def TryGo(context: AppContext, z: int) -> bool:
    """
    Try to move in one of 4 directions.

    Attempts to find a valid road in a random direction, preferring
    not to reverse the last direction taken.

    Args:
        z: Current step count

    Returns:
        True if valid move found, False otherwise
    """
    # Try 4 directions starting from random offset
    rdir = sim_rand(context) & 3
    for x in range(rdir, rdir + 4):
        realdir = x & 3
        if realdir == context.l_dir:
            continue  # Skip last direction
        if RoadTest(GetFromMap(context, realdir)):
            MoveMapSim(context, realdir)
            context.l_dir = (realdir + 2) & 3  # Set new last direction
            if z & 1:  # Save position every other move
                PushPos(context)
            return True
    return False


def GetFromMap(context: AppContext, x: int) -> int:
    """
    Get tile from map in specified direction.

    Args:
        x: Direction (0=north, 1=east, 2=south, 3=west)

    Returns:
        Tile ID if in bounds, False (0) otherwise
    """
    if x == 0:  # North
        if context.s_map_y > 0:
            return context.map_data[context.s_map_x][context.s_map_y - 1] & LOMASK
    elif x == 1:  # East
        if context.s_map_x < (WORLD_X - 1):
            return context.map_data[context.s_map_x + 1][context.s_map_y] & LOMASK
    elif x == 2:  # South
        if context.s_map_y < (WORLD_Y - 1):
            return context.map_data[context.s_map_x][context.s_map_y + 1] & LOMASK
    elif x == 3:  # West
        if context.s_map_x > 0:
            return context.map_data[context.s_map_x - 1][context.s_map_y] & LOMASK

    return 0  # False


def MoveMapSim(context: AppContext, realdir: int) -> None:
    """
    Move position in specified direction.

    Args:
        realdir: Direction to move (0=north, 1=east, 2=south, 3=west)
    """
    if realdir == 0:  # North
        context.s_map_y -= 1
    elif realdir == 1:  # East
        context.s_map_x += 1
    elif realdir == 2:  # South
        context.s_map_y += 1
    elif realdir == 3:  # West
        context.s_map_x -= 1


def DriveDone(context: AppContext) -> bool:
    """
    Check if current position is a valid destination.

    Destinations vary by zone type:
    - Residential: Commercial zones
    - Commercial: Nuclear, Port, Commercial
    - Industrial: Residential zones

    Returns:
        True if valid destination reached, False otherwise
    """
    # Destination tile ranges by zone type
    TARGL = [COMBASE, LHTHR, LHTHR]  # Low range
    TARGH = [NUCLEAR, PORT, COMBASE]  # High range

    L = TARGL[context.z_source]
    H = TARGH[context.z_source]

    # Check all 4 adjacent tiles
    if context.s_map_y > 0:
        z = context.map_data[context.s_map_x][context.s_map_y - 1] & LOMASK
        if (z >= L) and (z <= H):
            return True
    if context.s_map_x < (WORLD_X - 1):
        z = context.map_data[context.s_map_x + 1][context.s_map_y] & LOMASK
        if (z >= L) and (z <= H):
            return True
    if context.s_map_y < (WORLD_Y - 1):
        z = context.map_data[context.s_map_x][context.s_map_y + 1] & LOMASK
        if (z >= L) and (z <= H):
            return True
    if context.s_map_x > 0:
        z = context.map_data[context.s_map_x - 1][context.s_map_y] & LOMASK
        if (z >= L) and (z <= H):
            return True

    return False


def RoadTest(x: int) -> bool:
    """
    Test if tile is a valid road/rail for traffic.

    Args:
        x: Tile ID (with or without status bits)

    Returns:
        True if tile is road/rail, False otherwise
    """
    x = x & LOMASK
    if x < ROADBASE:
        return False
    if x > LASTRAIL:
        return False
    if (x >= POWERBASE) and (x < RAILHPOWERV):
        return False
    return True


def AverageTrf(context: AppContext) -> int:
    """
    Compute an average of the traffic density overlay.
    :param context: 
    """
    if not context.trf_density:
        return 0

    total = 0
    count = 0
    for row in context.trf_density:
        total += sum(row)
        count += len(row)

    return int(total / count) if count else 0
