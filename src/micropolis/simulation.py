"""
simulation.py - Core simulation step logic for Micropolis Python port

This module contains the main simulation loop and supporting functions
ported from s_sim.c, implementing the city simulation mechanics.
"""

from typing import Optional
import time

import micropolis.constants
import micropolis.utilities

from . import types, macros, power, zones, sprite_manager as sprites


# ============================================================================
# Simulation Control Variables (from s_sim.c globals)
# ============================================================================

# Valve control
ValveFlag: int = 0
CrimeRamp: int = 0
PolluteRamp: int = 0
RValve: int = 0
CValve: int = 0
IValve: int = 0

# Capacity limits
ResCap: int = 0
ComCap: int = 0
IndCap: int = 0

# Financial
CashFlow: int = 0
EMarket: float = 4.0

# Disaster control
DisasterEvent: int = 0
DisasterWait: int = 0

# Scoring
ScoreType: int = 0
ScoreWait: int = 0

# Power statistics
PwrdZCnt: int = 0
unPwrdZCnt: int = 0
NewPower: int = 0

# Tax averaging
AvCityTax: int = 0

# Cycle counters
Scycle: int = 0
Fcycle: int = 0
Spdcycle: int = 0

# Initial evaluation flag
DoInitialEval: int = 0

# Melt down coordinates
MeltX: int = 0
MeltY: int = 0


# ============================================================================
# Simulation Control Variables (from s_sim.c globals)
# ============================================================================

# Valve control
ValveFlag: int = 0
CrimeRamp: int = 0
PolluteRamp: int = 0
RValve: int = 0
CValve: int = 0
IValve: int = 0

# Capacity limits
ResCap: int = 0
ComCap: int = 0
IndCap: int = 0

# Financial
CashFlow: int = 0
EMarket: float = 4.0

# Disaster control
DisasterEvent: int = 0
DisasterWait: int = 0

# Scoring
ScoreType: int = 0
ScoreWait: int = 0

# Power statistics
PwrdZCnt: int = 0
unPwrdZCnt: int = 0
NewPower: int = 0

# Tax averaging
AvCityTax: int = 0

# Cycle counters
Scycle: int = 0
Fcycle: int = 0
Spdcycle: int = 0

# Initial evaluation flag
DoInitialEval: int = 0

# Melt down coordinates
MeltX: int = 0
MeltY: int = 0


# ============================================================================
# Main Simulation Functions
# ============================================================================


def SimFrame() -> None:
    """
    Main simulation frame function.

    Called each frame to advance the simulation based on speed settings.
    Ported from SimFrame() in s_sim.c.
    """
    global Spdcycle, Fcycle

    if types.sim_speed == 0:
        return

    Spdcycle = (Spdcycle + 1) % 1024

    if types.sim_speed == 1 and (Spdcycle % 5) != 0:
        return

    if types.sim_speed == 2 and (Spdcycle % 3) != 0:
        return

    Fcycle = (Fcycle + 1) % 1024
    # if InitSimLoad: Fcycle = 0;  # XXX: commented out in original

    Simulate(Fcycle & 15)


def Simulate(mod16: int) -> None:
    """
    Main simulation loop function.

    Executes different simulation phases based on the mod16 counter.
    Ported from Simulate() in s_sim.c.

    Args:
        mod16: Current simulation phase (0-15)
    """
    global Scycle, DoInitialEval, AvCityTax

    # Speed control tables (from original C code)
    SpdPwr = [1, 2, 4, 5]
    SpdPtl = [1, 2, 7, 17]
    SpdCri = [1, 1, 8, 18]
    SpdPop = [1, 1, 9, 19]
    SpdFir = [1, 1, 10, 20]

    x = types.sim_speed
    if x > 3:
        x = 3

    if mod16 == 0:
        Scycle = (Scycle + 1) % 1024  # This is cosmic
        if DoInitialEval:
            DoInitialEval = 0
            CityEvaluation()
        types.city_time += 1
        AvCityTax += types.city_tax  # post
        if (Scycle & 1) == 0:
            SetValves()
        ClearCensus()

    elif mod16 == 1:
        MapScan(0, 1 * micropolis.constants.WORLD_X // 8)
    elif mod16 == 2:
        MapScan(
            1 * micropolis.constants.WORLD_X // 8, 2 * micropolis.constants.WORLD_X // 8
        )
    elif mod16 == 3:
        MapScan(
            2 * micropolis.constants.WORLD_X // 8, 3 * micropolis.constants.WORLD_X // 8
        )
    elif mod16 == 4:
        MapScan(
            3 * micropolis.constants.WORLD_X // 8, 4 * micropolis.constants.WORLD_X // 8
        )
    elif mod16 == 5:
        MapScan(
            4 * micropolis.constants.WORLD_X // 8, 5 * micropolis.constants.WORLD_X // 8
        )
    elif mod16 == 6:
        MapScan(
            5 * micropolis.constants.WORLD_X // 8, 6 * micropolis.constants.WORLD_X // 8
        )
    elif mod16 == 7:
        MapScan(
            6 * micropolis.constants.WORLD_X // 8, 7 * micropolis.constants.WORLD_X // 8
        )
    elif mod16 == 8:
        MapScan(7 * micropolis.constants.WORLD_X // 8, micropolis.constants.WORLD_X)

    elif mod16 == 9:
        if (types.city_time % micropolis.constants.CENSUSRATE) == 0:
            TakeCensus()
        if (types.city_time % (micropolis.constants.CENSUSRATE * 12)) == 0:
            Take2Census()

        if (types.city_time % micropolis.constants.TAXFREQ) == 0:
            CollectTax()
            CityEvaluation()

    elif mod16 == 10:
        if (Scycle % 5) == 0:
            DecROGMem()
        DecTrafficMem()
        types.new_map_flags[micropolis.constants.TDMAP] = 1
        types.new_map_flags[micropolis.constants.RDMAP] = 1
        types.new_map_flags[micropolis.constants.ALMAP] = 1
        types.new_map_flags[micropolis.constants.REMAP] = 1
        types.new_map_flags[micropolis.constants.COMAP] = 1
        types.new_map_flags[micropolis.constants.INMAP] = 1
        types.new_map_flags[micropolis.constants.DYMAP] = 1
        SendMessages()

    elif mod16 == 11:
        if (Scycle % SpdPwr[x]) == 0:
            DoPowerScan()
            NewPower = 1  # post-release change

    elif mod16 == 12:
        if (Scycle % SpdPtl[x]) == 0:
            # PTLScan() - Pollution scanning (placeholder)
            pass

    elif mod16 == 13:
        if (Scycle % SpdCri[x]) == 0:
            # CrimeScan() - Crime scanning (placeholder)
            pass

    elif mod16 == 14:
        if (Scycle % SpdPop[x]) == 0:
            # PopDenScan() - Population density scanning (placeholder)
            pass

    elif mod16 == 15:
        if (Scycle % SpdFir[x]) == 0:
            # FireAnalysis() - Fire analysis (placeholder)
            pass
        DoDisasters()


def DoSimInit() -> None:
    """
    Initialize simulation when loading a city.

    Ported from DoSimInit() in s_sim.c.
    """
    global Fcycle, Scycle

    Fcycle = 0
    Scycle = 0

    if types.init_sim_load == 2:  # if new city
        InitSimMemory()

    if types.init_sim_load == 1:  # if city just loaded
        SimLoadInit()

    SetValves()
    ClearCensus()
    # MapScan(0, WORLD_X)  # XXX: commented out in original
    power.DoPowerScan()
    NewPower = 1  # post rel
    # PTLScan() - placeholder
    # CrimeScan() - placeholder
    # PopDenScan() - placeholder
    # FireAnalysis() - placeholder
    types.new_map = 1
    # doAllGraphs() - placeholder
    types.new_graph = 1
    types.total_pop = 1
    DoInitialEval = 1


# ============================================================================
# Memory Management Functions
# ============================================================================


def DecTrafficMem() -> None:
    """
    Gradually reduces traffic density values.

    Ported from DecTrafficMem() in s_sim.c.
    """
    for x in range(micropolis.constants.HWLDX):
        for y in range(micropolis.constants.HWLDY):
            z = types.trf_density[x][y]
            if z > 0:
                if z > 24:
                    if z > 200:
                        types.trf_density[x][y] = z - 34
                    else:
                        types.trf_density[x][y] = z - 24
                else:
                    types.trf_density[x][y] = 0


def DecROGMem() -> None:
    """
    Gradually reduces RateOGMem values.

    Ported from DecROGMem() in s_sim.c.
    """
    for x in range(micropolis.constants.SM_X):
        for y in range(micropolis.constants.SM_Y):
            z = types.rate_og_mem[x][y]
            if z == 0:
                continue
            if z > 0:
                types.rate_og_mem[x][y] -= 1
                if z > 200:
                    types.rate_og_mem[x][y] = 200  # prevent overflow
                continue
            if z < 0:
                types.rate_og_mem[x][y] += 1
                if z < -200:
                    types.rate_og_mem[x][y] = -200


def InitSimMemory() -> None:
    """
    Initialize simulation memory for a new city.

    Ported from InitSimMemory() in s_sim.c.
    """
    global CrimeRamp, PolluteRamp, EMarket, DisasterEvent, ScoreType

    z = 0
    # SetCommonInits() - placeholder
    for x in range(240):
        types.res_his[x] = z
        types.com_his[x] = z
        types.ind_his[x] = z
        types.money_his[x] = 128
        types.crime_his[x] = z
        types.pollution_his[x] = z

    CrimeRamp = z
    PolluteRamp = z
    types.total_pop = z
    RValve = z
    CValve = z
    IValve = z
    ResCap = z
    ComCap = z
    IndCap = z

    EMarket = 6.0
    DisasterEvent = 0
    ScoreType = 0

    # Clear power map
    for z in range(types.PWRMAPSIZE):
        types.power_map[z] = ~0  # set power Map
    power.DoPowerScan()
    NewPower = 1  # post rel

    types.init_sim_load = 0


def SimLoadInit() -> None:
    """
    Initialize simulation when loading a saved city.

    Ported from SimLoadInit() in s_sim.c.
    """
    # Disaster wait times for different scenarios
    DisTab = [0, 2, 10, 5, 20, 3, 5, 5, 2 * 48]
    ScoreWaitTab = [
        0,
        30 * 48,
        5 * 48,
        5 * 48,
        10 * 48,
        5 * 48,
        10 * 48,
        5 * 48,
        10 * 48,
    ]

    global EMarket, RValve, CValve, IValve, CrimeRamp, PolluteRamp

    z = 0
    EMarket = float(types.misc_his[1])
    types.res_pop = types.misc_his[2]
    types.com_pop = types.misc_his[3]
    types.ind_pop = types.misc_his[4]
    RValve = types.misc_his[5]
    CValve = types.misc_his[6]
    IValve = types.misc_his[7]
    CrimeRamp = types.misc_his[10]
    PolluteRamp = types.misc_his[11]
    types.lv_average = types.misc_his[12]
    types.crime_average = types.misc_his[13]
    types.pollute_average = types.misc_his[14]
    types.game_level = types.misc_his[15]

    if types.city_time < 0:
        types.city_time = 0
    if EMarket == 0:
        EMarket = 4.0
    if (types.game_level > 2) or (types.game_level < 0):
        types.game_level = 0
    # SetGameLevel(GameLevel) - placeholder

    # SetCommonInits() - placeholder

    types.city_class = types.misc_his[16]
    types.city_score = types.misc_his[17]

    if (types.city_class > 5) or (types.city_class < 0):
        types.city_class = 0
    if (types.city_score > 999) or (types.city_score < 1):
        types.city_score = 500

    ResCap = 0
    ComCap = 0
    IndCap = 0

    AvCityTax = (types.city_time % 48) * 7  # post

    for z in range(types.PWRMAPSIZE):
        types.power_map[z] = 0xFFFF  # set power Map
    DoNilPower()

    if types.scenario_id > 8:
        types.scenario_id = 0

    if types.scenario_id:
        DisasterEvent = types.scenario_id
        DisasterWait = DisTab[types.scenario_id]
        ScoreType = types.scenario_id
        ScoreWait = ScoreWaitTab[types.scenario_id]
    else:
        DisasterEvent = 0
        ScoreType = 0

    types.road_effect = 32
    types.police_effect = 1000  # post
    types.fire_effect = 1000
    types.init_sim_load = 0


def DoNilPower() -> None:
    """
    Set power for all zones when loading a city.

    Ported from DoNilPower() in s_sim.c.
    """
    for x in range(micropolis.constants.WORLD_X):
        for y in range(micropolis.constants.WORLD_Y):
            z = types.map_data[x][y]
            if z & types.ZONEBIT:
                types.s_map_x = x
                types.s_map_y = y
                types.cchr = z
                zones.SetZPower()


# ============================================================================
# Valve and Census Functions
# ============================================================================


def SetValves() -> None:
    """
    Set zone growth valves based on economic conditions.

    Ported from SetValves() in s_sim.c.
    """
    # Tax table for different tax rates
    TaxTable = [
        200,
        150,
        120,
        100,
        80,
        50,
        30,
        0,
        -10,
        -40,
        -100,
        -150,
        -200,
        -250,
        -300,
        -350,
        -400,
        -450,
        -500,
        -550,
        -600,
    ]

    global ValveFlag, RValve, CValve, IValve

    # Store current values in MiscHis
    types.misc_his[1] = int(EMarket)
    types.misc_his[2] = types.res_pop
    types.misc_his[3] = types.com_pop
    types.misc_his[4] = types.ind_pop
    types.misc_his[5] = RValve
    types.misc_his[6] = CValve
    types.misc_his[7] = IValve
    types.misc_his[10] = CrimeRamp
    types.misc_his[11] = PolluteRamp
    types.misc_his[12] = types.lv_average
    types.misc_his[13] = types.crime_average
    types.misc_his[14] = types.pollute_average
    types.misc_his[15] = types.game_level
    types.misc_his[16] = types.city_class
    types.misc_his[17] = types.city_score

    # Calculate normalized residential population
    NormResPop = types.res_pop / 8
    types.last_total_pop = types.total_pop
    types.total_pop = NormResPop + types.com_pop + types.ind_pop

    # Calculate employment rate
    if NormResPop:
        Employment = (types.com_his[1] + types.ind_his[1]) / NormResPop
    else:
        Employment = 1

    # Calculate migration and births
    Migration = NormResPop * (Employment - 1)
    Births = NormResPop * 0.02  # Birth Rate
    PjResPop = NormResPop + Migration + Births  # Projected Res.Pop

    # Calculate labor base
    if types.com_his[1] + types.ind_his[1]:
        LaborBase = types.res_his[1] / (types.com_his[1] + types.ind_his[1])
    else:
        LaborBase = 1
    if LaborBase > 1.3:
        LaborBase = 1.3
    if LaborBase < 0:
        LaborBase = 0  # LB > 1 - .1

    # Calculate temporary values for market calculations
    for z in range(2):
        temp = types.res_his[z] + types.com_his[z] + types.ind_his[z]
    IntMarket = (NormResPop + types.com_pop + types.ind_pop) / 3.7

    # Calculate projected commercial population
    PjComPop = IntMarket * LaborBase

    # Adjust for game level
    z = types.game_level
    temp = 1
    if z == 0:
        temp = 1.2
    elif z == 1:
        temp = 1.1
    elif z == 2:
        temp = 0.98

    PjIndPop = types.ind_pop * LaborBase * temp
    if PjIndPop < 5:
        PjIndPop = 5

    # Calculate ratios
    if NormResPop:
        Rratio = PjResPop / NormResPop  # projected -vs- actual
    else:
        Rratio = 1.3
    if types.com_pop:
        Cratio = PjComPop / types.com_pop
    else:
        Cratio = PjComPop
    if types.ind_pop:
        Iratio = PjIndPop / types.ind_pop
    else:
        Iratio = PjIndPop

    # Clamp ratios
    if Rratio > 2:
        Rratio = 2
    if Cratio > 2:
        Cratio = 2
    if Iratio > 2:
        Iratio = 2

    # Apply tax effects
    z = types.city_tax + types.game_level
    if z > 20:
        z = 20
    Rratio = ((Rratio - 1) * 600) + TaxTable[z]  # global tax/Glevel effects
    Cratio = ((Cratio - 1) * 600) + TaxTable[z]
    Iratio = ((Iratio - 1) * 600) + TaxTable[z]

    # Update valves
    if Rratio > 0:
        if RValve < 2000:
            RValve += int(Rratio)
    if Rratio < 0:
        if RValve > -2000:
            RValve += int(Rratio)
    if Cratio > 0:
        if CValve < 1500:
            CValve += int(Cratio)
    if Cratio < 0:
        if CValve > -1500:
            CValve += int(Cratio)
    if Iratio > 0:
        if IValve < 1500:
            IValve += int(Iratio)
    if Iratio < 0:
        if IValve > -1500:
            IValve += int(Iratio)

    # Clamp valve values
    if RValve > 2000:
        RValve = 2000
    if RValve < -2000:
        RValve = -2000
    if CValve > 1500:
        CValve = 1500
    if CValve < -1500:
        CValve = -1500
    if IValve > 1500:
        IValve = 1500
    if IValve < -1500:
        IValve = -1500

    # Apply capacity limits
    if ResCap and RValve > 0:
        RValve = 0  # Stad, Prt, Airprt
    if ComCap and CValve > 0:
        CValve = 0
    if IndCap and IValve > 0:
        IValve = 0
    ValveFlag = 1


def ClearCensus() -> None:
    """
    Reset all census counters.

    Ported from ClearCensus() in s_sim.c.
    """
    global PwrdZCnt, unPwrdZCnt

    z = 0
    PwrdZCnt = z
    unPwrdZCnt = z
    types.fire_pop = z
    types.road_total = z
    types.rail_total = z
    types.res_pop = z
    types.com_pop = z
    types.ind_pop = z
    types.res_z_pop = z
    types.ComZPop = z
    types.IndZPop = z
    types.hosp_pop = z
    types.church_pop = z
    types.police_pop = z
    types.fire_st_pop = z
    types.stadium_pop = z
    types.coal_pop = z
    types.nuclear_pop = z
    types.port_pop = z
    types.airport_pop = z
    power.PowerStackNum = z  # Reset before Mapscan

    for x in range(micropolis.constants.SM_X):
        for y in range(micropolis.constants.SM_Y):
            types.fire_st_map[x][y] = z
            types.police_map[x][y] = z


def TakeCensus() -> None:
    """
    Record population data in history graphs.

    Ported from TakeCensus() in s_sim.c.
    """
    global CrimeRamp, PolluteRamp

    # Scroll data
    for x in range(118, -1, -1):
        types.res_his[x + 1] = types.res_his[x]
        types.com_his[x + 1] = types.com_his[x]
        types.ind_his[x + 1] = types.ind_his[x]
        types.crime_his[x + 1] = types.crime_his[x]
        types.pollution_his[x + 1] = types.pollution_his[x]
        types.money_his[x + 1] = types.money_his[x]

    # Update max values
    ResHisMax = 0
    ComHisMax = 0
    IndHisMax = 0
    for x in range(119):
        if types.res_his[x] > ResHisMax:
            ResHisMax = types.res_his[x]
        if types.com_his[x] > ComHisMax:
            ComHisMax = types.com_his[x]
        if types.ind_his[x] > IndHisMax:
            IndHisMax = types.ind_his[x]

    types.graph_10_max = ResHisMax
    if ComHisMax > types.graph_10_max:
        types.graph_10_max = ComHisMax
    if IndHisMax > types.graph_10_max:
        types.graph_10_max = IndHisMax

    # Set current values
    types.res_his[0] = types.res_pop // 8
    types.com_his[0] = types.com_pop
    types.ind_his[0] = types.ind_pop

    # Update crime and pollution ramps
    CrimeRamp += (types.crime_average - CrimeRamp) // 4
    types.crime_his[0] = CrimeRamp

    PolluteRamp += (types.pollute_average - PolluteRamp) // 4
    types.pollution_his[0] = PolluteRamp

    # Scale cash flow to 0..255
    x = (CashFlow // 20) + 128
    if x < 0:
        x = 0
    if x > 255:
        x = 255

    types.money_his[0] = x
    if types.crime_his[0] > 255:
        types.crime_his[0] = 255
    if types.pollution_his[0] > 255:
        types.pollution_his[0] = 255

    # ChangeCensus() - placeholder for 10 year graph view

    # Check hospital and church needs
    if types.hosp_pop < (types.res_pop >> 8):
        types.need_hosp = micropolis.constants.TRUE
    if types.hosp_pop > (types.res_pop >> 8):
        types.need_hosp = -1
    if types.hosp_pop == (types.res_pop >> 8):
        types.need_hosp = micropolis.constants.FALSE

    if types.church_pop < (types.res_pop >> 8):
        types.need_church = micropolis.constants.TRUE
    if types.church_pop > (types.res_pop >> 8):
        types.need_church = -1
    if types.church_pop == (types.res_pop >> 8):
        types.need_church = micropolis.constants.FALSE


def Take2Census() -> None:
    """
    Record long-term population data.

    Ported from Take2Census() in s_sim.c.
    """
    # Scroll 120-year data
    for x in range(238, 119, -1):
        types.res_his[x + 1] = types.res_his[x]
        types.com_his[x + 1] = types.com_his[x]
        types.ind_his[x + 1] = types.ind_his[x]
        types.crime_his[x + 1] = types.crime_his[x]
        types.pollution_his[x + 1] = types.pollution_his[x]
        types.money_his[x + 1] = types.money_his[x]

    # Update max values
    Res2HisMax = 0
    Com2HisMax = 0
    Ind2HisMax = 0
    for x in range(120, 239):
        if types.res_his[x] > Res2HisMax:
            Res2HisMax = types.res_his[x]
        if types.com_his[x] > Com2HisMax:
            Com2HisMax = types.com_his[x]
        if types.ind_his[x] > Ind2HisMax:
            Ind2HisMax = types.ind_his[x]

    types.graph_12_max = Res2HisMax
    if Com2HisMax > types.graph_12_max:
        types.graph_12_max = Com2HisMax
    if Ind2HisMax > types.graph_12_max:
        types.graph_12_max = Ind2HisMax

    # Set 120-year values
    types.res_his[120] = types.res_pop // 8
    types.com_his[120] = types.com_pop
    types.ind_his[120] = types.ind_pop
    types.crime_his[120] = types.crime_his[0]
    types.pollution_his[120] = types.pollution_his[0]
    types.money_his[120] = types.money_his[0]
    # ChangeCensus() - placeholder for 120 year graph view


# ============================================================================
# Tax and Financial Functions
# ============================================================================


def CollectTax() -> None:
    """
    Calculate and collect taxes.

    Ported from CollectTax() in s_sim.c.
    """
    global CashFlow, AvCityTax

    # Tax level factors
    r_levels = [0.7, 0.9, 1.2]
    f_levels = [1.4, 1.2, 0.8]

    CashFlow = 0
    if not types.tax_flag:  # if the Tax Port is clear
        # XXX: do something with z
        z = AvCityTax // 48  # post
        AvCityTax = 0

        types.police_fund = types.police_pop * 100
        types.fire_fund = types.fire_st_pop * 100
        types.road_fund = (types.road_total + (types.rail_total * 2)) * r_levels[
            types.game_level
        ]
        types.tax_fund = (
            ((types.total_pop * types.lv_average) // 120)
            * types.city_tax
            * f_levels[types.game_level]
        )

        if types.total_pop:  # if there are people to tax
            CashFlow = int(
                types.tax_fund - (types.police_fund + types.fire_fund + types.road_fund)
            )

            # DoBudget() - placeholder
        else:
            types.road_effect = 32
            types.police_effect = 1000
            types.fire_effect = 1000


def UpdateFundEffects() -> None:
    """
    Update service effects based on funding levels.

    Ported from UpdateFundEffects() in s_sim.c.
    """
    if types.road_fund:
        types.road_effect = int((types.road_spend / types.road_fund) * 32.0)
    else:
        types.road_effect = 32

    if types.police_fund:
        types.police_effect = int((types.police_spend / types.police_fund) * 1000.0)
    else:
        types.police_effect = 1000

    if types.fire_fund:
        types.fire_effect = int(((types.fire_spend / types.fire_fund) * 1000.0))
    else:
        types.fire_effect = 1000

    # drawCurrPercents() - placeholder


# ============================================================================
# Map Scanning Functions
# ============================================================================


def MapScan(x1: int, x2: int) -> None:
    """
    Scan and process tiles in the specified range.

    Ported from MapScan() in s_sim.c.

    Args:
        x1: Starting x coordinate
        x2: Ending x coordinate
    """
    for x in range(x1, x2):
        for y in range(micropolis.constants.WORLD_Y):
            types.cchr = types.map_data[x][y]
            if types.cchr:
                types.cchr9 = types.cchr & types.LOMASK  # Mask off status bits
                if types.cchr9 >= types.FLOOD:
                    types.s_map_x = x
                    types.s_map_y = y
                    if types.cchr9 < types.ROADBASE:
                        if types.cchr9 >= types.FIREBASE:
                            types.fire_pop += 1
                            if (micropolis.utilities.Rand16() & 3) == 0:  # 1 in 4 times
                                DoFire()
                            continue
                        if types.cchr9 < types.RADTILE:
                            DoFlood()
                        else:
                            DoRadTile()
                        continue

                    if NewPower and (types.cchr & types.CONDBIT):
                        zones.SetZPower()

                    if (types.cchr9 >= types.ROADBASE) and (
                        types.cchr9 < types.POWERBASE
                    ):
                        DoRoad()
                        continue

                    if types.cchr & types.ZONEBIT:  # process Zones
                        DoZone()
                        continue

                    if (types.cchr9 >= types.RAILBASE) and (
                        types.cchr9 < types.RESBASE
                    ):
                        DoRail()
                        continue
                    if (types.cchr9 >= types.SOMETINYEXP) and (
                        types.cchr9 <= types.LASTTINYEXP
                    ):
                        # clear AniRubble
                        types.map_data[x][y] = (
                            types.RUBBLE
                            + (micropolis.utilities.Rand16() & 3)
                            + types.BULLBIT
                        )


# ============================================================================
# Tile Processing Functions
# ============================================================================


def DoRail() -> None:
    """
    Process rail tiles.

    Ported from DoRail() in s_sim.c.
    """
    types.rail_total += 1
    sprites.GenerateTrain(types.s_map_x, types.s_map_y)
    if types.road_effect < 30:  # Deteriorating Rail
        if (micropolis.utilities.Rand16() & 511) == 0:
            if (types.cchr & types.CONDBIT) == 0:
                if types.road_effect < (micropolis.utilities.Rand16() & 31):
                    if types.cchr9 < (types.RAILBASE + 2):
                        types.map_data[types.s_map_x][types.s_map_y] = types.RIVER
                    else:
                        types.map_data[types.s_map_x][types.s_map_y] = (
                            types.RUBBLE
                            + (micropolis.utilities.Rand16() & 3)
                            + types.BULLBIT
                        )


def DoRadTile() -> None:
    """
    Process radioactive tiles.

    Ported from DoRadTile() in s_sim.c.
    """
    if (micropolis.utilities.Rand16() & 4095) == 0:
        types.map_data[types.s_map_x][types.s_map_y] = 0  # Radioactive decay


def DoRoad() -> None:
    """
    Process road tiles.

    Ported from DoRoad() in s_sim.c.
    """
    global types

    DenTab = [types.ROADBASE, types.LTRFBASE, types.HTRFBASE]

    types.road_total += 1
    sprites.GenerateBus(types.s_map_x, types.s_map_y)

    if types.road_effect < 30:  # Deteriorating Roads
        if (micropolis.utilities.Rand16() & 511) == 0:
            if (types.cchr & types.CONDBIT) == 0:
                if types.road_effect < (micropolis.utilities.Rand16() & 31):
                    if ((types.cchr9 & 15) < 2) or ((types.cchr9 & 15) == 15):
                        types.map_data[types.s_map_x][types.s_map_y] = types.RIVER
                    else:
                        types.map_data[types.s_map_x][types.s_map_y] = (
                            types.RUBBLE
                            + (micropolis.utilities.Rand16() & 3)
                            + types.BULLBIT
                        )
                    return

    if types.cchr & types.BURNBIT:  # If Bridge
        types.road_total += 4
        if DoBridge():
            return

    if types.cchr9 < types.LTRFBASE:
        tden = 0
    else:
        if types.cchr9 < types.HTRFBASE:
            tden = 1
        else:
            types.road_total += 1
            tden = 2

    # Set Traf Density
    Density = (types.trf_density[types.s_map_x >> 1][types.s_map_y >> 1]) >> 6
    if Density > 1:
        Density -= 1
    if tden != Density:  # tden 0..2
        z = ((types.cchr9 - types.ROADBASE) & 15) + DenTab[Density]
        z += types.cchr & (types.ALLBITS - types.ANIMBIT)
        if Density:
            z += types.ANIMBIT
        types.map_data[types.s_map_x][types.s_map_y] = z


def DoBridge() -> bool:
    """
    Handle bridge opening and closing.

    Ported from DoBridge() in s_sim.c.

    Returns:
        True if bridge was processed, False otherwise
    """
    # Bridge tile tables
    HDx = [-2, 2, -2, -1, 0, 1, 2]
    HDy = [-1, -1, 0, 0, 0, 0, 0]
    HBRTAB = [
        types.HBRDG1 | types.BULLBIT,
        types.HBRDG3 | types.BULLBIT,
        types.HBRDG0 | types.BULLBIT,
        types.RIVER,
        types.BRWH | types.BULLBIT,
        types.RIVER,
        types.HBRDG2 | types.BULLBIT,
    ]
    HBRTAB2 = [
        types.RIVER,
        types.RIVER,
        types.HBRIDGE | types.BULLBIT,
        types.HBRIDGE | types.BULLBIT,
        types.HBRIDGE | types.BULLBIT,
        types.HBRIDGE | types.BULLBIT,
        types.HBRIDGE | types.BULLBIT,
    ]
    VDx = [0, 1, 0, 0, 0, 0, 1]
    VDy = [-2, -2, -1, 0, 1, 2, 2]
    VBRTAB = [
        types.VBRDG0 | types.BULLBIT,
        types.VBRDG1 | types.BULLBIT,
        types.RIVER,
        types.BRWV | types.BULLBIT,
        types.RIVER,
        types.VBRDG2 | types.BULLBIT,
        types.VBRDG3 | types.BULLBIT,
    ]
    VBRTAB2 = [
        types.VBRIDGE | types.BULLBIT,
        types.RIVER,
        types.VBRIDGE | types.BULLBIT,
        types.VBRIDGE | types.BULLBIT,
        types.VBRIDGE | types.BULLBIT,
        types.VBRIDGE | types.BULLBIT,
        types.RIVER,
    ]

    if types.cchr9 == types.BRWV:  # Vertical bridge close
        if ((micropolis.utilities.Rand16() & 3) == 0) and (GetBoatDis() > 340):
            for z in range(7):  # Close
                x = types.s_map_x + VDx[z]
                y = types.s_map_y + VDy[z]
                if macros.TestBounds(x, y):
                    if (types.map_data[x][y] & types.LOMASK) == (
                        VBRTAB[z] & types.LOMASK
                    ):
                        types.map_data[x][y] = VBRTAB2[z]
        return True

    if types.cchr9 == types.BRWH:  # Horizontal bridge close
        if ((micropolis.utilities.Rand16() & 3) == 0) and (GetBoatDis() > 340):
            for z in range(7):  # Close
                x = types.s_map_x + HDx[z]
                y = types.s_map_y + HDy[z]
                if macros.TestBounds(x, y):
                    if (types.map_data[x][y] & types.LOMASK) == (
                        HBRTAB[z] & types.LOMASK
                    ):
                        types.map_data[x][y] = HBRTAB2[z]
        return True

    if (GetBoatDis() < 300) or ((micropolis.utilities.Rand16() & 7) == 0):
        if types.cchr9 & 1:  # Vertical open
            if types.s_map_x < (micropolis.constants.WORLD_X - 1):
                if types.map_data[types.s_map_x + 1][types.s_map_y] == types.CHANNEL:
                    for z in range(7):
                        x = types.s_map_x + VDx[z]
                        y = types.s_map_y + VDy[z]
                        if macros.TestBounds(x, y):
                            MPtem = types.map_data[x][y]
                            if (MPtem == types.CHANNEL) or (
                                (MPtem & 15) == (VBRTAB2[z] & 15)
                            ):
                                types.map_data[x][y] = VBRTAB[z]
                    return True
            return False
        else:  # Horizontal open
            if types.s_map_y > 0:
                if types.map_data[types.s_map_x][types.s_map_y - 1] == types.CHANNEL:
                    for z in range(7):
                        x = types.s_map_x + HDx[z]
                        y = types.s_map_y + HDy[z]
                        if macros.TestBounds(x, y):
                            MPtem = types.map_data[x][y]
                            if ((MPtem & 15) == (HBRTAB2[z] & 15)) or (
                                MPtem == types.CHANNEL
                            ):
                                types.map_data[x][y] = HBRTAB[z]
                    return True
            return False
    return False


def GetBoatDis() -> int:
    """
    Get distance to nearest boat.

    Ported from GetBoatDis() in s_sim.c.

    Returns:
        Distance to nearest boat sprite
    """
    dist = 99999
    mx = (types.s_map_x << 4) + 8
    my = (types.s_map_y << 4) + 8

    sprite = types.sim.sprite
    while sprite is not None:
        if (sprite.type == types.SHI) and (sprite.frame != 0):
            dx = sprite.x + sprite.x_hot - mx
            dy = sprite.y + sprite.y_hot - my
            if dx < 0:
                dx = -dx
            if dy < 0:
                dy = -dy
            dx += dy
            if dx < dist:
                dist = dx
        sprite = sprite.next

    return dist


def DoFire() -> None:
    """
    Handle fire spread from fire tiles.

    Ported from DoFire() in s_sim.c.
    """
    DX = [-1, 0, 1, 0]
    DY = [0, -1, 0, 1]

    for z in range(4):
        if (micropolis.utilities.Rand16() & 7) == 0:
            Xtem = types.s_map_x + DX[z]
            Ytem = types.s_map_y + DY[z]
            if macros.TestBounds(Xtem, Ytem):
                c = types.map_data[Xtem][Ytem]
                if c & types.BURNBIT:
                    if c & types.ZONEBIT:
                        FireZone(Xtem, Ytem, c)
                        if (c & types.LOMASK) > types.IZB:  # Explode
                            sprites.MakeExplosionAt((Xtem << 4) + 8, (Ytem << 4) + 8)
                    types.map_data[Xtem][Ytem] = (
                        types.FIRE + (micropolis.utilities.Rand16() & 3) + types.ANIMBIT
                    )

    z = types.fire_rate[types.s_map_x >> 3][types.s_map_y >> 3]
    Rate = 10
    if z:
        Rate = 3
        if z > 20:
            Rate = 2
        if z > 100:
            Rate = 1
    if micropolis.utilities.Rand(Rate) == 0:
        types.map_data[types.s_map_x][types.s_map_y] = (
            types.RUBBLE + (micropolis.utilities.Rand16() & 3) + types.BULLBIT
        )


def FireZone(Xloc: int, Yloc: int, ch: int) -> None:
    """
    Handle fire damage to zones.

    Ported from FireZone() in s_sim.c.

    Args:
        Xloc: X coordinate of fire
        Yloc: Y coordinate of fire
        ch: Tile value
    """
    types.rate_og_mem[Xloc >> 3][Yloc >> 3] -= 20

    ch = ch & types.LOMASK
    if ch < types.PORTBASE:
        XYmax = 2
    else:
        if ch == types.AIRPORT:
            XYmax = 5
        else:
            XYmax = 4

    for x in range(-1, XYmax):
        for y in range(-1, XYmax):
            Xtem = Xloc + x
            Ytem = Yloc + y
            if (
                (Xtem < 0)
                or (Xtem > (micropolis.constants.WORLD_X - 1))
                or (Ytem < 0)
                or (Ytem > (micropolis.constants.WORLD_Y - 1))
            ):
                continue
            if (
                types.map_data[Xtem][Ytem] & types.LOMASK
            ) >= types.ROADBASE:  # post release
                types.map_data[Xtem][Ytem] |= types.BULLBIT


def RepairZone(ZCent: int, zsize: int) -> None:
    """
    Repair a zone by rebuilding damaged tiles.

    Ported from RepairZone() in s_sim.c.

    Args:
        ZCent: Center tile value for the zone
        zsize: Size of the zone
    """
    cnt = 0
    zsize -= 1
    for y in range(-1, zsize):
        for x in range(-1, zsize):
            xx = types.s_map_x + x
            yy = types.s_map_y + y
            cnt += 1
            if macros.TestBounds(xx, yy):
                ThCh = types.map_data[xx][yy]
                if ThCh & types.ZONEBIT:
                    continue
                if ThCh & types.ANIMBIT:
                    continue
                ThCh = ThCh & types.LOMASK
                if (ThCh < types.RUBBLE) or (ThCh >= types.ROADBASE):
                    types.map_data[xx][yy] = (
                        ZCent - 3 - zsize + cnt + types.CONDBIT + types.BURNBIT
                    )


def DoSPZone(PwrOn: int) -> None:
    """
    Handle special zones (power plants, fire stations, etc.).

    Ported from DoSPZone() in s_sim.c.

    Args:
        PwrOn: Whether zone is powered
    """
    if types.cchr9 == types.POWERPLANT:
        types.coal_pop += 1
        if (types.city_time & 7) == 0:
            RepairZone(types.POWERPLANT, 4)  # post
        power.PushPowerStack()
        CoalSmoke(types.s_map_x, types.s_map_y)
        return

    if types.cchr9 == types.NUCLEAR:
        if (not types.no_disasters) and (
            micropolis.utilities.Rand(types.MltdwnTab[types.game_level]) == 0
        ):
            DoMeltdown(types.s_map_x, types.s_map_y)
            return
        types.nuclear_pop += 1
        if (types.city_time & 7) == 0:
            RepairZone(types.NUCLEAR, 4)  # post
        power.PushPowerStack()
        return

    if types.cchr9 == types.FIRESTATION:
        types.fire_st_pop += 1
        if (types.city_time & 7) == 0:
            RepairZone(types.FIRESTATION, 3)  # post

        if PwrOn:
            z = types.fire_effect  # if powered get effect
        else:
            z = types.fire_effect >> 1  # from the funding ratio

        if not FindPRoad():
            z = z >> 1  # post FD's need roads

        types.fire_st_map[types.s_map_x >> 3][types.s_map_y >> 3] += z
        return

    if types.cchr9 == types.POLICESTATION:
        types.police_pop += 1
        if (types.city_time & 7) == 0:
            RepairZone(types.POLICESTATION, 3)  # post

        if PwrOn:
            z = types.police_effect
        else:
            z = types.police_effect >> 1

        if not FindPRoad():
            z = z >> 1  # post PD's need roads

        types.police_map[types.s_map_x >> 3][types.s_map_y >> 3] += z
        return

    if types.cchr9 == types.STADIUM:
        types.stadium_pop += 1
        if (types.city_time & 15) == 0:
            RepairZone(types.STADIUM, 4)
        if PwrOn:
            if (
                (types.city_time + types.s_map_x + types.s_map_y) & 31
            ) == 0:  # post release
                DrawStadium(types.FULLSTADIUM)
                types.map_data[types.s_map_x + 1][types.s_map_y] = (
                    types.FOOTBALLGAME1 + types.ANIMBIT
                )
                types.map_data[types.s_map_x + 1][types.s_map_y + 1] = (
                    types.FOOTBALLGAME2 + types.ANIMBIT
                )
        return

    if types.cchr9 == types.FULLSTADIUM:
        types.stadium_pop += 1
        if ((types.city_time + types.s_map_x + types.s_map_y) & 7) == 0:  # post release
            DrawStadium(types.STADIUM)
        return

    if types.cchr9 == types.AIRPORT:
        types.airport_pop += 1
        if (types.city_time & 7) == 0:
            RepairZone(types.AIRPORT, 6)

        if PwrOn:  # post
            if (
                types.map_data[types.s_map_x + 1][types.s_map_y - 1] & types.LOMASK
            ) == types.RADAR:
                types.map_data[types.s_map_x + 1][types.s_map_y - 1] = (
                    types.RADAR + types.ANIMBIT + types.CONDBIT + types.BURNBIT
                )
        else:
            types.map_data[types.s_map_x + 1][types.s_map_y - 1] = (
                types.RADAR + types.CONDBIT + types.BURNBIT
            )

        if PwrOn:
            DoAirport()
        return

    if types.cchr9 == types.PORT:
        types.port_pop += 1
        if (types.city_time & 15) == 0:
            RepairZone(types.PORT, 4)
        if PwrOn and (sprites.GetSprite(types.SHI) is None):
            sprites.GenerateShip()
        return


def DrawStadium(z: int) -> None:
    """
    Draw stadium tiles.

    Ported from DrawStadium() in s_sim.c.

    Args:
        z: Base tile value
    """
    z = z - 5
    for y in range(types.s_map_y - 1, types.s_map_y + 3):
        for x in range(types.s_map_x - 1, types.s_map_x + 3):
            types.map_data[x][y] = (z) | types.BNCNBIT
    types.map_data[types.s_map_x][types.s_map_y] |= types.ZONEBIT | types.PWRBIT


def DoAirport() -> None:
    """
    Handle airport operations.

    Ported from DoAirport() in s_sim.c.
    """
    if micropolis.utilities.Rand(5) == 0:
        sprites.GeneratePlane(types.s_map_x, types.s_map_y)
        return
    if micropolis.utilities.Rand(12) == 0:
        sprites.GenerateCopter(types.s_map_x, types.s_map_y)


def CoalSmoke(mx: int, my: int) -> None:
    """
    Generate coal smoke from power plants.

    Ported from CoalSmoke() in s_sim.c.

    Args:
        mx: X coordinate
        my: Y coordinate
    """
    SmTb = [types.COALSMOKE1, types.COALSMOKE2, types.COALSMOKE3, types.COALSMOKE4]
    dx = [1, 2, 1, 2]
    dy = [-1, -1, 0, 0]

    for x in range(4):
        types.map_data[mx + dx[x]][my + dy[x]] = (
            SmTb[x] | types.ANIMBIT | types.CONDBIT | types.PWRBIT | types.BURNBIT
        )


def DoMeltdown(SX: int, SY: int) -> None:
    """
    Handle nuclear meltdown disaster.

    Ported from DoMeltdown() in s_sim.c.

    Args:
        SX: X coordinate of meltdown
        SY: Y coordinate of meltdown
    """
    global MeltX, MeltY

    MeltX = SX
    MeltY = SY

    sprites.MakeExplosion(SX - 1, SY - 1)
    sprites.MakeExplosion(SX - 1, SY + 2)
    sprites.MakeExplosion(SX + 2, SY - 1)
    sprites.MakeExplosion(SX + 2, SY + 2)

    for x in range(SX - 1, SX + 3):
        for y in range(SY - 1, SY + 3):
            types.map_data[x][y] = (
                types.FIRE + (micropolis.utilities.Rand16() & 3) + types.ANIMBIT
            )

    for z in range(200):
        x = SX - 20 + micropolis.utilities.Rand(40)
        y = SY - 15 + micropolis.utilities.Rand(30)
        if (
            (x < 0)
            or (x >= micropolis.constants.WORLD_X)
            or (y < 0)
            or (y >= micropolis.constants.WORLD_Y)
        ):
            continue
        t = types.map_data[x][y]
        if t & types.ZONEBIT:
            continue
        if (t & types.BURNBIT) or (t == 0):
            types.map_data[x][y] = types.RADTILE

    messages.ClearMes()
    messages.SendMesAt(-43, SX, SY)


# ============================================================================
# Random Number Functions
# ============================================================================

RANDOM_RANGE = 0xFFFF


def Rand(range_val: int) -> int:
    """
    Generate random number in range.

    Ported from Rand() in s_sim.c.

    Args:
        range_val: Upper bound (exclusive)

    Returns:
        Random number between 0 and range_val-1
    """
    range_val += 1
    maxMultiple = RANDOM_RANGE // range_val
    maxMultiple *= range_val
    while True:
        rnum = micropolis.utilities.Rand16()
        if rnum < maxMultiple:
            break
    return rnum % range_val


def Rand16() -> int:
    """
    Generate 16-bit random number.

    Ported from Rand16() in s_sim.c.

    Returns:
        Random number from sim_rand()
    """
    return micropolis.utilities.sim_rand()


def Rand16Signed() -> int:
    """
    Generate signed 16-bit random number.

    Ported from Rand16Signed() in s_sim.c.

    Returns:
        Signed random number
    """
    i = micropolis.utilities.sim_rand()
    if i > 32767:
        i = 32767 - i
    return i


def RandomlySeedRand() -> None:
    """
    Seed random number generator with current time.

    Ported from RandomlySeedRand() in s_sim.c.
    """
    # Use current time for seeding
    current_time = time.time()
    seed = int(current_time * 1000000)  # microseconds
    SeedRand(seed)


def SeedRand(seed: int) -> None:
    """
    Seed the random number generator.

    Ported from SeedRand() in s_sim.c.

    Args:
        seed: Seed value
    """
    micropolis.utilities.sim_srand(seed)


# ============================================================================
# Placeholder Functions (to be implemented)
# ============================================================================


def CityEvaluation() -> None:
    """City evaluation - placeholder for evaluation.py"""
    pass


def SendMessages() -> None:
    """Send messages - placeholder for messages.py"""
    pass


def DoPowerScan() -> None:
    """Power grid scanning - implemented in power.py"""
    power.DoPowerScan()


def DoDisasters() -> None:
    """Handle disasters - placeholder for disasters.py"""
    pass


def DoFlood() -> None:
    """Handle flood tiles - placeholder"""
    pass


def DoZone() -> None:
    """Process zone tiles - placeholder for zones.py"""
    pass


def FindPRoad() -> bool:
    """Find if there's a powered road nearby - placeholder"""
    return True  # Assume roads are powered for now


# ============================================================================
# Set Common Inits (placeholder)
# ============================================================================


def SetCommonInits() -> None:
    """
    Set common initialization values.

    Ported from SetCommonInits() in s_sim.c.
    """
    # evaluation.EvalInit() - placeholder
    types.road_effect = 32
    types.police_effect = 1000
    types.fire_effect = 1000
    types.tax_flag = 0
    types.tax_fund = 0
