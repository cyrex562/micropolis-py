"""
initialization.py - Simulation initialization for Micropolis Python port

This module contains the initialization functions ported from s_init.c,
responsible for setting up the initial simulation state and resetting components.
"""

import time

import micropolis.constants
from . import types, random, allocation, simulation

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
    random.sim_srand(current_time)
    random.sim_srandom(current_time)


def InitGraphMax() -> None:
    """
    Initialize graph maximum values.

    Sets up the maximum values for graphs based on current game level.
    """
    # Initialize history graph maximums
    types.res_his_max = 0
    types.com_his__max = 0
    types.ind_his_max = 0

    # Initialize graph display maximums
    types.graph_10_max = 0
    types.graph_12_max = 0
    types.res_2_his_max = 0
    types.com_2_his_max = 0
    types.ind_2_his_max = 0


def DestroyAllSprites() -> None:
    """
    Destroy all sprites in the simulation.

    Removes all moving objects (cars, disasters, etc.) from the sprite list.
    """
    if types.sim and types.sim.sprite:
        # Clear the sprite list
        types.sim.sprite = None
        types.sim.sprites = 0


def ResetLastKeys() -> None:
    """
    Reset keyboard state tracking.

    Clears any stored keyboard input state.
    """
    # This would be implemented when keyboard handling is added
    # For now, it's a placeholder
    pass


def DoNewGame() -> None:
    """
    Initialize a new game state.

    Sets up initial game parameters for starting a new city.
    """
    # Set initial game level and scenario
    types.game_level = 0
    types.scenario_id = 0
    types.startup_game_level = 0

    # Initialize city name and file
    types.city_name = "Micropolis"
    types.city_file_name = ""
    types.startup_name = ""

    # Set initial difficulty and disaster settings
    types.no_disasters = 0
    types.auto_bulldoze = 1
    types.auto_budget = 1
    types.auto_go = 0

    # Initialize tool settings
    types.pending_tool = -1
    types.pending_x = 0
    types.pending_y = 0


def DoUpdateHeads() -> None:
    """
    Update display headers.

    Refreshes the UI headers that show current game state.
    """
    # This would update UI components when they're implemented
    # For now, it's a placeholder
    pass


def InitWillStuff() -> None:
    """
    Main initialization function.

    Initializes all simulation state variables and clears data arrays.
    This is called when starting a new game or loading a saved game.
    """
    # Seed random number generator
    RandomlySeedRand()

    # Initialize graph maximums
    InitGraphMax()

    # Initialize effect values
    types.road_effect = 32
    types.police_effect = 1000
    types.fire_effect = 1000

    # Initialize city statistics
    types.city_score = 500
    types.city_pop = -1

    # Initialize time tracking
    types.last_city_time = -1
    types.last_city_year = -1
    types.last_city_month = -1
    types.last_funds = -1

    # Initialize population tracking
    types.last_r = -999999
    types.last_c = -999999
    types.last_i = -999999

    # Initialize override and tool settings
    types.over_ride = 0
    types.pending_tool = -1

    # Initialize message system
    types.mes_num = 0
    types.message_port = 0

    # Initialize financial tracking
    types.road_fund = 0
    types.police_fund = 0
    types.fire_fund = 0

    # Initialize update flags
    types.update_delayed = 0
    types.valve_flag = 1

    # Destroy all sprites
    DestroyAllSprites()

    # Initialize disaster system
    types.disaster_event = 0
    types.tax_flag = 0

    # Clear overlay arrays
    for x in range(micropolis.constants.HWLDX):
        for y in range(micropolis.constants.HWLDY):
            types.pop_density[x][y] = 0
            types.trf_density[x][y] = 0
            types.pollution_mem[x][y] = 0
            types.land_value_mem[x][y] = 0
            types.crime_mem[x][y] = 0

    # Clear terrain memory
    for x in range(micropolis.constants.QWX):
        for y in range(micropolis.constants.QWY):
            types.terrain_mem[x][y] = 0

    # Clear small arrays
    for x in range(micropolis.constants.SM_X):
        for y in range(micropolis.constants.SM_Y):
            types.rate_og_mem[x][y] = 0
            types.fire_rate[x][y] = 0
            types.com_rate[x][y] = 0
            types.police_map[x][y] = 0
            types.police_map_effect[x][y] = 0
            # Note: FireRate is set twice in original C code, keeping both
            types.fire_rate[x][y] = 0

    # Reset keyboard state
    ResetLastKeys()

    # Initialize new game
    DoNewGame()

    # Update display headers
    DoUpdateHeads()


def ResetMapState() -> None:
    """
    Reset all map view states to default.

    Sets all map views to show the "all" overlay mode.
    """
    if not types.sim:
        return

    view = types.sim.map
    while view:
        view.map_state = micropolis.constants.ALMAP
        view = view.next


def ResetEditorState() -> None:
    """
    Reset all editor view tool states to default.

    Sets all editor views to use the bulldozer tool.
    """
    if not types.sim:
        return

    view = types.sim.editor
    while view:
        view.tool_state = types.DOZE_STATE
        view.tool_state_save = -1
        view = view.next


# ============================================================================
# Additional Initialization Helpers
# ============================================================================


def InitializeSimulation() -> bool:
    """
    Complete simulation initialization sequence.

    This function should be called once at program startup to set up
    the entire simulation environment.

    Returns:
        True if initialization successful, False otherwise
    """
    try:
        # Initialize memory arrays
        result = allocation.init_map_arrays()
        if result != 0:
            print("Failed to initialize map arrays", file=__import__("sys").stderr)
            return False

        # Initialize simulation state
        InitWillStuff()

        # Reset view states
        ResetMapState()
        ResetEditorState()

        return True

    except Exception as e:
        print(
            f"Error during simulation initialization: {e}",
            file=__import__("sys").stderr,
        )
        return False


def InitGame() -> None:
    """
    Legacy entry point that performs a full new-game initialization sequence.
    """
    if not InitializeSimulation():
        return

    InitFundingLevel()
    simulation.do_sim_init(context)
    types.init_sim_load = 2
    types.do_initial_eval = 0


def ResetSimulation() -> None:
    """
    Reset the simulation to initial state.

    This can be called to restart the simulation without reinitializing memory.
    """
    InitWillStuff()
    ResetMapState()
    ResetEditorState()


def InitFundingLevel() -> None:
    """
    Initialize funding levels for city services.

    Sets up the initial budget allocations for police, fire, and road services.
    """
    # Set default funding levels
    types.road_percent = 1.0
    types.police_percent = 0.0
    types.fire_percent = 0.0

    # Set maximum values
    types.road_max_value = 100
    types.police_max_value = 100
    types.fire_max_value = 100

    # Set effects
    types.road_effect = 32
    types.police_effect = 1000
    types.fire_effect = 1000

    # Initialize tax and fund values
    types.city_tax = 7
    types.road_fund = 0
    types.police_fund = 0
    types.fire_fund = 0
    types.tax_fund = 0
