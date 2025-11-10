"""
ui_utilities.py - UI utility functions for Micropolis Python port
"""

import re
from typing import Any

# Import simulation modules
from . import (
    evaluation_ui,
    file_io,
    generation,
    graphs,
    initialization,
    sim_control,
    types,
    view_types,
)

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

def pause() -> None:
    """
    Pause the simulation.

    Ported from Pause() in w_util.c.
    Saves current speed and sets speed to 0.
    """
    if not sim_control.is_sim_paused():
        # Save current speed before pausing
        types.sim_paused_speed = sim_control.get_sim_speed()
        sim_control.pause_simulation()


def resume() -> None:
    """
    Resume the simulation.

    Ported from Resume() in w_util.c.
    Restores previously saved speed.
    """
    if sim_control.is_sim_paused():
        sim_control.resume_simulation()
        # Restore saved speed
        sim_control.set_sim_speed(types.sim_paused_speed)


def set_speed(speed: int) -> None:
    """
    Set simulation speed.

    Ported from setSpeed() in w_util.c.
    Clamps speed to valid range (0-3) and handles pause state.

    Args:
        speed: New simulation speed (0-3)
    """
    # Clamp speed to valid range
    if speed < 0:
        speed = 0
    elif speed > 3:
        speed = 3

    types.SimMetaSpeed = speed

    if sim_control.is_sim_paused():
        types.sim_paused_speed = types.SimMetaSpeed
        speed = 0

    types.SimSpeed = speed

    # Update TCL interface (adapted for pygame)
    # In pygame version, this would trigger UI updates
    sim_control.set_sim_speed(speed)


def set_skips(skips: int) -> None:
    """
    Set simulation skip frames.

    Ported from setSkips() in w_util.c.

    Args:
        skips: Number of frames to skip
    """
    sim_control.set_sim_skips(skips)


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
    types.ALMAP,
    types.REMAP,
    types.COMAP,
    types.INMAP,
    types.PDMAP,
    types.RGMAP,
    types.TDMAP,
    types.PLMAP,
    types.CRMAP,
    types.LVMAP,
    types.FIMAP,
    types.POMAP,
    types.DYMAP,
]

_overlay_index: int = 0
_graph_display_enabled: bool = False
_evaluation_display_enabled: bool = False


def toggle_pause() -> None:
    """Toggle between paused and running simulation states."""
    if sim_control.is_sim_paused():
        resume()
    else:
        pause()


def adjust_speed(delta: int) -> None:
    """Increment simulation speed by delta within the valid range."""
    new_speed = max(0, min(3, types.SimSpeed + delta))
    set_speed(new_speed)


def handle_keyboard_shortcut(key_code: int) -> bool:
    """
    Handle global keyboard shortcuts used by pygame front-ends.

    Args:
        key_code: Integer key code (pygame-compatible)

    Returns:
        True if the key was handled, False otherwise.
    """
    if key_code in _PAUSE_KEYS:
        toggle_pause()
        return True

    if key_code in _DIRECT_SPEED_KEYS:
        set_speed(_DIRECT_SPEED_KEYS[key_code])
        return True

    if key_code in (ASCII_EQUALS, ASCII_PLUS):
        adjust_speed(1)
        return True

    if key_code in (ASCII_MINUS, ASCII_UNDERSCORE):
        adjust_speed(-1)
        return True

    if key_code in _BUDGET_KEYS:
        _open_budget_window()
        return True

    if key_code in _GRAPH_KEYS:
        toggle_graph_display()
        return True

    if key_code in _EVALUATION_KEYS:
        toggle_evaluation_display()
        return True

    if key_code in _OVERLAY_NEXT_KEYS:
        cycle_map_overlay(1)
        return True

    if key_code in _OVERLAY_PREV_KEYS:
        cycle_map_overlay(-1)
        return True

    return False


def _open_budget_window() -> None:
    """Trigger the budget overlay and pause simulation for interaction."""
    from . import budget

    budget.draw_budget_window()
    budget.show_budget_window_and_start_waiting()


def toggle_graph_display() -> None:
    """
    Toggle graph window visibility and flag a redraw.
    """
    global _graph_display_enabled
    _graph_display_enabled = not _graph_display_enabled
    graphs.set_graph_panel_visible(_graph_display_enabled)
    graphs.request_graph_panel_redraw()
    types.NewGraph = 1


def toggle_evaluation_display() -> None:
    """
    Toggle evaluation panel visibility and request updated data.
    """
    global _evaluation_display_enabled
    _evaluation_display_enabled = not _evaluation_display_enabled
    evaluation_ui.set_evaluation_panel_visible(_evaluation_display_enabled)

    if _evaluation_display_enabled:
        evaluation_ui.do_score_card()
        evaluation_ui.draw_evaluation()
    else:
        evaluation_ui.update_evaluation()


def cycle_map_overlay(direction: int) -> None:
    """
    Cycle through predefined map overlays.

    Args:
        direction: +1 for next overlay, -1 for previous.
    """
    if not _OVERLAY_SEQUENCE:
        return

    global _overlay_index
    _overlay_index = (_overlay_index + direction) % len(_OVERLAY_SEQUENCE)
    set_map_overlay(_OVERLAY_SEQUENCE[_overlay_index])


def set_map_overlay(mode: int) -> None:
    """
    Apply a specific overlay mode to all map views.

    Args:
        mode: Overlay constant (ALMAP, PDMAP, etc.)
    """
    if not types.sim:
        return

    for view in _iter_views(types.sim.map):
        view.map_state = mode
        view.invalid = True

    types.NewMap = 1
    if 0 <= mode < len(types.NewMapFlags):
        types.NewMapFlags[mode] = 1


def _iter_views(head: types.SimView | None):
    """Yield linked SimView objects starting from head."""
    current = head
    while current:
        yield current
        current = current.next


# ============================================================================
# Game Level Management
# ============================================================================

def set_game_level_funds(level: int) -> None:
    """
    Set initial funds based on game difficulty level.

    Ported from SetGameLevelFunds() in w_util.c.

    Args:
        level: Game difficulty level (0=easy, 1=medium, 2=hard)
    """
    if level == 0:
        types.SetFunds(20000)
        set_game_level(0)
    elif level == 1:
        types.SetFunds(10000)
        set_game_level(1)
    elif level == 2:
        types.SetFunds(5000)
        set_game_level(2)
    # Default to easy
    else:
        types.SetFunds(20000)
        set_game_level(0)


def set_game_level(level: int) -> None:
    """
    Set game difficulty level.

    Ported from SetGameLevel() in w_util.c.

    Args:
        level: Game difficulty level (0=easy, 1=medium, 2=hard)
    """
    types.GameLevel = level
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

def set_city_name(name: str) -> None:
    """
    Set city name with validation.

    Ported from setCityName() in w_util.c.
    Sanitizes name by replacing non-alphanumeric characters with underscores.

    Args:
        name: New city name
    """
    # Sanitize name - replace non-alphanumeric with underscores
    sanitized_name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    set_any_city_name(sanitized_name)


def set_any_city_name(name: str) -> None:
    """
    Set city name without validation.

    Ported from setAnyCityName() in w_util.c.

    Args:
        name: New city name
    """
    types.CityName = name
    # In pygame version, this would trigger UI updates
    # For now, just update the name


# ============================================================================
# Time Management
# ============================================================================

def set_year(year: int) -> None:
    """
    Set the current year.

    Ported from SetYear() in w_util.c.
    Prevents year from going negative and updates CityTime accordingly.

    Args:
        year: New year (must be >= StartingYear)
    """
    # Prevent year from going negative
    if year < types.StartingYear:
        year = types.StartingYear

    # Calculate year offset and update CityTime
    year_offset = year - types.StartingYear - (types.CityTime // 48)
    types.CityTime += year_offset * 48

    # In original C code, this calls doTimeStuff()
    # In pygame version, this would trigger time-based updates
    # For now, this is handled by the simulation loop


def current_year() -> int:
    """
    Get the current year.

    Ported from CurrentYear() in w_util.c.

    Returns:
        Current year based on CityTime
    """
    return (types.CityTime // 48) + types.StartingYear


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

def do_new_game() -> None:
    """
    Start a new game.

    Ported from DoNewGame() in w_util.c.
    """
    # In pygame version, this would reset the game state
    # For now, delegate to initialization
    initialization.InitializeSimulation()


# ============================================================================
# Stub Functions (Not implemented in pygame version)
# ============================================================================

def do_generated_city_image(name: str, time: int, pop: int, class_type: str, score: int) -> None:
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


class UIUtilitiesCommand:
    """TCL command interface for UI utilities."""

    def handle_command(self, command: str, *args) -> str:
        """
        Handle TCL UI utility commands.

        Args:
            command: Command name
            *args: Command arguments

        Returns:
            Command result string

        Raises:
            ValueError: For unknown commands or invalid arguments
        """
        if command == "pause":
            pause()
            return ""

        elif command == "resume":
            resume()
            return ""

        elif command == "setspeed":
            if len(args) != 1:
                raise ValueError("Usage: setspeed <speed>")
            speed = int(args[0])
            set_speed(speed)
            return ""

        elif command == "setskips":
            if len(args) != 1:
                raise ValueError("Usage: setskips <skips>")
            skips = int(args[0])
            set_skips(skips)
            return ""

        elif command == "setgamelevelfunds":
            if len(args) != 1:
                raise ValueError("Usage: setgamelevelfunds <level>")
            level = int(args[0])
            set_game_level_funds(level)
            return ""

        elif command == "setgamelevel":
            if len(args) != 1:
                raise ValueError("Usage: setgamelevel <level>")
            level = int(args[0])
            set_game_level(level)
            return ""

        elif command == "setcityname":
            if len(args) != 1:
                raise ValueError("Usage: setcityname <name>")
            name = args[0]
            set_city_name(name)
            return ""

        elif command == "setanycityname":
            if len(args) != 1:
                raise ValueError("Usage: setanycityname <name>")
            name = args[0]
            set_any_city_name(name)
            return ""

        elif command == "setyear":
            if len(args) != 1:
                raise ValueError("Usage: setyear <year>")
            year = int(args[0])
            set_year(year)
            return ""

        elif command == "currentyear":
            return str(current_year())

        elif command == "popupmessage":
            if len(args) != 1:
                raise ValueError("Usage: popupmessage <message>")
            msg = args[0]
            do_pop_up_message(msg)
            return ""

        else:
            raise ValueError(f"Unknown UI utility command: {command}")
