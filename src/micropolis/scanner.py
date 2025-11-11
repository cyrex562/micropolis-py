"""
scanner.py - Zone scanning and analysis functions for Micropolis Python port

This module contains the scanning and analysis functions ported from s_scan.c,
implementing fire analysis, population density scanning, pollution/terrain/land value
analysis, crime scanning, and various smoothing operations.
"""

import micropolis.constants
from . import simulation, types, zones

# ============================================================================
# Global Scanner State
# ============================================================================

# Map update flags
NewMap: int = 0
NewMapFlags: list[int] = [0] * micropolis.constants.NMAPS
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


def FireAnalysis() -> None:
    """
    Make fire rate map from fire station map.

    Ported from FireAnalysis() in s_scan.c.
    Called during simulation initialization.
    """
    SmoothFSMap()
    SmoothFSMap()
    SmoothFSMap()

    for x in range(micropolis.constants.SM_X):
        for y in range(micropolis.constants.SM_Y):
            types.fire_rate[x][y] = types.fire_st_map[x][y]

    NewMapFlags[micropolis.constants.DYMAP] = 1
    NewMapFlags[micropolis.constants.FIMAP] = 1


# ============================================================================
# Population Density Scanning
# ============================================================================


def PopDenScan() -> None:
    """
    Sets population density, commercial rate, and finds city center of mass.

    Ported from PopDenScan() in s_scan.c.
    Called during simulation initialization.
    """
    Xtot = 0
    Ytot = 0
    Ztot = 0

    ClrTemArray()

    for x in range(micropolis.constants.WORLD_X):
        for y in range(micropolis.constants.WORLD_Y):
            z = types.map_data[x][y]
            if z & types.ZONEBIT:
                z = z & types.LOMASK
                types.s_map_x = x
                types.s_map_y = y
                z = GetPDen(z) << 3
                if z > 254:
                    z = 254
                types.tem[x >> 1][y >> 1] = z
                Xtot += x
                Ytot += y
                Ztot += 1

    DoSmooth()  # T1 -> T2
    DoSmooth2()  # T2 -> T1
    DoSmooth()  # T1 -> T2

    for x in range(micropolis.constants.HWLDX):
        for y in range(micropolis.constants.HWLDY):
            types.pop_density[x][y] = types.tem2[x][y] << 1

    DistIntMarket()  # set ComRate w/ (/ComMap)

    # Find Center of Mass for City
    global CCx, CCy, CCx2, CCy2
    if Ztot:
        CCx = Xtot // Ztot
        CCy = Ytot // Ztot
    else:
        CCx = micropolis.constants.HWLDX  # if pop=0 center of Map is CC
        CCy = micropolis.constants.HWLDY

    CCx2 = CCx >> 1
    CCy2 = CCy >> 1

    NewMapFlags[micropolis.constants.DYMAP] = 1
    NewMapFlags[micropolis.constants.PDMAP] = 1
    NewMapFlags[micropolis.constants.RGMAP] = 1


def GetPDen(Ch9: int) -> int:
    """
    Get population density for a zone tile.

    Ported from GetPDen() in s_scan.c.

    Args:
        Ch9: Zone tile value

    Returns:
        Population density value
    """
    if Ch9 == types.FREEZ:
        pop = zones.DoFreePop()
        return pop

    if Ch9 < types.COMBASE:
        pop = zones.RZPop(Ch9)
        return pop

    if Ch9 < types.INDBASE:
        pop = zones.CZPop(Ch9) << 3
        return pop

    if Ch9 < types.PORTBASE:
        pop = zones.IZPop(Ch9) << 3
        return pop

    return 0


# ============================================================================
# Pollution, Terrain, Land Value Scanning
# ============================================================================


def PTLScan() -> None:
    """
    Does pollution, terrain, and land value scanning.

    Ported from PTLScan() in s_scan.c.
    Called during simulation initialization.
    """
    ptot = 0
    LVtot = 0
    LVnum = 0

    # Initialize Qtem array
    for x in range(micropolis.constants.QWX):
        for y in range(micropolis.constants.QWY):
            types.Qtem[x][y] = 0

    for x in range(micropolis.constants.HWLDX):
        for y in range(micropolis.constants.HWLDY):
            Plevel = 0
            LVflag = 0
            zx = x << 1
            zy = y << 1

            for Mx in range(zx, zx + 2):
                for My in range(zy, zy + 2):
                    loc = types.map_data[Mx][My] & types.LOMASK
                    if loc:
                        if loc < types.RUBBLE:
                            types.Qtem[x >> 1][y >> 1] += 15  # inc terrainMem
                            continue
                        Plevel += GetPValue(loc)
                        if loc >= types.ROADBASE:
                            LVflag += 1

            # Cap pollution level
            if Plevel > 255:
                Plevel = 255

            types.tem[x][y] = Plevel

            if LVflag:  # LandValue Equation
                dis = 34 - GetDisCC(x, y)
                dis = dis << 2
                dis += types.terrain_mem[x >> 1][y >> 1]
                dis -= types.pollution_mem[x][y]
                if types.crime_mem[x][y] > 190:
                    dis -= 20
                if dis > 250:
                    dis = 250
                if dis < 1:
                    dis = 1
                types.land_value_mem[x][y] = dis
                LVtot += dis
                LVnum += 1
            else:
                types.land_value_mem[x][y] = 0

    # Calculate land value average
    if LVnum:
        types.lv_average = LVtot // LVnum
    else:
        types.lv_average = 0

    DoSmooth()
    DoSmooth2()

    # Process pollution data
    global PolMaxX, PolMaxY
    pmax = 0
    pnum = 0
    ptot = 0

    for x in range(micropolis.constants.HWLDX):
        for y in range(micropolis.constants.HWLDY):
            z = types.tem[x][y]
            types.pollution_mem[x][y] = z
            if z:  # get pollute average
                pnum += 1
                ptot += z
                # find max pol for monster
                if (z > pmax) or ((z == pmax) and ((simulation.Rand16() & 3) == 0)):
                    pmax = z
                    PolMaxX = x << 1
                    PolMaxY = y << 1

    # Calculate pollution average
    if pnum:
        types.pollute_average = ptot // pnum
    else:
        types.pollute_average = 0

    SmoothTerrain()

    NewMapFlags[micropolis.constants.DYMAP] = 1
    NewMapFlags[micropolis.constants.PLMAP] = 1
    NewMapFlags[micropolis.constants.LVMAP] = 1


def GetPValue(loc: int) -> int:
    """
    Get pollution value for a tile location.

    Ported from GetPValue() in s_scan.c.

    Args:
        loc: Tile location value

    Returns:
        Pollution contribution value
    """
    if loc < types.POWERBASE:
        if loc >= types.HTRFBASE:
            return 75  # heavy traf
        if loc >= types.LTRFBASE:
            return 50  # light traf
        if loc < types.ROADBASE:
            if loc > types.FIREBASE:
                return 90
            if loc >= types.RADTILE:
                return 255  # radioactivity
    else:
        if loc <= types.LASTIND:
            return 0
        if loc < types.PORTBASE:
            return 50  # Ind
        if loc <= types.LASTPOWERPLANT:
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


def CrimeScan() -> None:
    """
    Analyze crime rates based on land value, population, and police coverage.

    Ported from CrimeScan() in s_scan.c.
    Called during simulation initialization.
    """
    SmoothPSMap()
    SmoothPSMap()
    SmoothPSMap()

    totz = 0
    numz = 0
    cmax = 0

    global CrimeMaxX, CrimeMaxY

    for x in range(micropolis.constants.HWLDX):
        for y in range(micropolis.constants.HWLDY):
            z = types.land_value_mem[x][y]
            if z:
                numz += 1
                z = 128 - z
                z += types.pop_density[x][y]
                if z > 300:
                    z = 300
                z -= types.police_map[x >> 2][y >> 2]
                if z > 250:
                    z = 250
                if z < 0:
                    z = 0
                types.crime_mem[x][y] = z
                totz += z

                # Find max crime for monster
                if (z > cmax) or ((z == cmax) and ((simulation.Rand16() & 3) == 0)):
                    cmax = z
                    CrimeMaxX = x << 1
                    CrimeMaxY = y << 1
            else:
                types.crime_mem[x][y] = 0

    # Calculate crime average
    if numz:
        types.crime_average = totz // numz
    else:
        types.crime_average = 0

    # Copy police map to effect map
    for x in range(micropolis.constants.SM_X):
        for y in range(micropolis.constants.SM_Y):
            types.police_map_effect[x][y] = types.police_map[x][y]

    NewMapFlags[micropolis.constants.DYMAP] = 1
    NewMapFlags[micropolis.constants.CRMAP] = 1
    NewMapFlags[micropolis.constants.POMAP] = 1


# ============================================================================
# Smoothing Functions
# ============================================================================


def SmoothTerrain() -> None:
    """
    Smooth terrain data using dithering algorithm.

    Ported from SmoothTerrain() in s_scan.c.
    """
    if DonDither & 1:
        x = 0
        y = 0
        z = 0
        dir = 1

        while x < micropolis.constants.QWX:
            while (y != micropolis.constants.QWY) and (y != -1):
                z += types.Qtem[x if x == 0 else x - 1][y]
                z += types.Qtem[x if x == (micropolis.constants.QWX - 1) else x + 1][y]
                z += types.Qtem[x][y if y == 0 else y - 1]
                z += types.Qtem[x][y if y == (micropolis.constants.QWY - 1) else y + 1]
                z += types.Qtem[x][y] << 2
                types.terrain_mem[x][y] = (z >> 3) & 0xFF
                z &= 0x7
                y += dir

            dir = -dir
            y += dir
            x += 1
    else:
        for x in range(micropolis.constants.QWX):
            for y in range(micropolis.constants.QWY):
                z = 0
                if x > 0:
                    z += types.Qtem[x - 1][y]
                if x < (micropolis.constants.QWX - 1):
                    z += types.Qtem[x + 1][y]
                if y > 0:
                    z += types.Qtem[x][y - 1]
                if y < (micropolis.constants.QWY - 1):
                    z += types.Qtem[x][y + 1]
                types.terrain_mem[x][y] = ((z >> 2) + types.Qtem[x][y]) >> 1


def DoSmooth() -> None:
    """
    Smooth data in tem[x][y] into tem2[x][y].

    Ported from DoSmooth() in s_scan.c.
    """
    if DonDither & 2:
        x = 0
        y = 0
        z = 0
        dir = 1

        while x < micropolis.constants.HWLDX:
            while (y != micropolis.constants.HWLDY) and (y != -1):
                z += types.tem[x if x == 0 else x - 1][y]
                z += types.tem[x if x == (micropolis.constants.HWLDX - 1) else x + 1][y]
                z += types.tem[x][y if y == 0 else y - 1]
                z += types.tem[x][y if y == (micropolis.constants.HWLDY - 1) else y + 1]
                z += types.tem[x][y]
                types.tem2[x][y] = (z >> 2) & 0xFF
                z &= 3
                y += dir

            dir = -dir
            y += dir
            x += 1
    else:
        for x in range(micropolis.constants.HWLDX):
            for y in range(micropolis.constants.HWLDY):
                z = 0
                if x > 0:
                    z += types.tem[x - 1][y]
                if x < (micropolis.constants.HWLDX - 1):
                    z += types.tem[x + 1][y]
                if y > 0:
                    z += types.tem[x][y - 1]
                if y < (micropolis.constants.HWLDY - 1):
                    z += types.tem[x][y + 1]
                z = (z + types.tem[x][y]) >> 2
                if z > 255:
                    z = 255
                types.tem2[x][y] = z


def DoSmooth2() -> None:
    """
    Smooth data in tem2[x][y] into tem[x][y].

    Ported from DoSmooth2() in s_scan.c.
    """
    if DonDither & 4:
        x = 0
        y = 0
        z = 0
        dir = 1

        while x < micropolis.constants.HWLDX:
            while (y != micropolis.constants.HWLDY) and (y != -1):
                z += types.tem2[x if x == 0 else x - 1][y]
                z += types.tem2[x if x == (micropolis.constants.HWLDX - 1) else x + 1][
                    y
                ]
                z += types.tem2[x][y if y == 0 else y - 1]
                z += types.tem2[x][
                    y if y == (micropolis.constants.HWLDY - 1) else y + 1
                ]
                z += types.tem2[x][y]
                types.tem[x][y] = (z >> 2) & 0xFF
                z &= 3
                y += dir

            dir = -dir
            y += dir
            x += 1
    else:
        for x in range(micropolis.constants.HWLDX):
            for y in range(micropolis.constants.HWLDY):
                z = 0
                if x > 0:
                    z += types.tem2[x - 1][y]
                if x < (micropolis.constants.HWLDX - 1):
                    z += types.tem2[x + 1][y]
                if y > 0:
                    z += types.tem2[x][y - 1]
                if y < (micropolis.constants.HWLDY - 1):
                    z += types.tem2[x][y + 1]
                z = (z + types.tem2[x][y]) >> 2
                if z > 255:
                    z = 255
                types.tem[x][y] = z


def ClrTemArray() -> None:
    """
    Clear the temporary array.

    Ported from ClrTemArray() in s_scan.c.
    """
    z = 0
    for x in range(micropolis.constants.HWLDX):
        for y in range(micropolis.constants.HWLDY):
            types.tem[x][y] = z


def SmoothFSMap() -> None:
    """
    Smooth fire station map.

    Ported from SmoothFSMap() in s_scan.c.
    """
    for x in range(micropolis.constants.SM_X):
        for y in range(micropolis.constants.SM_Y):
            edge = 0
            if x > 0:
                edge += types.fire_st_map[x - 1][y]
            if x < (micropolis.constants.SM_X - 1):
                edge += types.fire_st_map[x + 1][y]
            if y > 0:
                edge += types.fire_st_map[x][y - 1]
            if y < (micropolis.constants.SM_Y - 1):
                edge += types.fire_st_map[x][y + 1]
            edge = (edge >> 2) + types.fire_st_map[x][y]
            types.stem[x][y] = edge >> 1

    for x in range(micropolis.constants.SM_X):
        for y in range(micropolis.constants.SM_Y):
            types.fire_st_map[x][y] = types.stem[x][y]


def SmoothPSMap() -> None:
    """
    Smooth police station map.

    Ported from SmoothPSMap() in s_scan.c.
    """
    for x in range(micropolis.constants.SM_X):
        for y in range(micropolis.constants.SM_Y):
            edge = 0
            if x > 0:
                edge += types.police_map[x - 1][y]
            if x < (micropolis.constants.SM_X - 1):
                edge += types.police_map[x + 1][y]
            if y > 0:
                edge += types.police_map[x][y - 1]
            if y < (micropolis.constants.SM_Y - 1):
                edge += types.police_map[x][y + 1]
            edge = (edge >> 2) + types.police_map[x][y]
            types.stem[x][y] = edge >> 1

    for x in range(micropolis.constants.SM_X):
        for y in range(micropolis.constants.SM_Y):
            types.police_map[x][y] = types.stem[x][y]


def DistIntMarket() -> None:
    """
    Distribute commercial rate based on distance from city center.

    Ported from DistIntMarket() in s_scan.c.
    """
    for x in range(micropolis.constants.SM_X):
        for y in range(micropolis.constants.SM_Y):
            z = GetDisCC(x << 2, y << 2)
            z = z << 2
            z = 64 - z
            types.com_rate[x][y] = z
