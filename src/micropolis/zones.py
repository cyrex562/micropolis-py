"""
zones.py - Zone processing and growth mechanics for Micropolis Python port

This module contains the zone growth and management functions ported from s_zone.c,
implementing residential, commercial, and industrial zone development logic.
"""
from src.micropolis.constants import PORTBASE, HOSPITAL, COMBASE, INDBASE, CHURCH, RESBASE, IND1, IND2, IND4, IND6, \
    IND8, IND3, IND5, IND7, IND9, IZB, LOMASK, ASCBIT, SMOKEBASE, REGBIT, FREEZ, BLBNCNBIT, ZONEBIT, LHTHR, HHTHR, \
    INDCLR, RZB, COMCLR, CZB, HOUSE, LASTROAD, FLOOD, ROADBASE, BNCNBIT, BULLBIT, NUCLEAR, POWERPLANT, PWRMAPSIZE, \
    PWRBIT
from src.micropolis.context import AppContext
from src.micropolis.macros import TestBounds
from src.micropolis.power import powerword
from src.micropolis.simulation import do_sp_zone, repair_zone, rand, rand16, rand16_signed


# ============================================================================
# Zone Processing Functions
# ============================================================================


def DoZone(context: AppContext) -> None:
    """
    Main zone processing function.

    Determines zone type and calls appropriate processing function.
    Ported from DoZone() in s_zone.c.
    """
    ZonePwrFlg = SetZPower(context)  # Set Power Bit in Map from PowerMap

    if ZonePwrFlg:
        context.pwrd_z_cnt += 1
    else:
        context.un_pwrd_z_cnt += 1

    if context.cchr9 > PORTBASE:  # do Special Zones
        do_sp_zone(context, ZonePwrFlg)
        return

    if context.cchr9 < HOSPITAL:
        DoResidential(context,ZonePwrFlg)
        return

    if context.cchr9 < COMBASE:
        DoHospChur(context)
        return

    if context.cchr9 < INDBASE:
        DoCommercial(context,ZonePwrFlg)
        return

    DoIndustrial(context,ZonePwrFlg)


def DoHospChur(context: AppContext) -> None:
    """
    Process hospital and church zones.

    Handles hospital and church population counting and repair.
    Ported from DoHospChur() in s_zone.c.
    """
    if context.cchr9 == HOSPITAL:
        context.hosp_pop += 1
        if (context.city_time & 15) == 0:
            repair_zone(context, HOSPITAL, 3)  # post
        if context.need_hosp == -1:
            if rand(context, 20) == 0:
                ZonePlop(context, RESBASE)

    if context.cchr9 == CHURCH:
        context.church_pop += 1
        if (context.city_time & 15) == 0:
            repair_zone(context, CHURCH, 3)  # post
        if context.need_church == -1:
            if rand(context, 20) == 0:
                ZonePlop(context, RESBASE)


def SetSmoke(context: AppContext,ZonePower: int) -> None:
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
    AniTabC = [IND1, 0, IND2, IND4, 0, 0, IND6, IND8]
    AniTabD = [IND1, 0, IND3, IND5, 0, 0, IND7, IND9]

    if context.cchr9 < IZB:
        return

    z = (context.cchr9 - IZB) >> 3
    z = z & 7

    if AniThis[z]:
        xx = context.s_map_x + DX1[z]
        yy = context.s_map_y + DY1[z]
        if TestBounds(xx, yy):
            if ZonePower:
                if (context.map_data[xx][yy] & LOMASK) == AniTabC[z]:
                    context.map_data[xx][yy] = ASCBIT | (
                        SMOKEBASE + AniTabA[z]
                    )
                    # Note: Original has duplicate line, keeping for compatibility
                    context.map_data[xx][yy] = ASCBIT | (
                        SMOKEBASE + AniTabB[z]
                    )
            else:
                if (context.map_data[xx][yy] & LOMASK) > AniTabC[z]:
                    context.map_data[xx][yy] = REGBIT | AniTabC[z]
                    # Note: Original has duplicate line, keeping for compatibility
                    context.map_data[xx][yy] = REGBIT | AniTabD[z]


def DoIndustrial(context: AppContext, ZonePwrFlg: int) -> None:
    """
    Process industrial zone growth.

    Ported from DoIndustrial() in s_zone.c.

    Args:
        context: Application context
        ZonePwrFlg: Whether zone is powered
    """
    tpop = IZPop(context.cchr9)
    context.ind_pop += tpop

    if tpop > rand(context, 5):
        TrfGood = MakeTraf(2)
    else:
        TrfGood = True

    if TrfGood == -1:
        DoIndOut(context,tpop, rand16(context) & 1)
        return

    if (rand16(context) & 7) == 0:
        zscore = context.i_value + EvalInd(TrfGood)
        if not ZonePwrFlg:
            zscore = -500

        if (zscore > -350) and ((zscore - 26380) > rand16_signed(context)):
            DoIndIn(context,tpop, rand16(context,) & 1)
            return

        if (zscore < 350) and ((zscore + 26380) < rand16_signed(context)):
            DoIndOut(context,tpop, rand16(context,) & 1)


def DoCommercial(context: AppContext, ZonePwrFlg: int) -> None:
    """
    Process commercial zone growth.

    Ported from DoCommercial() in s_zone.c.

    Args:
        ZonePwrFlg: Whether zone is powered
    """
    tpop = CZPop(context.cchr9)
    context.com_pop += tpop

    if tpop > rand(context, 5):
        TrfGood = MakeTraf(1)
    else:
        TrfGood = True

    if TrfGood == -1:
        value = GetCRVal(context,)
        DoComOut(context,tpop, value)
        return

    if (rand16(context) & 7) == 0:
        locvalve = EvalCom(context, TrfGood)
        zscore = context.c_value + locvalve
        if not ZonePwrFlg:
            zscore = -500

        if (
            TrfGood
            and (zscore > -350)
            and ((zscore - 26380) > rand16_signed(context))
        ):
            value = GetCRVal(context,)
            DoComIn(context,tpop, value)
            return

        if (zscore < 350) and ((zscore + 26380) < rand16_signed(context)):
            value = GetCRVal(context,)
            DoComOut(context,tpop, value)


def DoResidential(context: AppContext, ZonePwrFlg: int) -> None:
    """
    Process residential zone growth.

    Ported from DoResidential() in s_zone.c.

    Args:
        ZonePwrFlg: Whether zone is powered
    """
    if context.cchr9 == FREEZ:
        tpop = DoFreePop(context)
    else:
        tpop = RZPop(context.cchr9)

    context.res_pop += tpop

    if tpop > rand(context, 35):
        TrfGood = MakeTraf(0)
    else:
        TrfGood = True

    if TrfGood == -1:
        value = GetCRVal(context,)
        DoResOut(context,tpop, value)
        return

    if (context.cchr9 == FREEZ) or ((rand16(context) & 7) == 0):
        locvalve = EvalRes(context,TrfGood)
        zscore = context.r_value + locvalve
        if not ZonePwrFlg:
            zscore = -500

        if (zscore > -350) and ((zscore - 26380) > rand16_signed(context)):
            if (not tpop) and ((rand16(context) & 3) == 0):
                MakeHosp(context)
                return
            value = GetCRVal(context,)
            DoResIn(context,tpop, value)
            return

        if (zscore < 350) and ((zscore + 26380) < rand16_signed(context)):
            value = GetCRVal(context,)
            DoResOut(context,tpop, value)


def MakeHosp(context: AppContext) -> None:
    """
    Create hospital or church if needed.

    Ported from MakeHosp() in s_zone.c.
    """
    if context.need_hosp > 0:
        ZonePlop(context, HOSPITAL - 4)
        context.need_hosp = False
        return

    if context.need_church > 0:
        ZonePlop(context, CHURCH - 4)
        context.need_church = False


def GetCRVal(context: AppContext) -> int:
    """
    Get commercial/residential value based on land value and pollution.

    Ported from GetCRVal() in s_zone.c.

    Returns:
        Value from 0-3 based on land value minus pollution
    """
    LVal = context.land_value_mem[context.s_map_x >> 1][context.s_map_y >> 1]
    LVal -= context.pollution_mem[context.s_map_x >> 1][context.s_map_y >> 1]

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


def DoResIn(context: AppContext, pop: int, value: int) -> None:
    """
    Handle residential zone growth inward.

    Ported from DoResIn() in s_zone.c.

    Args:
        context: Application context
        pop: Current population
        value: Land value rating
    """
    z = context.pollution_mem[context.s_map_x >> 1][context.s_map_y >> 1]
    if z > 128:
        return

    if context.cchr9 == FREEZ:
        if pop < 8:
            BuildHouse(context,value)
            IncROG(context, 1)
            return
        if context.pop_density[context.s_map_x >> 1][context.s_map_y >> 1] > 64:
            ResPlop(context,0, value)
            IncROG(context, 8)
            return
        return

    if pop < 40:
        ResPlop(context,(pop // 8) - 1, value)
        IncROG(context, 8)


def DoComIn(context: AppContext,pop: int, value: int) -> None:
    """
    Handle commercial zone growth inward.

    Ported from DoComIn() in s_zone.c.

    Args:
        context: Application context
        pop: Current population
        value: Land value rating
    """
    z = context.land_value_mem[context.s_map_x >> 1][context.s_map_y >> 1]
    z = z >> 5
    if pop > z:
        return

    if pop < 5:
        ComPlop(context, pop, value)
        IncROG(context, 8)


def DoIndIn(context: AppContext, pop: int, value: int) -> None:
    """
    Handle industrial zone growth inward.

    Ported from DoIndIn() in s_zone.c.

    Args:
        context: Application context
        pop: Current population
        value: Land value rating
    """
    if pop < 4:
        IndPlop(context,pop, value)
        IncROG(context, 8)


def IncROG(context: AppContext, amount: int) -> None:
    """
    Increment rate of growth.

    Ported from IncROG() in s_zone.c.

    Args:
        amount: Amount to increment
        :param context:
    """
    context.rate_og_mem[context.s_map_x >> 3][context.s_map_y >> 3] += amount << 2


# ============================================================================
# Zone Shrinkage Functions
# ============================================================================


def DoResOut(context: AppContext, pop: int, value: int) -> None:
    """
    Handle residential zone shrinkage outward.

    Ported from DoResOut() in s_zone.c.

    Args:
        context: Application context
        pop: Current population
        value: Land value rating
    """
    Brdr = [0, 3, 6, 1, 4, 7, 2, 5, 8]

    if not pop:
        return

    if pop > 16:
        ResPlop(context,((pop - 24) // 8), value)
        IncROG(context, -8)
        return

    if pop == 16:
        IncROG(context, -8)
        context.map_data[context.s_map_x][context.s_map_y] = (
            FREEZ | BLBNCNBIT | ZONEBIT
        )
        for x in range(context.s_map_x - 1, context.s_map_x + 2):
            for y in range(context.s_map_y - 1, context.s_map_y + 2):
                if TestBounds(x, y):
                    if (context.map_data[x][y] & LOMASK) != FREEZ:
                        context.map_data[x][y] = (
                                LHTHR + value + rand(context, 2) + BLBNCNBIT
                        )

    if pop < 16:
        IncROG(context, -1)
        z = 0
        for x in range(context.s_map_x - 1, context.s_map_x + 2):
            for y in range(context.s_map_y - 1, context.s_map_y + 2):
                if TestBounds(x, y):
                    loc = context.map_data[x][y] & LOMASK
                    if (loc >= LHTHR) and (loc <= HHTHR):
                        context.map_data[x][y] = (
                            Brdr[z] + BLBNCNBIT + FREEZ - 4
                        )
                        return
                z += 1


def DoComOut(context: AppContext, pop: int, value: int) -> None:
    """
    Handle commercial zone shrinkage outward.

    Ported from DoComOut() in s_zone.c.

    Args:
        pop: Current population
        value: Land value rating
    """
    if pop > 1:
        ComPlop(context, pop - 2, value)
        IncROG(context, -8)
        return

    if pop == 1:
        ZonePlop(context, COMBASE)
        IncROG(context, -8)


def DoIndOut(context: AppContext, pop: int, value: int) -> None:
    """
    Handle industrial zone shrinkage outward.

    Ported from DoIndOut() in s_zone.c.

    Args:
        pop: Current population
        value: Land value rating
    """
    if pop > 1:
        IndPlop(context,pop - 2, value)
        IncROG(context, -8)
        return

    if pop == 1:
        ZonePlop(context, INDCLR - 4)
        IncROG(context, -8)


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
    CzDen = ((Ch9 - RZB) // 9) % 4
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
    if Ch9 == COMCLR:
        return 0
    CzDen = (((Ch9 - CZB) // 9) % 5) + 1
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
    if Ch9 == INDCLR:
        return 0
    CzDen = (((Ch9 - IZB) // 9) % 4) + 1
    return CzDen


# ============================================================================
# Building and Construction Functions
# ============================================================================


def BuildHouse(context: AppContext, value: int) -> None:
    """
    Build a house in an empty residential lot.

    Ported from BuildHouse() in s_zone.c.

    Args:
        context: Application context
        value: Land value rating
    """
    ZeX = [0, -1, 0, 1, -1, 1, -1, 0, 1]
    ZeY = [0, -1, -1, -1, 0, 0, 1, 1, 1]

    BestLoc = 0
    hscore = 0

    for z in range(1, 9):
        xx = context.s_map_x + ZeX[z]
        yy = context.s_map_y + ZeY[z]
        if TestBounds(xx, yy):
            score = EvalLot(context, xx, yy)
            if score != 0:
                if score > hscore:
                    hscore = score
                    BestLoc = z
                if (score == hscore) and ((rand16(context,) & 7) == 0):
                    BestLoc = z

    if BestLoc:
        xx = context.s_map_x + ZeX[BestLoc]
        yy = context.s_map_y + ZeY[BestLoc]
        if TestBounds(xx, yy):
            context.map_data[xx][yy] = (
                    HOUSE + BLBNCNBIT + rand(context, 2) + (value * 3)
            )


def ResPlop(context: AppContext, Den: int, Value: int) -> None:
    """
    Place residential zone tiles.

    Ported from ResPlop() in s_zone.c.

    Args:
        context: Application context
        Den: Density level
        Value: Land value rating
    """
    base = (((Value * 4) + Den) * 9) + RZB - 4
    ZonePlop(context, base)


def ComPlop(context: AppContext, Den: int, Value: int) -> None:
    """
    Place commercial zone tiles.

    Ported from ComPlop() in s_zone.c.

    Args:
        Den: Density level
        Value: Land value rating
        :param context:
    """
    base = (((Value * 5) + Den) * 9) + CZB - 4
    ZonePlop(context, base)


def IndPlop(context: AppContext, Den: int, Value: int) -> None:
    """
    Place industrial zone tiles.

    Ported from IndPlop() in s_zone.c.

    Args:
        context: Application context
        Den: Density level
        Value: Land value rating
    """
    base = (((Value * 4) + Den) * 9) + (IZB - 4)
    ZonePlop(context, base)


def EvalLot(context: AppContext, x: int, y: int) -> int:
    """
    Evaluate a lot for building suitability.

    Ported from EvalLot() in s_zone.c.

    Args:
        x: X coordinate
        y: Y coordinate

    Returns:
        Score from -1 (bad) to 4 (good)
        :param context:
    """
    DX = [0, 1, 0, -1]
    DY = [-1, 0, 1, 0]

    # test for clear lot
    z = context.map_data[x][y] & LOMASK
    if z and ((z < RESBASE) or (z > RESBASE + 8)):
        return -1

    score = 1
    for z in range(4):
        xx = x + DX[z]
        yy = y + DY[z]
        if (
            TestBounds(xx, yy)
            and context.map_data[xx][yy]
            and ((context.map_data[xx][yy] & LOMASK) <= LASTROAD)
        ):
            score += 1  # look for road

    return score


def ZonePlop(context: AppContext, base: int) -> bool:
    """
    Place a zone of 3x3 tiles.

    Ported from ZonePlop() in s_zone.c.

    Args:
        base: Base tile value

    Returns:
        True if successful, False if blocked by fire/flood
        :param context:
    """
    Zx = [-1, 0, 1, -1, 0, 1, -1, 0, 1]
    Zy = [-1, -1, -1, 0, 0, 0, 1, 1, 1]

    # check for fire/flood
    for z in range(9):
        xx = context.s_map_x + Zx[z]
        yy = context.s_map_y + Zy[z]
        if TestBounds(xx, yy):
            x = context.map_data[xx][yy] & LOMASK
            if (x >= FLOOD) and (x < ROADBASE):
                return False

    # place zone tiles
    for z in range(9):
        xx = context.s_map_x + Zx[z]
        yy = context.s_map_y + Zy[z]
        if TestBounds(xx, yy):
            context.map_data[xx][yy] = base + BNCNBIT
        base += 1

    context.cchr = context.map_data[context.s_map_x][context.s_map_y]
    SetZPower(context,)
    context.map_data[context.s_map_x][context.s_map_y] |= ZONEBIT | BULLBIT
    return True


# ============================================================================
# Evaluation Functions
# ============================================================================


def EvalRes(context: AppContext, traf: int) -> int:
    """
    Evaluate residential zone desirability.

    Ported from EvalRes() in s_zone.c.

    Args:
        context: Application context
        traf: Traffic rating

    Returns:
        Score from -3000 to 3000
    """
    if traf < 0:
        return -3000

    Value = context.land_value_mem[context.s_map_x >> 1][context.s_map_y >> 1]
    Value -= context.pollution_mem[context.s_map_x >> 1][context.s_map_y >> 1]

    if Value < 0:
        Value = 0  # Cap at 0
    else:
        Value = Value << 5

    if Value > 6000:
        Value = 6000  # Cap at 6000

    Value = Value - 3000
    return Value


def EvalCom(context: AppContext, traf: int) -> int:
    """
    Evaluate commercial zone desirability.

    Ported from EvalCom() in s_zone.c.

    Args:
        context: Application context
        traf: Traffic rating

    Returns:
        Commercial rate value
    """
    if traf < 0:
        return -3000

    Value = context.com_rate[context.s_map_x >> 3][context.s_map_y >> 3]
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


def DoFreePop(context: AppContext) -> int:
    """
    Count population in free zone area.

    Ported from DoFreePop() in s_zone.c.

    Returns:
        Population count
        :param context:
    """
    count = 0
    for x in range(context.s_map_x - 1, context.s_map_x + 2):
        for y in range(context.s_map_y - 1, context.s_map_y + 2):
            if TestBounds(x, y):
                loc = context.map_data[x][y] & LOMASK
                if (loc >= LHTHR) and (loc <= HHTHR):
                    count += 1
    return count


# ============================================================================
# Power Management Functions
# ============================================================================


def SetZPower(context: AppContext) -> int:
    """
    Set power bit in map based on power grid connectivity.

    Ported from SetZPower() in s_zone.c.

    Returns:
        1 if powered, 0 if not powered
    """
    # Test for special power cases or power map connectivity
    if (
        (context.cchr9 == NUCLEAR)
        or (context.cchr9 == POWERPLANT)
        or (
            (
                powerword(context.s_map_x, context.s_map_y)
                < PWRMAPSIZE
            )
            and (
                context.power_map[
                    powerword(context.s_map_x, context.s_map_y)
                ]
                & (1 << (context.s_map_x & 15))
            )
        )
    ):
        context.map_data[context.s_map_x][context.s_map_y] = context.cchr | PWRBIT
        return 1
    else:
        context.map_data[context.s_map_x][context.s_map_y] = context.cchr & (~PWRBIT)
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
