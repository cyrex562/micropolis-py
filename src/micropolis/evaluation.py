#!/usr/bin/env python3
"""
evaluation.py - City evaluation and scoring system for Micropolis Python port

This module implements the city evaluation system ported from s_eval.c,
responsible for calculating city scores, identifying problems, and determining
city classification based on population and infrastructure.
"""

from . import types, budget

# ============================================================================
# Evaluation State Variables
# ============================================================================

EvalValid: int = 0
CityYes: int = 0
CityNo: int = 0
ProblemTable: list[int] = [0] * types.PROBNUM
ProblemTaken: list[int] = [0] * types.PROBNUM
ProblemVotes: list[int] = [0] * types.PROBNUM  # votes for each problem
ProblemOrder: list[int] = [0] * 4  # sorted index to above
CityPop: int = 0
deltaCityPop: int = 0
CityAssValue: int = 0
CityClass: int = 0  # 0..5
CityScore: int = 0
deltaCityScore: int = 0
AverageCityScore: int = 0
TrafficAverage: int = 0

# ============================================================================
# Main Evaluation Function
# ============================================================================

def CityEvaluation() -> None:
    """
    Main city evaluation function.

    Ported from CityEvaluation() in s_eval.c.
    Called from SpecialInit and Simulate.
    """
    global EvalValid

    EvalValid = 0
    if types.TotalPop:
        GetAssValue()
        DoPopNum()
        DoProblems()
        GetScore()
        DoVotes()
        ChangeEval()
    else:
        EvalInit()
        ChangeEval()
    EvalValid = 1

# ============================================================================
# Initialization Functions
# ============================================================================

def EvalInit() -> None:
    """
    Initialize evaluation variables to default values.

    Ported from EvalInit() in s_eval.c.
    Called from CityEvaluation and SetCommonInits.
    """
    global CityYes, CityNo, CityPop, deltaCityPop, CityAssValue
    global CityClass, CityScore, deltaCityScore, EvalValid
    global ProblemVotes, ProblemOrder

    z = 0
    CityYes = z
    CityNo = z
    CityPop = z
    deltaCityPop = z
    CityAssValue = z
    CityClass = z
    CityScore = 500
    deltaCityScore = z
    EvalValid = 1

    for x in range(types.PROBNUM):
        ProblemVotes[x] = z
    for x in range(4):
        ProblemOrder[x] = z

# ============================================================================
# Assessment Value Calculation
# ============================================================================

def GetAssValue() -> None:
    """
    Calculate the assessed value of the city based on infrastructure.

    Ported from GetAssValue() in s_eval.c.
    Called from CityEvaluation.
    """
    global CityAssValue

    z = types.RoadTotal * 5
    z += types.RailTotal * 10
    z += types.PolicePop * 1000
    z += types.FireStPop * 1000
    z += types.HospPop * 400
    z += types.StadiumPop * 3000
    z += types.PortPop * 5000
    z += types.APortPop * 10000
    z += types.CoalPop * 3000
    z += types.NuclearPop * 6000
    CityAssValue = z * 1000

# ============================================================================
# Population and Classification
# ============================================================================

def DoPopNum() -> None:
    """
    Calculate city population and determine city class.

    Ported from DoPopNum() in s_eval.c.
    Called from CityEvaluation.
    """
    global CityPop, deltaCityPop, CityClass

    OldCityPop = CityPop
    CityPop = ((types.ResPop) + (types.ComPop * 8) + (types.IndPop * 8)) * 20

    if OldCityPop == -1:
        OldCityPop = CityPop

    deltaCityPop = CityPop - OldCityPop

    CityClass = 0  # village
    if CityPop > 2000:
        CityClass += 1  # town
    if CityPop > 10000:
        CityClass += 1  # city
    if CityPop > 50000:
        CityClass += 1  # capital
    if CityPop > 100000:
        CityClass += 1  # metropolis
    if CityPop > 500000:
        CityClass += 1  # megalopolis

# ============================================================================
# Problem Analysis and Voting
# ============================================================================

def DoProblems() -> None:
    """
    Analyze city problems and determine which ones are most significant.

    Ported from DoProblems() in s_eval.c.
    Called from CityEvaluation.
    """
    global ProblemTable, ProblemTaken, ProblemOrder

    # Initialize problem table
    for z in range(types.PROBNUM):
        ProblemTable[z] = 0

    # Calculate problem severity scores
    ProblemTable[0] = types.CrimeAverage        # Crime
    ProblemTable[1] = types.PolluteAverage      # Pollution
    ProblemTable[2] = int(types.LVAverage * 0.7)  # Housing
    ProblemTable[3] = types.CityTax * 10        # Taxes
    ProblemTable[4] = AverageTrf()              # Traffic
    ProblemTable[5] = GetUnemployment()         # Unemployment
    ProblemTable[6] = GetFire()                 # Fire

    # Vote on problems
    VoteProblems()

    # Initialize problem taken array
    for z in range(types.PROBNUM):
        ProblemTaken[z] = 0

    # Find top 4 problems
    for z in range(4):
        Max = 0
        ThisProb = -1
        for x in range(7):  # Check first 7 problems
            if (ProblemVotes[x] > Max) and (not ProblemTaken[x]):
                ThisProb = x
                Max = ProblemVotes[x]

        if Max and ThisProb >= 0:
            ProblemTaken[ThisProb] = 1
            ProblemOrder[z] = ThisProb
        else:
            ProblemOrder[z] = 7
            ProblemTable[7] = 0

def VoteProblems() -> None:
    """
    Simulate voting on city problems based on their severity.

    Ported from VoteProblems() in s_eval.c.
    Called from DoProblems.
    """
    global ProblemVotes

    # Initialize votes
    for z in range(types.PROBNUM):
        ProblemVotes[z] = 0

    x = 0
    z = 0
    count = 0

    # Simulate 100 votes with diminishing returns
    while (z < 100) and (count < 600):
        if types.Rand(300) < ProblemTable[x]:
            ProblemVotes[x] += 1
            z += 1
        x += 1
        if x > types.PROBNUM - 1:
            x = 0
        count += 1

def AverageTrf() -> int:
    """
    Calculate average traffic density.

    Ported from AverageTrf() in s_eval.c.
    Called from DoProblems.

    Returns:
        Average traffic value (0-255 range)
    """
    global TrafficAverage

    TrfTotal = 0
    count = 1

    # Sum traffic density over land value areas
    for x in range(types.HWLDX):
        for y in range(types.HWLDY):
            if types.LandValueMem[x][y]:
                TrfTotal += types.TrfDensity[x][y]
                count += 1

    TrafficAverage = int((TrfTotal / count) * 2.4)
    return TrafficAverage

def GetUnemployment() -> int:
    """
    Calculate unemployment rate.

    Ported from GetUnemployment() in s_eval.c.
    Called from DoProblems.

    Returns:
        Unemployment rate (0-255 range)
    """
    b = (types.ComPop + types.IndPop) << 3
    if b:
        r = types.ResPop / b
    else:
        return 0

    b = int((r - 1) * 255)
    if b > 255:
        b = 255
    if b < 0:
        b = 0
    return b

def GetFire() -> int:
    """
    Calculate fire danger level.

    Ported from GetFire() in s_eval.c.
    Called from DoProblems and GetScore.

    Returns:
        Fire danger level (0-255 range)
    """
    z = types.FirePop * 5
    if z > 255:
        return 255
    else:
        return z

# ============================================================================
# Score Calculation
# ============================================================================

def GetScore() -> None:
    """
    Calculate the overall city score based on various factors.

    Ported from GetScore() in s_eval.c.
    Called from CityEvaluation.
    """
    global CityScore, deltaCityScore

    OldCityScore = CityScore
    x = 0

    # Sum all 7 problems
    for z in range(7):
        x += ProblemTable[z]

    x = x // 3  # 7 + 2 average
    if x > 256:
        x = 256

    z = (256 - x) * 4
    if z > 1000:
        z = 1000
    if z < 0:
        z = 0

    # Apply capacity penalties
    if types.ResCap:
        z = int(z * 0.85)
    if types.ComCap:
        z = int(z * 0.85)
    if types.IndCap:
        z = int(z * 0.85)

    # Apply infrastructure effects
    if types.RoadEffect < 32:
        z = z - (32 - types.RoadEffect)
    if types.PoliceEffect < 1000:
        z = int(z * (0.9 + (types.PoliceEffect / 10000.1)))
    if types.FireEffect < 1000:
        z = int(z * (0.9 + (types.FireEffect / 10000.1)))

    # Apply demand penalties
    if types.RValve < -1000:
        z = int(z * 0.85)
    if types.CValve < -1000:
        z = int(z * 0.85)
    if types.IValve < -1000:
        z = int(z * 0.85)

    # Apply population growth modifier
    SM = 1.0
    if (CityPop == 0) or (deltaCityPop == 0):
        SM = 1.0
    elif deltaCityPop == CityPop:
        SM = 1.0
    elif deltaCityPop > 0:
        SM = (deltaCityPop / CityPop) + 1.0
    elif deltaCityPop < 0:
        SM = 0.95 + (deltaCityPop / (CityPop - deltaCityPop))

    z = int(z * SM)

    # Subtract fire and tax penalties
    z = z - GetFire()
    z = z - types.CityTax

    # Apply power ratio modifier
    TM = types.unPwrdZCnt + types.PwrdZCnt  # total zones
    if TM:
        SM = types.PwrdZCnt / TM  # powered ratio
    else:
        SM = 1.0
    z = int(z * SM)

    # Clamp final score
    if z > 1000:
        z = 1000
    if z < 0:
        z = 0

    # Average with previous score
    CityScore = (CityScore + z) // 2

    deltaCityScore = CityScore - OldCityScore

# ============================================================================
# Voting and UI Updates
# ============================================================================

def DoVotes() -> None:
    """
    Simulate citizen voting based on city score.

    Ported from DoVotes() in s_eval.c.
    Called from CityEvaluation.
    """
    global CityYes, CityNo

    CityYes = 0
    CityNo = 0

    # Simulate 100 votes
    for z in range(100):
        if types.Rand(1000) < CityScore:
            CityYes += 1
        else:
            CityNo += 1

def ChangeEval() -> None:
    """
    Update evaluation display (placeholder for UI integration).

    Ported from ChangeEval() in s_eval.c.
    Called from CityEvaluation.
    """
    # This would update the UI in the original TCL/Tk version
    # For now, it's a placeholder
    pass


def UpdateBudget() -> None:
    """
    Update budget display (placeholder for UI integration).

    Ported from UpdateBudget() in w_budget.c.
    Called when budget settings change.
    """
    # This would update the UI in the original TCL/Tk version
    # For now, it's a placeholder until budget.py is implemented
    pass


def DoBudget() -> None:
    """
    Run the standard annual budget sequence.
    """
    budget.do_budget()
    types.MustUpdateFunds = 1


def DoBudgetFromMenu() -> None:
    """
    Trigger the budget workflow via the modern budget module.
    """
    budget.do_budget_from_menu()
    types.MustUpdateFunds = 1
