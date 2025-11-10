# traffic.py: Traffic simulation and pathfinding for Micropolis Python port
#
# This module implements the traffic generation and pathfinding system
# that simulates how residential, commercial, and industrial zones generate
# traffic and attempt to reach destinations via road networks.
#
# Original C file: s_traf.c
# Ported to maintain algorithmic fidelity with the original Micropolis simulation

import src.micropolis.types as types
import src.micropolis.macros as macros
import src.micropolis.random as random


# ============================================================================
# Traffic Generation Constants
# ============================================================================

MAXDIS = 30  # Maximum distance to try driving


# ============================================================================
# Traffic Generation Functions
# ============================================================================

def MakeTraf(Zt: int) -> int:
    """
    Generate traffic from a zone.

    Attempts to find a road on the zone perimeter and drive to a destination.
    If successful, updates traffic density.

    Args:
        Zt: Zone type (0=Residential, 1=Commercial, 2=Industrial)

    Returns:
        1 if traffic passed, 0 if failed, -1 if no road found
    """
    # Save current position
    xtem = types.SMapX
    ytem = types.SMapY

    # Set zone source type
    types.Zsource = Zt
    types.PosStackN = 0

    # Check for telecommuting (currently disabled in original)
    # if (not random.Rand(2)) and FindPTele():
    #     return True

    # Look for road on zone perimeter
    if FindPRoad():
        # Attempt to drive somewhere
        if TryDrive():
            # If successful, increment traffic density
            SetTrafMem()
            types.SMapX = xtem
            types.SMapY = ytem
            return 1  # traffic passed
        else:
            types.SMapX = xtem
            types.SMapY = ytem
            return 0  # traffic failed
    else:
        return -1  # no road found


def SetTrafMem() -> None:
    """
    Update traffic density memory along the driven path.

    Increments traffic density for road tiles along the path taken.
    Occasionally spawns police cars for high traffic areas.
    """

    for x in range(types.PosStackN, 0, -1):
        PullPos()
        if macros.TestBounds(types.SMapX, types.SMapY):
            z = types.Map[types.SMapX][types.SMapY] & macros.LOMASK
            if (z >= macros.ROADBASE) and (z < macros.POWERBASE):
                # Update traffic density (downsampled to 60x50 grid)
                density_x = types.SMapX >> 1
                density_y = types.SMapY >> 1
                z = types.TrfDensity[density_x][density_y]
                z += 50
                if (z > 240) and (not random.Rand(5)):
                    z = 240
                    # Set police car destination
                    types.TrafMaxX = types.SMapX << 4
                    types.TrafMaxY = types.SMapY << 4
                    # Try to assign police car sprite
                    sprite = types.GetSprite()
                    if sprite and (sprite.control == -1):
                        sprite.dest_x = types.TrafMaxX
                        sprite.dest_y = types.TrafMaxY
                types.TrfDensity[density_x][density_y] = z


def PushPos() -> None:
    """
    Push current position onto the position stack.
    """
    types.PosStackN += 1
    # Ensure stacks are large enough
    while len(types.SMapXStack) <= types.PosStackN:
        types.SMapXStack.append(0)
    while len(types.SMapYStack) <= types.PosStackN:
        types.SMapYStack.append(0)
    types.SMapXStack[types.PosStackN] = types.SMapX
    types.SMapYStack[types.PosStackN] = types.SMapY


def PullPos() -> None:
    """
    Pull position from the position stack.
    """
    types.SMapX = types.SMapXStack[types.PosStackN]
    types.SMapY = types.SMapYStack[types.PosStackN]
    types.PosStackN -= 1


def FindPRoad() -> bool:
    """
    Look for road on zone edges (perimeter).

    Checks 12 perimeter positions around the current zone for road tiles.

    Returns:
        True if road found, False otherwise
    """
    # Perimeter offsets: 12 positions around zone
    PerimX = [-1, 0, 1, 2, 2, 2, 1, 0, -1, -2, -2, -2]
    PerimY = [-2, -2, -2, -1, 0, 1, 2, 2, 2, 1, 0, -1]

    for z in range(12):
        tx = types.SMapX + PerimX[z]
        ty = types.SMapY + PerimY[z]
        if macros.TestBounds(tx, ty):
            if RoadTest(types.Map[tx][ty]):
                types.SMapX = tx
                types.SMapY = ty
                return True
    return False


def FindPTele() -> bool:
    """
    Look for telecommunication on zone edges.

    Checks perimeter positions for telecommunication tiles.

    Returns:
        True if telecommunication found, False otherwise
    """
    # Perimeter offsets: same as FindPRoad
    PerimX = [-1, 0, 1, 2, 2, 2, 1, 0, -1, -2, -2, -2]
    PerimY = [-2, -2, -2, -1, 0, 1, 2, 2, 2, 1, 0, -1]

    for z in range(12):
        tx = types.SMapX + PerimX[z]
        ty = types.SMapY + PerimY[z]
        if macros.TestBounds(tx, ty):
            tile = types.Map[tx][ty] & macros.LOMASK
            if (tile >= macros.TELEBASE) and (tile <= macros.TELELAST):
                return True
    return False


def TryDrive() -> bool:
    """
    Attempt to drive to a destination.

    Uses pathfinding to try to reach a destination within MAXDIS steps.

    Returns:
        True if destination reached, False if failed
    """
    types.LDir = 5  # Reset last direction

    for z in range(macros.MAXDIS):
        if TryGo(z):
            if DriveDone():
                return True  # Destination reached
        else:
            if types.PosStackN:  # Dead end, backup
                types.PosStackN -= 1
                z += 3  # Skip ahead
            else:
                return False  # Give up at start

    return False  # Gone max distance


def TryGo(z: int) -> bool:
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
    rdir = random.sim_rand() & 3
    for x in range(rdir, rdir + 4):
        realdir = x & 3
        if realdir == types.LDir:
            continue  # Skip last direction
        if RoadTest(GetFromMap(realdir)):
            MoveMapSim(realdir)
            types.LDir = (realdir + 2) & 3  # Set new last direction
            if z & 1:  # Save position every other move
                PushPos()
            return True
    return False


def GetFromMap(x: int) -> int:
    """
    Get tile from map in specified direction.

    Args:
        x: Direction (0=north, 1=east, 2=south, 3=west)

    Returns:
        Tile ID if in bounds, False (0) otherwise
    """
    if x == 0:  # North
        if types.SMapY > 0:
            return types.Map[types.SMapX][types.SMapY - 1] & macros.LOMASK
    elif x == 1:  # East
        if types.SMapX < (macros.WORLD_X - 1):
            return types.Map[types.SMapX + 1][types.SMapY] & macros.LOMASK
    elif x == 2:  # South
        if types.SMapY < (macros.WORLD_Y - 1):
            return types.Map[types.SMapX][types.SMapY + 1] & macros.LOMASK
    elif x == 3:  # West
        if types.SMapX > 0:
            return types.Map[types.SMapX - 1][types.SMapY] & macros.LOMASK

    return 0  # False


def MoveMapSim(realdir: int) -> None:
    """
    Move position in specified direction.

    Args:
        realdir: Direction to move (0=north, 1=east, 2=south, 3=west)
    """
    if realdir == 0:  # North
        types.SMapY -= 1
    elif realdir == 1:  # East
        types.SMapX += 1
    elif realdir == 2:  # South
        types.SMapY += 1
    elif realdir == 3:  # West
        types.SMapX -= 1


def DriveDone() -> bool:
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
    TARGL = [macros.COMBASE, macros.LHTHR, macros.LHTHR]  # Low range
    TARGH = [macros.NUCLEAR, macros.PORT, macros.COMBASE]  # High range

    L = TARGL[types.Zsource]
    H = TARGH[types.Zsource]

    # Check all 4 adjacent tiles
    if types.SMapY > 0:
        z = types.Map[types.SMapX][types.SMapY - 1] & macros.LOMASK
        if (z >= L) and (z <= H):
            return True
    if types.SMapX < (macros.WORLD_X - 1):
        z = types.Map[types.SMapX + 1][types.SMapY] & macros.LOMASK
        if (z >= L) and (z <= H):
            return True
    if types.SMapY < (macros.WORLD_Y - 1):
        z = types.Map[types.SMapX][types.SMapY + 1] & macros.LOMASK
        if (z >= L) and (z <= H):
            return True
    if types.SMapX > 0:
        z = types.Map[types.SMapX - 1][types.SMapY] & macros.LOMASK
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
    x = x & macros.LOMASK
    if x < macros.ROADBASE:
        return False
    if x > macros.LASTRAIL:
        return False
    if (x >= macros.POWERBASE) and (x < macros.RAILHPOWERV):
        return False
    return True