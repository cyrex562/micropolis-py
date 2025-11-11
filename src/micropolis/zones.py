"""
zones.py - Zone processing and growth mechanics for Micropolis Python port

This module contains the zone growth and management functions ported from s_zone.c,
implementing residential, commercial, and industrial zone development logic.
"""

import micropolis.power
from . import types, macros, simulation


# ============================================================================
# Zone Processing Functions
# ============================================================================


def DoZone() -> None:
    """
    Main zone processing function.

    Determines zone type and calls appropriate processing function.
    Ported from DoZone() in s_zone.c.
    """
    ZonePwrFlg = SetZPower()  # Set Power Bit in Map from PowerMap

    if ZonePwrFlg:
        types.pwrd_z_cnt += 1
    else:
        types.un_pwrd_z_cnt += 1

    if types.cchr9 > types.PORTBASE:  # do Special Zones
        simulation.DoSPZone(ZonePwrFlg)
        return

    if types.cchr9 < types.HOSPITAL:
        DoResidential(ZonePwrFlg)
        return

    if types.cchr9 < types.COMBASE:
        DoHospChur()
        return

    if types.cchr9 < types.INDBASE:
        DoCommercial(ZonePwrFlg)
        return

    DoIndustrial(ZonePwrFlg)


def DoHospChur() -> None:
    """
    Process hospital and church zones.

    Handles hospital and church population counting and repair.
    Ported from DoHospChur() in s_zone.c.
    """
    if types.cchr9 == types.HOSPITAL:
        types.hosp_pop += 1
        if (types.city_time & 15) == 0:
            simulation.RepairZone(types.HOSPITAL, 3)  # post
        if types.need_hosp == -1:
            if simulation.Rand(20) == 0:
                ZonePlop(types.RESBASE)

    if types.cchr9 == types.CHURCH:
        types.church_pop += 1
        if (types.city_time & 15) == 0:
            simulation.RepairZone(types.CHURCH, 3)  # post
        if types.need_church == -1:
            if simulation.Rand(20) == 0:
                ZonePlop(types.RESBASE)


def SetSmoke(ZonePower: int) -> None:
    """
    Set smoke animation for industrial zones.

    Ported from SetSmoke() in s_zone.c.

    Args:
        ZonePower: Whether zone is powered
    """
    # Animation tables
    AniThis = [True, False, True, True, False, False, True, True]
    DX1 = [-1, 0, 1, 0, 0, 0, 0, 1]
    DY1 = [-1, 0, -1, -1, 0, 0, -1, -1]
    DX2 = [-1, 0, 1, 1, 0, 0, 1, 1]
    DY2 = [-1, 0, 0, -1, 0, 0, -1, 0]
    AniTabA = [0, 0, 32, 40, 0, 0, 48, 56]
    AniTabB = [0, 0, 36, 44, 0, 0, 52, 60]
    AniTabC = [types.IND1, 0, types.IND2, types.IND4, 0, 0, types.IND6, types.IND8]
    AniTabD = [types.IND1, 0, types.IND3, types.IND5, 0, 0, types.IND7, types.IND9]

    if types.cchr9 < types.IZB:
        return

    z = (types.cchr9 - types.IZB) >> 3
    z = z & 7

    if AniThis[z]:
        xx = types.s_map_x + DX1[z]
        yy = types.s_map_y + DY1[z]
        if macros.TestBounds(xx, yy):
            if ZonePower:
                if (types.map_data[xx][yy] & types.LOMASK) == AniTabC[z]:
                    types.map_data[xx][yy] = types.ASCBIT | (
                        types.SMOKEBASE + AniTabA[z]
                    )
                    # Note: Original has duplicate line, keeping for compatibility
                    types.map_data[xx][yy] = types.ASCBIT | (
                        types.SMOKEBASE + AniTabB[z]
                    )
            else:
                if (types.map_data[xx][yy] & types.LOMASK) > AniTabC[z]:
                    types.map_data[xx][yy] = types.REGBIT | AniTabC[z]
                    # Note: Original has duplicate line, keeping for compatibility
                    types.map_data[xx][yy] = types.REGBIT | AniTabD[z]


def DoIndustrial(ZonePwrFlg: int) -> None:
    """
    Process industrial zone growth.

    Ported from DoIndustrial() in s_zone.c.

    Args:
        ZonePwrFlg: Whether zone is powered
    """
    tpop = IZPop(types.cchr9)
    types.ind_pop += tpop

    if tpop > simulation.Rand(5):
        TrfGood = MakeTraf(2)
    else:
        TrfGood = True

    if TrfGood == -1:
        DoIndOut(tpop, simulation.Rand16() & 1)
        return

    if (simulation.Rand16() & 7) == 0:
        zscore = types.i_value + EvalInd(TrfGood)
        if not ZonePwrFlg:
            zscore = -500

        if (zscore > -350) and ((zscore - 26380) > simulation.Rand16Signed()):
            DoIndIn(tpop, simulation.Rand16() & 1)
            return

        if (zscore < 350) and ((zscore + 26380) < simulation.Rand16Signed()):
            DoIndOut(tpop, simulation.Rand16() & 1)


def DoCommercial(ZonePwrFlg: int) -> None:
    """
    Process commercial zone growth.

    Ported from DoCommercial() in s_zone.c.

    Args:
        ZonePwrFlg: Whether zone is powered
    """
    tpop = CZPop(types.cchr9)
    types.com_pop += tpop

    if tpop > simulation.Rand(5):
        TrfGood = MakeTraf(1)
    else:
        TrfGood = True

    if TrfGood == -1:
        value = GetCRVal()
        DoComOut(tpop, value)
        return

    if (simulation.Rand16() & 7) == 0:
        locvalve = EvalCom(TrfGood)
        zscore = types.c_value + locvalve
        if not ZonePwrFlg:
            zscore = -500

        if (
            TrfGood
            and (zscore > -350)
            and ((zscore - 26380) > simulation.Rand16Signed())
        ):
            value = GetCRVal()
            DoComIn(tpop, value)
            return

        if (zscore < 350) and ((zscore + 26380) < simulation.Rand16Signed()):
            value = GetCRVal()
            DoComOut(tpop, value)


def DoResidential(ZonePwrFlg: int) -> None:
    """
    Process residential zone growth.

    Ported from DoResidential() in s_zone.c.

    Args:
        ZonePwrFlg: Whether zone is powered
    """
    if types.cchr9 == types.FREEZ:
        tpop = DoFreePop()
    else:
        tpop = RZPop(types.cchr9)

    types.res_pop += tpop

    if tpop > simulation.Rand(35):
        TrfGood = MakeTraf(0)
    else:
        TrfGood = True

    if TrfGood == -1:
        value = GetCRVal()
        DoResOut(tpop, value)
        return

    if (types.cchr9 == types.FREEZ) or ((simulation.Rand16() & 7) == 0):
        locvalve = EvalRes(TrfGood)
        zscore = types.r_value + locvalve
        if not ZonePwrFlg:
            zscore = -500

        if (zscore > -350) and ((zscore - 26380) > simulation.Rand16Signed()):
            if (not tpop) and ((simulation.Rand16() & 3) == 0):
                MakeHosp()
                return
            value = GetCRVal()
            DoResIn(tpop, value)
            return

        if (zscore < 350) and ((zscore + 26380) < simulation.Rand16Signed()):
            value = GetCRVal()
            DoResOut(tpop, value)


def MakeHosp() -> None:
    """
    Create hospital or church if needed.

    Ported from MakeHosp() in s_zone.c.
    """
    if types.need_hosp > 0:
        ZonePlop(types.HOSPITAL - 4)
        types.need_hosp = False
        return

    if types.need_church > 0:
        ZonePlop(types.CHURCH - 4)
        types.need_church = False


def GetCRVal() -> int:
    """
    Get commercial/residential value based on land value and pollution.

    Ported from GetCRVal() in s_zone.c.

    Returns:
        Value from 0-3 based on land value minus pollution
    """
    LVal = types.land_value_mem[types.s_map_x >> 1][types.s_map_y >> 1]
    LVal -= types.pollution_mem[types.s_map_x >> 1][types.s_map_y >> 1]

    if LVal < 30:
        return 0
    if LVal < 80:
        return 1
    if LVal < 150:
        return 2
    return 3


# ============================================================================
# Zone Growth Functions
# ============================================================================


def DoResIn(pop: int, value: int) -> None:
    """
    Handle residential zone growth inward.

    Ported from DoResIn() in s_zone.c.

    Args:
        pop: Current population
        value: Land value rating
    """
    z = types.pollution_mem[types.s_map_x >> 1][types.s_map_y >> 1]
    if z > 128:
        return

    if types.cchr9 == types.FREEZ:
        if pop < 8:
            BuildHouse(value)
            IncROG(1)
            return
        if types.pop_density[types.s_map_x >> 1][types.s_map_y >> 1] > 64:
            ResPlop(0, value)
            IncROG(8)
            return
        return

    if pop < 40:
        ResPlop((pop // 8) - 1, value)
        IncROG(8)


def DoComIn(pop: int, value: int) -> None:
    """
    Handle commercial zone growth inward.

    Ported from DoComIn() in s_zone.c.

    Args:
        pop: Current population
        value: Land value rating
    """
    z = types.land_value_mem[types.s_map_x >> 1][types.s_map_y >> 1]
    z = z >> 5
    if pop > z:
        return

    if pop < 5:
        ComPlop(pop, value)
        IncROG(8)


def DoIndIn(pop: int, value: int) -> None:
    """
    Handle industrial zone growth inward.

    Ported from DoIndIn() in s_zone.c.

    Args:
        pop: Current population
        value: Land value rating
    """
    if pop < 4:
        IndPlop(pop, value)
        IncROG(8)


def IncROG(amount: int) -> None:
    """
    Increment rate of growth.

    Ported from IncROG() in s_zone.c.

    Args:
        amount: Amount to increment
    """
    types.rate_og_mem[types.s_map_x >> 3][types.s_map_y >> 3] += amount << 2


# ============================================================================
# Zone Shrinkage Functions
# ============================================================================


def DoResOut(pop: int, value: int) -> None:
    """
    Handle residential zone shrinkage outward.

    Ported from DoResOut() in s_zone.c.

    Args:
        pop: Current population
        value: Land value rating
    """
    Brdr = [0, 3, 6, 1, 4, 7, 2, 5, 8]

    if not pop:
        return

    if pop > 16:
        ResPlop(((pop - 24) // 8), value)
        IncROG(-8)
        return

    if pop == 16:
        IncROG(-8)
        types.map_data[types.s_map_x][types.s_map_y] = (
            types.FREEZ | types.BLBNCNBIT | types.ZONEBIT
        )
        for x in range(types.s_map_x - 1, types.s_map_x + 2):
            for y in range(types.s_map_y - 1, types.s_map_y + 2):
                if macros.TestBounds(x, y):
                    if (types.map_data[x][y] & types.LOMASK) != types.FREEZ:
                        types.map_data[x][y] = (
                            types.LHTHR + value + simulation.Rand(2) + types.BLBNCNBIT
                        )

    if pop < 16:
        IncROG(-1)
        z = 0
        for x in range(types.s_map_x - 1, types.s_map_x + 2):
            for y in range(types.s_map_y - 1, types.s_map_y + 2):
                if macros.TestBounds(x, y):
                    loc = types.map_data[x][y] & types.LOMASK
                    if (loc >= types.LHTHR) and (loc <= types.HHTHR):
                        types.map_data[x][y] = (
                            Brdr[z] + types.BLBNCNBIT + types.FREEZ - 4
                        )
                        return
                z += 1


def DoComOut(pop: int, value: int) -> None:
    """
    Handle commercial zone shrinkage outward.

    Ported from DoComOut() in s_zone.c.

    Args:
        pop: Current population
        value: Land value rating
    """
    if pop > 1:
        ComPlop(pop - 2, value)
        IncROG(-8)
        return

    if pop == 1:
        ZonePlop(types.COMBASE)
        IncROG(-8)


def DoIndOut(pop: int, value: int) -> None:
    """
    Handle industrial zone shrinkage outward.

    Ported from DoIndOut() in s_zone.c.

    Args:
        pop: Current population
        value: Land value rating
    """
    if pop > 1:
        IndPlop(pop - 2, value)
        IncROG(-8)
        return

    if pop == 1:
        ZonePlop(types.INDCLR - 4)
        IncROG(-8)


# ============================================================================
# Population Calculation Functions
# ============================================================================


def RZPop(Ch9: int) -> int:
    """
    Calculate residential zone population.

    Ported from RZPop() in s_zone.c.

    Args:
        Ch9: Zone tile value

    Returns:
        Population count
    """
    CzDen = ((Ch9 - types.RZB) // 9) % 4
    return (CzDen * 8) + 16


def CZPop(Ch9: int) -> int:
    """
    Calculate commercial zone population.

    Ported from CZPop() in s_zone.c.

    Args:
        Ch9: Zone tile value

    Returns:
        Population count
    """
    if Ch9 == types.COMCLR:
        return 0
    CzDen = (((Ch9 - types.CZB) // 9) % 5) + 1
    return CzDen


def IZPop(Ch9: int) -> int:
    """
    Calculate industrial zone population.

    Ported from IZPop() in s_zone.c.

    Args:
        Ch9: Zone tile value

    Returns:
        Population count
    """
    if Ch9 == types.INDCLR:
        return 0
    CzDen = (((Ch9 - types.IZB) // 9) % 4) + 1
    return CzDen


# ============================================================================
# Building and Construction Functions
# ============================================================================


def BuildHouse(value: int) -> None:
    """
    Build a house in an empty residential lot.

    Ported from BuildHouse() in s_zone.c.

    Args:
        value: Land value rating
    """
    ZeX = [0, -1, 0, 1, -1, 1, -1, 0, 1]
    ZeY = [0, -1, -1, -1, 0, 0, 1, 1, 1]

    BestLoc = 0
    hscore = 0

    for z in range(1, 9):
        xx = types.s_map_x + ZeX[z]
        yy = types.s_map_y + ZeY[z]
        if macros.TestBounds(xx, yy):
            score = EvalLot(xx, yy)
            if score != 0:
                if score > hscore:
                    hscore = score
                    BestLoc = z
                if (score == hscore) and ((simulation.Rand16() & 7) == 0):
                    BestLoc = z

    if BestLoc:
        xx = types.s_map_x + ZeX[BestLoc]
        yy = types.s_map_y + ZeY[BestLoc]
        if macros.TestBounds(xx, yy):
            types.map_data[xx][yy] = (
                types.HOUSE + types.BLBNCNBIT + simulation.Rand(2) + (value * 3)
            )


def ResPlop(Den: int, Value: int) -> None:
    """
    Place residential zone tiles.

    Ported from ResPlop() in s_zone.c.

    Args:
        Den: Density level
        Value: Land value rating
    """
    base = (((Value * 4) + Den) * 9) + types.RZB - 4
    ZonePlop(base)


def ComPlop(Den: int, Value: int) -> None:
    """
    Place commercial zone tiles.

    Ported from ComPlop() in s_zone.c.

    Args:
        Den: Density level
        Value: Land value rating
    """
    base = (((Value * 5) + Den) * 9) + types.CZB - 4
    ZonePlop(base)


def IndPlop(Den: int, Value: int) -> None:
    """
    Place industrial zone tiles.

    Ported from IndPlop() in s_zone.c.

    Args:
        Den: Density level
        Value: Land value rating
    """
    base = (((Value * 4) + Den) * 9) + (types.IZB - 4)
    ZonePlop(base)


def EvalLot(x: int, y: int) -> int:
    """
    Evaluate a lot for building suitability.

    Ported from EvalLot() in s_zone.c.

    Args:
        x: X coordinate
        y: Y coordinate

    Returns:
        Score from -1 (bad) to 4 (good)
    """
    DX = [0, 1, 0, -1]
    DY = [-1, 0, 1, 0]

    # test for clear lot
    z = types.map_data[x][y] & types.LOMASK
    if z and ((z < types.RESBASE) or (z > types.RESBASE + 8)):
        return -1

    score = 1
    for z in range(4):
        xx = x + DX[z]
        yy = y + DY[z]
        if (
            macros.TestBounds(xx, yy)
            and types.map_data[xx][yy]
            and ((types.map_data[xx][yy] & types.LOMASK) <= types.LASTROAD)
        ):
            score += 1  # look for road

    return score


def ZonePlop(base: int) -> bool:
    """
    Place a zone of 3x3 tiles.

    Ported from ZonePlop() in s_zone.c.

    Args:
        base: Base tile value

    Returns:
        True if successful, False if blocked by fire/flood
    """
    Zx = [-1, 0, 1, -1, 0, 1, -1, 0, 1]
    Zy = [-1, -1, -1, 0, 0, 0, 1, 1, 1]

    # check for fire/flood
    for z in range(9):
        xx = types.s_map_x + Zx[z]
        yy = types.s_map_y + Zy[z]
        if macros.TestBounds(xx, yy):
            x = types.map_data[xx][yy] & types.LOMASK
            if (x >= types.FLOOD) and (x < types.ROADBASE):
                return False

    # place zone tiles
    for z in range(9):
        xx = types.s_map_x + Zx[z]
        yy = types.s_map_y + Zy[z]
        if macros.TestBounds(xx, yy):
            types.map_data[xx][yy] = base + types.BNCNBIT
        base += 1

    types.cchr = types.map_data[types.s_map_x][types.s_map_y]
    SetZPower()
    types.map_data[types.s_map_x][types.s_map_y] |= types.ZONEBIT | types.BULLBIT
    return True


# ============================================================================
# Evaluation Functions
# ============================================================================


def EvalRes(traf: int) -> int:
    """
    Evaluate residential zone desirability.

    Ported from EvalRes() in s_zone.c.

    Args:
        traf: Traffic rating

    Returns:
        Score from -3000 to 3000
    """
    if traf < 0:
        return -3000

    Value = types.land_value_mem[types.s_map_x >> 1][types.s_map_y >> 1]
    Value -= types.pollution_mem[types.s_map_x >> 1][types.s_map_y >> 1]

    if Value < 0:
        Value = 0  # Cap at 0
    else:
        Value = Value << 5

    if Value > 6000:
        Value = 6000  # Cap at 6000

    Value = Value - 3000
    return Value


def EvalCom(traf: int) -> int:
    """
    Evaluate commercial zone desirability.

    Ported from EvalCom() in s_zone.c.

    Args:
        traf: Traffic rating

    Returns:
        Commercial rate value
    """
    if traf < 0:
        return -3000

    Value = types.com_rate[types.s_map_x >> 3][types.s_map_y >> 3]
    return Value


def EvalInd(traf: int) -> int:
    """
    Evaluate industrial zone desirability.

    Ported from EvalInd() in s_zone.c.

    Args:
        traf: Traffic rating

    Returns:
        Score value
    """
    if traf < 0:
        return -1000
    return 0


# ============================================================================
# Population Counting Functions
# ============================================================================


def DoFreePop() -> int:
    """
    Count population in free zone area.

    Ported from DoFreePop() in s_zone.c.

    Returns:
        Population count
    """
    count = 0
    for x in range(types.s_map_x - 1, types.s_map_x + 2):
        for y in range(types.s_map_y - 1, types.s_map_y + 2):
            if macros.TestBounds(x, y):
                loc = types.map_data[x][y] & types.LOMASK
                if (loc >= types.LHTHR) and (loc <= types.HHTHR):
                    count += 1
    return count


# ============================================================================
# Power Management Functions
# ============================================================================


def SetZPower() -> int:
    """
    Set power bit in map based on power grid connectivity.

    Ported from SetZPower() in s_zone.c.

    Returns:
        1 if powered, 0 if not powered
    """
    # Test for special power cases or power map connectivity
    if (
        (types.cchr9 == types.NUCLEAR)
        or (types.cchr9 == types.POWERPLANT)
        or (
            (
                micropolis.power.powerword(types.s_map_x, types.s_map_y)
                < types.PWRMAPSIZE
            )
            and (
                types.power_map[
                    micropolis.power.powerword(types.s_map_x, types.s_map_y)
                ]
                & (1 << (types.s_map_x & 15))
            )
        )
    ):
        types.map_data[types.s_map_x][types.s_map_y] = types.cchr | types.PWRBIT
        return 1
    else:
        types.map_data[types.s_map_x][types.s_map_y] = types.cchr & (~types.PWRBIT)
        return 0


# ============================================================================
# Traffic Functions (placeholders - will be implemented in traffic.py)
# ============================================================================


def MakeTraf(kind: int) -> int:
    """
    Make traffic for zone.

    Placeholder for traffic simulation - will be implemented in traffic.py.

    Args:
        kind: Traffic type (0=res, 1=com, 2=ind)

    Returns:
        Traffic rating
    """
    # Placeholder - return good traffic for now
    return 1
