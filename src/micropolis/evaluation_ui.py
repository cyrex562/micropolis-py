"""
evaluation_ui.py - City evaluation display system for Micropolis Python port

This module implements the city evaluation UI ported from w_eval.c,
responsible for displaying city evaluation results, scores, and statistics
in a pygame-compatible format.
"""

import pygame

from micropolis import sim_control
from micropolis import types as types
from micropolis import evaluation as evaluation
from micropolis.context import AppContext

# Feature flag so tests can toggle pygame availability
PYGAME_AVAILABLE: bool = True

# ============================================================================
# City Classification and Level Strings
# ============================================================================

CITY_CLASS_STRINGS = ["VILLAGE", "TOWN", "CITY", "CAPITAL", "METROPOLIS", "MEGALOPOLIS"]

CITY_LEVEL_STRINGS = ["Easy", "Medium", "Hard"]

PROBLEM_STRINGS = [
    "CRIME",
    "POLLUTION",
    "HOUSING COSTS",
    "TAXES",
    "TRAFFIC",
    "UNEMPLOYMENT",
    "FIRES",
]

# ============================================================================
# UI State Variables
# ============================================================================

# Drawing flags for pygame integration
must_draw_evaluation: bool = False
_evaluation_panel_visible: bool = False
_evaluation_panel_dirty: bool = False
_evaluation_panel_size: tuple[int, int] = (320, 200)
_evaluation_surface: pygame.Surface | None = None

# ============================================================================
# Utility Functions
# ============================================================================


def current_year(context: AppContext | None) -> int:
    """
    Get the current game year.

    Ported from CurrentYear() in w_util.c.
    Returns the current year based on CityTime.
    """
    # Prefer legacy types.CityTime/StartingYear when tests patch them
    city_time = getattr(types, "CityTime", None)
    starting_year = getattr(types, "StartingYear", None)
    if city_time is not None and starting_year is not None:
        return (city_time // 48) + starting_year

    if context is None:
        return 0

    return (context.city_time // 48) + context.starting_year


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

        result = ["$"]  # Start with dollar sign

        # Add first group (before first comma)
        num_index = 0
        for _ in range(left_most_set):
            if num_index < len(num_str):
                result.append(num_str[num_index])
                num_index += 1

        # Add remaining groups with commas
        for _ in range(num_of_commas):
            result.append(",")
            for _ in range(3):
                if num_index < len(num_str):
                    result.append(num_str[num_index])
                    num_index += 1

        return "".join(result)


# ============================================================================
# Evaluation Display Functions
# ============================================================================


def do_score_card(context: AppContext | None) -> None:
    """Generate and display the city evaluation scorecard.

    Prefer values from the legacy `evaluation` module (tests patch this)
    and fall back to values on the provided AppContext.
    """
    # Title: if context provided use current_year(context), else best-effort
    title = f"City Evaluation  {current_year(context) if context is not None else getattr(types, 'StartingYear', 0)}"

    # Percentages and scores: prefer legacy evaluation module attributes
    goodyes = f"{getattr(evaluation, 'CityYes', getattr(context, 'city_yes', 0))}%"
    goodno = f"{getattr(evaluation, 'CityNo', getattr(context, 'city_no', 0))}%"

    # Problem votes/order
    prob_votes = getattr(
        evaluation, "ProblemVotes", getattr(context, "problem_votes", [])
    )
    prob_order = getattr(
        evaluation,
        "ProblemOrder",
        getattr(context, "problem_order", list(range(len(prob_votes)))),
    )

    prob_percentages: list[str] = []
    for i in range(4):
        idx = prob_order[i] if i < len(prob_order) else i
        if idx < len(prob_votes) and prob_votes[idx]:
            prob_percentages.append(f"{prob_votes[idx]}%")
        else:
            prob_percentages.append("")

    # Population and delta
    pop = f"{getattr(evaluation, 'CityPop', getattr(context, 'city_pop', 0))}"
    delta = (
        f"{getattr(evaluation, 'deltaCityPop', getattr(context, 'delta_city_pop', 0))}"
    )

    # Assessed value
    assessed_dollars = make_dollar_decimal_str(
        str(getattr(evaluation, "CityAssValue", getattr(context, "city_ass_value", 0))),
        "",
    )

    # Score and change
    score = f"{getattr(evaluation, 'CityScore', getattr(context, 'city_score', 0))}"
    changed = f"{getattr(evaluation, 'deltaCityScore', getattr(context, 'delta_city_score', 0))}"

    # Problem names
    problem_names: list[str] = []
    for i in range(4):
        idx = prob_order[i] if i < len(prob_order) else i
        if idx < len(prob_votes) and prob_votes[idx]:
            problem_names.append(PROBLEM_STRINGS[idx])
        else:
            problem_names.append("")

    if problem_names[0]:
        problem_names[0] = f"**{problem_names[0]}**"

    # City class and level
    city_class = getattr(evaluation, "CityClass", getattr(context, "city_class", 0))
    game_level = getattr(types, "GameLevel", getattr(context, "game_level", 0))

    # Call set_evaluation using legacy signature (without context) for compatibility
    set_evaluation(
        changed,
        score,
        problem_names[0],
        problem_names[1],
        problem_names[2],
        problem_names[3],
        prob_percentages[0],
        prob_percentages[1],
        prob_percentages[2],
        prob_percentages[3],
        pop,
        delta,
        assessed_dollars,
        CITY_CLASS_STRINGS[city_class],
        CITY_LEVEL_STRINGS[game_level],
        goodyes,
        goodno,
        title,
    )


def change_eval(context: AppContext | None) -> None:
    """
    Mark evaluation for update.

    Ported from ChangeEval() in w_eval.c.
    Sets flag to trigger evaluation display update.
    :param context:
    """
    # Mirror legacy behaviour: set both context flag and types.eval_changed
    if context is not None:
        setattr(context, "eval_changed", 1)
    setattr(types, "eval_changed", 1)


def score_doer(context: AppContext | None) -> None:
    """
    Handle evaluation display updates.

    Ported from scoreDoer() in w_eval.c.
    Called from UI update loop to refresh evaluation display.
    :param context:
    """
    # Accept either legacy types.eval_changed or context.eval_changed
    changed_flag = getattr(types, "eval_changed", None)
    if changed_flag is None and context is not None:
        changed_flag = getattr(context, "eval_changed", 0)

    if changed_flag:
        do_score_card(context)
        # Clear both
        if context is not None:
            setattr(context, "eval_changed", 0)
        setattr(types, "eval_changed", 0)


def set_evaluation(*args) -> None:
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
    # Backwards-compatible wrapper: accept either (context, ...) or legacy signature without context
    if len(args) == 0:
        return

    if isinstance(args[0], AppContext):
        # signature: (context, changed, score, ... , title)
        context = args[0]
        try:
            (
                _,
                changed,
                score,
                ps0,
                ps1,
                ps2,
                ps3,
                pv0,
                pv1,
                pv2,
                pv3,
                pop,
                delta,
                assessed_dollars,
                cityclass,
                citylevel,
                goodyes,
                goodno,
                title,
            ) = args
        except ValueError:
            # incorrect args
            return
    else:
        # legacy signature without context
        context = None
        try:
            (
                changed,
                score,
                ps0,
                ps1,
                ps2,
                ps3,
                pv0,
                pv1,
                pv2,
                pv3,
                pop,
                delta,
                assessed_dollars,
                cityclass,
                citylevel,
                goodyes,
                goodno,
                title,
            ) = args
        except ValueError:
            return

    data = {
        "title": title,
        "score": score,
        "changed": changed,
        "problems": [ps0, ps1, ps2, ps3],
        "problem_votes": [pv0, pv1, pv2, pv3],
        "population": pop,
        "population_delta": delta,
        "assessed_value": assessed_dollars,
        "city_class": cityclass,
        "city_level": citylevel,
        "approval_rating": goodyes,
        "disapproval_rating": goodno,
    }

    if context is not None:
        setattr(context, "_evaluation_data", data)
    else:
        global _evaluation_data
        _evaluation_data = data

    # Mark for redraw
    if context is not None:
        draw_evaluation(context)
    else:
        draw_evaluation()


# ============================================================================
# UI Drawing Functions (Adapted for pygame)
# ============================================================================


def draw_evaluation(context: AppContext | None = None) -> None:
    """
    Mark evaluation display for redraw.

    Ported from drawEvaluation() equivalent in w_eval.c.
    In pygame version, this sets a flag for UI update.
    """
    if context is None:
        global must_draw_evaluation, _evaluation_panel_visible, _evaluation_panel_dirty
        must_draw_evaluation = True
        if _evaluation_panel_visible:
            _evaluation_panel_dirty = True
    else:
        context.must_draw_evaluation = True
        if getattr(context, "_evaluation_panel_visible", False):
            setattr(context, "_evaluation_panel_dirty", True)


def really_draw_evaluation(context: AppContext | None = None) -> None:
    """
    Actually draw/update the evaluation display.

    Ported from ReallyDrawEvaluation() equivalent in w_eval.c.
    In pygame version, this would update the UI display.
    """
    # global must_draw_evaluation

    # In pygame version, this would render the evaluation data
    # For now, just mark as drawn
    if context is None:
        global must_draw_evaluation
        must_draw_evaluation = False
        if _evaluation_panel_visible:
            _render_evaluation_surface(None)
    else:
        context.must_draw_evaluation = False
        if getattr(context, "_evaluation_panel_visible", False):
            _render_evaluation_surface(context)


def update_evaluation(context: AppContext | None = None) -> None:
    """
    Update evaluation display if needed.

    Ported from UpdateEvaluation() equivalent in w_eval.c.
    Checks flags and updates display accordingly.
    """
    # global must_draw_evaluation

    if context is None:
        global must_draw_evaluation
        if must_draw_evaluation:
            really_draw_evaluation()
            must_draw_evaluation = False
    else:
        if getattr(context, "must_draw_evaluation", False):
            really_draw_evaluation(context)
            setattr(context, "must_draw_evaluation", False)


# ============================================================================
# Data Access Functions
# ============================================================================

_evaluation_data: dict | None = None


def get_evaluation_data(context: AppContext | None = None) -> dict | None:
    """
    Get the current evaluation display data.

    Returns:
        Dictionary containing evaluation data, or None if not available
    """
    if context is None:
        return _evaluation_data
    return getattr(context, "_evaluation_data", None)


def set_evaluation_panel_visible(*args) -> None:
    """Toggle the pygame evaluation overlay visibility.

    Backwards compatible: accepts either (visible,) or (context, visible).
    """
    if len(args) == 1 and isinstance(args[0], bool):
        visible = args[0]
        context = None
    elif len(args) == 2:
        context, visible = args
    else:
        raise TypeError(
            "set_evaluation_panel_visible requires visible or (context, visible)"
        )

    if context is None:
        global _evaluation_panel_visible, _evaluation_panel_dirty
        _evaluation_panel_visible = visible
        _evaluation_panel_dirty = True if visible else False
    else:
        setattr(context, "_evaluation_panel_visible", visible)
        setattr(context, "_evaluation_panel_dirty", True if visible else False)


def is_evaluation_panel_visible(context: AppContext | None = None) -> bool:
    """Return True if the evaluation panel should be shown."""
    if context is None:
        return _evaluation_panel_visible
    return getattr(context, "_evaluation_panel_visible", False)


def set_evaluation_panel_size(
    context: AppContext | None, width: int, height: int
) -> None:
    """Resize the evaluation panel surface used during rendering."""
    if context is None:
        global _evaluation_panel_size, _evaluation_panel_dirty
        _evaluation_panel_size = (max(1, width), max(1, height))
        _evaluation_panel_dirty = True
    else:
        setattr(context, "_evaluation_panel_size", (max(1, width), max(1, height)))
        setattr(context, "_evaluation_panel_dirty", True)


def get_evaluation_surface() -> pygame.Surface | None:
    """
    Return the pygame surface representing the evaluation panel, rendering it if necessary.
    """
    # Respect PYGAME_AVAILABLE flag
    if not PYGAME_AVAILABLE:
        return None

    if not _evaluation_panel_visible:
        return None

    global _evaluation_surface, _evaluation_panel_size, _evaluation_panel_dirty
    if (_evaluation_surface is None) or (
        _evaluation_surface.get_size() != _evaluation_panel_size
    ):
        _create_evaluation_surface(None)

    if _evaluation_panel_dirty:
        _render_evaluation_surface(None)

    return _evaluation_surface


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


def do_score_card_command(context: AppContext) -> None:
    """
    Execute score card display.

    Ported from SimCmdDoScoreCard in w_sim.c.
    TCL command interface for triggering evaluation display.
    :param context:
    """
    do_score_card(context)
    sim_control.kick()


def change_eval_command(context: AppContext) -> None:
    """
    Mark evaluation for change.

    Ported from SimCmdChangeEval in w_sim.c.
    TCL command interface for marking evaluation as changed.
    :param context:
    """
    change_eval(context)
    sim_control.kick()


def update_evaluation_command(context: AppContext) -> None:
    """
    Update evaluation display.

    Ported from SimCmdUpdateEvaluation in w_sim.c.
    TCL command interface for updating evaluation UI.
    :param context:
    """
    update_evaluation(context)
    sim_control.kick()


# ============================================================================
# Internal helpers
# ============================================================================


def _create_evaluation_surface(context: AppContext | None) -> None:
    """Create the pygame surface for evaluation data."""
    if context is None:
        global _evaluation_panel_size, _evaluation_surface, _evaluation_panel_dirty
        width, height = _evaluation_panel_size
        _evaluation_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        _evaluation_panel_dirty = True
    else:
        width, height = getattr(context, "_evaluation_panel_size", (320, 200))
        setattr(
            context,
            "_evaluation_surface",
            pygame.Surface((width, height), pygame.SRCALPHA),
        )
        setattr(context, "_evaluation_panel_dirty", True)


def _render_evaluation_surface(context: AppContext | None) -> None:
    """Render evaluation data into the pygame surface."""
    if context is None:
        global \
            _evaluation_panel_dirty, \
            _evaluation_surface, \
            _evaluation_panel_visible, \
            _evaluation_data
        if not (_evaluation_panel_visible and _evaluation_surface):
            _evaluation_panel_dirty = False
            return

        surface = _evaluation_surface
        surface.fill((0, 0, 0, 200))
        data = _evaluation_data or {}
    else:
        if not (
            getattr(context, "_evaluation_panel_visible", False)
            and getattr(context, "_evaluation_surface", None)
        ):
            setattr(context, "_evaluation_panel_dirty", False)
            return

        surface = getattr(context, "_evaluation_surface")
        surface.fill((0, 0, 0, 200))
        data = getattr(context, "_evaluation_data", {}) or {}
    # Draw a simple textual summary using pygame fonts if available; otherwise colored bars
    font = None
    if pygame.font.get_init() or pygame.font.get_init() is False:
        try:
            font = pygame.font.SysFont("Verdana", 14)
        except Exception:
            font = None

    lines = [
        data.get("title", "City Evaluation"),
        f"Score: {data.get('score', '0')} ({data.get('changed', '0')})",
        f"Population: {data.get('population', '0')} ({data.get('population_delta', '0')})",
        f"Approval: {data.get('approval_rating', '0%')} vs {data.get('disapproval_rating', '0%')}",
    ]

    if font:
        y = 10
        for line in lines:
            text_surface = font.render(line, True, (255, 255, 255))
            surface.blit(text_surface, (10, y))
            y += text_surface.get_height() + 2
    else:
        # Fallback: draw colored stripes
        colors = [(0, 120, 0), (120, 0, 0), (0, 0, 120), (120, 120, 0)]
        stripe_height = max(1, surface.get_height() // len(colors))
        for idx, color in enumerate(colors):
            pygame.draw.rect(
                surface,
                color,
                pygame.Rect(0, idx * stripe_height, surface.get_width(), stripe_height),
            )

    if context is None:
        _evaluation_panel_dirty = False
    else:
        setattr(context, "_evaluation_panel_dirty", False)
