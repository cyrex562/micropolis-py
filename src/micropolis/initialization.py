"""
initialization.py - Simulation initialization for Micropolis Python port

This module contains the initialization functions ported from s_init.c,
responsible for setting up the initial simulation state and resetting components.
"""

import time
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
    types.ResHisMax = 0
    types.ComHisMax = 0
    types.IndHisMax = 0

    # Initialize graph display maximums
    types.Graph10Max = 0
    types.Graph120Max = 0
    types.Res2HisMax = 0
    types.Com2HisMax = 0
    types.Ind2HisMax = 0

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
    types.GameLevel = 0
    types.ScenarioID = 0
    types.StartupGameLevel = 0

    # Initialize city name and file
    types.CityName = "Micropolis"
    types.CityFileName = ""
    types.StartupName = ""

    # Set initial difficulty and disaster settings
    types.NoDisasters = 0
    types.autoBulldoze = 1
    types.autoBudget = 1
    types.autoGo = 0

    # Initialize tool settings
    types.PendingTool = -1
    types.PendingX = 0
    types.PendingY = 0

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
    types.RoadEffect = 32
    types.PoliceEffect = 1000
    types.FireEffect = 1000

    # Initialize city statistics
    types.CityScore = 500
    types.CityPop = -1

    # Initialize time tracking
    types.LastCityTime = -1
    types.LastCityYear = -1
    types.LastCityMonth = -1
    types.LastFunds = -1

    # Initialize population tracking
    types.LastR = -999999
    types.LastC = -999999
    types.LastI = -999999

    # Initialize override and tool settings
    types.OverRide = 0
    types.PendingTool = -1

    # Initialize message system
    types.MesNum = 0
    types.MessagePort = 0

    # Initialize financial tracking
    types.RoadFund = 0
    types.PoliceFund = 0
    types.FireFund = 0

    # Initialize update flags
    types.UpdateDelayed = 0
    types.ValveFlag = 1

    # Destroy all sprites
    DestroyAllSprites()

    # Initialize disaster system
    types.DisasterEvent = 0
    types.TaxFlag = 0

    # Clear overlay arrays
    for x in range(types.HWLDX):
        for y in range(types.HWLDY):
            types.PopDensity[x][y] = 0
            types.TrfDensity[x][y] = 0
            types.PollutionMem[x][y] = 0
            types.LandValueMem[x][y] = 0
            types.CrimeMem[x][y] = 0

    # Clear terrain memory
    for x in range(types.QWX):
        for y in range(types.QWY):
            types.TerrainMem[x][y] = 0

    # Clear small arrays
    for x in range(types.SmX):
        for y in range(types.SmY):
            types.RateOGMem[x][y] = 0
            types.FireRate[x][y] = 0
            types.ComRate[x][y] = 0
            types.PoliceMap[x][y] = 0
            types.PoliceMapEffect[x][y] = 0
            # Note: FireRate is set twice in original C code, keeping both
            types.FireRate[x][y] = 0

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
        view.map_state = types.ALMAP
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
        view.tool_state = types.dozeState
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
        result = allocation.initMapArrays()
        if result != 0:
            print("Failed to initialize map arrays", file=__import__('sys').stderr)
            return False

        # Initialize simulation state
        InitWillStuff()

        # Reset view states
        ResetMapState()
        ResetEditorState()

        return True

    except Exception as e:
        print(f"Error during simulation initialization: {e}", file=__import__('sys').stderr)
        return False


def InitGame() -> None:
    """
    Legacy entry point that performs a full new-game initialization sequence.
    """
    if not InitializeSimulation():
        return

    InitFundingLevel()
    simulation.DoSimInit()
    types.InitSimLoad = 2
    types.DoInitialEval = 0


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
    types.roadPercent = 1.0
    types.policePercent = 0.0
    types.firePercent = 0.0

    # Set maximum values
    types.roadMaxValue = 100
    types.policeMaxValue = 100
    types.fireMaxValue = 100

    # Set effects
    types.RoadEffect = 32
    types.PoliceEffect = 1000
    types.FireEffect = 1000

    # Initialize tax and fund values
    types.CityTax = 7
    types.RoadFund = 0
    types.PoliceFund = 0
    types.FireFund = 0
    types.TaxFund = 0
