"""
stubs.py - Stub implementations for unused features

This module provides stub implementations for functions and global variables
that are referenced in the Micropolis codebase but not fully implemented.
These stubs maintain API compatibility while providing minimal functionality.

Adapted from w_stubs.c for the Python port.
"""

import time

from src.micropolis.context import AppContext
from src.micropolis.updates import UpdateFunds
from .engine import sim_exit
from .sim_control import set_city_name
from .tkinter_bridge import invalidate_maps, invalidate_editors
from .file_io import LoadCity
from .tkinter_bridge import eval_command
from .ui_utilities import set_speed


# ============================================================================
# Global Variables (from w_stubs.c)
# ============================================================================




# ============================================================================
# Financial Functions
# ============================================================================

def Spend(context: AppContext,dollars: int) -> None:
    """
    Spend money from the city funds.

    Args:
        dollars: Amount to spend
        :param context:
    """
    SetFunds(context.total_funds - dollars)


def SetFunds(context: AppContext,dollars: int) -> None:
    """
    Set the total city funds.

    Args:
        dollars: New funds amount
    """
    # global total_funds
    context.total_funds = dollars
    UpdateFunds()


# ============================================================================
# Mac Compatibility Functions
# ============================================================================

def TickCount(context: AppContext) -> int:
    """
    Get the current tick count (Mac-style timing).

    Returns:
        Current time in ticks (minutes since epoch)
    """
    elapsed = time.perf_counter() - context._tick_base
    return int(elapsed * 60)


def NewPtr(size: int) -> bytes | None:
    """
    Allocate a new pointer (Mac-style memory allocation).

    Args:
        size: Size in bytes to allocate

    Returns:
        Allocated byte buffer or None if allocation fails
    """
    try:
        return bytes(size)
    except (MemoryError, OverflowError):
        return None


# ============================================================================
# Game Lifecycle Functions
# ============================================================================

def GameStarted(context: AppContext) -> None:
    """
    Called when the game has started.
    Handles initial game setup based on startup mode.
    """


    # global startup, startup_name, start_time

    # Invalidate views to force redraw
    invalidate_maps()
    invalidate_editors()

    # Record start time
    start_time = time.time()

    # Handle different startup modes
    if context.startup == -2:  # Load a city
        if context.startup_name and LoadCity(context, context.startup_name):
            DoStartLoad()
            context.startup_name = None
        else:
            context.startup_name = None
            # Fall through to -1 case
            context.startup = -1

    if context.startup == -1:  # New city
        if context.startup_name:
            set_city_name(context.startup_name)
            context.startup_name = None
        else:
            set_city_name(context, "NowHere")
        DoPlayNewCity()

    elif context.startup == 0:  # Really start game
        DoReallyStartGame()

    else:  # Scenario number
        DoStartScenario(context.startup)


def DoPlayNewCity(context: AppContext) -> None:
    """
    Start a new city game.
    """

    eval_command(context, "UIPlayNewCity")


def DoReallyStartGame(context: AppContext) -> None:
    """
    Really start the game (after initialization).
    """
    eval_command(context, "UIReallyStartGame")


def DoStartLoad(context: AppContext) -> None:
    """
    Start loading a saved city.
    """
    eval_command(context, "UIStartLoad")


def DoStartScenario(context: AppContext, scenario: int) -> None:
    """
    Start a scenario game.

    Args:
        scenario: Scenario number to start
    """
    eval_command(context, f"UIStartScenario {scenario}")


def DropFireBombs(context: AppContext) -> None:
    """
    Drop fire bombs (disaster effect).
    """
    eval_command(context, "DropFireBombs")


def InitGame(context: AppContext) -> None:
    """
    Initialize game state variables.
    """
    # global sim_skips, sim_skip, sim_paused, sim_paused_speed, heat_steps

    context.sim_skips = 0
    context.sim_skip = 0
    context.sim_paused = 0
    context.sim_paused_speed = 0
    context.heat_steps = 0

    set_speed(context, 0)


def ReallyQuit(context: AppContext) -> None:
    """
    Really quit the game.
    """
    # from .engine import sim_exit
    sim_exit(context, 0)


# ============================================================================
# Additional Stub Functions
# ============================================================================

def GetGameLevel(context: AppContext) -> int:
    """
    Get the current game difficulty level.

    Returns:
        Current game level
    """
    return context.game_level


def SetGameLevel(context: AppContext, level: int) -> None:
    """
    Set the game difficulty level.

    Args:
        level: New game level
    """
    # global GameLevel
    context.game_level = level


def GetSimSpeed(context: AppContext) -> int:
    """
    Get the current simulation speed.

    Returns:
        Current simulation speed
        :param context:
    """
    return context.sim_speed


def SetSimSpeed(context: AppContext, speed: int) -> None:
    """
    Set the simulation speed.

    Args:
        speed: New simulation speed
    """
    # global SimSpeed
    context.sim_speed = speed


def GetNoDisasters(context: AppContext) -> bool:
    """
    Check if disasters are disabled.

    Returns:
        True if disasters are disabled
    """
    return context.no_disasters


def SetNoDisasters(context: AppContext, disabled: bool) -> None:
    """
    Enable or disable disasters.

    Args:
        disabled: True to disable disasters
    """
    # global no_disasters
    context.no_disasters = 1 if disabled else 0


def GetAutoBulldoze(context: AppContext) -> bool:
    """
    Check if auto-bulldoze is enabled.

    Returns:
        True if auto-bulldoze is enabled
    """
    return context.auto_bulldoze


def SetAutoBulldoze(context: AppContext, enabled: bool) -> None:
    """
    Enable or disable auto-bulldoze.

    Args:
        enabled: True to enable auto-bulldoze
    """
    # global auto_bulldoze
    context.auto_bulldoze = 1 if enabled else 0


def GetAutoBudget(context: AppContext) -> bool:
    """
    Check if auto-budget is enabled.

    Returns:
        True if auto-budget is enabled
    """
    return context.auto_budget


def SetAutoBudget(context: AppContext, enabled: bool) -> None:
    """
    Enable or disable auto-budget.

    Args:
        enabled: True to enable auto-budget
    """
    # global auto_budget
    context.auto_budget = 1 if enabled else 0


def GetUserSoundOn(context: AppContext) -> bool:
    """
    Check if user sound is enabled.

    Returns:
        True if user sound is enabled
    """
    return context.user_sound_on


def SetUserSoundOn(context: AppContext, enabled: bool) -> None:
    """
    Enable or disable user sound.

    Args:
        enabled: True to enable user sound
    """
    # global user_sound_on
    context.user_sound_on = 1 if enabled else 0


def GetCityName(context: AppContext) -> str:
    """
    Get the current city name.

    Returns:
        Current city name
    """
    return context.city_name or ""


def SetCityName(context: AppContext, name: str) -> None:
    """
    Set the city name.

    Args:
        name: New city name
    """
    # global CityName
    context.city_name = name


def GetScenarioID(context: AppContext) -> int:
    """
    Get the current scenario ID.

    Returns:
        Current scenario ID
    """
    return context.scenario_id


def SetScenarioID(context: AppContext, scenario_id: int) -> None:
    """
    Set the scenario ID.

    Args:
        scenario_id: New scenario ID
        :param context:
    """
    # global scenario_id
    context.scenario_id = scenario_id


def GetStartupMode(context: AppContext) -> int:
    """
    Get the startup mode.

    Returns:
        Current startup mode
    """
    return context.startup


def SetStartupMode(context: AppContext, mode: int) -> None:
    """
    Set the startup mode.

    Args:
        mode: New startup mode
    """
    # global startup
    context.startup = mode


def GetStartupName(context: AppContext) -> str | None:
    """
    Get the startup city name.

    Returns:
        Startup city name or None
    """
    return context.startup_name


def SetStartupName(context: AppContext, name: str | None) -> None:
    """
    Set the startup city name.

    Args:
        name: Startup city name
    """
    # global startup_name
    context.startup_name = name


# ============================================================================
# Placeholder Functions for Future Implementation
# ============================================================================

def PlaceholderFunction(context: AppContext, name: str, *args, **kwargs) -> None:
    """
    Placeholder function for future implementation.

    Args:
        context: Application context
        name: Function name for logging
        *args: Positional arguments
        **kwargs: Keyword arguments
    """
    # This function can be used as a placeholder for any unimplemented functions
    # It silently does nothing but could be extended to log calls for debugging
    pass


# ============================================================================
# Initialization
# ============================================================================

def initialize_stubs(context: AppContext) -> None:
    """
    Initialize stub system.
    Called during program startup.
    """
    # global start_time
    context.start_time = time.time()


def cleanup_stubs(context: AppContext) -> None:
    """
    Clean up stub system.
    Called during program shutdown.
    """
    pass
