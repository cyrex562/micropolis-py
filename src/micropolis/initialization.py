"""
initialization.py - Simulation initialization for Micropolis Python port

This module contains the initialization functions ported from s_init.c,
responsible for setting up the initial simulation state and resetting components.
"""

import time

from src.micropolis.allocation import init_map_arrays
from src.micropolis.constants import (
    HWLDX,
    HWLDY,
    QWX,
    QWY,
    SM_X,
    SM_Y,
    ALMAP,
    DOZE_STATE,
)
from src.micropolis.context import AppContext
from src.micropolis.random import sim_srand, sim_srandom
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # type-only import to avoid circular import at module import time
    from src.micropolis.simulation import do_sim_init


# ============================================================================
# Initialization Functions
# ============================================================================


def RandomlySeedRand() -> None:
    """
    Seed the random number generator with current time.

    This provides a different seed each time the program runs.
    """
    # Use current time as seed for reproducibility testing
    # In production, you might want to use a more random seed
    current_time = int(time.time())
    sim_srand(current_time)
    sim_srandom(context, current_time)


def InitGraphMax(context: AppContext) -> None:
    """
    Initialize graph maximum values.

    Sets up the maximum values for graphs based on current game level.
    :param context:
    """
    # Initialize history graph maximums
    context.res_his_max = 0
    context.com_his__max = 0
    context.ind_his_max = 0

    # Initialize graph display maximums
    context.graph_10_max = 0
    context.graph_12_max = 0
    context.res_2_his_max = 0
    context.com_2_his_max = 0
    context.ind_2_his_max = 0


def DestroyAllSprites(context: AppContext) -> None:
    """
    Destroy all sprites in the simulation.

    Removes all moving objects (cars, disasters, etc.) from the sprite list.
    :param context:
    """
    if context.sim and context.sim.sprite:
        # Clear the sprite list
        context.sim.sprite = None
        context.sim.sprites = 0


def ResetLastKeys() -> None:
    """
    Reset keyboard state tracking.

    Clears any stored keyboard input state.
    """
    # This would be implemented when keyboard handling is added
    # For now, it's a placeholder
    pass


def DoNewGame(context: AppContext) -> None:
    """
    Initialize a new game state.

    Sets up initial game parameters for starting a new city.
    :param context:
    """
    # Set initial game level and scenario
    context.game_level = 0
    context.scenario_id = 0
    context.startup_game_level = 0

    # Initialize city name and file
    context.city_name = "Micropolis"
    context.city_file_name = ""
    context.startup_name = ""

    # Set initial difficulty and disaster settings
    context.no_disasters = False
    context.auto_bulldoze = True
    context.auto_budget = True
    context.auto_go = False

    # Initialize tool settings
    context.pending_tool = -1
    context.pending_x = 0
    context.pending_y = 0


def DoUpdateHeads(context: AppContext) -> None:
    """
    Update display headers.

    Refreshes the UI headers that show current game state.
    :param context:
    """
    # This would update UI components when they're implemented
    # For now, it's a placeholder
    pass


def InitWillStuff(context: AppContext) -> None:
    """
    Main initialization function.

    Initializes all simulation state variables and clears data arrays.
    This is called when starting a new game or loading a saved game.
    """
    # Seed random number generator
    RandomlySeedRand()

    # Initialize graph maximums
    InitGraphMax(context)

    # Initialize effect values
    context.road_effect = 32
    context.police_effect = 1000
    context.fire_effect = 1000

    # Initialize city statistics
    context.city_score = 500
    context.city_pop = -1

    # Initialize time tracking
    context.last_city_time = -1
    context.last_city_year = -1
    context.last_city_month = -1
    context.last_funds = -1

    # Initialize population tracking
    context.last_r = -999999
    context.last_c = -999999
    context.last_i = -999999

    # Initialize override and tool settings
    context.over_ride = 0
    context.pending_tool = -1

    # Initialize message system
    context.mes_num = 0
    context.message_port = 0

    # Initialize financial tracking
    context.road_fund = 0
    context.police_fund = 0
    context.fire_fund = 0

    # Initialize update flags
    context.update_delayed = 0
    context.valve_flag = 1

    # Destroy all sprites
    DestroyAllSprites(context)

    # Initialize disaster system
    context.disaster_event = 0
    context.tax_flag = 0

    # Clear overlay arrays
    for x in range(HWLDX):
        for y in range(HWLDY):
            context.pop_density[x][y] = 0
            context.trf_density[x][y] = 0
            context.pollution_mem[x][y] = 0
            context.land_value_mem[x][y] = 0
            context.crime_mem[x][y] = 0

    # Clear terrain memory
    for x in range(QWX):
        for y in range(QWY):
            context.terrain_mem[x][y] = 0

    # Clear small arrays
    for x in range(SM_X):
        for y in range(SM_Y):
            context.rate_og_mem[x][y] = 0
            context.fire_rate[x][y] = 0
            context.com_rate[x][y] = 0
            context.police_map[x][y] = 0
            context.police_map_effect[x][y] = 0
            # Note: FireRate is set twice in original C code, keeping both
            context.fire_rate[x][y] = 0

    # Reset keyboard state
    ResetLastKeys()

    # Initialize new game
    DoNewGame(context)

    # Update display headers
    DoUpdateHeads(context)


def ResetMapState(context: AppContext) -> None:
    """
    Reset all map view states to default.

    Sets all map views to show the "all" overlay mode.
    :param context:
    """
    if not context.sim:
        return

    view = context.sim.map
    while view:
        view.map_state = ALMAP
        view = view.next


def ResetEditorState(context: AppContext) -> None:
    """
    Reset all editor view tool states to default.

    Sets all editor views to use the bulldozer tool.
    """
    if not context.sim:
        return

    view = context.sim.editor
    while view:
        view.tool_state = DOZE_STATE
        view.tool_state_save = -1
        view = view.next


# ============================================================================
# Additional Initialization Helpers
# ============================================================================


def InitializeSimulation(context: AppContext) -> bool:
    """
    Complete simulation initialization sequence.

    This function should be called once at program startup to set up
    the entire simulation environment.

    Returns:
        True if initialization successful, False otherwise
        :param context:
    """
    try:
        # Initialize memory arrays
        result = init_map_arrays(context)
        if result != 0:
            print("Failed to initialize map arrays", file=__import__("sys").stderr)
            return False

        # Initialize simulation state
        InitWillStuff(context)

        # Reset view states
        ResetMapState(context)
        ResetEditorState(context)

        return True

    except Exception as e:
        print(
            f"Error during simulation initialization: {e}",
            file=__import__("sys").stderr,
        )
        return False


def InitGame(context: AppContext) -> None:
    """
    Legacy entry point that performs a full new-game initialization sequence.
    :param context:
    """
    if not InitializeSimulation(context):
        return

    InitFundingLevel(context)
    # Import do_sim_init here to avoid circular import issues
    from src.micropolis.simulation import do_sim_init

    do_sim_init(context)
    context.init_sim_load = 2
    context.do_initial_eval = 0


def ResetSimulation(context: AppContext) -> None:
    """
    Reset the simulation to initial state.

    This can be called to restart the simulation without reinitializing memory.
    :param context:
    """
    InitWillStuff(context)
    ResetMapState(context)
    ResetEditorState(context)


def InitFundingLevel(context: AppContext) -> None:
    """
    Initialize funding levels for city services.

    Sets up the initial budget allocations for police, fire, and road services.
    :param context:
    """
    # Set default funding levels
    context.road_percent = 1.0
    context.police_percent = 0.0
    context.fire_percent = 0.0

    # Set maximum values
    context.road_max_value = 100
    context.police_max_value = 100
    context.fire_max_value = 100

    # Set effects
    context.road_effect = 32
    context.police_effect = 1000
    context.fire_effect = 1000

    # Initialize tax and fund values
    context.city_tax = 7
    context.road_fund = 0
    context.police_fund = 0
    context.fire_fund = 0
    context.tax_fund = 0
