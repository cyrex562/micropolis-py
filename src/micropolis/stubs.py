"""
stubs.py - Stub implementations for unused features

This module provides stub implementations for functions and global variables
that are referenced in the Micropolis codebase but not fully implemented.
These stubs maintain API compatibility while providing minimal functionality.

Adapted from w_stubs.c for the Python port.
"""

import time

from micropolis.context import AppContext
from micropolis.updates import UpdateFunds
from . import engine
from . import sim_control
from .sim_control import set_city_name
from . import tkinter_bridge as tkbridge
from .file_io import LoadCity


# ============================================================================
# Global Variables (from w_stubs.c)
# ============================================================================

# ============================================================================  
# Global Variables (from w_stubs.c)
# These module-level names provide conservative, test-only compatibility
# for legacy call-sites and tests that expect module globals. During
# migration the canonical storage is `AppContext` but tests call the
# legacy API shapes (no explicit context). We keep module-level copies
# and synchronize them in the functions below. These are safe for tests
# and will not be used by production code which should pass an AppContext.
# ============================================================================

total_funds: int = 0
TotalFunds = total_funds

# Game state / flags
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

# Startup
Startup: int = 0
StartupName: str | None = None

# Timing
start_time: float | None = None

# Legacy API compatibility helpers -----------------------------------------

# Provide a `types` alias that mirrors the legacy `LegacyTypes` interface
# so tests can patch `src.micropolis.stubs.types` without breaking the
# production code that continues to import `micropolis.sim_control`.
types = sim_control.types

# Simulation control counters
sim_skips: int = 0
sim_skip: int = 0
sim_paused: int = 0
sim_paused_speed: int = 0
heat_steps: int = 0


# ============================================================================
# Financial Functions
# ============================================================================


def Spend(context: AppContext, dollars: int) -> None:
    """
    Spend money from the city funds.

    Args:
        dollars: Amount to spend
        :param context:
    """
    SetFunds(context.total_funds - dollars)


def SetFunds(context: AppContext, dollars: int) -> None:
    """
    Set the total city funds.

    Args:
        dollars: New funds amount
    """
    # Update canonical AppContext and module-level alias for tests
    global total_funds, TotalFunds
    if isinstance(context, AppContext):
        context.total_funds = dollars
    total_funds = dollars
    TotalFunds = total_funds
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
    # Call through the module so unit-test patches on
    # `src.micropolis.tkinter_bridge.invalidate_maps` and
    # `invalidate_editors` are observed by this code.
    tkbridge.invalidate_maps()
    tkbridge.invalidate_editors()

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
            types.setCityName(context.startup_name)
            set_city_name(context, context.startup_name)
            context.startup_name = None
        else:
            types.setCityName("NowHere")
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

    # Call through the tkinter_bridge module so test patches attach
    tkbridge.eval_command("UIPlayNewCity")


def DoReallyStartGame(context: AppContext) -> None:
    """
    Really start the game (after initialization).
    """
    tkbridge.eval_command("UIReallyStartGame")


def DoStartLoad(context: AppContext) -> None:
    """
    Start loading a saved city.
    """
    tkbridge.eval_command("UIStartLoad")


def DoStartScenario(context: AppContext, scenario: int) -> None:
    """
    Start a scenario game.

    Args:
        scenario: Scenario number to start
    """
    tkbridge.eval_command(f"UIStartScenario {scenario}")


def DropFireBombs(context: AppContext) -> None:
    """
    Drop fire bombs (disaster effect).
    """
    tkbridge.eval_command("DropFireBombs")


def InitGame(context: AppContext) -> None:
    """
    Initialize game state variables.
    """
    # global sim_skips, sim_skip, sim_paused, sim_paused_speed, heat_steps
    global sim_skips, sim_skip, sim_paused, sim_paused_speed, heat_steps

    sim_skips = 0
    sim_skip = 0
    sim_paused = 0
    sim_paused_speed = 0
    heat_steps = 0

    if isinstance(context, AppContext):
        context.sim_skips = 0
        context.sim_skip = 0
        context.sim_paused = 0
        context.sim_paused_speed = 0
        context.heat_steps = 0

    # Set speed through ui_utilities
    try:
        from .ui_utilities import set_speed

        set_speed(context, 0)
    except Exception:
        pass

    try:
        types.setSpeed(0)
    except Exception:
        pass


def ReallyQuit(context: AppContext) -> None:
    """
    Really quit the game.
    """
    # Use the engine module attribute so tests that patch
    # `src.micropolis.engine.sim_exit` are effective.
    engine.sim_exit(0)


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
    global GameLevel
    if isinstance(context, AppContext):
        context.game_level = level
    GameLevel = level


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
    global SimSpeed
    if isinstance(context, AppContext):
        context.sim_speed = speed
    SimSpeed = speed


def GetNoDisasters(context: AppContext) -> bool:
    """
    Check if disasters are disabled.

    Returns:
        True if disasters are disabled
    """
    # Ensure boolean return for tests that assert `is True/False`.
    return bool(context.no_disasters)


def SetNoDisasters(context: AppContext, disabled: bool) -> None:
    """
    Enable or disable disasters.

    Args:
        disabled: True to disable disasters
    """
    global NoDisasters
    if isinstance(context, AppContext):
        context.no_disasters = 1 if disabled else 0
    NoDisasters = 1 if disabled else 0


def GetAutoBulldoze(context: AppContext) -> bool:
    """
    Check if auto-bulldoze is enabled.

    Returns:
        True if auto-bulldoze is enabled
    """
    return bool(context.auto_bulldoze)


def SetAutoBulldoze(context: AppContext, enabled: bool) -> None:
    """
    Enable or disable auto-bulldoze.

    Args:
        enabled: True to enable auto-bulldoze
    """
    global autoBulldoze
    if isinstance(context, AppContext):
        context.auto_bulldoze = 1 if enabled else 0
    autoBulldoze = 1 if enabled else 0


def GetAutoBudget(context: AppContext) -> bool:
    """
    Check if auto-budget is enabled.

    Returns:
        True if auto-budget is enabled
    """
    return bool(context.auto_budget)


def SetAutoBudget(context: AppContext, enabled: bool) -> None:
    """
    Enable or disable auto-budget.

    Args:
        enabled: True to enable auto-budget
    """
    global autoBudget
    if isinstance(context, AppContext):
        context.auto_budget = 1 if enabled else 0
    autoBudget = 1 if enabled else 0


def GetUserSoundOn(context: AppContext) -> bool:
    """
    Check if user sound is enabled.

    Returns:
        True if user sound is enabled
    """
    return bool(context.user_sound_on)


def SetUserSoundOn(context: AppContext, enabled: bool) -> None:
    """
    Enable or disable user sound.

    Args:
        enabled: True to enable user sound
    """
    global UserSoundOn
    if isinstance(context, AppContext):
        context.user_sound_on = 1 if enabled else 0
    UserSoundOn = 1 if enabled else 0


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
    global CityName
    if isinstance(context, AppContext):
        context.city_name = name
    CityName = name


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
    global ScenarioID
    if isinstance(context, AppContext):
        context.scenario_id = scenario_id
    ScenarioID = scenario_id


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
    global Startup
    if isinstance(context, AppContext):
        context.startup = mode
    Startup = mode


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
    global StartupName
    if isinstance(context, AppContext):
        context.startup_name = name
    StartupName = name


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
    global start_time
    start_time = time.time()
    if isinstance(context, AppContext):
        context.start_time = start_time


def cleanup_stubs(context: AppContext) -> None:
    """
    Clean up stub system.
    Called during program shutdown.
    """
    pass


# ------------------------------------------------------------------
# Test-only wrappers to support legacy call-shapes (no explicit context)
# These wrappers rely on the test fixture `micropolis._AUTO_TEST_CONTEXT`
# being set by `tests/conftest.py`'s autouse fixture. They do NOT relax
# the canonical APIs used in production.
# ------------------------------------------------------------------


def _get_auto_ctx() -> AppContext | None:
    try:
        from micropolis import _AUTO_TEST_CONTEXT

        return _AUTO_TEST_CONTEXT
    except Exception:
        return None


def _make_optional_context(fn):
    """Return a wrapper that inserts the autouse test context when the
    wrapped function was called without an AppContext as the first argument.
    """
    from functools import wraps

    @wraps(fn)
    def _wrapper(*args, **kwargs):
        if len(args) == 0 or not isinstance(args[0], AppContext):
            ctx = _get_auto_ctx()
            if ctx is None:
                # No auto context available — assume caller intended to pass
                # a context and let Python raise the usual TypeError.
                return fn(*args, **kwargs)
            return fn(ctx, *args, **kwargs)
        return fn(*args, **kwargs)

    return _wrapper


# Now wrap public functions so tests can call them without context.
Spend = _make_optional_context(Spend)
SetFunds = _make_optional_context(SetFunds)
TickCount = _make_optional_context(TickCount)
GameStarted = _make_optional_context(GameStarted)
DoPlayNewCity = _make_optional_context(DoPlayNewCity)
DoReallyStartGame = _make_optional_context(DoReallyStartGame)
DoStartLoad = _make_optional_context(DoStartLoad)
DoStartScenario = _make_optional_context(DoStartScenario)
DropFireBombs = _make_optional_context(DropFireBombs)
InitGame = _make_optional_context(InitGame)
ReallyQuit = _make_optional_context(ReallyQuit)
GetGameLevel = _make_optional_context(GetGameLevel)
SetGameLevel = _make_optional_context(SetGameLevel)
GetSimSpeed = _make_optional_context(GetSimSpeed)
SetSimSpeed = _make_optional_context(SetSimSpeed)
GetNoDisasters = _make_optional_context(GetNoDisasters)
SetNoDisasters = _make_optional_context(SetNoDisasters)
GetAutoBulldoze = _make_optional_context(GetAutoBulldoze)
SetAutoBulldoze = _make_optional_context(SetAutoBulldoze)
GetAutoBudget = _make_optional_context(GetAutoBudget)
SetAutoBudget = _make_optional_context(SetAutoBudget)
GetUserSoundOn = _make_optional_context(GetUserSoundOn)
SetUserSoundOn = _make_optional_context(SetUserSoundOn)
GetCityName = _make_optional_context(GetCityName)
SetCityName = _make_optional_context(SetCityName)
GetScenarioID = _make_optional_context(GetScenarioID)
SetScenarioID = _make_optional_context(SetScenarioID)
GetStartupMode = _make_optional_context(GetStartupMode)
SetStartupMode = _make_optional_context(SetStartupMode)
GetStartupName = _make_optional_context(GetStartupName)
SetStartupName = _make_optional_context(SetStartupName)
initialize_stubs = _make_optional_context(initialize_stubs)
cleanup_stubs = _make_optional_context(cleanup_stubs)
