"""
simulation.py - Core simulation step logic for Micropolis Python port

This module contains the main simulation loop and supporting functions
ported from s_sim.c, implementing the city simulation mechanics.
"""

from typing import Optional
import time

from . import types, macros, power, zones


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

    if types.SimSpeed == 0:
        return

    Spdcycle = (Spdcycle + 1) % 1024

    if types.SimSpeed == 1 and (Spdcycle % 5) != 0:
        return

    if types.SimSpeed == 2 and (Spdcycle % 3) != 0:
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

    x = types.SimSpeed
    if x > 3:
        x = 3

    if mod16 == 0:
        Scycle = (Scycle + 1) % 1024  # This is cosmic
        if DoInitialEval:
            DoInitialEval = 0
            CityEvaluation()
        types.CityTime += 1
        AvCityTax += types.CityTax  # post
        if (Scycle & 1) == 0:
            SetValves()
        ClearCensus()

    elif mod16 == 1:
        MapScan(0, 1 * types.WORLD_X // 8)
    elif mod16 == 2:
        MapScan(1 * types.WORLD_X // 8, 2 * types.WORLD_X // 8)
    elif mod16 == 3:
        MapScan(2 * types.WORLD_X // 8, 3 * types.WORLD_X // 8)
    elif mod16 == 4:
        MapScan(3 * types.WORLD_X // 8, 4 * types.WORLD_X // 8)
    elif mod16 == 5:
        MapScan(4 * types.WORLD_X // 8, 5 * types.WORLD_X // 8)
    elif mod16 == 6:
        MapScan(5 * types.WORLD_X // 8, 6 * types.WORLD_X // 8)
    elif mod16 == 7:
        MapScan(6 * types.WORLD_X // 8, 7 * types.WORLD_X // 8)
    elif mod16 == 8:
        MapScan(7 * types.WORLD_X // 8, types.WORLD_X)

    elif mod16 == 9:
        if (types.CityTime % types.CENSUSRATE) == 0:
            TakeCensus()
        if (types.CityTime % (types.CENSUSRATE * 12)) == 0:
            Take2Census()

        if (types.CityTime % types.TAXFREQ) == 0:
            CollectTax()
            CityEvaluation()

    elif mod16 == 10:
        if (Scycle % 5) == 0:
            DecROGMem()
        DecTrafficMem()
        types.NewMapFlags[types.TDMAP] = 1
        types.NewMapFlags[types.RDMAP] = 1
        types.NewMapFlags[types.ALMAP] = 1
        types.NewMapFlags[types.REMAP] = 1
        types.NewMapFlags[types.COMAP] = 1
        types.NewMapFlags[types.INMAP] = 1
        types.NewMapFlags[types.DYMAP] = 1
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

    if types.InitSimLoad == 2:  # if new city
        InitSimMemory()

    if types.InitSimLoad == 1:  # if city just loaded
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
    types.NewMap = 1
    # doAllGraphs() - placeholder
    types.NewGraph = 1
    types.TotalPop = 1
    DoInitialEval = 1


# ============================================================================
# Memory Management Functions
# ============================================================================

def DecTrafficMem() -> None:
    """
    Gradually reduces traffic density values.

    Ported from DecTrafficMem() in s_sim.c.
    """
    for x in range(types.HWLDX):
        for y in range(types.HWLDY):
            z = types.TrfDensity[x][y]
            if z > 0:
                if z > 24:
                    if z > 200:
                        types.TrfDensity[x][y] = z - 34
                    else:
                        types.TrfDensity[x][y] = z - 24
                else:
                    types.TrfDensity[x][y] = 0


def DecROGMem() -> None:
    """
    Gradually reduces RateOGMem values.

    Ported from DecROGMem() in s_sim.c.
    """
    for x in range(types.SmX):
        for y in range(types.SmY):
            z = types.RateOGMem[x][y]
            if z == 0:
                continue
            if z > 0:
                types.RateOGMem[x][y] -= 1
                if z > 200:
                    types.RateOGMem[x][y] = 200  # prevent overflow
                continue
            if z < 0:
                types.RateOGMem[x][y] += 1
                if z < -200:
                    types.RateOGMem[x][y] = -200


def InitSimMemory() -> None:
    """
    Initialize simulation memory for a new city.

    Ported from InitSimMemory() in s_sim.c.
    """
    global CrimeRamp, PolluteRamp, EMarket, DisasterEvent, ScoreType

    z = 0
    # SetCommonInits() - placeholder
    for x in range(240):
        types.ResHis[x] = z
        types.ComHis[x] = z
        types.IndHis[x] = z
        types.MoneyHis[x] = 128
        types.CrimeHis[x] = z
        types.PollutionHis[x] = z

    CrimeRamp = z
    PolluteRamp = z
    types.TotalPop = z
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
        types.PowerMap[z] = ~0  # set power Map
    power.DoPowerScan()
    NewPower = 1  # post rel

    types.InitSimLoad = 0


def SimLoadInit() -> None:
    """
    Initialize simulation when loading a saved city.

    Ported from SimLoadInit() in s_sim.c.
    """
    # Disaster wait times for different scenarios
    DisTab = [0, 2, 10, 5, 20, 3, 5, 5, 2 * 48]
    ScoreWaitTab = [0, 30 * 48, 5 * 48, 5 * 48, 10 * 48,
                   5 * 48, 10 * 48, 5 * 48, 10 * 48]

    global EMarket, RValve, CValve, IValve, CrimeRamp, PolluteRamp

    z = 0
    EMarket = float(types.MiscHis[1])
    types.ResPop = types.MiscHis[2]
    types.ComPop = types.MiscHis[3]
    types.IndPop = types.MiscHis[4]
    RValve = types.MiscHis[5]
    CValve = types.MiscHis[6]
    IValve = types.MiscHis[7]
    CrimeRamp = types.MiscHis[10]
    PolluteRamp = types.MiscHis[11]
    types.LVAverage = types.MiscHis[12]
    types.CrimeAverage = types.MiscHis[13]
    types.PolluteAverage = types.MiscHis[14]
    types.GameLevel = types.MiscHis[15]

    if types.CityTime < 0:
        types.CityTime = 0
    if EMarket == 0:
        EMarket = 4.0
    if (types.GameLevel > 2) or (types.GameLevel < 0):
        types.GameLevel = 0
    # SetGameLevel(GameLevel) - placeholder

    # SetCommonInits() - placeholder

    types.CityClass = types.MiscHis[16]
    types.CityScore = types.MiscHis[17]

    if (types.CityClass > 5) or (types.CityClass < 0):
        types.CityClass = 0
    if (types.CityScore > 999) or (types.CityScore < 1):
        types.CityScore = 500

    ResCap = 0
    ComCap = 0
    IndCap = 0

    AvCityTax = (types.CityTime % 48) * 7  # post

    for z in range(types.PWRMAPSIZE):
        types.PowerMap[z] = 0xFFFF  # set power Map
    DoNilPower()

    if types.ScenarioID > 8:
        types.ScenarioID = 0

    if types.ScenarioID:
        DisasterEvent = types.ScenarioID
        DisasterWait = DisTab[types.ScenarioID]
        ScoreType = types.ScenarioID
        ScoreWait = ScoreWaitTab[types.ScenarioID]
    else:
        DisasterEvent = 0
        ScoreType = 0

    types.RoadEffect = 32
    types.PoliceEffect = 1000  # post
    types.FireEffect = 1000
    types.InitSimLoad = 0


def DoNilPower() -> None:
    """
    Set power for all zones when loading a city.

    Ported from DoNilPower() in s_sim.c.
    """
    for x in range(types.WORLD_X):
        for y in range(types.WORLD_Y):
            z = types.Map[x][y]
            if z & types.ZONEBIT:
                types.SMapX = x
                types.SMapY = y
                types.CChr = z
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
        200, 150, 120, 100, 80, 50, 30, 0, -10, -40, -100,
        -150, -200, -250, -300, -350, -400, -450, -500, -550, -600
    ]

    global ValveFlag, RValve, CValve, IValve

    # Store current values in MiscHis
    types.MiscHis[1] = int(EMarket)
    types.MiscHis[2] = types.ResPop
    types.MiscHis[3] = types.ComPop
    types.MiscHis[4] = types.IndPop
    types.MiscHis[5] = RValve
    types.MiscHis[6] = CValve
    types.MiscHis[7] = IValve
    types.MiscHis[10] = CrimeRamp
    types.MiscHis[11] = PolluteRamp
    types.MiscHis[12] = types.LVAverage
    types.MiscHis[13] = types.CrimeAverage
    types.MiscHis[14] = types.PolluteAverage
    types.MiscHis[15] = types.GameLevel
    types.MiscHis[16] = types.CityClass
    types.MiscHis[17] = types.CityScore

    # Calculate normalized residential population
    NormResPop = types.ResPop / 8
    types.LastTotalPop = types.TotalPop
    types.TotalPop = NormResPop + types.ComPop + types.IndPop

    # Calculate employment rate
    if NormResPop:
        Employment = ((types.ComHis[1] + types.IndHis[1]) / NormResPop)
    else:
        Employment = 1

    # Calculate migration and births
    Migration = NormResPop * (Employment - 1)
    Births = NormResPop * 0.02  # Birth Rate
    PjResPop = NormResPop + Migration + Births  # Projected Res.Pop

    # Calculate labor base
    if (types.ComHis[1] + types.IndHis[1]):
        LaborBase = (types.ResHis[1] / (types.ComHis[1] + types.IndHis[1]))
    else:
        LaborBase = 1
    if LaborBase > 1.3:
        LaborBase = 1.3
    if LaborBase < 0:
        LaborBase = 0  # LB > 1 - .1

    # Calculate temporary values for market calculations
    for z in range(2):
        temp = types.ResHis[z] + types.ComHis[z] + types.IndHis[z]
    IntMarket = (NormResPop + types.ComPop + types.IndPop) / 3.7

    # Calculate projected commercial population
    PjComPop = IntMarket * LaborBase

    # Adjust for game level
    z = types.GameLevel
    temp = 1
    if z == 0:
        temp = 1.2
    elif z == 1:
        temp = 1.1
    elif z == 2:
        temp = 0.98

    PjIndPop = types.IndPop * LaborBase * temp
    if PjIndPop < 5:
        PjIndPop = 5

    # Calculate ratios
    if NormResPop:
        Rratio = (PjResPop / NormResPop)  # projected -vs- actual
    else:
        Rratio = 1.3
    if types.ComPop:
        Cratio = (PjComPop / types.ComPop)
    else:
        Cratio = PjComPop
    if types.IndPop:
        Iratio = (PjIndPop / types.IndPop)
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
    z = types.CityTax + types.GameLevel
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
    types.FirePop = z
    types.RoadTotal = z
    types.RailTotal = z
    types.ResPop = z
    types.ComPop = z
    types.IndPop = z
    types.ResZPop = z
    types.ComZPop = z
    types.IndZPop = z
    types.HospPop = z
    types.ChurchPop = z
    types.PolicePop = z
    types.FireStPop = z
    types.StadiumPop = z
    types.CoalPop = z
    types.NuclearPop = z
    types.PortPop = z
    types.APortPop = z
    types.PowerStackNum = z  # Reset before Mapscan

    for x in range(types.SmX):
        for y in range(types.SmY):
            types.FireStMap[x][y] = z
            types.PoliceMap[x][y] = z


def TakeCensus() -> None:
    """
    Record population data in history graphs.

    Ported from TakeCensus() in s_sim.c.
    """
    global CrimeRamp, PolluteRamp

    # Scroll data
    for x in range(118, -1, -1):
        types.ResHis[x + 1] = types.ResHis[x]
        types.ComHis[x + 1] = types.ComHis[x]
        types.IndHis[x + 1] = types.IndHis[x]
        types.CrimeHis[x + 1] = types.CrimeHis[x]
        types.PollutionHis[x + 1] = types.PollutionHis[x]
        types.MoneyHis[x + 1] = types.MoneyHis[x]

    # Update max values
    ResHisMax = 0
    ComHisMax = 0
    IndHisMax = 0
    for x in range(119):
        if types.ResHis[x] > ResHisMax:
            ResHisMax = types.ResHis[x]
        if types.ComHis[x] > ComHisMax:
            ComHisMax = types.ComHis[x]
        if types.IndHis[x] > IndHisMax:
            IndHisMax = types.IndHis[x]

    types.Graph10Max = ResHisMax
    if ComHisMax > types.Graph10Max:
        types.Graph10Max = ComHisMax
    if IndHisMax > types.Graph10Max:
        types.Graph10Max = IndHisMax

    # Set current values
    types.ResHis[0] = types.ResPop // 8
    types.ComHis[0] = types.ComPop
    types.IndHis[0] = types.IndPop

    # Update crime and pollution ramps
    CrimeRamp += (types.CrimeAverage - CrimeRamp) // 4
    types.CrimeHis[0] = CrimeRamp

    PolluteRamp += (types.PolluteAverage - PolluteRamp) // 4
    types.PollutionHis[0] = PolluteRamp

    # Scale cash flow to 0..255
    x = (CashFlow // 20) + 128
    if x < 0:
        x = 0
    if x > 255:
        x = 255

    types.MoneyHis[0] = x
    if types.CrimeHis[0] > 255:
        types.CrimeHis[0] = 255
    if types.PollutionHis[0] > 255:
        types.PollutionHis[0] = 255

    # ChangeCensus() - placeholder for 10 year graph view

    # Check hospital and church needs
    if types.HospPop < (types.ResPop >> 8):
        types.NeedHosp = types.TRUE
    if types.HospPop > (types.ResPop >> 8):
        types.NeedHosp = -1
    if types.HospPop == (types.ResPop >> 8):
        types.NeedHosp = types.FALSE

    if types.ChurchPop < (types.ResPop >> 8):
        types.NeedChurch = types.TRUE
    if types.ChurchPop > (types.ResPop >> 8):
        types.NeedChurch = -1
    if types.ChurchPop == (types.ResPop >> 8):
        types.NeedChurch = types.FALSE


def Take2Census() -> None:
    """
    Record long-term population data.

    Ported from Take2Census() in s_sim.c.
    """
    # Scroll 120-year data
    for x in range(238, 119, -1):
        types.ResHis[x + 1] = types.ResHis[x]
        types.ComHis[x + 1] = types.ComHis[x]
        types.IndHis[x + 1] = types.IndHis[x]
        types.CrimeHis[x + 1] = types.CrimeHis[x]
        types.PollutionHis[x + 1] = types.PollutionHis[x]
        types.MoneyHis[x + 1] = types.MoneyHis[x]

    # Update max values
    Res2HisMax = 0
    Com2HisMax = 0
    Ind2HisMax = 0
    for x in range(120, 239):
        if types.ResHis[x] > Res2HisMax:
            Res2HisMax = types.ResHis[x]
        if types.ComHis[x] > Com2HisMax:
            Com2HisMax = types.ComHis[x]
        if types.IndHis[x] > Ind2HisMax:
            Ind2HisMax = types.IndHis[x]

    types.Graph120Max = Res2HisMax
    if Com2HisMax > types.Graph120Max:
        types.Graph120Max = Com2HisMax
    if Ind2HisMax > types.Graph120Max:
        types.Graph120Max = Ind2HisMax

    # Set 120-year values
    types.ResHis[120] = types.ResPop // 8
    types.ComHis[120] = types.ComPop
    types.IndHis[120] = types.IndPop
    types.CrimeHis[120] = types.CrimeHis[0]
    types.PollutionHis[120] = types.PollutionHis[0]
    types.MoneyHis[120] = types.MoneyHis[0]
    # ChangeCensus() - placeholder for 120 year graph view


# ============================================================================
# Tax and Financial Functions
# ============================================================================

def CollectTax() -> None:
    """
    Calculate and collect taxes.

    Ported from CollectTax() in s_sim.c.
    """
    global CashFlow

    # Tax level factors
    RLevels = [0.7, 0.9, 1.2]
    FLevels = [1.4, 1.2, 0.8]

def CollectTax() -> None:
    """
    Calculate and collect taxes.

    Ported from CollectTax() in s_sim.c.
    """
    global CashFlow, AvCityTax

    # Tax level factors
    RLevels = [0.7, 0.9, 1.2]
    FLevels = [1.4, 1.2, 0.8]

    CashFlow = 0
    if not types.TaxFlag:  # if the Tax Port is clear
        # XXX: do something with z
        z = AvCityTax // 48  # post
        AvCityTax = 0

        types.PoliceFund = types.PolicePop * 100
        types.FireFund = types.FireStPop * 100
        types.RoadFund = (types.RoadTotal + (types.RailTotal * 2)) * RLevels[types.GameLevel]
        types.TaxFund = (((types.TotalPop * types.LVAverage) // 120) *
                        types.CityTax * FLevels[types.GameLevel])

        if types.TotalPop:  # if there are people to tax
            CashFlow = int(types.TaxFund - (types.PoliceFund + types.FireFund + types.RoadFund))

            # DoBudget() - placeholder
        else:
            types.RoadEffect = 32
            types.PoliceEffect = 1000
            types.FireEffect = 1000


def UpdateFundEffects() -> None:
    """
    Update service effects based on funding levels.

    Ported from UpdateFundEffects() in s_sim.c.
    """
    if types.RoadFund:
        types.RoadEffect = int(((types.RoadSpend / types.RoadFund) * 32.0))
    else:
        types.RoadEffect = 32

    if types.PoliceFund:
        types.PoliceEffect = int(((types.PoliceSpend / types.PoliceFund) * 1000.0))
    else:
        types.PoliceEffect = 1000

    if types.FireFund:
        types.FireEffect = int(((types.FireSpend / types.FireFund) * 1000.0))
    else:
        types.FireEffect = 1000

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
        for y in range(types.WORLD_Y):
            types.CChr = types.Map[x][y]
            if types.CChr:
                types.CChr9 = types.CChr & types.LOMASK  # Mask off status bits
                if types.CChr9 >= types.FLOOD:
                    types.SMapX = x
                    types.SMapY = y
                    if types.CChr9 < types.ROADBASE:
                        if types.CChr9 >= types.FIREBASE:
                            types.FirePop += 1
                            if (types.Rand16() & 3) == 0:  # 1 in 4 times
                                DoFire()
                            continue
                        if types.CChr9 < types.RADTILE:
                            DoFlood()
                        else:
                            DoRadTile()
                        continue

                    if NewPower and (types.CChr & types.CONDBIT):
                        zones.SetZPower()

                    if (types.CChr9 >= types.ROADBASE) and (types.CChr9 < types.POWERBASE):
                        DoRoad()
                        continue

                    if types.CChr & types.ZONEBIT:  # process Zones
                        DoZone()
                        continue

                    if (types.CChr9 >= types.RAILBASE) and (types.CChr9 < types.RESBASE):
                        DoRail()
                        continue
                    if (types.CChr9 >= types.SOMETINYEXP) and (types.CChr9 <= types.LASTTINYEXP):
                        # clear AniRubble
                        types.Map[x][y] = types.RUBBLE + (types.Rand16() & 3) + types.BULLBIT


# ============================================================================
# Tile Processing Functions
# ============================================================================

def DoRail() -> None:
    """
    Process rail tiles.

    Ported from DoRail() in s_sim.c.
    """
    types.RailTotal += 1
    sprites.GenerateTrain(types.SMapX, types.SMapY)
    if types.RoadEffect < 30:  # Deteriorating Rail
        if (types.Rand16() & 511) == 0:
            if (types.CChr & types.CONDBIT) == 0:
                if types.RoadEffect < (types.Rand16() & 31):
                    if types.CChr9 < (types.RAILBASE + 2):
                        types.Map[types.SMapX][types.SMapY] = types.RIVER
                    else:
                        types.Map[types.SMapX][types.SMapY] = types.RUBBLE + (types.Rand16() & 3) + types.BULLBIT


def DoRadTile() -> None:
    """
    Process radioactive tiles.

    Ported from DoRadTile() in s_sim.c.
    """
    if (types.Rand16() & 4095) == 0:
        types.Map[types.SMapX][types.SMapY] = 0  # Radioactive decay


def DoRoad() -> None:
    """
    Process road tiles.

    Ported from DoRoad() in s_sim.c.
    """
    global types

    DenTab = [types.ROADBASE, types.LTRFBASE, types.HTRFBASE]

    types.RoadTotal += 1
    # GenerateBus(SMapX, SMapY) - placeholder

    if types.RoadEffect < 30:  # Deteriorating Roads
        if (types.Rand16() & 511) == 0:
            if (types.CChr & types.CONDBIT) == 0:
                if types.RoadEffect < (types.Rand16() & 31):
                    if ((types.CChr9 & 15) < 2) or ((types.CChr9 & 15) == 15):
                        types.Map[types.SMapX][types.SMapY] = types.RIVER
                    else:
                        types.Map[types.SMapX][types.SMapY] = types.RUBBLE + (types.Rand16() & 3) + types.BULLBIT
                    return

    if types.CChr & types.BURNBIT:  # If Bridge
        types.RoadTotal += 4
        if DoBridge():
            return

    if types.CChr9 < types.LTRFBASE:
        tden = 0
    else:
        if types.CChr9 < types.HTRFBASE:
            tden = 1
        else:
            types.RoadTotal += 1
            tden = 2

    # Set Traf Density
    Density = (types.TrfDensity[types.SMapX >> 1][types.SMapY >> 1]) >> 6
    if Density > 1:
        Density -= 1
    if tden != Density:  # tden 0..2
        z = ((types.CChr9 - types.ROADBASE) & 15) + DenTab[Density]
        z += types.CChr & (types.ALLBITS - types.ANIMBIT)
        if Density:
            z += types.ANIMBIT
        types.Map[types.SMapX][types.SMapY] = z


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
    HBRTAB = [types.HBRDG1 | types.BULLBIT, types.HBRDG3 | types.BULLBIT,
              types.HBRDG0 | types.BULLBIT, types.RIVER,
              types.BRWH | types.BULLBIT, types.RIVER,
              types.HBRDG2 | types.BULLBIT]
    HBRTAB2 = [types.RIVER, types.RIVER, types.HBRIDGE | types.BULLBIT,
               types.HBRIDGE | types.BULLBIT, types.HBRIDGE | types.BULLBIT,
               types.HBRIDGE | types.BULLBIT, types.HBRIDGE | types.BULLBIT]
    VDx = [0, 1, 0, 0, 0, 0, 1]
    VDy = [-2, -2, -1, 0, 1, 2, 2]
    VBRTAB = [types.VBRDG0 | types.BULLBIT, types.VBRDG1 | types.BULLBIT,
              types.RIVER, types.BRWV | types.BULLBIT,
              types.RIVER, types.VBRDG2 | types.BULLBIT,
              types.VBRDG3 | types.BULLBIT]
    VBRTAB2 = [types.VBRIDGE | types.BULLBIT, types.RIVER,
               types.VBRIDGE | types.BULLBIT, types.VBRIDGE | types.BULLBIT,
               types.VBRIDGE | types.BULLBIT, types.VBRIDGE | types.BULLBIT,
               types.RIVER]

    if types.CChr9 == types.BRWV:  # Vertical bridge close
        if ((types.Rand16() & 3) == 0) and (GetBoatDis() > 340):
            for z in range(7):  # Close
                x = types.SMapX + VDx[z]
                y = types.SMapY + VDy[z]
                if macros.TestBounds(x, y):
                    if (types.Map[x][y] & types.LOMASK) == (VBRTAB[z] & types.LOMASK):
                        types.Map[x][y] = VBRTAB2[z]
        return True

    if types.CChr9 == types.BRWH:  # Horizontal bridge close
        if ((types.Rand16() & 3) == 0) and (GetBoatDis() > 340):
            for z in range(7):  # Close
                x = types.SMapX + HDx[z]
                y = types.SMapY + HDy[z]
                if macros.TestBounds(x, y):
                    if (types.Map[x][y] & types.LOMASK) == (HBRTAB[z] & types.LOMASK):
                        types.Map[x][y] = HBRTAB2[z]
        return True

    if (GetBoatDis() < 300) or ((types.Rand16() & 7) == 0):
        if types.CChr9 & 1:  # Vertical open
            if types.SMapX < (types.WORLD_X - 1):
                if types.Map[types.SMapX + 1][types.SMapY] == types.CHANNEL:
                    for z in range(7):
                        x = types.SMapX + VDx[z]
                        y = types.SMapY + VDy[z]
                        if macros.TestBounds(x, y):
                            MPtem = types.Map[x][y]
                            if (MPtem == types.CHANNEL) or \
                               ((MPtem & 15) == (VBRTAB2[z] & 15)):
                                types.Map[x][y] = VBRTAB[z]
                    return True
            return False
        else:  # Horizontal open
            if types.SMapY > 0:
                if types.Map[types.SMapX][types.SMapY - 1] == types.CHANNEL:
                    for z in range(7):
                        x = types.SMapX + HDx[z]
                        y = types.SMapY + HDy[z]
                        if macros.TestBounds(x, y):
                            MPtem = types.Map[x][y]
                            if ((MPtem & 15) == (HBRTAB2[z] & 15)) or \
                               (MPtem == types.CHANNEL):
                                types.Map[x][y] = HBRTAB[z]
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
    mx = (types.SMapX << 4) + 8
    my = (types.SMapY << 4) + 8

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
        if (types.Rand16() & 7) == 0:
            Xtem = types.SMapX + DX[z]
            Ytem = types.SMapY + DY[z]
            if macros.TestBounds(Xtem, Ytem):
                c = types.Map[Xtem][Ytem]
                if c & types.BURNBIT:
                    if c & types.ZONEBIT:
                        FireZone(Xtem, Ytem, c)
                        if (c & types.LOMASK) > types.IZB:  # Explode
                            sprites.MakeExplosionAt((Xtem << 4) + 8, (Ytem << 4) + 8)
                    types.Map[Xtem][Ytem] = types.FIRE + (types.Rand16() & 3) + types.ANIMBIT

    z = types.FireRate[types.SMapX >> 3][types.SMapY >> 3]
    Rate = 10
    if z:
        Rate = 3
        if z > 20:
            Rate = 2
        if z > 100:
            Rate = 1
    if types.Rand(Rate) == 0:
        types.Map[types.SMapX][types.SMapY] = types.RUBBLE + (types.Rand16() & 3) + types.BULLBIT


def FireZone(Xloc: int, Yloc: int, ch: int) -> None:
    """
    Handle fire damage to zones.

    Ported from FireZone() in s_sim.c.

    Args:
        Xloc: X coordinate of fire
        Yloc: Y coordinate of fire
        ch: Tile value
    """
    types.RateOGMem[Xloc >> 3][Yloc >> 3] -= 20

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
            if ((Xtem < 0) or (Xtem > (types.WORLD_X - 1)) or
                (Ytem < 0) or (Ytem > (types.WORLD_Y - 1))):
                continue
            if (types.Map[Xtem][Ytem] & types.LOMASK) >= types.ROADBASE:  # post release
                types.Map[Xtem][Ytem] |= types.BULLBIT


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
            xx = types.SMapX + x
            yy = types.SMapY + y
            cnt += 1
            if macros.TestBounds(xx, yy):
                ThCh = types.Map[xx][yy]
                if ThCh & types.ZONEBIT:
                    continue
                if ThCh & types.ANIMBIT:
                    continue
                ThCh = ThCh & types.LOMASK
                if (ThCh < types.RUBBLE) or (ThCh >= types.ROADBASE):
                    types.Map[xx][yy] = ZCent - 3 - zsize + cnt + types.CONDBIT + types.BURNBIT


def DoSPZone(PwrOn: int) -> None:
    """
    Handle special zones (power plants, fire stations, etc.).

    Ported from DoSPZone() in s_sim.c.

    Args:
        PwrOn: Whether zone is powered
    """
    if types.CChr9 == types.POWERPLANT:
        types.CoalPop += 1
        if (types.CityTime & 7) == 0:
            RepairZone(types.POWERPLANT, 4)  # post
        power.PushPowerStack()
        CoalSmoke(types.SMapX, types.SMapY)
        return

    if types.CChr9 == types.NUCLEAR:
        if (not types.NoDisasters) and (types.Rand(types.MltdwnTab[types.GameLevel]) == 0):
            DoMeltdown(types.SMapX, types.SMapY)
            return
        types.NuclearPop += 1
        if (types.CityTime & 7) == 0:
            RepairZone(types.NUCLEAR, 4)  # post
        power.PushPowerStack()
        return

    if types.CChr9 == types.FIRESTATION:
        types.FireStPop += 1
        if (types.CityTime & 7) == 0:
            RepairZone(types.FIRESTATION, 3)  # post

        if PwrOn:
            z = types.FireEffect  # if powered get effect
        else:
            z = types.FireEffect >> 1  # from the funding ratio

        if not FindPRoad():
            z = z >> 1  # post FD's need roads

        types.FireStMap[types.SMapX >> 3][types.SMapY >> 3] += z
        return

    if types.CChr9 == types.POLICESTATION:
        types.PolicePop += 1
        if (types.CityTime & 7) == 0:
            RepairZone(types.POLICESTATION, 3)  # post

        if PwrOn:
            z = types.PoliceEffect
        else:
            z = types.PoliceEffect >> 1

        if not FindPRoad():
            z = z >> 1  # post PD's need roads

        types.PoliceMap[types.SMapX >> 3][types.SMapY >> 3] += z
        return

    if types.CChr9 == types.STADIUM:
        types.StadiumPop += 1
        if (types.CityTime & 15) == 0:
            RepairZone(types.STADIUM, 4)
        if PwrOn:
            if ((types.CityTime + types.SMapX + types.SMapY) & 31) == 0:  # post release
                DrawStadium(types.FULLSTADIUM)
                types.Map[types.SMapX + 1][types.SMapY] = types.FOOTBALLGAME1 + types.ANIMBIT
                types.Map[types.SMapX + 1][types.SMapY + 1] = types.FOOTBALLGAME2 + types.ANIMBIT
        return

    if types.CChr9 == types.FULLSTADIUM:
        types.StadiumPop += 1
        if ((types.CityTime + types.SMapX + types.SMapY) & 7) == 0:  # post release
            DrawStadium(types.STADIUM)
        return

    if types.CChr9 == types.AIRPORT:
        types.APortPop += 1
        if (types.CityTime & 7) == 0:
            RepairZone(types.AIRPORT, 6)

        if PwrOn:  # post
            if (types.Map[types.SMapX + 1][types.SMapY - 1] & types.LOMASK) == types.RADAR:
                types.Map[types.SMapX + 1][types.SMapY - 1] = types.RADAR + types.ANIMBIT + types.CONDBIT + types.BURNBIT
        else:
            types.Map[types.SMapX + 1][types.SMapY - 1] = types.RADAR + types.CONDBIT + types.BURNBIT

        if PwrOn:
            DoAirport()
        return

    if types.CChr9 == types.PORT:
        types.PortPop += 1
        if (types.CityTime & 15) == 0:
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
    for y in range(types.SMapY - 1, types.SMapY + 3):
        for x in range(types.SMapX - 1, types.SMapX + 3):
            types.Map[x][y] = (z) | types.BNCNBIT
    types.Map[types.SMapX][types.SMapY] |= types.ZONEBIT | types.PWRBIT


def DoAirport() -> None:
    """
    Handle airport operations.

    Ported from DoAirport() in s_sim.c.
    """
    if types.Rand(5) == 0:
        sprites.GeneratePlane(types.SMapX, types.SMapY)
        return
    if types.Rand(12) == 0:
        sprites.GenerateCopter(types.SMapX, types.SMapY)


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
        types.Map[mx + dx[x]][my + dy[x]] = \
            SmTb[x] | types.ANIMBIT | types.CONDBIT | types.PWRBIT | types.BURNBIT


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
            types.Map[x][y] = types.FIRE + (types.Rand16() & 3) + types.ANIMBIT

    for z in range(200):
        x = SX - 20 + types.Rand(40)
        y = SY - 15 + types.Rand(30)
        if ((x < 0) or (x >= types.WORLD_X) or
            (y < 0) or (y >= types.WORLD_Y)):
            continue
        t = types.Map[x][y]
        if t & types.ZONEBIT:
            continue
        if (t & types.BURNBIT) or (t == 0):
            types.Map[x][y] = types.RADTILE

    messages.ClearMes()
    messages.SendMesAt(-43, SX, SY)


# ============================================================================
# Random Number Functions
# ============================================================================

RANDOM_RANGE = 0xffff


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
        rnum = types.Rand16()
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
    return types.sim_rand()


def Rand16Signed() -> int:
    """
    Generate signed 16-bit random number.

    Ported from Rand16Signed() in s_sim.c.

    Returns:
        Signed random number
    """
    i = types.sim_rand()
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
    types.sim_srand(seed)


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
    types.RoadEffect = 32
    types.PoliceEffect = 1000
    types.FireEffect = 1000
    types.TaxFlag = 0
    types.TaxFund = 0