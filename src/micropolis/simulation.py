"""
simulation.py - Core simulation step logic for Micropolis Python port

This module contains the main simulation loop and supporting functions
ported from s_sim.c, implementing the city simulation mechanics.
"""

import time

from .constants import WORLD_X, CENSUSRATE, TAXFREQ, TDMAP, RDMAP, ALMAP, REMAP, COMAP, INMAP, DYMAP, HWLDX, HWLDY, \
    SM_X, SM_Y, WORLD_Y
from .context import AppContext
from .macros import TestBounds
from .messages import clear_mes, send_mes_at
from .power import DoPowerScan, PushPowerStack
from .random import sim_rand, sim_srand
from .sprite_manager import GenerateTrain, GenerateBus, MakeExplosionAt, GeneratePlane, GenerateCopter, GetSprite, \
    GenerateShip, MakeExplosion
from .zones import SetZPower


# ============================================================================
# Simulation Control Variables (from s_sim.c globals)
# ============================================================================

# Valve control
# valve_flag: int = 0
# crime_ramp: int = 0
# pollute_ramp: int = 0
# r_valve: int = 0
# c_valve: int = 0
# i_valve: int = 0

# Capacity limits
# res_cap: int = 0
# com_cap: int = 0
# ind_cap: int = 0

# Financial
# cash_flow: int = 0
# e_market: float = 4.0

# Disaster control
# disaster_event: int = 0
# disaster_wait: int = 0

# Scoring
# score_type: int = 0
# score_wait: int = 0

# Power statistics
# pwrd_z_cnt: int = 0
# un_pwrd_z_cnt: int = 0
# new_power: int = 0

# Tax averaging
# av_city_tax: int = 0

# Cycle counters
# scycle: int = 0
# fcycle: int = 0
# spdcycle: int = 0

# Initial evaluation flag
# do_initial_eval: int = 0

# Melt down coordinates
# melt_x: int = 0
# melt_y: int = 0


# ============================================================================
# Simulation Control Variables (from s_sim.c globals)
# ============================================================================








# ============================================================================
# Main Simulation Functions
# ============================================================================


def sim_frame(context: AppContext) -> None:
    """
    ported from SimFrame
    Main simulation frame function.

    Called each frame to advance the simulation based on speed settings.
    Ported from SimFrame() in s_sim.c.
    """
    # global spdcycle, fcycle

    if context.sim_speed == 0:
        return

    context.spdcycle = (context.spdcycle + 1) % 1024

    if context.sim_speed == 1 and (context.spdcycle % 5) != 0:
        return

    if context.sim_speed == 2 and (context.spdcycle % 3) != 0:
        return

    context.fcycle = (context.fcycle + 1) % 1024
    # if InitSimLoad: Fcycle = 0;  # XXX: commented out in original

    simulate(context, context.fcycle & 15)


def simulate(context: AppContext, mod16: int) -> None:
    """
    ported from Simulate
    Main simulation loop function.

    Executes different simulation phases based on the mod16 counter.
    Ported from Simulate() in s_sim.c.

    Args:
        mod16: Current simulation phase (0-15)
        :param mod16:
        :param context:
    """
    # global scycle, do_initial_eval, av_city_tax

    # Speed control tables (from original C code)
    spd_pwr = [1, 2, 4, 5]
    spd_ptl = [1, 2, 7, 17]
    spd_cri = [1, 1, 8, 18]
    spd_pop = [1, 1, 9, 19]
    spd_fir = [1, 1, 10, 20]

    x = context.sim_speed
    if x > 3:
        x = 3

    if mod16 == 0:
        context.scycle = (context.scycle + 1) % 1024  # This is cosmic
        if context.do_initial_eval:
            context.do_initial_eval = 0
            city_evaluation()
        context.city_time += 1
        context.av_city_tax += context.city_tax  # post
        if (context.scycle & 1) == 0:
            set_valves(context)
        clear_census(context)

    elif mod16 == 1:
        map_scan(context, 0, 1 * WORLD_X // 8)
    elif mod16 == 2:
        map_scan(context, 1 * WORLD_X // 8, 2 * WORLD_X // 8)
    elif mod16 == 3:
        map_scan(context, 2 * WORLD_X // 8, 3 * WORLD_X // 8)
    elif mod16 == 4:
        map_scan(context, 3 * WORLD_X // 8, 4 * WORLD_X // 8)
    elif mod16 == 5:
        map_scan(context, 4 * WORLD_X // 8, 5 * WORLD_X // 8)
    elif mod16 == 6:
        map_scan(context, 5 * WORLD_X // 8, 6 * WORLD_X // 8)
    elif mod16 == 7:
        map_scan(context, 6 * WORLD_X // 8, 7 * WORLD_X // 8)
    elif mod16 == 8:
        map_scan(context, 7 * WORLD_X // 8, WORLD_X)

    elif mod16 == 9:
        if (context.city_time % CENSUSRATE) == 0:
            take_census(context)
        if (context.city_time % (CENSUSRATE * 12)) == 0:
            take2_census(context)

        if (context.city_time % TAXFREQ) == 0:
            collect_tax(context)
            city_evaluation()

    elif mod16 == 10:
        if (context.scycle % 5) == 0:
            dec_rog_mem(context)
        dec_traffic_mem(context)
        context.new_map_flags[TDMAP] = 1
        context.new_map_flags[RDMAP] = 1
        context.new_map_flags[ALMAP] = 1
        context.new_map_flags[REMAP] = 1
        context.new_map_flags[COMAP] = 1
        context.new_map_flags[INMAP] = 1
        context.new_map_flags[DYMAP] = 1
        send_messages()

    elif mod16 == 11:
        if (context.scycle % spd_pwr[x]) == 0:
            do_power_scan(context)
            context.new_power = 1  # post-release change

    elif mod16 == 12:
        if (context.scycle % spd_ptl[x]) == 0:
            # PTLScan() - Pollution scanning (placeholder)
            pass

    elif mod16 == 13:
        if (context.scycle % spd_cri[x]) == 0:
            # CrimeScan() - Crime scanning (placeholder)
            pass

    elif mod16 == 14:
        if (context.scycle % spd_pop[x]) == 0:
            # PopDenScan() - Population density scanning (placeholder)
            pass

    elif mod16 == 15:
        if (context.scycle % spd_fir[x]) == 0:
            # FireAnalysis() - Fire analysis (placeholder)
            pass
        do_disasters()


def do_sim_init(context: AppContext) -> None:
    """
    ported from do_sim_init
    Initialize simulation when loading a city.

    Ported from DoSimInit() in s_sim.c.
    :param context:
    """
    # global fcycle, scycle

    context.fcycle = 0
    context.scycle = 0

    if context.init_sim_load == 2:  # if new city
        init_sim_memory(context)

    if context.init_sim_load == 1:  # if city just loaded
        sim_load_init(context)

    set_valves(context)
    clear_census(context)
    # MapScan(0, WORLD_X)  # XXX: commented out in original
    DoPowerScan(context)
    context.new_power = 1  # post rel
    # PTLScan() - placeholder
    # CrimeScan() - placeholder
    # PopDenScan() - placeholder
    # FireAnalysis() - placeholder
    context.new_map = 1
    # doAllGraphs() - placeholder
    context.new_graph = 1
    context.total_pop = 1
    context.do_initial_eval = 1


# ============================================================================
# Memory Management Functions
# ============================================================================


def dec_traffic_mem(context: AppContext) -> None:
    """
    ported from dec_traffic_mem
    Gradually reduces traffic density values.

    Ported from DecTrafficMem() in s_sim.c.
    :param context:
    """
    for x in range(HWLDX):
        for y in range(HWLDY):
            z = context.trf_density[x][y]
            if z > 0:
                if z > 24:
                    if z > 200:
                        context.trf_density[x][y] = z - 34
                    else:
                        context.trf_density[x][y] = z - 24
                else:
                    context.trf_density[x][y] = 0


def dec_rog_mem(context: AppContext) -> None:
    """
    ported from DecROGMem
    Gradually reduces RateOGMem values.

    Ported from DecROGMem() in s_sim.c.
    :param context:
    """
    for x in range(SM_X):
        for y in range(SM_Y):
            z = context.rate_og_mem[x][y]
            if z == 0:
                continue
            if z > 0:
                context.rate_og_mem[x][y] -= 1
                if z > 200:
                    context.rate_og_mem[x][y] = 200  # prevent overflow
                continue
            if z < 0:
                context.rate_og_mem[x][y] += 1
                if z < -200:
                    context.rate_og_mem[x][y] = -200


def init_sim_memory(context: AppContext) -> None:
    """
    ported from InitSimMemory
    Initialize simulation memory for a new city.

    Ported from InitSimMemory() in s_sim.c.
    :param context:
    """
    # global crime_ramp, pollute_ramp, e_market, disaster_event, score_type

    z = 0
    # SetCommonInits() - placeholder
    for x in range(240):
        context.res_his[x] = z
        context.com_his[x] = z
        context.ind_his[x] = z
        context.money_his[x] = 128
        context.crime_his[x] = z
        context.pollution_his[x] = z

    context.crime_ramp = z
    context.pollute_ramp = z
    context.total_pop = z
    context.r_value = z
    context.c_value = z
    context.i_val = z
    context.res_cap = z
    context.com_cap = z
    context.ind_cap = z

    context.e_market = 6.0
    context.disaster_event = 0
    context.score_type = 0

    # Clear power map
    for z in range(context.PWRMAPSIZE):
        context.power_map[z] = ~0  # set power Map
    DoPowerScan(context)
    context.new_power = 1  # post rel

    context.init_sim_load = 0


def sim_load_init(context: AppContext) -> None:
    """
    ported SimLoadInit
    Initialize simulation when loading a saved city.

    Ported from SimLoadInit() in s_sim.c.
    :param context:
    """
    # Disaster wait times for different scenarios
    dis_tab = [0, 2, 10, 5, 20, 3, 5, 5, 2 * 48]
    score_wait_tab = [
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

    # global e_market, r_valve, c_valve, i_valve, crime_ramp, pollute_ramp

    z = 0
    context.e_market = float(context.misc_his[1])
    context.res_pop = context.misc_his[2]
    context.com_pop = context.misc_his[3]
    context.ind_pop = context.misc_his[4]
    context.r_valve = context.misc_his[5]
    context.c_valve = context.misc_his[6]
    context.i_valve = context.misc_his[7]
    context.crime_ramp = context.misc_his[10]
    context.pollute_ramp = context.misc_his[11]
    context.lv_average = context.misc_his[12]
    context.crime_average = context.misc_his[13]
    context.pollute_average = context.misc_his[14]
    context.game_level = context.misc_his[15]

    if context.city_time < 0:
        context.city_time = 0
    if context.e_market == 0:
        context.e_market = 4.0
    if (context.game_level > 2) or (context.game_level < 0):
        context.game_level = 0
    # SetGameLevel(GameLevel) - placeholder

    # SetCommonInits() - placeholder

    context.city_class = context.misc_his[16]
    context.city_score = context.misc_his[17]

    if (context.city_class > 5) or (context.city_class < 0):
        context.city_class = 0
    if (context.city_score > 999) or (context.city_score < 1):
        context.city_score = 500

    context.res_cap = 0
    context.com_cap = 0
    context.ind_cap = 0

    context.av_city_tax = (context.city_time % 48) * 7  # post

    for z in range(context.PWRMAPSIZE):
        context.power_map[z] = 0xFFFF  # set power Map
    do_nil_power(context)

    if context.scenario_id > 8:
        context.scenario_id = 0

    if context.scenario_id:
        context.disaster_event = context.scenario_id
        context.disaster_wait = dis_tab[context.scenario_id]
        context.score_type = context.scenario_id
        context.score_wait = score_wait_tab[context.scenario_id]
    else:
        context.disaster_event = 0
        context.score_type = 0

    context.road_effect = 32
    context.police_effect = 1000  # post
    context.fire_effect = 1000
    context.init_sim_load = 0


def do_nil_power(context: AppContext) -> None:
    """
    DoNilPower
    Set power for all zones when loading a city.

    Ported from DoNilPower() in s_sim.c.
    :param context:
    """
    for x in range(WORLD_X):
        for y in range(WORLD_Y):
            z = context.map_data[x][y]
            if z & context.ZONEBIT:
                context.s_map_x = x
                context.s_map_y = y
                context.cchr = z
                SetZPower()


# ============================================================================
# Valve and Census Functions
# ============================================================================


def set_valves(context: AppContext) -> None:
    """
    ported from SetValves
    Set zone growth valves based on economic conditions.

    Ported from SetValves() in s_sim.c.
    """
    # Tax table for different tax rates
    tax_table = [
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

    # global valve_flag, r_valve, c_valve, i_valve

    # Store current values in MiscHis
    context.misc_his[1] = int(context.e_market)
    context.misc_his[2] = context.res_pop
    context.misc_his[3] = context.com_pop
    context.misc_his[4] = context.ind_pop
    context.misc_his[5] = context.r_valve
    context.misc_his[6] = context.c_valve
    context.misc_his[7] = context.i_valve
    context.misc_his[10] = context.crime_ramp
    context.misc_his[11] = context.pollute_ramp
    context.misc_his[12] = context.lv_average
    context.misc_his[13] = context.crime_average
    context.misc_his[14] = context.pollute_average
    context.misc_his[15] = context.game_level
    context.misc_his[16] = context.city_class
    context.misc_his[17] = context.city_score

    # Calculate normalized residential population
    norm_res_pop = context.res_pop / 8
    context.last_total_pop = context.total_pop
    context.total_pop = norm_res_pop + context.com_pop + context.ind_pop

    # Calculate employment rate
    if norm_res_pop:
        employment = (context.com_his[1] + context.ind_his[1]) / norm_res_pop
    else:
        employment = 1

    # Calculate migration and births
    migration = norm_res_pop * (employment - 1)
    births = norm_res_pop * 0.02  # Birth Rate
    pj_res_pop = norm_res_pop + migration + births  # Projected Res.Pop

    # Calculate labor base
    if context.com_his[1] + context.ind_his[1]:
        labor_base = context.res_his[1] / (context.com_his[1] + context.ind_his[1])
    else:
        labor_base = 1
    if labor_base > 1.3:
        labor_base = 1.3
    if labor_base < 0:
        labor_base = 0  # LB > 1 - .1

    # Calculate temporary values for market calculations
    for z in range(2):
        temp = context.res_his[z] + context.com_his[z] + context.ind_his[z]
    int_market = (norm_res_pop + context.com_pop + context.ind_pop) / 3.7

    # Calculate projected commercial population
    pj_com_pop = int_market * labor_base

    # Adjust for game level
    z = context.game_level
    temp = 1
    if z == 0:
        temp = 1.2
    elif z == 1:
        temp = 1.1
    elif z == 2:
        temp = 0.98

    pj_ind_pop = context.ind_pop * labor_base * temp
    if pj_ind_pop < 5:
        pj_ind_pop = 5

    # Calculate ratios
    if norm_res_pop:
        rratio = pj_res_pop / norm_res_pop  # projected -vs- actual
    else:
        rratio = 1.3
    if context.com_pop:
        cratio = pj_com_pop / context.com_pop
    else:
        cratio = pj_com_pop
    if context.ind_pop:
        iratio = pj_ind_pop / context.ind_pop
    else:
        iratio = pj_ind_pop

    # Clamp ratios
    if rratio > 2:
        rratio = 2
    if cratio > 2:
        cratio = 2
    if iratio > 2:
        iratio = 2

    # Apply tax effects
    z = context.city_tax + context.game_level
    if z > 20:
        z = 20
    rratio = ((rratio - 1) * 600) + tax_table[z]  # global tax/Glevel effects
    cratio = ((cratio - 1) * 600) + tax_table[z]
    iratio = ((iratio - 1) * 600) + tax_table[z]

    # Update valves
    if rratio > 0:
        if context.r_valve < 2000:
            context.r_valve += int(rratio)
    if rratio < 0:
        if context.r_valve > -2000:
            context.r_valve += int(rratio)
    if cratio > 0:
        if context.c_valve < 1500:
            context.c_valve += int(cratio)
    if cratio < 0:
        if context.c_valve > -1500:
            context.c_valve += int(cratio)
    if iratio > 0:
        if context.i_valve < 1500:
            context.i_valve += int(iratio)
    if iratio < 0:
        if context.i_valve > -1500:
            context.i_valve += int(iratio)

    # Clamp valve values
    if context.r_valve > 2000:
        context.r_valve = 2000
    if context.r_valve < -2000:
        context.r_valve = -2000
    if context.c_valve > 1500:
        context.c_valve = 1500
    if context.c_valve < -1500:
        context.c_valve = -1500
    if context.i_valve > 1500:
        context.i_valve = 1500
    if context.i_valve < -1500:
        context.i_valve = -1500

    # Apply capacity limits
    if context.res_cap and context.r_valve > 0:
        context.r_valve = 0  # Stad, Prt, Airprt
    if context.com_cap and context.c_valve > 0:
        context.c_valve = 0
    if context.ind_cap and context.i_valve > 0:
        context.i_valve = 0
    context.valve_flag = 1


def clear_census(context: AppContext) -> None:
    """
    ported from ClearCensus
    Reset all census counters.

    Ported from ClearCensus() in s_sim.c.
    :param context:
    """
    # global pwrd_z_cnt, un_pwrd_z_cnt

    z = 0
    context.pwrd_z_cnt = z
    context.un_pwrd_z_cnt = z
    context.fire_pop = z
    context.road_total = z
    context.rail_total = z
    context.res_pop = z
    context.com_pop = z
    context.ind_pop = z
    context.res_z_pop = z
    context.ComZPop = z
    context.IndZPop = z
    context.hosp_pop = z
    context.church_pop = z
    context.police_pop = z
    context.fire_st_pop = z
    context.stadium_pop = z
    context.coal_pop = z
    context.nuclear_pop = z
    context.port_pop = z
    context.airport_pop = z
    context.power_stack_num = z  # Reset before Mapscan

    for x in range(SM_X):
        for y in range(SM_Y):
            context.fire_st_map[x][y] = z
            context.police_map[x][y] = z


def take_census(context: AppContext) -> None:
    """
    ported from TakeCensus
    Record population data in history graphs.

    Ported from TakeCensus() in s_sim.c.
    :param context:
    """
    # global crime_ramp, pollute_ramp

    # Scroll data
    for x in range(118, -1, -1):
        context.res_his[x + 1] = context.res_his[x]
        context.com_his[x + 1] = context.com_his[x]
        context.ind_his[x + 1] = context.ind_his[x]
        context.crime_his[x + 1] = context.crime_his[x]
        context.pollution_his[x + 1] = context.pollution_his[x]
        context.money_his[x + 1] = context.money_his[x]

    # Update max values
    res_his_max = 0
    com_his_max = 0
    ind_his_max = 0
    for x in range(119):
        if context.res_his[x] > res_his_max:
            res_his_max = context.res_his[x]
        if context.com_his[x] > com_his_max:
            com_his_max = context.com_his[x]
        if context.ind_his[x] > ind_his_max:
            ind_his_max = context.ind_his[x]

    context.graph_10_max = res_his_max
    if com_his_max > context.graph_10_max:
        context.graph_10_max = com_his_max
    if ind_his_max > context.graph_10_max:
        context.graph_10_max = ind_his_max

    # Set current values
    context.res_his[0] = context.res_pop // 8
    context.com_his[0] = context.com_pop
    context.ind_his[0] = context.ind_pop

    # Update crime and pollution ramps
    context.crime_ramp += (context.crime_average - context.crime_ramp) // 4
    context.crime_his[0] = context.crime_ramp

    context.pollute_ramp += (context.pollute_average - context.pollute_ramp) // 4
    context.pollution_his[0] = context.pollute_ramp

    # Scale cash flow to 0..255
    x = (context.cash_flow // 20) + 128
    if x < 0:
        x = 0
    if x > 255:
        x = 255

    context.money_his[0] = x
    if context.crime_his[0] > 255:
        context.crime_his[0] = 255
    if context.pollution_his[0] > 255:
        context.pollution_his[0] = 255

    # ChangeCensus() - placeholder for 10 year graph view

    # Check hospital and church needs
    if context.hosp_pop < (context.res_pop >> 8):
        context.need_hosp = True
    if context.hosp_pop > (context.res_pop >> 8):
        context.need_hosp = -1
    if context.hosp_pop == (context.res_pop >> 8):
        context.need_hosp = False

    if context.church_pop < (context.res_pop >> 8):
        context.need_church = True
    if context.church_pop > (context.res_pop >> 8):
        context.need_church = -1
    if context.church_pop == (context.res_pop >> 8):
        context.need_church = False


def take2_census(context: AppContext) -> None:
    """
    ported from Take2Census
    Record long-term population data.

    Ported from Take2Census() in s_sim.c.
    :param context:
    """
    # Scroll 120-year data
    for x in range(238, 119, -1):
        context.res_his[x + 1] = context.res_his[x]
        context.com_his[x + 1] = context.com_his[x]
        context.ind_his[x + 1] = context.ind_his[x]
        context.crime_his[x + 1] = context.crime_his[x]
        context.pollution_his[x + 1] = context.pollution_his[x]
        context.money_his[x + 1] = context.money_his[x]

    # Update max values
    res2_his_max = 0
    com2_his_max = 0
    ind2_his_max = 0
    for x in range(120, 239):
        if context.res_his[x] > res2_his_max:
            res2_his_max = context.res_his[x]
        if context.com_his[x] > com2_his_max:
            com2_his_max = context.com_his[x]
        if context.ind_his[x] > ind2_his_max:
            ind2_his_max = context.ind_his[x]

    context.graph_12_max = res2_his_max
    if com2_his_max > context.graph_12_max:
        context.graph_12_max = com2_his_max
    if ind2_his_max > context.graph_12_max:
        context.graph_12_max = ind2_his_max

    # Set 120-year values
    context.res_his[120] = context.res_pop // 8
    context.com_his[120] = context.com_pop
    context.ind_his[120] = context.ind_pop
    context.crime_his[120] = context.crime_his[0]
    context.pollution_his[120] = context.pollution_his[0]
    context.money_his[120] = context.money_his[0]
    # ChangeCensus() - placeholder for 120 year graph view


# ============================================================================
# Tax and Financial Functions
# ============================================================================


def collect_tax(context: AppContext) -> None:
    """
    ported from CollectTax
    Calculate and collect taxes.

    Ported from CollectTax() in s_sim.c.
    :param context:
    """
    # global cash_flow, av_city_tax

    # Tax level factors
    r_levels = [0.7, 0.9, 1.2]
    f_levels = [1.4, 1.2, 0.8]

    context.cash_flow = 0
    if not context.tax_flag:  # if the Tax Port is clear
        # XXX: do something with z
        z = context.av_city_tax // 48  # post
        context.av_city_tax = 0

        context.police_fund = context.police_pop * 100
        context.fire_fund = context.fire_st_pop * 100
        context.road_fund = (context.road_total + (context.rail_total * 2)) * r_levels[
            context.game_level
        ]
        context.tax_fund = (
            ((context.total_pop * context.lv_average) // 120)
            * context.city_tax
            * f_levels[context.game_level]
        )

        if context.total_pop:  # if there are people to tax
            context.cash_flow = int(
                context.tax_fund - (context.police_fund + context.fire_fund + context.road_fund)
            )

            # DoBudget() - placeholder
        else:
            context.road_effect = 32
            context.police_effect = 1000
            context.fire_effect = 1000


def update_fund_effects(context: AppContext) -> None:
    """
    ported from UpdateFundEffects
    Update service effects based on funding levels.

    Ported from UpdateFundEffects() in s_sim.c.
    :param context:
    """
    if context.road_fund:
        context.road_effect = int((context.road_spend / context.road_fund) * 32.0)
    else:
        context.road_effect = 32

    if context.police_fund:
        context.police_effect = int((context.police_spend / context.police_fund) * 1000.0)
    else:
        context.police_effect = 1000

    if context.fire_fund:
        context.fire_effect = int(((context.fire_spend / context.fire_fund) * 1000.0))
    else:
        context.fire_effect = 1000

    # drawCurrPercents() - placeholder


# ============================================================================
# Map Scanning Functions
# ============================================================================


def map_scan(context: AppContext, x1: int, x2: int) -> None:
    """
    ported from MapScan
    Scan and process tiles in the specified range.

    Ported from MapScan() in s_sim.c.

    Args:
        x1: Starting x coordinate
        x2: Ending x coordinate
        :param context:
    """
    for x in range(x1, x2):
        for y in range(WORLD_Y):
            context.cchr = context.map_data[x][y]
            if context.cchr:
                context.cchr9 = context.cchr & context.LOMASK  # Mask off status bits
                if context.cchr9 >= context.FLOOD:
                    context.s_map_x = x
                    context.s_map_y = y
                    if context.cchr9 < context.ROADBASE:
                        if context.cchr9 >= context.FIREBASE:
                            context.fire_pop += 1
                            if (rand16() & 3) == 0:  # 1 in 4 times
                                do_fire(context)
                            continue
                        if context.cchr9 < context.RADTILE:
                            do_flood()
                        else:
                            do_rad_tile(context)
                        continue

                    if context.new_power and (context.cchr & context.CONDBIT):
                        SetZPower()

                    if (context.cchr9 >= context.ROADBASE) and (
                        context.cchr9 < context.POWERBASE
                    ):
                        do_road(context)
                        continue

                    if context.cchr & context.ZONEBIT:  # process Zones
                        do_zone()
                        continue

                    if (context.cchr9 >= context.RAILBASE) and (
                        context.cchr9 < context.RESBASE
                    ):
                        do_rail(context)
                        continue
                    if (context.cchr9 >= context.SOMETINYEXP) and (
                        context.cchr9 <= context.LASTTINYEXP
                    ):
                        # clear AniRubble
                        context.map_data[x][y] = (
                            context.RUBBLE
                            + (rand16() & 3)
                            + context.BULLBIT
                        )


# ============================================================================
# Tile Processing Functions
# ============================================================================


def do_rail(context: AppContext) -> None:
    """
    ported from DoRail
    Process rail tiles.

    Ported from DoRail() in s_sim.c.
    :param context:
    """
    context.rail_total += 1
    GenerateTrain(context, context.s_map_x, context.s_map_y)
    if context.road_effect < 30:  # Deteriorating Rail
        if (rand16() & 511) == 0:
            if (context.cchr & context.CONDBIT) == 0:
                if context.road_effect < (rand16() & 31):
                    if context.cchr9 < (context.RAILBASE + 2):
                        context.map_data[context.s_map_x][context.s_map_y] = context.RIVER
                    else:
                        context.map_data[context.s_map_x][context.s_map_y] = (
                            context.RUBBLE
                            + (rand16() & 3)
                            + context.BULLBIT
                        )


def do_rad_tile(context: AppContext) -> None:
    """
    ported from DoRadTile
    Process radioactive tiles.

    Ported from DoRadTile() in s_sim.c.
    :param context:
    """
    if (rand16() & 4095) == 0:
        context.map_data[context.s_map_x][context.s_map_y] = 0  # Radioactive decay


def do_road(context: AppContext) -> None:
    """
    ported from DoRoad
    Process road tiles.

    Ported from DoRoad() in s_sim.c.
    """
    # global types

    den_tab = [context.ROADBASE, context.LTRFBASE, context.HTRFBASE]

    context.road_total += 1
    GenerateBus(context, context.s_map_x, context.s_map_y)

    if context.road_effect < 30:  # Deteriorating Roads
        if (rand16() & 511) == 0:
            if (context.cchr & context.CONDBIT) == 0:
                if context.road_effect < (rand16() & 31):
                    if ((context.cchr9 & 15) < 2) or ((context.cchr9 & 15) == 15):
                        context.map_data[context.s_map_x][context.s_map_y] = context.RIVER
                    else:
                        context.map_data[context.s_map_x][context.s_map_y] = (
                            context.RUBBLE
                            + (rand16() & 3)
                            + context.BULLBIT
                        )
                    return

    if context.cchr & context.BURNBIT:  # If Bridge
        context.road_total += 4
        if do_bridge(context):
            return

    if context.cchr9 < context.LTRFBASE:
        tden = 0
    else:
        if context.cchr9 < context.HTRFBASE:
            tden = 1
        else:
            context.road_total += 1
            tden = 2

    # Set Traf Density
    density = (context.trf_density[context.s_map_x >> 1][context.s_map_y >> 1]) >> 6
    if density > 1:
        density -= 1
    if tden != density:  # tden 0..2
        z = ((context.cchr9 - context.ROADBASE) & 15) + den_tab[density]
        z += context.cchr & (context.ALLBITS - context.ANIMBIT)
        if density:
            z += context.ANIMBIT
        context.map_data[context.s_map_x][context.s_map_y] = z


def do_bridge(context: AppContext) -> bool:
    """
    ported from DoBridge
    Handle bridge opening and closing.

    Ported from DoBridge() in s_sim.c.

    Returns:
        True if bridge was processed, False otherwise
        :param context:
    """
    # Bridge tile tables
    h_dx = [-2, 2, -2, -1, 0, 1, 2]
    h_dy = [-1, -1, 0, 0, 0, 0, 0]
    hbrtab = [
        context.HBRDG1 | context.BULLBIT,
        context.HBRDG3 | context.BULLBIT,
        context.HBRDG0 | context.BULLBIT,
        context.RIVER,
        context.BRWH | context.BULLBIT,
        context.RIVER,
        context.HBRDG2 | context.BULLBIT,
    ]
    hbrtab2 = [
        context.RIVER,
        context.RIVER,
        context.HBRIDGE | context.BULLBIT,
        context.HBRIDGE | context.BULLBIT,
        context.HBRIDGE | context.BULLBIT,
        context.HBRIDGE | context.BULLBIT,
        context.HBRIDGE | context.BULLBIT,
    ]
    v_dx = [0, 1, 0, 0, 0, 0, 1]
    v_dy = [-2, -2, -1, 0, 1, 2, 2]
    vbrtab = [
        context.VBRDG0 | context.BULLBIT,
        context.VBRDG1 | context.BULLBIT,
        context.RIVER,
        context.BRWV | context.BULLBIT,
        context.RIVER,
        context.VBRDG2 | context.BULLBIT,
        context.VBRDG3 | context.BULLBIT,
    ]
    vbrtab2 = [
        context.VBRIDGE | context.BULLBIT,
        context.RIVER,
        context.VBRIDGE | context.BULLBIT,
        context.VBRIDGE | context.BULLBIT,
        context.VBRIDGE | context.BULLBIT,
        context.VBRIDGE | context.BULLBIT,
        context.RIVER,
    ]

    if context.cchr9 == context.BRWV:  # Vertical bridge close
        if ((rand16() & 3) == 0) and (get_boat_dis(context) > 340):
            for z in range(7):  # Close
                x = context.s_map_x + v_dx[z]
                y = context.s_map_y + v_dy[z]
                if TestBounds(x, y):
                    if (context.map_data[x][y] & context.LOMASK) == (
                        vbrtab[z] & context.LOMASK
                    ):
                        context.map_data[x][y] = vbrtab2[z]
        return True

    if context.cchr9 == context.BRWH:  # Horizontal bridge close
        if ((rand16() & 3) == 0) and (get_boat_dis(context) > 340):
            for z in range(7):  # Close
                x = context.s_map_x + h_dx[z]
                y = context.s_map_y + h_dy[z]
                if TestBounds(x, y):
                    if (context.map_data[x][y] & context.LOMASK) == (
                        hbrtab[z] & context.LOMASK
                    ):
                        context.map_data[x][y] = hbrtab2[z]
        return True

    if (get_boat_dis(context) < 300) or ((rand16() & 7) == 0):
        if context.cchr9 & 1:  # Vertical open
            if context.s_map_x < (WORLD_X - 1):
                if context.map_data[context.s_map_x + 1][context.s_map_y] == context.CHANNEL:
                    for z in range(7):
                        x = context.s_map_x + v_dx[z]
                        y = context.s_map_y + v_dy[z]
                        if TestBounds(x, y):
                            m_ptem = context.map_data[x][y]
                            if (m_ptem == context.CHANNEL) or (
                                (m_ptem & 15) == (vbrtab2[z] & 15)
                            ):
                                context.map_data[x][y] = vbrtab[z]
                    return True
            return False
        else:  # Horizontal open
            if context.s_map_y > 0:
                if context.map_data[context.s_map_x][context.s_map_y - 1] == context.CHANNEL:
                    for z in range(7):
                        x = context.s_map_x + h_dx[z]
                        y = context.s_map_y + h_dy[z]
                        if TestBounds(x, y):
                            m_ptem = context.map_data[x][y]
                            if ((m_ptem & 15) == (hbrtab2[z] & 15)) or (
                                m_ptem == context.CHANNEL
                            ):
                                context.map_data[x][y] = hbrtab[z]
                    return True
            return False
    return False


def get_boat_dis(context: AppContext) -> int:
    """
    ported from GetBoatDis
    Get distance to nearest boat.

    Ported from GetBoatDis() in s_sim.c.

    Returns:
        Distance to nearest boat sprite
        :param context:
    """
    dist = 99999
    mx = (context.s_map_x << 4) + 8
    my = (context.s_map_y << 4) + 8

    sprite = context.sim.sprite
    while sprite is not None:
        if (sprite.type == context.SHI) and (sprite.frame != 0):
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


def do_fire(context: AppContext) -> None:
    """
    ported from DoFire
    Handle fire spread from fire tiles.

    Ported from DoFire() in s_sim.c.
    :param context:
    """
    dx = [-1, 0, 1, 0]
    dy = [0, -1, 0, 1]

    for z in range(4):
        if (rand16() & 7) == 0:
            xtem = context.s_map_x + dx[z]
            ytem = context.s_map_y + dy[z]
            if TestBounds(xtem, ytem):
                c = context.map_data[xtem][ytem]
                if c & context.BURNBIT:
                    if c & context.ZONEBIT:
                        fire_zone(context, xtem, ytem, c)
                        if (c & context.LOMASK) > context.IZB:  # Explode
                            MakeExplosionAt((xtem << 4) + 8, (ytem << 4) + 8)
                    context.map_data[xtem][ytem] = (
                            context.FIRE + (rand16() & 3) + context.ANIMBIT
                    )

    z = context.fire_rate[context.s_map_x >> 3][context.s_map_y >> 3]
    rate = 10
    if z:
        rate = 3
        if z > 20:
            rate = 2
        if z > 100:
            rate = 1
    if rand(context, rate) == 0:
        context.map_data[context.s_map_x][context.s_map_y] = (
                context.RUBBLE + (rand16() & 3) + context.BULLBIT
        )


def fire_zone(context: AppContext, xloc: int, yloc: int, ch: int) -> None:
    """
    ported from fire_zone
    Handle fire damage to zones.

    Ported from FireZone() in s_sim.c.

    Args:
        Xloc: X coordinate of fire
        Yloc: Y coordinate of fire
        ch: Tile value
        :param context:
    """
    context.rate_og_mem[xloc >> 3][yloc >> 3] -= 20

    ch = ch & context.LOMASK
    if ch < context.PORTBASE:
        x_ymax = 2
    else:
        if ch == context.AIRPORT:
            x_ymax = 5
        else:
            x_ymax = 4

    for x in range(-1, x_ymax):
        for y in range(-1, x_ymax):
            xtem = xloc + x
            ytem = yloc + y
            if (
                (xtem < 0)
                or (xtem > (WORLD_X - 1))
                or (ytem < 0)
                or (ytem > (WORLD_Y - 1))
            ):
                continue
            if (
                context.map_data[xtem][ytem] & context.LOMASK
            ) >= context.ROADBASE:  # post release
                context.map_data[xtem][ytem] |= context.BULLBIT


def repair_zone(context: AppContext, z_cent: int, zsize: int) -> None:
    """
    ported from RepairZone
    Repair a zone by rebuilding damaged tiles.

    Ported from RepairZone() in s_sim.c.

    Args:
        ZCent: Center tile value for the zone
        zsize: Size of the zone
        :param context:
    """
    cnt = 0
    zsize -= 1
    for y in range(-1, zsize):
        for x in range(-1, zsize):
            xx = context.s_map_x + x
            yy = context.s_map_y + y
            cnt += 1
            if TestBounds(xx, yy):
                th_ch = context.map_data[xx][yy]
                if th_ch & context.ZONEBIT:
                    continue
                if th_ch & context.ANIMBIT:
                    continue
                th_ch = th_ch & context.LOMASK
                if (th_ch < context.RUBBLE) or (th_ch >= context.ROADBASE):
                    context.map_data[xx][yy] = (
                            z_cent - 3 - zsize + cnt + context.CONDBIT + context.BURNBIT
                    )


def do_sp_zone(context: AppContext, pwr_on: int) -> None:
    """
    ported from DoSPZone
    Handle special zones (power plants, fire stations, etc.).

    Ported from DoSPZone() in s_sim.c.

    Args:
        PwrOn: Whether zone is powered
        :param context:
    """
    if context.cchr9 == context.POWERPLANT:
        context.coal_pop += 1
        if (context.city_time & 7) == 0:
            repair_zone(context, context.POWERPLANT, 4)  # post
        PushPowerStack(context)
        coal_smoke(context, context.s_map_x, context.s_map_y)
        return

    if context.cchr9 == context.NUCLEAR:
        if (not context.no_disasters) and (
                rand(context, context.MltdwnTab[context.game_level]) == 0
        ):
            do_meltdown(context, context.s_map_x, context.s_map_y)
            return
        context.nuclear_pop += 1
        if (context.city_time & 7) == 0:
            repair_zone(context, context.NUCLEAR, 4)  # post
        PushPowerStack(context)
        return

    if context.cchr9 == context.FIRESTATION:
        context.fire_st_pop += 1
        if (context.city_time & 7) == 0:
            repair_zone(context, context.FIRESTATION, 3)  # post

        if pwr_on:
            z = context.fire_effect  # if powered get effect
        else:
            z = context.fire_effect >> 1  # from the funding ratio

        if not find_p_road():
            z = z >> 1  # post FD's need roads

        context.fire_st_map[context.s_map_x >> 3][context.s_map_y >> 3] += z
        return

    if context.cchr9 == context.POLICESTATION:
        context.police_pop += 1
        if (context.city_time & 7) == 0:
            repair_zone(context, context.POLICESTATION, 3)  # post

        if pwr_on:
            z = context.police_effect
        else:
            z = context.police_effect >> 1

        if not find_p_road():
            z = z >> 1  # post PD's need roads

        context.police_map[context.s_map_x >> 3][context.s_map_y >> 3] += z
        return

    if context.cchr9 == context.STADIUM:
        context.stadium_pop += 1
        if (context.city_time & 15) == 0:
            repair_zone(context, context.STADIUM, 4)
        if pwr_on:
            if (
                (context.city_time + context.s_map_x + context.s_map_y) & 31
            ) == 0:  # post release
                draw_stadium(context, context.FULLSTADIUM)
                context.map_data[context.s_map_x + 1][context.s_map_y] = (
                    context.FOOTBALLGAME1 + context.ANIMBIT
                )
                context.map_data[context.s_map_x + 1][context.s_map_y + 1] = (
                    context.FOOTBALLGAME2 + context.ANIMBIT
                )
        return

    if context.cchr9 == context.FULLSTADIUM:
        context.stadium_pop += 1
        if ((context.city_time + context.s_map_x + context.s_map_y) & 7) == 0:  # post release
            draw_stadium(context, context.STADIUM)
        return

    if context.cchr9 == context.AIRPORT:
        context.airport_pop += 1
        if (context.city_time & 7) == 0:
            repair_zone(context, context.AIRPORT, 6)

        if pwr_on:  # post
            if (
                context.map_data[context.s_map_x + 1][context.s_map_y - 1] & context.LOMASK
            ) == context.RADAR:
                context.map_data[context.s_map_x + 1][context.s_map_y - 1] = (
                    context.RADAR + context.ANIMBIT + context.CONDBIT + context.BURNBIT
                )
        else:
            context.map_data[context.s_map_x + 1][context.s_map_y - 1] = (
                context.RADAR + context.CONDBIT + context.BURNBIT
            )

        if pwr_on:
            do_airport(context)
        return

    if context.cchr9 == context.PORT:
        context.port_pop += 1
        if (context.city_time & 15) == 0:
            repair_zone(context, context.PORT, 4)
        if pwr_on and (GetSprite(context, context.SHI) is None):
            GenerateShip(context)
        return


def draw_stadium(context: AppContext, z: int) -> None:
    """
    ported from DrawStadium
    Draw stadium tiles.

    Ported from DrawStadium() in s_sim.c.

    Args:
        z: Base tile value
        :param context:
    """
    z = z - 5
    for y in range(context.s_map_y - 1, context.s_map_y + 3):
        for x in range(context.s_map_x - 1, context.s_map_x + 3):
            context.map_data[x][y] = z | context.BNCNBIT
    context.map_data[context.s_map_x][context.s_map_y] |= context.ZONEBIT | context.PWRBIT


def do_airport(context: AppContext) -> None:
    """
    ported from DoAirport
    Handle airport operations.

    Ported from DoAirport() in s_sim.c.
    :param context:
    """
    if rand(context, 5) == 0:
        GeneratePlane(context, context.s_map_x, context.s_map_y)
        return
    if rand(context, 12) == 0:
        GenerateCopter(context.s_map_x, context.s_map_y)


def coal_smoke(context: AppContext, mx: int, my: int) -> None:
    """
    ported from CoalSmoke
    Generate coal smoke from power plants.

    Ported from CoalSmoke() in s_sim.c.

    Args:
        mx: X coordinate
        my: Y coordinate
        :param context:
    """
    sm_tb = [context.COALSMOKE1, context.COALSMOKE2, context.COALSMOKE3, context.COALSMOKE4]
    dx = [1, 2, 1, 2]
    dy = [-1, -1, 0, 0]

    for x in range(4):
        context.map_data[mx + dx[x]][my + dy[x]] = (
            sm_tb[x] | context.ANIMBIT | context.CONDBIT | context.PWRBIT | context.BURNBIT
        )


def do_meltdown(context: AppContext, sx: int, sy: int) -> None:
    """
    ported from DoMeltdown
    Handle nuclear meltdown disaster.

    Ported from DoMeltdown() in s_sim.c.

    Args:
        SX: X coordinate of meltdown
        SY: Y coordinate of meltdown
        :param context:
    """
    # global melt_x, melt_y

    context.melt_x = sx
    context.melt_y = sy

    MakeExplosion(sx - 1, sy - 1)
    MakeExplosion(sx - 1, sy + 2)
    MakeExplosion(sx + 2, sy - 1)
    MakeExplosion(sx + 2, sy + 2)

    for x in range(sx - 1, sx + 3):
        for y in range(sy - 1, sy + 3):
            context.map_data[x][y] = (
                    context.FIRE + (rand16() & 3) + context.ANIMBIT
            )

    for z in range(200):
        x = sx - 20 + rand(context, 40)
        y = sy - 15 + rand(context, 30)
        if (
            (x < 0)
            or (x >= WORLD_X)
            or (y < 0)
            or (y >= WORLD_Y)
        ):
            continue
        t = context.map_data[x][y]
        if t & context.ZONEBIT:
            continue
        if (t & context.BURNBIT) or (t == 0):
            context.map_data[x][y] = context.RADTILE

    clear_mes(context)
    send_mes_at(context, -43, sx, sy)


# ============================================================================
# Random Number Functions
# ============================================================================

RANDOM_RANGE = 0xFFFF


def rand(context: AppContext, range_val: int) -> int:
    """
    ported for Rand
    Generate random number in range.

    Ported from Rand() in s_sim.c.

    Args:
        range_val: Upper bound (exclusive)

    Returns:
        Random number between 0 and range_val-1
        :param context:
    """
    range_val += 1
    max_multiple = RANDOM_RANGE // range_val
    max_multiple *= range_val
    while True:
        rnum = rand16(context)
        if rnum < max_multiple:
            break
    return rnum % range_val


def rand16(context: AppContext) -> int:
    """
    ported Rand16
    Generate 16-bit random number.

    Ported from Rand16() in s_sim.c.

    Returns:
        Random number from sim_rand()
    """
    return sim_rand(context)


def rand16_signed(context: AppContext) -> int:
    """
    ported from Rand16Signed

    Generate signed 16-bit random number.

    Ported from Rand16Signed() in s_sim.c.

    Returns:
        Signed random number
        :param context:
    """
    i = sim_rand(context)
    if i > 32767:
        i = 32767 - i
    return i


def randomly_seed_rand() -> None:
    """
    ported from RandomlySeedRand
    Seed random number generator with current time.

    Ported from RandomlySeedRand() in s_sim.c.
    """
    # Use current time for seeding
    current_time = time.time()
    seed = int(current_time * 1000000)  # microseconds
    seed_rand(seed)


def seed_rand(seed: int) -> None:
    """
    ported from seed_rand
    Seed the random number generator.

    Ported from SeedRand() in s_sim.c.

    Args:
        seed: Seed value
    """
    sim_srand(seed)


# ============================================================================
# Placeholder Functions (to be implemented)
# ============================================================================


def city_evaluation() -> None:
    """ported from CityEvaluation City evaluation - placeholder for evaluation.py"""
    pass


def send_messages() -> None:
    """ported from SendMessages Send messages - placeholder for messages.py"""
    pass


def do_power_scan(context: AppContext) -> None:
    """ported from DoPowerScan Power grid scanning - implemented in power.py
    :param context:
    """
    DoPowerScan(context)


def do_disasters() -> None:
    """ported from DoDisasters Handle disasters - placeholder for disasters.py"""
    pass


def do_flood() -> None:
    """ported from DoFlood Handle flood tiles - placeholder"""
    pass


def do_zone() -> None:
    """ported from DoZone Process zone tiles - placeholder for zones.py"""
    pass


def find_p_road() -> bool:
    """ported FindPRoad Find if there's a powered road nearby - placeholder"""
    return True  # Assume roads are powered for now


# ============================================================================
# Set Common Inits (placeholder)
# ============================================================================


def set_common_inits(context: AppContext) -> None:
    """
    ported from SetCommonInits
    Set common initialization values.

    Ported from SetCommonInits() in s_sim.c.
    :param context:
    """
    # evaluation.EvalInit() - placeholder
    context.road_effect = 32
    context.police_effect = 1000
    context.fire_effect = 1000
    context.tax_flag = 0
    context.tax_fund = 0
