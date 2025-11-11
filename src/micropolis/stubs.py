"""
stubs.py - Stub implementations for unused features

This module provides stub implementations for functions and global variables
that are referenced in the Micropolis codebase but not fully implemented.
These stubs maintain API compatibility while providing minimal functionality.

Adapted from w_stubs.c for the Python port.
"""

import time

from . import types


# ============================================================================
# Global Variables (from w_stubs.c)
# ============================================================================

# Financial variables
TotalFunds: int = 0

# Game state variables
PunishCnt: int = 0
autoBulldoze: int = 0
autoBudget: int = 0
LastMesTime: int = 0
GameLevel: int = 0
InitSimLoad: int = 0
ScenarioID: int = 0
SimSpeed: int = 0
SimMetaSpeed: int = 0
UserSoundOn: int = 0
CityName: str = ""
NoDisasters: int = 0
MesNum: int = 0
EvalChanged: int = 0
flagBlink: int = 0

# Game startup state
startup: int = 0
startup_name: str | None = None

# Timing variables
start_time: float | None = None
_tick_base: float = time.perf_counter()

# Simulation control variables
sim_skips: int = 0
sim_skip: int = 0
sim_paused: int = 0
sim_paused_speed: int = 0
heat_steps: int = 0


# ============================================================================
# Financial Functions
# ============================================================================

def Spend(dollars: int) -> None:
    """
    Spend money from the city funds.

    Args:
        dollars: Amount to spend
    """
    SetFunds(TotalFunds - dollars)


def SetFunds(dollars: int) -> None:
    """
    Set the total city funds.

    Args:
        dollars: New funds amount
    """
    global TotalFunds
    TotalFunds = dollars
    types.UpdateFunds()


# ============================================================================
# Mac Compatibility Functions
# ============================================================================

def TickCount() -> int:
    """
    Get the current tick count (Mac-style timing).

    Returns:
        Current time in ticks (minutes since epoch)
    """
    elapsed = time.perf_counter() - _tick_base
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

def GameStarted() -> None:
    """
    Called when the game has started.
    Handles initial game setup based on startup mode.
    """
    from .tkinter_bridge import invalidate_maps, invalidate_editors
    from .file_io import LoadCity
    from .tkinter_bridge import eval_command

    global startup, startup_name, start_time

    # Invalidate views to force redraw
    invalidate_maps()
    invalidate_editors()

    # Record start time
    start_time = time.time()

    # Handle different startup modes
    if Startup == -2:  # Load a city
        if StartupName and LoadCity(StartupName):
            DoStartLoad()
            StartupName = None
        else:
            StartupName = None
            # Fall through to -1 case
            Startup = -1

    if Startup == -1:  # New city
        if StartupName:
            types.setCityName(StartupName)
            StartupName = None
        else:
            types.setCityName("NowHere")
        DoPlayNewCity()

    elif Startup == 0:  # Really start game
        DoReallyStartGame()

    else:  # Scenario number
        DoStartScenario(Startup)


def DoPlayNewCity() -> None:
    """
    Start a new city game.
    """
    from .tkinter_bridge import eval_command
    eval_command("UIPlayNewCity")


def DoReallyStartGame() -> None:
    """
    Really start the game (after initialization).
    """
    from .tkinter_bridge import eval_command
    eval_command("UIReallyStartGame")


def DoStartLoad() -> None:
    """
    Start loading a saved city.
    """
    from .tkinter_bridge import eval_command
    eval_command("UIStartLoad")


def DoStartScenario(scenario: int) -> None:
    """
    Start a scenario game.

    Args:
        scenario: Scenario number to start
    """
    from .tkinter_bridge import eval_command
    eval_command(f"UIStartScenario {scenario}")


def DropFireBombs() -> None:
    """
    Drop fire bombs (disaster effect).
    """
    from .tkinter_bridge import eval_command
    eval_command("DropFireBombs")


def InitGame() -> None:
    """
    Initialize game state variables.
    """
    global sim_skips, sim_skip, sim_paused, sim_paused_speed, heat_steps

    sim_skips = 0
    sim_skip = 0
    sim_paused = 0
    sim_paused_speed = 0
    heat_steps = 0

    types.setSpeed(0)


def ReallyQuit() -> None:
    """
    Really quit the game.
    """
    from .engine import sim_exit
    sim_exit(0)


# ============================================================================
# Additional Stub Functions
# ============================================================================

def GetGameLevel() -> int:
    """
    Get the current game difficulty level.

    Returns:
        Current game level
    """
    return GameLevel


def SetGameLevel(level: int) -> None:
    """
    Set the game difficulty level.

    Args:
        level: New game level
    """
    global GameLevel
    GameLevel = level


def GetSimSpeed() -> int:
    """
    Get the current simulation speed.

    Returns:
        Current simulation speed
    """
    return SimSpeed


def SetSimSpeed(speed: int) -> None:
    """
    Set the simulation speed.

    Args:
        speed: New simulation speed
    """
    global SimSpeed
    SimSpeed = speed


def GetNoDisasters() -> bool:
    """
    Check if disasters are disabled.

    Returns:
        True if disasters are disabled
    """
    return bool(NoDisasters)


def SetNoDisasters(disabled: bool) -> None:
    """
    Enable or disable disasters.

    Args:
        disabled: True to disable disasters
    """
    global NoDisasters
    NoDisasters = 1 if disabled else 0


def GetAutoBulldoze() -> bool:
    """
    Check if auto-bulldoze is enabled.

    Returns:
        True if auto-bulldoze is enabled
    """
    return bool(autoBulldoze)


def SetAutoBulldoze(enabled: bool) -> None:
    """
    Enable or disable auto-bulldoze.

    Args:
        enabled: True to enable auto-bulldoze
    """
    global autoBulldoze
    autoBulldoze = 1 if enabled else 0


def GetAutoBudget() -> bool:
    """
    Check if auto-budget is enabled.

    Returns:
        True if auto-budget is enabled
    """
    return bool(autoBudget)


def SetAutoBudget(enabled: bool) -> None:
    """
    Enable or disable auto-budget.

    Args:
        enabled: True to enable auto-budget
    """
    global autoBudget
    autoBudget = 1 if enabled else 0


def GetUserSoundOn() -> bool:
    """
    Check if user sound is enabled.

    Returns:
        True if user sound is enabled
    """
    return bool(UserSoundOn)


def SetUserSoundOn(enabled: bool) -> None:
    """
    Enable or disable user sound.

    Args:
        enabled: True to enable user sound
    """
    global UserSoundOn
    UserSoundOn = 1 if enabled else 0


def GetCityName() -> str:
    """
    Get the current city name.

    Returns:
        Current city name
    """
    return CityName or ""


def SetCityName(name: str) -> None:
    """
    Set the city name.

    Args:
        name: New city name
    """
    global CityName
    CityName = name


def GetScenarioID() -> int:
    """
    Get the current scenario ID.

    Returns:
        Current scenario ID
    """
    return ScenarioID


def SetScenarioID(scenario_id: int) -> None:
    """
    Set the scenario ID.

    Args:
        scenario_id: New scenario ID
    """
    global ScenarioID
    ScenarioID = scenario_id


def GetStartupMode() -> int:
    """
    Get the startup mode.

    Returns:
        Current startup mode
    """
    return startup


def SetStartupMode(mode: int) -> None:
    """
    Set the startup mode.

    Args:
        mode: New startup mode
    """
    global startup
    Startup = mode


def GetStartupName() -> str | None:
    """
    Get the startup city name.

    Returns:
        Startup city name or None
    """
    return startup_name


def SetStartupName(name: str | None) -> None:
    """
    Set the startup city name.

    Args:
        name: Startup city name
    """
    global startup_name
    StartupName = name


# ============================================================================
# Placeholder Functions for Future Implementation
# ============================================================================

def PlaceholderFunction(name: str, *args, **kwargs) -> None:
    """
    Placeholder function for future implementation.

    Args:
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

def initialize_stubs() -> None:
    """
    Initialize stub system.
    Called during program startup.
    """
    global start_time
    start_time = time.time()


def cleanup_stubs() -> None:
    """
    Clean up stub system.
    Called during program shutdown.
    """
    pass
