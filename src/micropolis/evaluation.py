#!/usr/bin/env python3
"""
evaluation.py - City evaluation and scoring system for Micropolis Python port

This module implements the city evaluation system ported from s_eval.c,
responsible for calculating city scores, identifying problems, and determining
city classification based on population and infrastructure.
"""

from src.micropolis.budget import (
    do_budget as budget_do_budget,
    do_budget_from_menu as budget_do_budget_from_menu,
)
from src.micropolis.constants import PROBNUM, HWLDX, HWLDY
from src.micropolis.context import AppContext
from src.micropolis.simulation import rand


# ============================================================================
# Evaluation State Variables
# ============================================================================

# eval_valid: int = 0
# city_yes: int = 0
# city_no: int = 0
# problem_table: list[int] = [0] * types.PROBNUM
# problem_taken: list[int] = [0] * types.PROBNUM
# problem_votes: list[int] = [0] * types.PROBNUM  # votes for each problem
# problem_order: list[int] = [0] * 4  # sorted index to above
# city_pop: int = 0
# delta_city_pop: int = 0
# city_ass_value: int = 0
# city_class: int = 0  # 0..5
# city_score: int = 0
# delta_city_score: int = 0
# average_city_score: int = 0
# traffic_average: int = 0

# ============================================================================
# Main Evaluation Function
# ============================================================================


def city_evaluation(context: AppContext) -> None:
    """
    Main city evaluation function.

    Ported from CityEvaluation() in s_eval.c.
    Called from SpecialInit and Simulate.
    :param context:
    """
    # global eval_valid

    context.eval_valid = 0
    if context.total_pop:
        get_ass_value(context)
        do_pop_num(context)
        do_problems(context)
        get_score(context)
        do_votes(context)
        change_eval()
    else:
        eval_init(context)
        change_eval()
    context.eval_valid = 1


# ============================================================================
# Initialization Functions
# ============================================================================


def eval_init(context: AppContext) -> None:
    """
    Initialize evaluation variables to default values.

    Ported from EvalInit() in s_eval.c.
    Called from city_evaluation and SetCommonInits.
    :param context:
    """
    # global city_yes, city_no, city_pop, delta_city_pop, city_ass_value
    # global city_class, city_score, delta_city_score, eval_valid
    # global problem_votes, problem_order

    z = 0
    context.city_yes = z
    context.city_no = z
    context.city_pop = z
    context.delta_city_pop = z
    context.city_ass_value = z
    context.city_class = z
    context.city_score = 500
    context.delta_city_score = z
    context.eval_valid = 1

    for x in range(PROBNUM):
        context.problem_votes[x] = z
    for x in range(4):
        context.problem_order[x] = z


# ============================================================================
# Assessment Value Calculation
# ============================================================================


def get_ass_value(context: AppContext) -> None:
    """
    Calculate the assessed value of the city based on infrastructure.

    Ported from GetAssValue() in s_eval.c.
    Called from city_evaluation.
    :param context:
    """
    # global city_ass_value

    z = context.road_total * 5
    z += context.rail_total * 10
    z += context.police_pop * 1000
    z += context.fire_st_pop * 1000
    z += context.hosp_pop * 400
    z += context.stadium_pop * 3000
    z += context.port_pop * 5000
    z += context.airport_pop * 10000
    z += context.coal_pop * 3000
    z += context.nuclear_pop * 6000
    context.city_ass_value = z * 1000


# ============================================================================
# Population and Classification
# ============================================================================


def do_pop_num(context: AppContext) -> None:
    """
    Calculate city population and determine city class.

    Ported from DoPopNum() in s_eval.c.
    Called from city_evaluation.
    :param context:
    """
    # global city_pop, delta_city_pop, city_class

    old_city_pop = context.city_pop
    context.city_pop = (
        context.res_pop + (context.com_pop * 8) + (context.ind_pop * 8)
    ) * 20

    if old_city_pop == -1:
        old_city_pop = context.city_pop

    context.delta_city_pop = context.city_pop - old_city_pop

    context.city_class = 0  # village
    if context.city_pop > 2000:
        context.city_class += 1  # town
    if context.city_pop > 10000:
        context.city_class += 1  # city
    if context.city_pop > 50000:
        context.city_class += 1  # capital
    if context.city_pop > 100000:
        context.city_class += 1  # metropolis
    if context.city_pop > 500000:
        context.city_class += 1  # megalopolis


# ============================================================================
# Problem Analysis and Voting
# ============================================================================


def do_problems(context: AppContext) -> None:
    """
    Analyze city problems and determine which ones are most significant.

    Ported from DoProblems() in s_eval.c.
    Called from city_evaluation.
    :param context:
    """
    # global problem_table, problem_taken, problem_order

    # Initialize problem table
    for z in range(PROBNUM):
        context.problem_table[z] = 0

    # Calculate problem severity scores
    context.problem_table[0] = context.crime_average  # Crime
    context.problem_table[1] = context.pollute_average  # Pollution
    context.problem_table[2] = int(context.lv_average * 0.7)  # Housing
    context.problem_table[3] = context.city_tax * 10  # Taxes
    context.problem_table[4] = average_trf(context)  # Traffic
    context.problem_table[5] = get_unemployment(context)  # Unemployment
    context.problem_table[6] = get_fire(context)  # Fire

    # Vote on problems
    vote_problems(context)

    # Initialize problem taken array
    for z in range(PROBNUM):
        context.problem_taken[z] = 0

    # Find top 4 problems
    for z in range(4):
        max_votes = 0
        selected_problem = -1
        for x in range(7):  # Check first 7 problems
            if (context.problem_votes[x] > max_votes) and (
                not context.problem_taken[x]
            ):
                selected_problem = x
                max_votes = context.problem_votes[x]

        if max_votes and selected_problem >= 0:
            context.problem_taken[selected_problem] = 1
            context.problem_order[z] = selected_problem
        else:
            context.problem_order[z] = 7
            context.problem_table[7] = 0


def vote_problems(context: AppContext) -> None:
    """
    Simulate voting on city problems based on their severity.

    Ported from VoteProblems() in s_eval.c.
    Called from do_problems.
    :param context:
    """
    # global problem_votes

    # Initialize votes
    for z in range(PROBNUM):
        context.problem_votes[z] = 0

    x = 0
    z = 0
    count = 0

    # Simulate 100 votes with diminishing returns
    while (z < 100) and (count < 600):
        if rand(context, 300) < context.problem_table[x]:
            context.problem_votes[x] += 1
            z += 1
        x += 1
        if x > PROBNUM - 1:
            x = 0
        count += 1


def average_trf(context: AppContext) -> int:
    """
    Calculate average traffic density.

    Ported from AverageTrf() in s_eval.c.
    Called from do_problems.

    Returns:
        Average traffic value (0-255 range)
        :param context:
    """
    # global traffic_average

    trf_total = 0
    count = 1

    # Sum traffic density over land value areas
    for x in range(HWLDX):
        for y in range(HWLDY):
            if context.land_value_mem[x][y]:
                trf_total += context.trf_density[x][y]
                count += 1

    traffic_average = int((trf_total / count) * 2.4)
    return traffic_average


def get_unemployment(context: AppContext) -> int:
    """
    Calculate unemployment rate.

    Ported from GetUnemployment() in s_eval.c.
    Called from do_problems.

    Returns:
        Unemployment rate (0-255 range)
        :param context:
    """
    b = (context.com_pop + context.ind_pop) << 3
    if b:
        r = context.res_pop / b
    else:
        return 0

    b = int((r - 1) * 255)
    if b > 255:
        b = 255
    if b < 0:
        b = 0
    return b


def get_fire(context: AppContext) -> int:
    """
    Calculate fire danger level.

    Ported from GetFire() in s_eval.c.
    Called from do_problems and get_score.

    Returns:
        Fire danger level (0-255 range)
        :param context:
    """
    z = context.fire_pop * 5
    if z > 255:
        return 255
    else:
        return z


# ============================================================================
# Score Calculation
# ============================================================================


def get_score(context: AppContext) -> None:
    """
    Calculate the overall city score based on various factors.

    Ported from GetScore() in s_eval.c.
    Called from city_evaluation.
    :param context:
    """
    # global city_score, delta_city_score

    old_city_score = context.city_score
    x = 0

    # Sum all 7 problems
    for z in range(7):
        x += context.problem_table[z]

    x = x // 3  # 7 + 2 average
    if x > 256:
        x = 256

    z = (256 - x) * 4
    if z > 1000:
        z = 1000
    if z < 0:
        z = 0

    # Apply capacity penalties
    if context.res_cap:
        z = int(z * 0.85)
    if context.com_cap:
        z = int(z * 0.85)
    if context.ind_cap:
        z = int(z * 0.85)

    # Apply infrastructure effects
    if context.road_effect < 32:
        z = z - (32 - context.road_effect)
    if context.police_effect < 1000:
        z = int(z * (0.9 + (context.police_effect / 10000.1)))
    if context.fire_effect < 1000:
        z = int(z * (0.9 + (context.fire_effect / 10000.1)))

    # Apply demand penalties
    if context.r_value < -1000:
        z = int(z * 0.85)
    if context.c_value < -1000:
        z = int(z * 0.85)
    if context.i_value < -1000:
        z = int(z * 0.85)

    # Apply population growth modifier
    score_modifier = 1.0
    if (context.city_pop == 0) or (context.delta_city_pop == 0):
        score_modifier = 1.0
    elif context.delta_city_pop == context.city_pop:
        score_modifier = 1.0
    elif context.delta_city_pop > 0:
        score_modifier = (context.delta_city_pop / context.city_pop) + 1.0
    elif context.delta_city_pop < 0:
        score_modifier = 0.95 + (
            context.delta_city_pop / (context.city_pop - context.delta_city_pop)
        )

    z = int(z * score_modifier)

    # Subtract fire and tax penalties
    z = z - get_fire(context)
    z = z - context.city_tax

    # Apply power ratio modifier
    total_zones = context.un_pwrd_z_cnt + context.pwrd_z_cnt  # total zones
    if total_zones:
        score_modifier = context.pwrd_z_cnt / total_zones  # powered ratio
    else:
        score_modifier = 1.0
    z = int(z * score_modifier)

    # Clamp final score
    if z > 1000:
        z = 1000
    if z < 0:
        z = 0

    # Average with previous score
    city_score = (context.city_score + z) // 2

    context.delta_city_score = city_score - old_city_score


# ============================================================================
# Voting and UI Updates
# ============================================================================


def do_votes(context: AppContext) -> None:
    """
    Simulate citizen voting based on city score.

    Ported from DoVotes() in s_eval.c.
    Called from city_evaluation.
    :param context:
    """
    # global city_yes, city_no

    context.city_yes = 0
    context.city_no = 0

    # Simulate 100 votes
    for z in range(100):
        if rand(context, 1000) < context.city_score:
            context.city_yes += 1
        else:
            context.city_no += 1


def change_eval() -> None:
    """
    Update evaluation display (placeholder for UI integration).

    Ported from ChangeEval() in s_eval.c.
    Called from city_evaluation.
    """
    # This would update the UI in the original TCL/Tk version
    # For now, it's a placeholder
    pass


def update_budget() -> None:
    """
    Update budget display (placeholder for UI integration).

    Ported from UpdateBudget() in w_budget.c.
    Called when budget settings change.
    """
    # This would update the UI in the original TCL/Tk version
    # For now, it's a placeholder until budget.py is implemented
    pass


def do_budget(context: AppContext) -> None:
    """
    Run the standard annual budget sequence.
    :param context:
    """
    budget_do_budget(context)
    context.must_update_funds = 1


def do_budget_from_menu(context: AppContext) -> None:
    """
    Trigger the budget workflow via the modern budget module.
    :param context:
    """
    budget_do_budget_from_menu(context)
    context.must_update_funds = 1
