"""
ui_utilities.py - UI utility functions for Micropolis Python port
"""

import re
from typing import Any

from .constants import (
    ALMAP,
    REMAP,
    COMAP,
    INMAP,
    PDMAP,
    RGMAP,
    TDMAP,
    PLMAP,
    CRMAP,
    LVMAP,
    FIMAP,
    POMAP,
    DYMAP,
)
from .context import AppContext
from .evaluation_ui import (
    set_evaluation_panel_visible,
    do_score_card,
    draw_evaluation,
    update_evaluation,
)
from .graphs import set_graph_panel_visible, request_graph_panel_redraw
from .initialization import InitializeSimulation
from .sim_view import SimView


# ============================================================================
# Dollar Formatting Functions
# ============================================================================


def make_dollar_decimal_str(num_str: str) -> str:
    """
    Format a number string as a dollar amount with commas.

    Ported from makeDollarDecimalStr() in w_util.c.
    Formats numbers like "1234567" into "$1,234,567".

    Args:
        num_str: Input number as string

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

        # Build the formatted string
        result = "$"
        num_index = 0

        # Add first group (may be shorter)
        for _ in range(left_most_set):
            result += num_str[num_index]
            num_index += 1

        # Add remaining groups with commas
        for _ in range(num_of_commas):
            result += ","
            result += num_str[num_index]
            num_index += 1
            result += num_str[num_index]
            num_index += 1
            result += num_str[num_index]
            num_index += 1

        return result


# ============================================================================
# Simulation Control Functions
# ============================================================================


def pause(context: AppContext) -> None:
    """
    Pause the simulation.

    Ported from Pause() in w_util.c.
    Saves current speed and sets speed to 0.
    :param context:
    """
    from .sim_control import get_sim_speed, is_sim_paused, pause_simulation

    if not is_sim_paused(context):
        # Save current speed before pausing
        context.sim_paused_speed = get_sim_speed(context)
        pause_simulation(context)


def resume(context: AppContext) -> None:
    """
    Resume the simulation.

    Ported from Resume() in w_util.c.
    Restores previously saved speed.
    :param context:
    """
    from .sim_control import is_sim_paused, resume_simulation, set_sim_speed

    if is_sim_paused(context):
        resume_simulation(context)
        # Restore saved speed
        set_sim_speed(context, context.sim_paused_speed)


def set_speed(context: AppContext, speed: int) -> None:
    """
    Set simulation speed.

    Ported from setSpeed() in w_util.c.
    Clamps speed to valid range (0-3) and handles pause state.

    Args:
        speed: New simulation speed (0-3)
        :param context:
    """
    from .sim_control import is_sim_paused, set_sim_speed

    # Clamp speed to valid range
    if speed < 0:
        speed = 0
    elif speed > 3:
        speed = 3

    context.sim_meta_speed = speed

    if is_sim_paused(context):
        context.sim_paused_speed = context.sim_meta_speed
        speed = 0

    context.sim_speed = speed

    # Update TCL interface (adapted for pygame)
    # In pygame version, this would trigger UI updates
    set_sim_speed(context, speed)


def set_skips(context: AppContext, skips: int) -> None:
    """
    Set simulation skip frames.

    Ported from setSkips() in w_util.c.

    Args:
        skips: Number of frames to skip
    """
    from .sim_control import set_sim_skips

    set_sim_skips(context, skips)


# def set_game_level(context: AppContext, level: int) -> None:
#     """
#     Set game difficulty level.
#
#     Args:
#         context: Application context
#         level: Difficulty level (1-5)
#     """
#     context.game_level = level


def set_funds(context: AppContext, funds: int) -> None:
    """
    Set city funds.

    Args:
        context: Application context
        funds: City funds
    """
    context.city_funds = funds


# def set_city_name(context: AppContext, name: str) -> None:
#     """
#     Set city name.
#
#     Args:
#         context: Application context
#         name: City name
#     """
#     context.city_name = name


def update_funds(context: AppContext) -> None:
    """
    Update city funds display.

    Args:
        context: Application context
    """
    pass


def did_load_scenario(context: AppContext) -> None:
    """
    Callback when scenario is loaded.
    """
    pass


def kick(context: AppContext) -> None:
    """
    Kick the game loop.
    """
    pass


def did_load_city(context: AppContext) -> None:
    """
    Callback when city is loaded.
    """
    pass


def didnt_load_city(context: AppContext) -> None:
    """
    Callback when city load fails.
    """
    pass


def did_save_city(context: AppContext) -> None:
    """
    Callback when city is saved.
    """
    pass


def didnt_save_city(context: AppContext) -> None:
    """
    Callback when city save fails.
    """
    pass


def do_save_city_as(context: AppContext) -> None:
    """
    Prompt user to choose a save filename.
    """
    pass


def eval_cmd_str(context: AppContext, cmd: str) -> None:
    """
    Evaluate a command string.

    Args:
        context: Application context
        cmd: Command string
    """
    pass


# ============================================================================
# Keyboard Shortcut Handling
# ============================================================================

# Key codes are ASCII compatible to avoid a hard dependency on pygame here.
ASCII_SPACE = 32
ASCII_EQUALS = ord("=")
ASCII_PLUS = ord("+")
ASCII_MINUS = ord("-")
ASCII_UNDERSCORE = ord("_")

_DIRECT_SPEED_KEYS = {
    ord("0"): 0,
    ord("1"): 1,
    ord("2"): 2,
    ord("3"): 3,
}

_BUDGET_KEYS = {ord("b"), ord("B")}
_PAUSE_KEYS = {ASCII_SPACE, ord("p"), ord("P")}
_GRAPH_KEYS = {ord("g"), ord("G")}
_EVALUATION_KEYS = {ord("e"), ord("E")}
_OVERLAY_NEXT_KEYS = {ord("]")}
_OVERLAY_PREV_KEYS = {ord("[")}

_OVERLAY_SEQUENCE = [
    ALMAP,
    REMAP,
    COMAP,
    INMAP,
    PDMAP,
    RGMAP,
    TDMAP,
    PLMAP,
    CRMAP,
    LVMAP,
    FIMAP,
    POMAP,
    DYMAP,
]

_overlay_index: int = 0
_graph_display_enabled: bool = False
_evaluation_display_enabled: bool = False


def toggle_pause(context: AppContext) -> None:
    """Toggle between paused and running simulation states.
    :param context:
    """
    from .sim_control import is_sim_paused

    if is_sim_paused(context):
        resume(context)
    else:
        pause(context)


def adjust_speed(context: AppContext, delta: int) -> None:
    """Increment simulation speed by delta within the valid range.
    :param context:
    """
    new_speed = max(0, min(3, context.sim_speed + delta))
    set_speed(context, new_speed)


def handle_keyboard_shortcut(context: AppContext, key_code: int) -> bool:
    """
    Handle global keyboard shortcuts used by pygame front-ends.

    Args:
        key_code: Integer key code (pygame-compatible)

    Returns:
        True if the key was handled, False otherwise.
        :param context:
    """
    if key_code in _PAUSE_KEYS:
        toggle_pause(context)
        return True

    if key_code in _DIRECT_SPEED_KEYS:
        set_speed(context, _DIRECT_SPEED_KEYS[key_code])
        return True

    if key_code in (ASCII_EQUALS, ASCII_PLUS):
        adjust_speed(context, 1)
        return True

    if key_code in (ASCII_MINUS, ASCII_UNDERSCORE):
        adjust_speed(context, -1)
        return True

    if key_code in _BUDGET_KEYS:
        _open_budget_window(context)
        return True

    if key_code in _GRAPH_KEYS:
        toggle_graph_display(context)
        return True

    if key_code in _EVALUATION_KEYS:
        toggle_evaluation_display(context)
        return True

    if key_code in _OVERLAY_NEXT_KEYS:
        cycle_map_overlay(context, 1)
        return True

    if key_code in _OVERLAY_PREV_KEYS:
        cycle_map_overlay(context, -1)
        return True

    return False


def _open_budget_window(context: AppContext) -> None:
    """Trigger the budget overlay and pause simulation for interaction.
    :param context:
    """
    from . import budget

    budget.draw_budget_window(context)
    budget.show_budget_window_and_start_waiting(context)


def toggle_graph_display(context: AppContext) -> None:
    """
    Toggle graph window visibility and flag a redraw.
    """
    # global _graph_display_enabled
    context._graph_display_enabled = not context._graph_display_enabled
    set_graph_panel_visible(context, context._graph_display_enabled)
    request_graph_panel_redraw(context)
    context.new_graph = 1


def toggle_evaluation_display(context: AppContext) -> None:
    """
    Toggle evaluation panel visibility and request updated data.
    :param context:
    """
    # global _evaluation_display_enabled
    context._evaluation_display_enabled = not context._evaluation_display_enabled
    set_evaluation_panel_visible(context._evaluation_display_enabled)

    if context._evaluation_display_enabled:
        do_score_card(context)
        draw_evaluation()
    else:
        update_evaluation()


def cycle_map_overlay(context: AppContext, direction: int) -> None:
    """
    Cycle through predefined map overlays.

    Args:
        direction: +1 for next overlay, -1 for previous.
        :param context:
    """
    if not _OVERLAY_SEQUENCE:
        return

    # global _overlay_index
    context.overlay_index = (context.overlay_index + direction) % len(_OVERLAY_SEQUENCE)
    set_map_overlay(context, _OVERLAY_SEQUENCE[context.overlay_index])


def set_map_overlay(context: AppContext, mode: int) -> None:
    """
    Apply a specific overlay mode to all map views.

    Args:
        mode: Overlay constant (ALMAP, PDMAP, etc.)
        :param context:
    """
    if not context.sim:
        return

    for view in _iter_views(context.sim.map):
        view.map_state = mode
        view.invalid = True

    context.new_map = 1
    if 0 <= mode < len(context.new_map_flags):
        context.new_map_flags[mode] = 1


def _iter_views(head: SimView | None):
    """Yield linked SimView objects starting from head."""
    current = head
    while current:
        yield current
        current = current.next


# ============================================================================
# Game Level Management
# ============================================================================


def set_game_level_funds(context: AppContext, level: int) -> None:
    """
    Set initial funds based on game difficulty level.

    Ported from SetGameLevelFunds() in w_util.c.

    Args:
        level: Game difficulty level (0=easy, 1=medium, 2=hard)
        :param context:
    """
    if level == 0:
        set_funds(context, 20000)
        set_game_level(context, 0)
    elif level == 1:
        set_funds(context, 10000)
        set_game_level(context, 1)
    elif level == 2:
        set_funds(context, 5000)
        set_game_level(context, 2)
    # Default to easy
    else:
        set_funds(context, 20000)
        set_game_level(context, 0)


def set_game_level(context: AppContext, level: int) -> None:
    """
    Set game difficulty level.

    Ported from SetGameLevel() in w_util.c.

    Args:
        level: Game difficulty level (0=easy, 1=medium, 2=hard)
        :param context:
    """
    context.game_level = level
    # In pygame version, this would trigger UI updates
    # For now, just update the level


def update_game_level() -> None:
    """
    Update game level display.

    Ported from UpdateGameLevel() in w_util.c.
    """
    # In pygame version, this would update UI elements
    # For now, this is a no-op as the level is already set
    pass


# ============================================================================
# City Name Management
# ============================================================================


def set_city_name(context: AppContext, name: str) -> None:
    """
    Set city name with validation.

    Ported from setCityName() in w_util.c.
    Sanitizes name by replacing non-alphanumeric characters with underscores.

    Args:
        name: New city name
        :param context:
    """
    # Sanitize name - replace non-alphanumeric with underscores
    sanitized_name = re.sub(r"[^a-zA-Z0-9]", "_", name)
    set_any_city_name(context, sanitized_name)


def set_any_city_name(context: AppContext, name: str) -> None:
    """
    Set city name without validation.

    Ported from setAnyCityName() in w_util.c.

    Args:
        name: New city name
        :param context:
    """
    context.city_name = name
    # In pygame version, this would trigger UI updates
    # For now, just update the name


# ============================================================================
# Time Management
# ============================================================================


def set_current_year(context: AppContext, year: int) -> None:
    """
    Set the current year.

    Ported from SetYear() in w_util.c.
    Prevents year from going negative and updates CityTime accordingly.

    Args:
        year: New year (must be >= StartingYear)
        :param year:
        :param context:
    """
    # Prevent year from going negative
    if year < context.starting_year:
        year = context.starting_year

    # Calculate year offset and update CityTime
    year_offset = year - context.starting_year - (context.city_time // 48)
    context.city_time += year_offset * 48

    # In original C code, this calls doTimeStuff()
    # In pygame version, this would trigger time-based updates
    # For now, this is handled by the simulation loop


def current_year(context: AppContext) -> int:
    """
    Get the current year.

    Ported from CurrentYear() in w_util.c.

    Returns:
        Current year based on CityTime
        :param context:
    """
    return (context.city_time // 48) + context.starting_year


# ============================================================================
# Map View Management
# ============================================================================


def do_set_map_state(view: Any, state: int) -> None:
    """
    Set map view state.

    Ported from DoSetMapState() in w_util.c.

    Args:
        view: Map view to update
        state: New map state
    """
    view.map_state = state
    view.invalid = True
    # In pygame version, this would trigger view redraw
    # For now, just update the state


# ============================================================================
# Game Management
# ============================================================================


def do_new_game(context: AppContext) -> None:
    """
    Start a new game.

    Ported from DoNewGame() in w_util.c.
    """
    # In pygame version, this would reset the game state
    # For now, delegate to initialization
    InitializeSimulation(context)


# ============================================================================
# Stub Functions (Not implemented in pygame version)
# ============================================================================


def do_generated_city_image(
    name: str, time: int, pop: int, class_type: str, score: int
) -> None:
    """
    Generate city image (stub).

    Ported from DoGeneratedCityImage() in w_util.c.
    Not implemented in pygame version.

    Args:
        name: City name
        time: Game time
        pop: Population
        class_type: City class
        score: City score
    """
    # XXX: TODO: print city (not implemented in pygame version)
    pass


def do_start_elmd() -> None:
    """
    Start ELM daemon (stub).

    Ported from DoStartElmd() in w_util.c.
    Not implemented in pygame version.
    """
    # XXX: TODO: start elm daemon (not implemented in pygame version)
    pass


def do_pop_up_message(msg: str) -> None:
    """
    Show popup message.

    Ported from DoPopUpMessage() in w_util.c.

    Args:
        msg: Message to display
    """
    # In pygame version, this would show a popup dialog
    # For now, just print to console
    print(f"Popup message: {msg}")


def handle_command(context: AppContext, command: str, *args) -> str:
    """
    Handle TCL UI utility commands.

    Args:
        command: Command name
        *args: Command arguments

    Returns:
        Command result string

    Raises:
        ValueError: For unknown commands or invalid arguments
        :param context:
    """
    if command == "pause":
        pause(context)
        return ""

    elif command == "resume":
        resume(context)
        return ""

    elif command == "setspeed":
        if len(args) != 1:
            raise ValueError("Usage: setspeed <speed>")
        speed = int(args[0])
        set_speed(context, speed)
        return ""

    elif command == "setskips":
        if len(args) != 1:
            raise ValueError("Usage: setskips <skips>")
        skips = int(args[0])
        set_skips(context, skips)
        return ""

    elif command == "setgamelevelfunds":
        if len(args) != 1:
            raise ValueError("Usage: setgamelevelfunds <level>")
        level = int(args[0])
        set_game_level_funds(context, level)
        return ""

    elif command == "setgamelevel":
        if len(args) != 1:
            raise ValueError("Usage: setgamelevel <level>")
        level = int(args[0])
        set_game_level(context, level)
        return ""

    elif command == "setcityname":
        if len(args) != 1:
            raise ValueError("Usage: setcityname <name>")
        name = args[0]
        set_city_name(context, name)
        return ""

    elif command == "setanycityname":
        if len(args) != 1:
            raise ValueError("Usage: setanycityname <name>")
        name = args[0]
        set_any_city_name(context, name)
        return ""

    elif command == "setyear":
        if len(args) != 1:
            raise ValueError("Usage: setyear <year>")
        year = int(args[0])
        set_current_year(context, year)
        return ""

    elif command == "currentyear":
        return str(current_year(context))

    elif command == "popupmessage":
        if len(args) != 1:
            raise ValueError("Usage: popupmessage <message>")
        msg = args[0]
        do_pop_up_message(msg)
        return ""

    else:
        raise ValueError(f"Unknown UI utility command: {command}")


class UIUtilitiesCommand:
    """TCL command interface for UI utilities."""
