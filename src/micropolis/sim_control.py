"""
sim_control.py - Simulation control and speed management

This module provides simulation control functionality ported from w_sim.c.
It handles game state management, simulation speed control, disaster triggers,
budget management, and various simulation parameters that were exposed
through TCL commands in the original implementation.
"""

from src.micropolis.constants import GOD, COP, WORLD_X, WORLD_Y, DYMAP
from src.micropolis.context import AppContext
from src.micropolis.disasters import create_fire_disaster, start_flood_disaster, spawn_tornado_disaster, \
    trigger_earthquake_disaster, spawn_monster_disaster, trigger_nuclear_meltdown, create_fire_bomb_explosion, \
    create_explosion
from src.micropolis.engine import SetGameLevelFunds, sim_update, ClearMap
from src.micropolis.evaluation import UpdateBudget, GetUnemployment, GetFire, DoBudget, DoBudgetFromMenu
from src.micropolis.evaluation_ui import current_year
from src.micropolis.file_io import save_current_city_state, load_city_from_file
from src.micropolis.generation import GenerateNewCity, GenerateSomeCity, ClearUnnatural, SmoothTrees, SmoothWater, \
    SmoothRiver
from src.micropolis.initialization import InitGame
from src.micropolis.simulation import update_fund_effects, rand, rand16
from src.micropolis.sprite_manager import GetSprite, GenerateCopter
from src.micropolis.traffic import AverageTrf
from src.micropolis.ui_utilities import set_current_year


# ============================================================================
# Simulation Control State
# ============================================================================



# ============================================================================
# Simulation Speed and Timing Functions
# ============================================================================


def get_sim_speed(context: AppContext) -> int:
    """Get the current simulation speed (0-7)
    :param context:
    """
    return context.sim_speed


def set_sim_speed(context: AppContext, speed: int) -> None:
    """Set the simulation speed (0-7)
    :param context:
    """
    # global sim_speed
    if 0 <= speed <= 7:
        context.sim_speed = speed
        # types.sim_speed = speed
        kick()  # Trigger UI updates


def is_sim_paused(context: AppContext) -> bool:
    """Check if simulation is paused
    :param context:
    """
    return context.sim_paused


def pause_simulation(context: AppContext) -> None:
    """Pause the simulation
    :param context:
    """
    # global sim_paused
    context.sim_paused = True
    kick()


def resume_simulation(context: AppContext) -> None:
    """Resume the simulation
    :param context:
    """
    # global sim_paused
    context.sim_paused = False
    kick()


def get_sim_delay(context: AppContext) -> int:
    """Get simulation delay in milliseconds
    :param context:
    """
    return context.sim_delay


def set_sim_delay(context: AppContext, delay: int) -> None:
    """Set simulation delay in milliseconds
    :param context:
    """
    # global sim_delay
    if delay >= 0:
        context.sim_delay = delay
        # types.sim_delay = delay
        kick()


def get_sim_skips(context: AppContext) -> int:
    """Get number of simulation steps to skip
    :param context:
    """
    return context.sim_skips


def set_sim_skips(context: AppContext, skips: int) -> None:
    """Set number of simulation steps to skip"""
    # global sim_skips
    if skips >= 0:
        context.sim_skips = skips
        # types.sim_skips = skips
        kick()


def get_sim_skip(context: AppContext) -> int:
    """Get current skip counter"""
    return context.sim_skip


def set_sim_skip(context: AppContext, skip: int) -> None:
    """Set current skip counter
    :param context:
    """
    # global sim_skip
    if skip >= 0:
        context.sim_skip = skip
        # types.sim_skip = skip


def get_heat_steps(context: AppContext) -> int:
    """Get heat simulation steps
    :param context:
    """
    return context.heat_steps


def set_heat_steps(context: AppContext, steps: int) -> None:
    """Set heat simulation steps
    :param context:
    """
    if steps >= 0:
        context.heat_steps = steps
        kick()


def get_heat_flow(context: AppContext) -> int:
    """Get heat flow setting
    :param context:
    """
    return context.heat_flow


def set_heat_flow(context: AppContext, flow: int) -> None:
    """Set heat flow setting
    :param context:
    """
    context.heat_flow = flow


def get_heat_rule(context: AppContext) -> int:
    """Get heat rule setting
    :param context:
    """
    return context.heat_rule


def set_heat_rule(context: AppContext, rule: int) -> None:
    """Set heat rule setting
    :param context:
    """
    context.heat_rule = rule


# ============================================================================
# Game State Management
# ============================================================================


def is_game_started(context: AppContext) -> bool:
    """Check if game has started
    :param context:
    """
    return context.game_started


def set_game_started(context: AppContext, started: bool = True) -> None:
    """Set game started state
    :param context:
    """
    # global game_started
    context.game_started = started
    if started:
        kick()


def init_game(context: AppContext) -> None:
    """Initialize a new game
    :param context:
    """
    InitGame(context)
    set_game_started(context, True)
    kick()


def save_city(context: AppContext) -> bool:
    """Save the current city
    :param context:
    """
    # This would typically show a save dialog, for now just auto-save
    return save_current_city_state(context, "autosave.cty")


def load_city(context: AppContext, filename: str) -> bool:
    """Load a city from file
    :param context:
    """
    success = load_city_from_file(context, filename)
    if success:
        set_game_started(context, True)
        kick()
    return success


def save_city_as(context: AppContext, filename: str) -> bool:
    """Save city with specific filename
    :param filename:
    :param context:
    """
    return save_current_city_state(context, filename)


def generate_new_city(context: AppContext) -> None:
    """Generate a new random city
    :param context:
    """
    GenerateNewCity(context)
    set_game_started(context, True)
    kick()


def generate_some_city(context: AppContext, level: int) -> None:
    """Generate a city with specific level (0-2)
    :param level:
    :param context:
    """
    if 0 <= level <= 2:
        GenerateSomeCity(context, level)
        set_game_started(context, True)
        kick()


def load_scenario(context: AppContext, scenario_num: int) -> None:
    """Load a scenario
    :param context:
    :param scenario_num:
    """
    # This would load predefined scenarios
    # For now, just generate a new city
    generate_new_city(context)


def get_city_name(context: AppContext) -> str:
    """Get current city name
    :param context:
    """
    return context.city_name


def set_city_name(context: AppContext, name: str) -> None:
    """Set city name
    :param name:
    :param context:
    """
    context.city_name = name


def get_city_file_name(context: AppContext) -> str | None:
    """Get current city file name
    :param context:
    """
    return context.city_file_name


def set_city_file_name(context: AppContext, filename: str | None) -> None:
    """Set city file name
    :param context:
    """
    # if context.city_file_name:
    #     # Free old filename if needed
    #     pass
    context.city_file_name = filename


# ============================================================================
# Disaster Control Functions
# ============================================================================


def make_fire(context: AppContext) -> None:
    """Start a fire disaster
    :param context:
    """
    create_fire_disaster(context)
    kick()


def make_flood(context: AppContext) -> None:
    """Start a flood disaster
    :param context:
    """
    start_flood_disaster(context)
    kick()


def make_tornado() -> None:
    """Start a tornado disaster"""
    spawn_tornado_disaster()
    kick()


def make_earthquake(context: AppContext) -> None:
    """Start an earthquake disaster
    :param context:
    """
    trigger_earthquake_disaster(context)
    kick()


def make_monster(context: AppContext) -> None:
    """Create a monster
    :param context:
    """
    spawn_monster_disaster(context)
    kick()


def make_meltdown(context: AppContext) -> None:
    """Start a nuclear meltdown
    :param context:
    """
    trigger_nuclear_meltdown(context)
    kick()


def fire_bomb(context: AppContext) -> None:
    """Drop a fire bomb (for debugging/testing)"""
    create_fire_bomb_explosion(context)
    kick()


def make_explosion(x: int, y: int) -> None:
    """Create an explosion at coordinates"""
    create_explosion(x, y)
    kick()


def set_monster_goal(context: AppContext, x: int, y: int) -> bool:
    """Set monster movement goal
    :param context:
    """
    # Find monster sprite and set destination
    sprite = GetSprite(context, GOD)
    if sprite is None:
        make_monster(context)
        sprite = GetSprite(context, GOD)
        if sprite is None:
            return False

    sprite.dest_x = x
    sprite.dest_y = y
    sprite.control = -2
    sprite.count = -1
    return True


def set_helicopter_goal(x: int, y: int) -> bool:
    """Set helicopter movement goal"""
    sprite = GetSprite(context, COP)
    if sprite is None:
        # Generate helicopter at position
        GenerateCopter(x, y)
        sprite = GetSprite(context, COP)
        if sprite is None:
            return False

    sprite.dest_x = x
    sprite.dest_y = y
    return True


def set_monster_direction(context: AppContext, direction: int) -> bool:
    """Set monster movement direction (-1 to 7)
    :param direction:
    :param context:
    """
    if not (-1 <= direction <= 7):
        return False

    sprite = GetSprite(context, GOD)
    if sprite is None:
        make_monster(context)
        sprite = GetSprite(context, GOD)
        if sprite is None:
            return False

    sprite.control = direction
    return True


# ============================================================================
# Budget and Finance Functions
# ============================================================================


def get_total_funds(context: AppContext) -> int:
    """Get total city funds
    :param context:
    """
    return context.total_funds


def set_total_funds(context: AppContext, funds: int) -> None:
    """Set total city funds
    :param context:
    """
    if funds >= 0:
        context.total_funds = funds
        context.must_update_funds = 1
        kick()


def get_tax_rate(context: AppContext) -> int:
    """Get current tax rate (0-20)
    :param context:
    """
    return context.city_tax


def set_tax_rate(context: AppContext, tax: int) -> None:
    """Set tax rate (0-20)
    :param context:
    """
    if 0 <= tax <= 20:
        context.city_tax = tax
        # drawBudgetWindow() equivalent would update UI
        kick()


def get_fire_fund_percentage(context: AppContext) -> int:
    """Get fire department funding percentage
    :param context:
    """
    return int(context.fire_percent * 100.0)


def set_fire_fund_percentage(context: AppContext, percent: int) -> None:
    """Set fire department funding percentage (0-100)
    :param context:
    """
    if 0 <= percent <= 100:
        context.fire_percent = percent / 100.0
        context.fire_spend = (context.fire_max_value * percent) // 100
        update_fund_effects(context)
        kick()


def get_police_fund_percentage(context: AppContext) -> int:
    """Get police department funding percentage
    :param context:
    """
    return int(context.police_percent * 100.0)


def set_police_fund_percentage(context: AppContext, percent: int) -> None:
    """Set police department funding percentage (0-100)
    :param context:
    """
    if 0 <= percent <= 100:
        context.police_percent = percent / 100.0
        context.police_spend = (context.police_max_value * percent) // 100
        update_fund_effects(context)
        kick()


def get_road_fund_percentage(context: AppContext) -> int:
    """Get road department funding percentage
    :param context:
    """
    return int(context.road_percent * 100.0)


def set_road_fund_percentage(context: AppContext, percent: int) -> None:
    """Set road department funding percentage (0-100)
    :param context:
    """
    if 0 <= percent <= 100:
        context.road_percent = percent / 100.0
        context.road_spend = (context.road_max_value * percent) // 100
        update_fund_effects(context)
        kick()


def get_game_level(context: AppContext) -> int:
    """Get current game difficulty level (0-2)
    :param context:
    """
    return context.game_level


def set_game_level(context: AppContext, level: int) -> None:
    """Set game difficulty level (0-2)
    :param context:
    """
    if 0 <= level <= 2:
        SetGameLevelFunds(context, level)


def get_year(context: AppContext) -> int:
    """Get current game year
    :param context:
    """
    return current_year(context)


def set_year(context: AppContext, year: int) -> None:
    """Set current game year
    :param year:
    :param context:
    """
    set_current_year(context, year)


def get_auto_budget(context: AppContext) -> bool:
    """Get auto-budget setting
    :param context:
    """
    return context.auto_budget


def set_auto_budget(context: AppContext, enabled: bool) -> None:
    """Set auto-budget setting
    :param context:
    """
    # global auto_budget
    context.auto_budget = enabled
    context.auto_budget = enabled
    context.must_update_options = 1
    kick()
    UpdateBudget()


def get_auto_goto(context: AppContext) -> bool:
    """Get auto-goto setting
    :param context:
    """
    return context.auto_goto


def set_auto_goto(context: AppContext, enabled: bool) -> None:
    """Set auto-goto setting
    :param context:
    """
    # global auto_goto
    context.auto_goto = enabled
    context.auto_go = enabled
    context.must_update_options = 1
    kick()


def get_auto_bulldoze(context: AppContext) -> bool:
    """Get auto-bulldoze setting
    :param context:
    """
    return context.auto_bulldoze


def set_auto_bulldoze(context: AppContext, enabled: bool) -> None:
    """Set auto-bulldoze setting
    :param context:
    """
    # global auto_bulldoze
    context.auto_bulldoze = enabled
    context.auto_bulldoze = enabled
    context.must_update_options = 1
    kick()


# ============================================================================
# Configuration Options
# ============================================================================


def get_disasters_enabled(context: AppContext) -> bool:
    """Get disasters enabled setting
    :param context:
    """
    return not context.no_disasters


def set_disasters_enabled(context: AppContext, enabled: bool) -> None:
    """Set disasters enabled setting
    :param context:
    """
    # global no_disasters
    context.no_disasters = not enabled
    context.no_disasters = context.no_disasters
    context.must_update_options = 1
    kick()


def get_sound_enabled(context: AppContext) -> bool:
    """Get sound enabled setting
    :param context:
    """
    return context.user_sound_on


def set_sound_enabled(context: AppContext, enabled: bool) -> None:
    """Set sound enabled setting
    :param context:
    """
    # global user_sound_on
    context.user_sound_on = enabled
    context.user_sound_on = enabled
    context.must_update_options = 1
    kick()


def sound_off(context: AppContext) -> None:
    """Turn sound off
    :param context:
    """
    set_sound_enabled(context, False)


def get_do_animation(context: AppContext) -> bool:
    """Get animation enabled setting
    :param context:
    """
    return context.do_animation


def set_do_animation(context: AppContext, enabled: bool) -> None:
    """Set animation enabled setting
    :param context:
    """
    # global do_animation
    context.do_animation = enabled
    context.do_animation = enabled
    context.must_update_options = 1
    kick()


def get_do_messages(context: AppContext) -> bool:
    """Get messages enabled setting
    :param context:
    """
    return context.do_messages


def set_do_messages(context: AppContext, enabled: bool) -> None:
    """Set messages enabled setting
    :param context:
    """
    # global do_messages
    context.do_messages = enabled
    context.do_messages = enabled
    context.must_update_options = 1
    kick()


def get_do_notices(context: AppContext) -> bool:
    """Get notices enabled setting
    :param context:
    """
    return context.do_notices


def set_do_notices(context: AppContext, enabled: bool) -> None:
    """Set notices enabled setting
    :param context:
    """
    # global do_notices
    context.do_notices = enabled
    context.do_notices = enabled
    context.must_update_options = 1
    kick()


# ============================================================================
# Bulldozer Control
# ============================================================================


def start_bulldozer() -> None:
    """Start bulldozer tool"""
    StartBulldozer()
    kick()


def stop_bulldozer() -> None:
    """Stop bulldozer tool"""
    StopBulldozer()
    kick()


# ============================================================================
# Map and Terrain Functions
# ============================================================================


def get_tile(context: AppContext, x: int, y: int) -> int:
    """Get tile value at coordinates
    :param context:
    """
    if 0 <= x < WORLD_X and 0 <= y < WORLD_Y:
        return context.map_data[x][y]
    return 0


def set_tile(context: AppContext, x: int, y: int, tile: int) -> None:
    """Set tile value at coordinates
    :param context:
    """
    if 0 <= x < WORLD_X and 0 <= y < WORLD_Y:
        context.map_data[x][y] = tile


def fill_map(context: AppContext, tile: int) -> None:
    """Fill entire map with tile value
    :param tile:
    :param context:
    """
    for x in range(WORLD_X):
        for y in range(WORLD_Y):
            context.map_data[x][y] = tile


def erase_overlay(context: AppContext) -> None:
    """Erase overlay data
    :param context:
    """
    # This would clear overlay visualizations
    pass


def clear_map(context: AppContext) -> None:
    """Clear the map"""
    ClearMap(context)
    kick()


def clear_unnatural(context: AppContext) -> None:
    """Clear unnatural elements from map
    :param context:
    """
    ClearUnnatural(context)
    kick()


def smooth_trees(context: AppContext) -> None:
    """Smooth tree placement
    :param context:
    """
    SmoothTrees(context)
    kick()


def smooth_water(context: AppContext) -> None:
    """Smooth water placement
    :param context:
    """
    SmoothWater(context)
    kick()


def smooth_river(context: AppContext) -> None:
    """Smooth river placement
    :param context:
    """
    SmoothRiver(context)
    kick()


# ============================================================================
# City Statistics and Information
# ============================================================================


def get_land_value(context: AppContext) -> int:
    """Get average land value"""
    return context.lv_average


def get_traffic_average(context: AppContext) -> int:
    """Get average traffic density
    :param context:
    """
    return AverageTrf(context)


def get_crime_average(context: AppContext) -> int:
    """Get average crime rate"""
    return context.crime_average


def get_unemployment_rate(context: AppContext) -> int:
    """Get unemployment rate"""
    return GetUnemployment(context)


def get_fire_coverage(context: AppContext) -> int:
    """Get fire department coverage
    :param context:
    """
    return GetFire(context)


def get_pollution_average(context: AppContext) -> int:
    """Get average pollution level
    :param context:
    """
    return context.pollute_average


def get_population_center(context: AppContext) -> tuple[int, int]:
    """Get population center coordinates"""
    return (context.cc_x << 4) + 8, (context.cc_y << 4) + 8


def get_pollution_center(context: AppContext) -> tuple[int, int]:
    """Get pollution center coordinates
    :param context:
    """
    return (context.pol_max_x << 4) + 8, (context.pol_max_y << 4) + 8


def get_crime_center(context: AppContext) -> tuple[int, int]:
    """Get crime center coordinates
    :param context:
    """
    return (context.crime_max_x << 4) + 8, (context.crime_max_y << 4) + 8


def get_traffic_center(context: AppContext) -> tuple[int, int]:
    """Get traffic center coordinates
    :param context:
    """
    return context.traf_max_x, context.traf_max_y


def get_flood_center(context: AppContext) -> tuple[int, int]:
    """Get flood center coordinates
    :param context:
    """
    return (context.flood_x << 4) + 8, (context.flood_y << 4) + 8


def get_crash_center(context: AppContext) -> tuple[int, int]:
    """Get airplane crash center coordinates
    :param context:
    """
    return (context.crash_x << 4) + 8, (context.crash_y << 4) + 8


def get_meltdown_center(context: AppContext) -> tuple[int, int]:
    """Get nuclear meltdown center coordinates
    :param context:
    """
    return (context.melt_x << 4) + 8, (context.melt_y << 4) + 8


# ============================================================================
# Dynamic Data and Performance
# ============================================================================


def get_dynamic_data(context: AppContext, index: int) -> int:
    """Get dynamic data value at index
    :param context:
    """
    if 0 <= index < 32:
        return context.dynamic_data[index]
    return 0


def set_dynamic_data(context: AppContext, index: int, value: int) -> None:
    """Set dynamic data value at index
    :param context:
    """
    if 0 <= index < 32:
        context.dynamic_data[index] = value
        context.new_map_flags[DYMAP] = 1
        kick()


def reset_dynamic_data(context: AppContext) -> None:
    """Reset dynamic data to defaults
    :param context:
    """
    for i in range(16):
        context.dynamic_data[i] = 99999 if (i & 1) else -99999
    context.new_map_flags[DYMAP] = 1
    kick()


def start_performance_timing(context: AppContext) -> None:
    """Start performance timing measurement
    :param context:
    """
    # global performance_timing, flush_time
    context.performance_timing = True
    context.flush_time = 0.0

    # Reset timing for all views
    view = context.sim.editor
    while view:
        view.updates = 0
        view.update_real = view.update_user = view.update_system = 0.0
        view = view.next


def get_performance_timing(context: AppContext) -> bool:
    """Get performance timing enabled state
    :param context:
    """
    return context.performance_timing


# ============================================================================
# Utility Functions
# ============================================================================


def get_world_size(context: AppContext) -> tuple[int, int]:
    """Get world dimensions
    :param context:
    """
    return WORLD_X, WORLD_Y


def get_override(context: AppContext) -> int:
    """Get override setting
    :param context:
    """
    return context.over_ride


def set_override(context: AppContext, value: int) -> None:
    """Set override setting
    :param context:
    """
    context.over_ride = value


def get_expensive(context: AppContext) -> int:
    """Get expensive setting
    :param context:
    """
    return context.expensive


def set_expensive(context: AppContext, value: int) -> None:
    """Set expensive setting
    :param context:
    """
    context.expensive = value


def get_players(context: AppContext) -> int:
    """Get number of players
    :param context:
    """
    return context.players


def set_players(context: AppContext, count: int) -> None:
    """Set number of players"""
    context.players = count


def get_votes(context: AppContext) -> int:
    """Get votes count
    :param context:
    """
    return context.votes


def set_votes(context: AppContext, count: int) -> None:
    """Set votes count
    :param context:
    """
    context.votes = count


def get_bob_height(context: AppContext) -> int:
    """Get bob height for animations"""
    return context.bob_height


def set_bob_height(context: AppContext, height: int) -> None:
    """Set bob height for animations
    :param context:
    """
    context.bob_height = height


def get_pending_tool(context: AppContext) -> int:
    """Get pending tool"""
    return context.pending_tool


def set_pending_tool(context: AppContext, tool: int) -> None:
    """Set pending tool
    :param context:
    """
    context.pending_tool = tool


def get_pending_position(context: AppContext) -> tuple[int, int]:
    """Get pending tool position
    :param context:
    """
    return context.pending_x, context.pending_y


def set_pending_position(context: AppContext, x: int, y: int) -> None:
    """Set pending tool position
    :param context:
    """
    context.pending_x = x
    context.pending_y = y


def get_displays(context: AppContext) -> str:
    """Get displays information
    :param context:
    """
    return context.displays or ""


def get_multi_player_mode(context: AppContext) -> bool:
    """Get multiplayer mode setting
    :param context:
    """
    return context.multi_player_mode


def get_sugar_mode(context: AppContext) -> bool:
    """Get Sugar mode setting
    :param context:
    """
    return context.sugar_mode


def get_need_rest(context: AppContext) -> bool:
    """Get need rest flag
    :param context:
    """
    return context.need_rest


def set_need_rest(context: AppContext, need_rest: bool) -> None:
    """Set need rest flag
    :param context:
    """
    # global need_rest
    context.need_rest = need_rest



def get_platform() -> str:
    """Get platform string"""
    import platform

    system = platform.system().lower()
    if system == "windows":
        return "msdos"  # For compatibility
    else:
        return "unix"


def get_version(context: AppContext) -> str:
    """Get Micropolis version
    :param context:
    """
    return context.micropolis_version


def get_random_number(context: AppContext, max_val: int | None = None) -> int:
    """Get random number
    :param max_val:
    :param context:
    """
    if max_val is not None:
        return rand(context, context)
    else:
        return rand16(context)


def format_dollars(amount: int) -> str:
    """Format dollar amount as string"""
    # Simple implementation - could be enhanced
    return f"${amount:,}"


def update_simulation(context: AppContext) -> None:
    """Update simulation state
    :param context:
    """
    sim_update(context)


def really_quit() -> None:
    """Handle quit confirmation"""
    # This would typically show a quit dialog
    # For now, just set a flag
    pass


# ============================================================================
# UI Update Triggers
# ============================================================================


def kick() -> None:
    """Trigger UI updates (equivalent to TCL Kick)"""
    # This would trigger updates to all UI components
    # For pygame implementation, this might queue events or set flags
    kick()


def update_heads() -> None:
    """Update header displays"""
    kick()


def update_maps() -> None:
    """Update map displays"""
    kick()


def update_editors() -> None:
    """Update editor displays"""
    kick()


def redraw_maps() -> None:
    """Redraw map displays"""
    kick()


def redraw_editors() -> None:
    """Redraw editor displays"""
    kick()


def update_graphs() -> None:
    """Update graph displays"""
    kick()


def update_evaluation() -> None:
    """Update evaluation displays"""
    kick()


def update_budget() -> None:
    """Update budget displays"""
    UpdateBudget()
    kick()


def update_budget_window() -> None:
    """Update budget window"""
    # drawBudgetWindow() equivalent
    kick()


def do_budget(context: AppContext
              ) -> None:
    """Execute budget calculations"""
    DoBudget(context)
    kick()


def do_budget_from_menu(context: AppContext) -> None:
    """Execute budget from menu
    :param context:
    """
    DoBudgetFromMenu(context)
    kick()


# ============================================================================
# Terrain Generation Parameters
# ============================================================================


def get_lake_level(context: AppContext) -> int:
    """Get lake level for city generation
    :param context:
    """
    return context.lake_level


def set_lake_level(context: AppContext, level: int) -> None:
    """Set lake level for city generation
    :param context:
    """
    context.lake_level = level


def get_tree_level(context: AppContext) -> int:
    """Get tree level for city generation
    :param context:
    """
    return context.tree_level


def set_tree_level(context: AppContext, level: int) -> None:
    """Set tree level for city generation
    :param context:
    """
    context.tree_level = level


def get_curve_level(context: AppContext) -> int:
    """Get curve level for city generation
    :param context:
    """
    return context.curve_level


def set_curve_level(context: AppContext, level: int) -> None:
    """Set curve level for city generation
    :param context:
    """
    context.curve_level = level


def get_create_island(context: AppContext) -> int:
    """Get create island setting
    :param context:
    """
    return context.create_island


def set_create_island(context: AppContext, island: int) -> None:
    """Set create island setting
    :param context:
    """
    context.create_island = island


# ============================================================================
# Display and Rendering Options
# ============================================================================


def get_do_overlay(context: AppContext) -> int:
    """Get overlay display setting
    :param context:
    """
    return context.do_overlay


def set_do_overlay(context: AppContext, overlay: int) -> None:
    """Set overlay display setting
    :param context:
    """
    context.do_overlay = overlay


def get_don_dither(context: AppContext) -> int:
    """Get dithering setting
    :param context:
    """
    return context.don_dither


def set_don_dither(context: AppContext, dither: int) -> None:
    """Set dithering setting
    :param context:
    """
    context.don_dither = dither


def get_flush_style(context: AppContext) -> int:
    """Get flush style setting
    :param context:
    """
    return context.flush_style


def set_flush_style(context: AppContext, style: int) -> None:
    """Set flush style setting"""
    context.flush_style = style


def get_collapse_motion(context: AppContext) -> int:
    """Get collapse motion setting
    :param context:
    """
    return context.tk_collapse_motion


def set_collapse_motion(context: AppContext, motion: int) -> None:
    """Set collapse motion setting"""
    context.tk_collapse_motion = motion


# ============================================================================
# Web and External Functions (Stub implementations)
# ============================================================================


def open_web_browser(url: str) -> int:
    """Open URL in web browser (stub)"""
    import webbrowser

    try:
        webbrowser.open(url)
        return 0
    except Exception:
        return 1


def quote_url(url: str) -> str:
    """URL encode a string (stub)"""
    import urllib.parse

    return urllib.parse.quote(url)


# ============================================================================
# Initialization
# ============================================================================


def initialize_sim_control(context: AppContext) -> None:
    """Initialize simulation control module
    :param context:
    """
    # Set default values
    # global sim_speed, sim_paused, sim_delay, sim_skips, sim_skip
    # global game_started, need_rest, performance_timing, flush_time
    # global auto_budget, auto_goto, auto_bulldoze, no_disasters
    # global user_sound_on, do_animation, do_messages, do_notices
    # global multi_player_mode, sugar_mode
    #
    context.sim_speed = 3
    context.sim_paused = False
    context.sim_delay = 10
    context.sim_skips = 0
    context.sim_skip = 0

    context.game_started = False
    context.need_rest = False
    context.performance_timing = False
    context.flush_time = 0.0

    context.auto_budget = True
    context.auto_goto = True
    context.auto_bulldoze = True
    context.no_disasters = False
    context.user_sound_on = True
    context.do_animation = True
    context.do_messages = True
    context.do_notices = True

    context.multi_player_mode = False
    context.sugar_mode = False
