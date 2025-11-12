"""
scanner.py - Zone scanning and analysis functions for Micropolis Python port

This module contains the scanning and analysis functions ported from s_scan.c,
implementing fire analysis, population density scanning, pollution/terrain/land value
analysis, crime scanning, and various smoothing operations.
"""
from src.micropolis.constants import NMAPS, SM_X, SM_Y, DYMAP, FIMAP, WORLD_X, WORLD_Y, ZONEBIT, LOMASK, HWLDX, HWLDY, \
    PDMAP, RGMAP, FREEZ, COMBASE, INDBASE, PORTBASE, QWX, QWY, RUBBLE, ROADBASE, PLMAP, LVMAP, POWERBASE, HTRFBASE, \
    LTRFBASE, FIREBASE, RADTILE, LASTIND, LASTPOWERPLANT, CRMAP, POMAP
from src.micropolis.context import AppContext
from src.micropolis.simulation import rand16
from src.micropolis.zones import DoFreePop, RZPop, CZPop, IZPop

# ============================================================================
# Global Scanner State
# ============================================================================

# Map update flags
NewMap: int = 0
NewMapFlags: list[int] = [0] * NMAPS
CCx: int = 0
CCy: int = 0
CCx2: int = 0
CCy2: int = 0
PolMaxX: int = 0
PolMaxY: int = 0
CrimeMaxX: int = 0
CrimeMaxY: int = 0
DonDither: int = 0


# ============================================================================
# Fire Analysis Functions
# ============================================================================


def FireAnalysis(context: AppContext) -> None:
    """
    Make fire rate map from fire station map.

    Ported from FireAnalysis() in s_scan.c.
    Called during simulation initialization.
    :param context: 
    """
    SmoothFSMap(context)
    SmoothFSMap(context)
    SmoothFSMap(context)

    for x in range(SM_X):
        for y in range(SM_Y):
            context.fire_rate[x][y] = context.fire_st_map[x][y]

    NewMapFlags[DYMAP] = 1
    NewMapFlags[FIMAP] = 1


# ============================================================================
# Population Density Scanning
# ============================================================================


def PopDenScan(context: AppContext) -> None:
    """
    Sets population density, commercial rate, and finds city center of mass.

    Ported from PopDenScan() in s_scan.c.
    Called during simulation initialization.
    :param context: 
    """
    Xtot = 0
    Ytot = 0
    Ztot = 0

    ClrTemArray(context)

    for x in range(WORLD_X):
        for y in range(WORLD_Y):
            z = context.map_data[x][y]
            if z & ZONEBIT:
                z = z & LOMASK
                context.s_map_x = x
                context.s_map_y = y
                z = GetPDen(z) << 3
                if z > 254:
                    z = 254
                context.tem[x >> 1][y >> 1] = z
                Xtot += x
                Ytot += y
                Ztot += 1

    DoSmooth(context)  # T1 -> T2
    DoSmooth2(context)  # T2 -> T1
    DoSmooth(context)  # T1 -> T2

    for x in range(HWLDX):
        for y in range(HWLDY):
            context.pop_density[x][y] = context.tem2[x][y] << 1

    DistIntMarket(context)  # set ComRate w/ (/ComMap)

    # Find Center of Mass for City
    # global CCx, CCy, CCx2, CCy2
    if Ztot:
        context.CCx = Xtot // Ztot
        context.CCy = Ytot // Ztot
    else:
        context.CCx = HWLDX  # if pop=0 center of Map is CC
        context.CCy = HWLDY

    context.CCx2 = context.CCx >> 1
    context.CCy2 = context.CCy >> 1

    NewMapFlags[DYMAP] = 1
    NewMapFlags[PDMAP] = 1
    NewMapFlags[RGMAP] = 1


def GetPDen(context: AppContext, Ch9: int) -> int:
    """
    Get population density for a zone tile.

    Ported from GetPDen() in s_scan.c.

    Args:
        context: Application context
        Ch9: Zone tile value

    Returns:
        Population density value
    """
    if Ch9 == FREEZ:
        pop = DoFreePop(context)
        return pop

    if Ch9 < COMBASE:
        pop = RZPop(Ch9)
        return pop

    if Ch9 < INDBASE:
        pop = CZPop(Ch9) << 3
        return pop

    if Ch9 < PORTBASE:
        pop = IZPop(Ch9) << 3
        return pop

    return 0


# ============================================================================
# Pollution, Terrain, Land Value Scanning
# ============================================================================


def PTLScan(context: AppContext) -> None:
    """
    Does pollution, terrain, and land value scanning.

    Ported from PTLScan() in s_scan.c.
    Called during simulation initialization.
    :param context: 
    """
    ptot = 0
    LVtot = 0
    LVnum = 0

    # Initialize Qtem array
    for x in range(QWX):
        for y in range(QWY):
            context.Qtem[x][y] = 0

    for x in range(HWLDX):
        for y in range(HWLDY):
            Plevel = 0
            LVflag = 0
            zx = x << 1
            zy = y << 1

            for Mx in range(zx, zx + 2):
                for My in range(zy, zy + 2):
                    loc = context.map_data[Mx][My] & LOMASK
                    if loc:
                        if loc < RUBBLE:
                            context.Qtem[x >> 1][y >> 1] += 15  # inc terrainMem
                            continue
                        Plevel += GetPValue(loc)
                        if loc >= ROADBASE:
                            LVflag += 1

            # Cap pollution level
            if Plevel > 255:
                Plevel = 255

            context.tem[x][y] = Plevel

            if LVflag:  # LandValue Equation
                dis = 34 - GetDisCC(x, y)
                dis = dis << 2
                dis += context.terrain_mem[x >> 1][y >> 1]
                dis -= context.pollution_mem[x][y]
                if context.crime_mem[x][y] > 190:
                    dis -= 20
                if dis > 250:
                    dis = 250
                if dis < 1:
                    dis = 1
                context.land_value_mem[x][y] = dis
                LVtot += dis
                LVnum += 1
            else:
                context.land_value_mem[x][y] = 0

    # Calculate land value average
    if LVnum:
        context.lv_average = LVtot // LVnum
    else:
        context.lv_average = 0

    DoSmooth(context)
    DoSmooth2(context)

    # Process pollution data
    # global PolMaxX, PolMaxY
    pmax = 0
    pnum = 0
    ptot = 0

    for x in range(HWLDX):
        for y in range(HWLDY):
            z = context.tem[x][y]
            context.pollution_mem[x][y] = z
            if z:  # get pollute average
                pnum += 1
                ptot += z
                # find max pol for monster
                if (z > pmax) or ((z == pmax) and ((rand16() & 3) == 0)):
                    pmax = z
                    context.PolMaxX = x << 1
                    context.PolMaxY = y << 1

    # Calculate pollution average
    if pnum:
        context.pollute_average = ptot // pnum
    else:
        context.pollute_average = 0

    SmoothTerrain(context)

    NewMapFlags[DYMAP] = 1
    NewMapFlags[PLMAP] = 1
    NewMapFlags[LVMAP] = 1


def GetPValue(loc: int) -> int:
    """
    Get pollution value for a tile location.

    Ported from GetPValue() in s_scan.c.

    Args:
        loc: Tile location value

    Returns:
        Pollution contribution value
    """
    if loc < POWERBASE:
        if loc >= HTRFBASE:
            return 75  # heavy traf
        if loc >= LTRFBASE:
            return 50  # light traf
        if loc < ROADBASE:
            if loc > FIREBASE:
                return 90
            if loc >= RADTILE:
                return 255  # radioactivity
    else:
        if loc <= LASTIND:
            return 0
        if loc < PORTBASE:
            return 50  # Ind
        if loc <= LASTPOWERPLANT:
            return 100  # prt, aprt, cpp

    return 0


def GetDisCC(x: int, y: int) -> int:
    """
    Get distance from city center.

    Ported from GetDisCC() in s_scan.c.

    Args:
        x: X coordinate
        y: Y coordinate

    Returns:
        Distance from city center (capped at 32)
    """
    if x > CCx2:
        xdis = x - CCx2
    else:
        xdis = CCx2 - x

    if y > CCy2:
        ydis = y - CCy2
    else:
        ydis = CCy2 - y

    z = xdis + ydis
    if z > 32:
        return 32
    else:
        return z


# ============================================================================
# Crime Analysis
# ============================================================================


def CrimeScan(context: AppContext) -> None:
    """
    Analyze crime rates based on land value, population, and police coverage.

    Ported from CrimeScan() in s_scan.c.
    Called during simulation initialization.
    :param context: 
    """
    SmoothPSMap(context)
    SmoothPSMap(context)
    SmoothPSMap(context)

    totz = 0
    numz = 0
    cmax = 0

    # global CrimeMaxX, CrimeMaxY

    for x in range(HWLDX):
        for y in range(HWLDY):
            z = context.land_value_mem[x][y]
            if z:
                numz += 1
                z = 128 - z
                z += context.pop_density[x][y]
                if z > 300:
                    z = 300
                z -= context.police_map[x >> 2][y >> 2]
                if z > 250:
                    z = 250
                if z < 0:
                    z = 0
                context.crime_mem[x][y] = z
                totz += z

                # Find max crime for monster
                if (z > cmax) or ((z == cmax) and ((rand16() & 3) == 0)):
                    cmax = z
                    context.CrimeMaxX = x << 1
                    context.CrimeMaxY = y << 1
            else:
                context.crime_mem[x][y] = 0

    # Calculate crime average
    if numz:
        context.crime_average = totz // numz
    else:
        context.crime_average = 0

    # Copy police map to effect map
    for x in range(SM_X):
        for y in range(SM_Y):
            context.police_map_effect[x][y] = context.police_map[x][y]

    NewMapFlags[DYMAP] = 1
    NewMapFlags[CRMAP] = 1
    NewMapFlags[POMAP] = 1


# ============================================================================
# Smoothing Functions
# ============================================================================


def SmoothTerrain(context: AppContext) -> None:
    """
    Smooth terrain data using dithering algorithm.

    Ported from SmoothTerrain() in s_scan.c.
    :param context:
    """
    if DonDither & 1:
        x = 0
        y = 0
        z = 0
        direction = 1

        while x < QWX:
            while (y != QWY) and (y != -1):
                z += context.Qtem[x if x == 0 else x - 1][y]
                z += context.Qtem[x if x == (QWX - 1) else x + 1][y]
                z += context.Qtem[x][y if y == 0 else y - 1]
                z += context.Qtem[x][y if y == (QWY - 1) else y + 1]
                z += context.Qtem[x][y] << 2
                context.terrain_mem[x][y] = (z >> 3) & 0xFF
                z &= 0x7
                y += direction

            direction = -direction
            y += direction
            x += 1
    else:
        for x in range(QWX):
            for y in range(QWY):
                z = 0
                if x > 0:
                    z += context.Qtem[x - 1][y]
                if x < (QWX - 1):
                    z += context.Qtem[x + 1][y]
                if y > 0:
                    z += context.Qtem[x][y - 1]
                if y < (QWY - 1):
                    z += context.Qtem[x][y + 1]
                context.terrain_mem[x][y] = ((z >> 2) + context.Qtem[x][y]) >> 1


def DoSmooth(context: AppContext) -> None:
    """
    Smooth data in tem[x][y] into tem2[x][y].

    Ported from DoSmooth() in s_scan.c.
    :param context:
    """
    if DonDither & 2:
        x = 0
        y = 0
        z = 0
        direction = 1

        while x < HWLDX:
            while (y != HWLDY) and (y != -1):
                z += context.tem[x if x == 0 else x - 1][y]
                z += context.tem[x if x == (HWLDX - 1) else x + 1][y]
                z += context.tem[x][y if y == 0 else y - 1]
                z += context.tem[x][y if y == (HWLDY - 1) else y + 1]
                z += context.tem[x][y]
                context.tem2[x][y] = (z >> 2) & 0xFF
                z &= 3
                y += direction

            direction = -direction
            y += direction
            x += 1
    else:
        for x in range(HWLDX):
            for y in range(HWLDY):
                z = 0
                if x > 0:
                    z += context.tem[x - 1][y]
                if x < (HWLDX - 1):
                    z += context.tem[x + 1][y]
                if y > 0:
                    z += context.tem[x][y - 1]
                if y < (HWLDY - 1):
                    z += context.tem[x][y + 1]
                z = (z + context.tem[x][y]) >> 2
                if z > 255:
                    z = 255
                context.tem2[x][y] = z


def DoSmooth2(context: AppContext) -> None:
    """
    Smooth data in tem2[x][y] into tem[x][y].

    Ported from DoSmooth2() in s_scan.c.
    :param context:
    """
    if DonDither & 4:
        x = 0
        y = 0
        z = 0
        direction = 1

        while x < HWLDX:
            while (y != HWLDY) and (y != -1):
                z += context.tem2[x if x == 0 else x - 1][y]
                z += context.tem2[x if x == (HWLDX - 1) else x + 1][
                    y
                ]
                z += context.tem2[x][y if y == 0 else y - 1]
                z += context.tem2[x][
                    y if y == (HWLDY - 1) else y + 1
                ]
                z += context.tem2[x][y]
                context.tem[x][y] = (z >> 2) & 0xFF
                z &= 3
                y += direction

            direction = -direction
            y += direction
            x += 1
    else:
        for x in range(HWLDX):
            for y in range(HWLDY):
                z = 0
                if x > 0:
                    z += context.tem2[x - 1][y]
                if x < (HWLDX - 1):
                    z += context.tem2[x + 1][y]
                if y > 0:
                    z += context.tem2[x][y - 1]
                if y < (HWLDY - 1):
                    z += context.tem2[x][y + 1]
                z = (z + context.tem2[x][y]) >> 2
                if z > 255:
                    z = 255
                context.tem[x][y] = z


def ClrTemArray(context: AppContext) -> None:
    """
    Clear the temporary array.

    Ported from ClrTemArray() in s_scan.c.
    :param context:
    """
    z = 0
    for x in range(HWLDX):
        for y in range(HWLDY):
            context.tem[x][y] = z


def SmoothFSMap(context: AppContext) -> None:
    """
    Smooth fire station map.

    Ported from SmoothFSMap() in s_scan.c.
    :param context:
    """
    for x in range(SM_X):
        for y in range(SM_Y):
            edge = 0
            if x > 0:
                edge += context.fire_st_map[x - 1][y]
            if x < (SM_X - 1):
                edge += context.fire_st_map[x + 1][y]
            if y > 0:
                edge += context.fire_st_map[x][y - 1]
            if y < (SM_Y - 1):
                edge += context.fire_st_map[x][y + 1]
            edge = (edge >> 2) + context.fire_st_map[x][y]
            context.stem[x][y] = edge >> 1

    for x in range(SM_X):
        for y in range(SM_Y):
            context.fire_st_map[x][y] = context.stem[x][y]


def SmoothPSMap(context: AppContext) -> None:
    """
    Smooth police station map.

    Ported from SmoothPSMap() in s_scan.c.
    """
    for x in range(SM_X):
        for y in range(SM_Y):
            edge = 0
            if x > 0:
                edge += context.police_map[x - 1][y]
            if x < (SM_X - 1):
                edge += context.police_map[x + 1][y]
            if y > 0:
                edge += context.police_map[x][y - 1]
            if y < (SM_Y - 1):
                edge += context.police_map[x][y + 1]
            edge = (edge >> 2) + context.police_map[x][y]
            context.stem[x][y] = edge >> 1

    for x in range(SM_X):
        for y in range(SM_Y):
            context.police_map[x][y] = context.stem[x][y]


def DistIntMarket(context: AppContext) -> None:
    """
    Distribute commercial rate based on distance from city center.

    Ported from DistIntMarket() in s_scan.c.
    :param context:
    """
    for x in range(SM_X):
        for y in range(SM_Y):
            z = GetDisCC(x << 2, y << 2)
            z = z << 2
            z = 64 - z
            context.com_rate[x][y] = z
