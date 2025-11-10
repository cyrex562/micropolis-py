"""
evaluation_ui.py - City evaluation display system for Micropolis Python port

This module implements the city evaluation UI ported from w_eval.c,
responsible for displaying city evaluation results, scores, and statistics
in a pygame-compatible format.
"""

from typing import Optional
from . import types, evaluation, sim_control

# ============================================================================
# City Classification and Level Strings
# ============================================================================

CITY_CLASS_STRINGS = [
    "VILLAGE", "TOWN", "CITY", "CAPITAL", "METROPOLIS", "MEGALOPOLIS"
]

CITY_LEVEL_STRINGS = [
    "Easy", "Medium", "Hard"
]

PROBLEM_STRINGS = [
    "CRIME", "POLLUTION", "HOUSING COSTS", "TAXES",
    "TRAFFIC", "UNEMPLOYMENT", "FIRES"
]

# ============================================================================
# UI State Variables
# ============================================================================

# Drawing flags for pygame integration
must_draw_evaluation: bool = False

# ============================================================================
# Utility Functions
# ============================================================================

def current_year() -> int:
    """
    Get the current game year.

    Ported from CurrentYear() in w_util.c.
    Returns the current year based on CityTime.
    """
    return (types.CityTime // 48) + types.StartingYear


def make_dollar_decimal_str(num_str: str, dollar_str: str, max_len: int = 32) -> str:
    """
    Format a number string as a dollar amount with commas.

    Ported from makeDollarDecimalStr() in w_util.c.
    Converts a numeric string to a formatted dollar string.

    Args:
        num_str: The numeric string to format
        dollar_str: Output buffer (unused in Python, returned as string)
        max_len: Maximum length for safety

    Returns:
        Formatted dollar string
    """
    num_of_digits = len(num_str)

    if num_of_digits == 1:
        return f"${num_str[0]}"
    elif num_of_digits == 2:
        return f"${num_str[0]}{num_str[1]}"
    elif num_of_digits == 3:
        return f"${num_str[0]}{num_str[1]}{num_str[2]}"
    else:
        left_most_set = num_of_digits % 3
        if left_most_set == 0:
            left_most_set = 3

        num_of_commas = (num_of_digits - 1) // 3
        
        result = ['$']  # Start with dollar sign

        # Add first group (before first comma)
        num_index = 0
        for _ in range(left_most_set):
            if num_index < len(num_str):
                result.append(num_str[num_index])
                num_index += 1

        # Add remaining groups with commas
        for _ in range(num_of_commas):
            result.append(',')
            for _ in range(3):
                if num_index < len(num_str):
                    result.append(num_str[num_index])
                    num_index += 1

        return ''.join(result)


# ============================================================================
# Evaluation Display Functions
# ============================================================================

def do_score_card() -> None:
    """
    Generate and display the city evaluation scorecard.

    Ported from doScoreCard() in w_eval.c.
    Collects evaluation data and formats it for display.
    """
    # Format title
    title = f"City Evaluation  {current_year()}"

    # Format percentages
    goodyes = f"{evaluation.CityYes}%"
    goodno = f"{evaluation.CityNo}%"

    # Format problem percentages
    prob_percentages = []
    for i in range(4):
        if evaluation.ProblemVotes[evaluation.ProblemOrder[i]]:
            prob_percentages.append(f"{evaluation.ProblemVotes[evaluation.ProblemOrder[i]]}%")
        else:
            prob_percentages.append("")

    # Format statistics
    pop = f"{evaluation.CityPop}"
    delta = f"{evaluation.deltaCityPop}"

    # Format assessed value
    assessed_dollars = make_dollar_decimal_str(str(evaluation.CityAssValue), "")

    # Format score and change
    score = f"{evaluation.CityScore}"
    changed = f"{evaluation.deltaCityScore}"

    # Get problem names
    problem_names = []
    for i in range(4):
        problem_idx = evaluation.ProblemOrder[i]
        if evaluation.ProblemVotes[problem_idx]:
            problem_names.append(PROBLEM_STRINGS[problem_idx])
        else:
            problem_names.append("")

    # Mark first problem name as bold (in pygame, this could be a flag)
    if problem_names[0]:
        problem_names[0] = f"**{problem_names[0]}**"  # Placeholder for bold formatting

    # Send evaluation data to UI
    set_evaluation(
        changed, score,
        problem_names[0], problem_names[1], problem_names[2], problem_names[3],
        prob_percentages[0], prob_percentages[1], prob_percentages[2], prob_percentages[3],
        pop, delta, assessed_dollars,
        CITY_CLASS_STRINGS[evaluation.CityClass],
        CITY_LEVEL_STRINGS[types.GameLevel],
        goodyes, goodno, title
    )


def change_eval() -> None:
    """
    Mark evaluation for update.

    Ported from ChangeEval() in w_eval.c.
    Sets flag to trigger evaluation display update.
    """
    types.EvalChanged = 1


def score_doer() -> None:
    """
    Handle evaluation display updates.

    Ported from scoreDoer() in w_eval.c.
    Called from UI update loop to refresh evaluation display.
    """
    if types.EvalChanged:
        do_score_card()
        types.EvalChanged = 0


def set_evaluation(changed: str, score: str,
                  ps0: str, ps1: str, ps2: str, ps3: str,
                  pv0: str, pv1: str, pv2: str, pv3: str,
                  pop: str, delta: str, assessed_dollars: str,
                  cityclass: str, citylevel: str,
                  goodyes: str, goodno: str, title: str) -> None:
    """
    Send evaluation data to the UI system.

    Ported from SetEvaluation() in w_eval.c.
    In pygame version, this prepares data for UI display.

    Args:
        changed: Annual score change
        score: Current city score
        ps0-ps3: Problem names (top 4)
        pv0-pv3: Problem vote percentages
        pop: City population
        delta: Population change
        assessed_dollars: Assessed value formatted as dollars
        cityclass: City classification string
        citylevel: Difficulty level string
        goodyes: Percentage who approve
        goodno: Percentage who disapprove
        title: Evaluation window title
    """
    # In pygame version, this would pass data to the UI system
    # For now, store the evaluation data for UI access

    global _evaluation_data
    _evaluation_data = {
        'title': title,
        'score': score,
        'changed': changed,
        'problems': [ps0, ps1, ps2, ps3],
        'problem_votes': [pv0, pv1, pv2, pv3],
        'population': pop,
        'population_delta': delta,
        'assessed_value': assessed_dollars,
        'city_class': cityclass,
        'city_level': citylevel,
        'approval_rating': goodyes,
        'disapproval_rating': goodno
    }

    # Mark for redraw
    draw_evaluation()


# ============================================================================
# UI Drawing Functions (Adapted for pygame)
# ============================================================================

def draw_evaluation() -> None:
    """
    Mark evaluation display for redraw.

    Ported from drawEvaluation() equivalent in w_eval.c.
    In pygame version, this sets a flag for UI update.
    """
    global must_draw_evaluation
    must_draw_evaluation = True


def really_draw_evaluation() -> None:
    """
    Actually draw/update the evaluation display.

    Ported from ReallyDrawEvaluation() equivalent in w_eval.c.
    In pygame version, this would update the UI display.
    """
    global must_draw_evaluation

    # In pygame version, this would render the evaluation data
    # For now, just mark as drawn
    must_draw_evaluation = False


def update_evaluation() -> None:
    """
    Update evaluation display if needed.

    Ported from UpdateEvaluation() equivalent in w_eval.c.
    Checks flags and updates display accordingly.
    """
    global must_draw_evaluation

    if must_draw_evaluation:
        really_draw_evaluation()
        must_draw_evaluation = False


# ============================================================================
# Data Access Functions
# ============================================================================

_evaluation_data: Optional[dict] = None


def get_evaluation_data() -> Optional[dict]:
    """
    Get the current evaluation display data.

    Returns:
        Dictionary containing evaluation data, or None if not available
    """
    return _evaluation_data


def get_city_class_string(city_class: int) -> str:
    """
    Get the string representation of a city class.

    Args:
        city_class: City class index (0-5)

    Returns:
        City class string
    """
    if 0 <= city_class < len(CITY_CLASS_STRINGS):
        return CITY_CLASS_STRINGS[city_class]
    return "UNKNOWN"


def get_city_level_string(city_level: int) -> str:
    """
    Get the string representation of a city difficulty level.

    Args:
        city_level: City level index (0-2)

    Returns:
        City level string
    """
    if 0 <= city_level < len(CITY_LEVEL_STRINGS):
        return CITY_LEVEL_STRINGS[city_level]
    return "UNKNOWN"


def get_problem_string(problem_idx: int) -> str:
    """
    Get the string representation of a city problem.

    Args:
        problem_idx: Problem index (0-6)

    Returns:
        Problem string
    """
    if 0 <= problem_idx < len(PROBLEM_STRINGS):
        return PROBLEM_STRINGS[problem_idx]
    return "UNKNOWN"


# ============================================================================
# TCL Command Interface Functions
# ============================================================================

def do_score_card_command() -> None:
    """
    Execute score card display.

    Ported from SimCmdDoScoreCard in w_sim.c.
    TCL command interface for triggering evaluation display.
    """
    do_score_card()
    sim_control.kick()


def change_eval_command() -> None:
    """
    Mark evaluation for change.

    Ported from SimCmdChangeEval in w_sim.c.
    TCL command interface for marking evaluation as changed.
    """
    change_eval()
    sim_control.kick()


def update_evaluation_command() -> None:
    """
    Update evaluation display.

    Ported from SimCmdUpdateEvaluation in w_sim.c.
    TCL command interface for updating evaluation UI.
    """
    update_evaluation()
    sim_control.kick()