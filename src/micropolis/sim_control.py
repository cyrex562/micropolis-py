"""
sim_control.py - Simulation control and speed management

This module provides simulation control functionality ported from w_sim.c.
It handles game state management, simulation speed control, disaster triggers,
budget management, and various simulation parameters that were exposed
through TCL commands in the original implementation.
"""

import random
import time

import micropolis.constants
import micropolis.utilities


# Import simulation modules
from . import (
    disasters,
    engine,
    evaluation,
    file_io,
    generation,
    initialization,
    terrain,
    traffic,
    types,
)
from . import random as sim_random

# ============================================================================
# Simulation Control State
# ============================================================================

# Simulation speed and timing
_sim_speed: int = 3  # Default simulation speed (0-7)
_sim_paused: bool = False
_sim_delay: int = 10  # Delay between simulation steps in milliseconds
_sim_skips: int = 0  # Number of simulation steps to skip
_sim_skip: int = 0  # Current skip counter

# Game state
_game_started: bool = False
_need_rest: bool = False

# Performance timing
_performance_timing: bool = False
_flush_time: float = 0.0

# Configuration options
_auto_budget: bool = True
_auto_goto: bool = True
_auto_bulldoze: bool = True
_no_disasters: bool = False
_user_sound_on: bool = True
_do_animation: bool = True
_do_messages: bool = True
_do_notices: bool = True

# Multiplayer and platform settings
_multi_player_mode: bool = False
_sugar_mode: bool = False

# ============================================================================
# Simulation Speed and Timing Functions
# ============================================================================


def get_sim_speed() -> int:
    """Get the current simulation speed (0-7)"""
    return _sim_speed


def set_sim_speed(speed: int) -> None:
    """Set the simulation speed (0-7)"""
    global _sim_speed
    if 0 <= speed <= 7:
        _sim_speed = speed
        types.sim_speed = speed
        kick()  # Trigger UI updates


def is_sim_paused() -> bool:
    """Check if simulation is paused"""
    return _sim_paused


def pause_simulation() -> None:
    """Pause the simulation"""
    global _sim_paused
    _sim_paused = True
    kick()


def resume_simulation() -> None:
    """Resume the simulation"""
    global _sim_paused
    _sim_paused = False
    kick()


def get_sim_delay() -> int:
    """Get simulation delay in milliseconds"""
    return _sim_delay


def set_sim_delay(delay: int) -> None:
    """Set simulation delay in milliseconds"""
    global _sim_delay
    if delay >= 0:
        _sim_delay = delay
        types.sim_delay = delay
        kick()


def get_sim_skips() -> int:
    """Get number of simulation steps to skip"""
    return _sim_skips


def set_sim_skips(skips: int) -> None:
    """Set number of simulation steps to skip"""
    global _sim_skips
    if skips >= 0:
        _sim_skips = skips
        types.sim_skips = skips
        kick()


def get_sim_skip() -> int:
    """Get current skip counter"""
    return _sim_skip


def set_sim_skip(skip: int) -> None:
    """Set current skip counter"""
    global _sim_skip
    if skip >= 0:
        _sim_skip = skip
        types.sim_skip = skip


def get_heat_steps() -> int:
    """Get heat simulation steps"""
    return types.heat_steps


def set_heat_steps(steps: int) -> None:
    """Set heat simulation steps"""
    if steps >= 0:
        types.heat_steps = steps
        kick()


def get_heat_flow() -> int:
    """Get heat flow setting"""
    return types.heat_flow


def set_heat_flow(flow: int) -> None:
    """Set heat flow setting"""
    types.heat_flow = flow


def get_heat_rule() -> int:
    """Get heat rule setting"""
    return types.heat_rule


def set_heat_rule(rule: int) -> None:
    """Set heat rule setting"""
    types.heat_rule = rule


# ============================================================================
# Game State Management
# ============================================================================


def is_game_started() -> bool:
    """Check if game has started"""
    return _game_started


def set_game_started(started: bool = True) -> None:
    """Set game started state"""
    global _game_started
    _game_started = started
    if started:
        kick()


def init_game() -> None:
    """Initialize a new game"""
    initialization.InitGame()
    set_game_started(True)
    kick()


def save_city() -> bool:
    """Save the current city"""
    # This would typically show a save dialog, for now just auto-save
    return file_io.save_city("autosave.cty")


def load_city(filename: str) -> bool:
    """Load a city from file"""
    success = file_io.load_city(filename)
    if success:
        set_game_started(True)
        kick()
    return success


def save_city_as(filename: str) -> bool:
    """Save city with specific filename"""
    return file_io.save_city(filename)


def generate_new_city() -> None:
    """Generate a new random city"""
    generation.GenerateNewCity()
    set_game_started(True)
    kick()


def generate_some_city(level: int) -> None:
    """Generate a city with specific level (0-2)"""
    if 0 <= level <= 2:
        generation.GenerateSomeCity(level)
        set_game_started(True)
        kick()


def load_scenario(scenario_num: int) -> None:
    """Load a scenario"""
    # This would load predefined scenarios
    # For now, just generate a new city
    generate_new_city()


def get_city_name() -> str:
    """Get current city name"""
    name = getattr(types, "CityName", None)
    if isinstance(name, str) and name.strip():
        return name
    return "Micropolis"


def set_city_name(name: str) -> None:
    """Set city name"""
    types.setCityName(name)


def get_city_file_name() -> str | None:
    """Get current city file name"""
    return types.city_file_name


def set_city_file_name(filename: str | None) -> None:
    """Set city file name"""
    if types.city_file_name:
        # Free old filename if needed
        pass
    types.city_file_name = filename


# ============================================================================
# Disaster Control Functions
# ============================================================================


def make_fire() -> None:
    """Start a fire disaster"""
    disasters.make_fire(context)
    kick()


def make_flood() -> None:
    """Start a flood disaster"""
    disasters.make_flood(context)
    kick()


def make_tornado() -> None:
    """Start a tornado disaster"""
    disasters.make_tornado()
    kick()


def make_earthquake() -> None:
    """Start an earthquake disaster"""
    disasters.make_earthquake(context)
    kick()


def make_monster() -> None:
    """Create a monster"""
    disasters.make_monster(context)
    kick()


def make_meltdown() -> None:
    """Start a nuclear meltdown"""
    disasters.make_meltdown(context)
    kick()


def fire_bomb() -> None:
    """Drop a fire bomb (for debugging/testing)"""
    disasters.fire_bomb(context)
    kick()


def make_explosion(x: int, y: int) -> None:
    """Create an explosion at coordinates"""
    disasters.make_explosion(x, y)
    kick()


def set_monster_goal(x: int, y: int) -> bool:
    """Set monster movement goal"""
    # Find monster sprite and set destination
    sprite = micropolis.utilities.GetSprite(types.GOD)
    if sprite is None:
        make_monster()
        sprite = micropolis.utilities.GetSprite(types.GOD)
        if sprite is None:
            return False

    sprite.dest_x = x
    sprite.dest_y = y
    sprite.control = -2
    sprite.count = -1
    return True


def set_helicopter_goal(x: int, y: int) -> bool:
    """Set helicopter movement goal"""
    sprite = micropolis.utilities.GetSprite(types.COP)
    if sprite is None:
        # Generate helicopter at position
        types.GenerateCopter(x, y)
        sprite = micropolis.utilities.GetSprite(types.COP)
        if sprite is None:
            return False

    sprite.dest_x = x
    sprite.dest_y = y
    return True


def set_monster_direction(direction: int) -> bool:
    """Set monster movement direction (-1 to 7)"""
    if not (-1 <= direction <= 7):
        return False

    sprite = micropolis.utilities.GetSprite(types.GOD)
    if sprite is None:
        make_monster()
        sprite = micropolis.utilities.GetSprite(types.GOD)
        if sprite is None:
            return False

    sprite.control = direction
    return True


# ============================================================================
# Budget and Finance Functions
# ============================================================================


def get_total_funds() -> int:
    """Get total city funds"""
    return types.total_funds


def set_total_funds(funds: int) -> None:
    """Set total city funds"""
    if funds >= 0:
        types.total_funds = funds
        types.must_update_funds = 1
        kick()


def get_tax_rate() -> int:
    """Get current tax rate (0-20)"""
    return types.city_tax


def set_tax_rate(tax: int) -> None:
    """Set tax rate (0-20)"""
    if 0 <= tax <= 20:
        types.city_tax = tax
        # drawBudgetWindow() equivalent would update UI
        kick()


def get_fire_fund_percentage() -> int:
    """Get fire department funding percentage"""
    return int(types.fire_percent * 100.0)


def set_fire_fund_percentage(percent: int) -> None:
    """Set fire department funding percentage (0-100)"""
    if 0 <= percent <= 100:
        types.fire_percent = percent / 100.0
        types.fire_spend = (types.fire_max_value * percent) // 100
        types.update_fund_effects(context)
        kick()


def get_police_fund_percentage() -> int:
    """Get police department funding percentage"""
    return int(types.police_percent * 100.0)


def set_police_fund_percentage(percent: int) -> None:
    """Set police department funding percentage (0-100)"""
    if 0 <= percent <= 100:
        types.police_percent = percent / 100.0
        types.police_spend = (types.police_max_value * percent) // 100
        types.update_fund_effects(context)
        kick()


def get_road_fund_percentage() -> int:
    """Get road department funding percentage"""
    return int(types.road_percent * 100.0)


def set_road_fund_percentage(percent: int) -> None:
    """Set road department funding percentage (0-100)"""
    if 0 <= percent <= 100:
        types.road_percent = percent / 100.0
        types.road_spend = (types.road_max_value * percent) // 100
        types.update_fund_effects(context)
        kick()


def get_game_level() -> int:
    """Get current game difficulty level (0-2)"""
    return types.game_level


def set_game_level(level: int) -> None:
    """Set game difficulty level (0-2)"""
    if 0 <= level <= 2:
        types.SetGameLevelFunds(level)


def get_year() -> int:
    """Get current game year"""
    return types.CurrentYear()


def set_year(year: int) -> None:
    """Set current game year"""
    types.SetYear(year)


def get_auto_budget() -> bool:
    """Get auto-budget setting"""
    return _auto_budget


def set_auto_budget(enabled: bool) -> None:
    """Set auto-budget setting"""
    global _auto_budget
    _auto_budget = enabled
    types.auto_budget = enabled
    types.must_update_options = 1
    kick()
    evaluation.UpdateBudget()


def get_auto_goto() -> bool:
    """Get auto-goto setting"""
    return _auto_goto


def set_auto_goto(enabled: bool) -> None:
    """Set auto-goto setting"""
    global _auto_goto
    _auto_goto = enabled
    types.auto_go = enabled
    types.must_update_options = 1
    kick()


def get_auto_bulldoze() -> bool:
    """Get auto-bulldoze setting"""
    return _auto_bulldoze


def set_auto_bulldoze(enabled: bool) -> None:
    """Set auto-bulldoze setting"""
    global _auto_bulldoze
    _auto_bulldoze = enabled
    types.auto_bulldoze = enabled
    types.must_update_options = 1
    kick()


# ============================================================================
# Configuration Options
# ============================================================================


def get_disasters_enabled() -> bool:
    """Get disasters enabled setting"""
    return not _no_disasters


def set_disasters_enabled(enabled: bool) -> None:
    """Set disasters enabled setting"""
    global _no_disasters
    _no_disasters = not enabled
    types.no_disasters = _no_disasters
    types.must_update_options = 1
    kick()


def get_sound_enabled() -> bool:
    """Get sound enabled setting"""
    return _user_sound_on


def set_sound_enabled(enabled: bool) -> None:
    """Set sound enabled setting"""
    global _user_sound_on
    _user_sound_on = enabled
    types.user_sound_on = enabled
    types.must_update_options = 1
    kick()


def sound_off() -> None:
    """Turn sound off"""
    set_sound_enabled(False)


def get_do_animation() -> bool:
    """Get animation enabled setting"""
    return _do_animation


def set_do_animation(enabled: bool) -> None:
    """Set animation enabled setting"""
    global _do_animation
    _do_animation = enabled
    types.do_animation = enabled
    types.must_update_options = 1
    kick()


def get_do_messages() -> bool:
    """Get messages enabled setting"""
    return _do_messages


def set_do_messages(enabled: bool) -> None:
    """Set messages enabled setting"""
    global _do_messages
    _do_messages = enabled
    types.do_messages = enabled
    types.must_update_options = 1
    kick()


def get_do_notices() -> bool:
    """Get notices enabled setting"""
    return _do_notices


def set_do_notices(enabled: bool) -> None:
    """Set notices enabled setting"""
    global _do_notices
    _do_notices = enabled
    types.do_notices = enabled
    types.must_update_options = 1
    kick()


# ============================================================================
# Bulldozer Control
# ============================================================================


def start_bulldozer() -> None:
    """Start bulldozer tool"""
    types.StartBulldozer()
    kick()


def stop_bulldozer() -> None:
    """Stop bulldozer tool"""
    types.StopBulldozer()
    kick()


# ============================================================================
# Map and Terrain Functions
# ============================================================================


def get_tile(x: int, y: int) -> int:
    """Get tile value at coordinates"""
    if 0 <= x < micropolis.constants.WORLD_X and 0 <= y < micropolis.constants.WORLD_Y:
        return types.map_data[x][y]
    return 0


def set_tile(x: int, y: int, tile: int) -> None:
    """Set tile value at coordinates"""
    if 0 <= x < micropolis.constants.WORLD_X and 0 <= y < micropolis.constants.WORLD_Y:
        types.map_data[x][y] = tile


def fill_map(tile: int) -> None:
    """Fill entire map with tile value"""
    for x in range(micropolis.constants.WORLD_X):
        for y in range(micropolis.constants.WORLD_Y):
            types.map_data[x][y] = tile


def erase_overlay() -> None:
    """Erase overlay data"""
    # This would clear overlay visualizations
    pass


def clear_map() -> None:
    """Clear the map"""
    terrain.ClearMap()
    kick()


def clear_unnatural() -> None:
    """Clear unnatural elements from map"""
    terrain.ClearUnnatural()
    kick()


def smooth_trees() -> None:
    """Smooth tree placement"""
    terrain.SmoothTrees()
    kick()


def smooth_water() -> None:
    """Smooth water placement"""
    terrain.SmoothWater()
    kick()


def smooth_river() -> None:
    """Smooth river placement"""
    terrain.SmoothRiver()
    kick()


# ============================================================================
# City Statistics and Information
# ============================================================================


def get_land_value() -> int:
    """Get average land value"""
    return types.lv_average


def get_traffic_average() -> int:
    """Get average traffic density"""
    return traffic.AverageTrf()


def get_crime_average() -> int:
    """Get average crime rate"""
    return types.crime_average


def get_unemployment_rate() -> int:
    """Get unemployment rate"""
    return evaluation.GetUnemployment(context)


def get_fire_coverage() -> int:
    """Get fire department coverage"""
    return evaluation.GetFire(context)


def get_pollution_average() -> int:
    """Get average pollution level"""
    return types.pollute_average


def get_population_center() -> tuple[int, int]:
    """Get population center coordinates"""
    return ((types.cc_x << 4) + 8, (types.cc_y << 4) + 8)


def get_pollution_center() -> tuple[int, int]:
    """Get pollution center coordinates"""
    return ((types.pol_max_x << 4) + 8, (types.pol_max_y << 4) + 8)


def get_crime_center() -> tuple[int, int]:
    """Get crime center coordinates"""
    return ((types.crime_max_x << 4) + 8, (types.crime_max_y << 4) + 8)


def get_traffic_center() -> tuple[int, int]:
    """Get traffic center coordinates"""
    return (types.traf_max_x, types.traf_max_y)


def get_flood_center() -> tuple[int, int]:
    """Get flood center coordinates"""
    return ((types.flood_x << 4) + 8, (types.flood_y << 4) + 8)


def get_crash_center() -> tuple[int, int]:
    """Get airplane crash center coordinates"""
    return ((types.crash_x << 4) + 8, (types.crash_y << 4) + 8)


def get_meltdown_center() -> tuple[int, int]:
    """Get nuclear meltdown center coordinates"""
    return ((types.melt_x << 4) + 8, (types.melt_y << 4) + 8)


# ============================================================================
# Dynamic Data and Performance
# ============================================================================


def get_dynamic_data(index: int) -> int:
    """Get dynamic data value at index"""
    if 0 <= index < 32:
        return types.dynamic_data[index]
    return 0


def set_dynamic_data(index: int, value: int) -> None:
    """Set dynamic data value at index"""
    if 0 <= index < 32:
        types.dynamic_data[index] = value
        types.new_map_flags[micropolis.constants.DYMAP] = 1
        kick()


def reset_dynamic_data() -> None:
    """Reset dynamic data to defaults"""
    for i in range(16):
        types.dynamic_data[i] = 99999 if (i & 1) else -99999
    types.new_map_flags[micropolis.constants.DYMAP] = 1
    kick()


def start_performance_timing() -> None:
    """Start performance timing measurement"""
    global _performance_timing, _flush_time
    _performance_timing = True
    _flush_time = 0.0

    # Reset timing for all views
    view = types.sim.editor
    while view:
        view.updates = 0
        view.update_real = view.update_user = view.update_system = 0.0
        view = view.next


def get_performance_timing() -> bool:
    """Get performance timing enabled state"""
    return _performance_timing


# ============================================================================
# Utility Functions
# ============================================================================


def get_world_size() -> tuple[int, int]:
    """Get world dimensions"""
    return (micropolis.constants.WORLD_X, micropolis.constants.WORLD_Y)


def get_override() -> int:
    """Get override setting"""
    return types.over_ride


def set_override(value: int) -> None:
    """Set override setting"""
    types.over_ride = value


def get_expensive() -> int:
    """Get expensive setting"""
    return types.expensive


def set_expensive(value: int) -> None:
    """Set expensive setting"""
    types.expensive = value


def get_players() -> int:
    """Get number of players"""
    return types.players


def set_players(count: int) -> None:
    """Set number of players"""
    types.players = count


def get_votes() -> int:
    """Get votes count"""
    return types.votes


def set_votes(count: int) -> None:
    """Set votes count"""
    types.votes = count


def get_bob_height() -> int:
    """Get bob height for animations"""
    return types.bob_height


def set_bob_height(height: int) -> None:
    """Set bob height for animations"""
    types.bob_height = height


def get_pending_tool() -> int:
    """Get pending tool"""
    return types.pending_tool


def set_pending_tool(tool: int) -> None:
    """Set pending tool"""
    types.pending_tool = tool


def get_pending_position() -> tuple[int, int]:
    """Get pending tool position"""
    return (types.pending_x, types.pending_y)


def set_pending_position(x: int, y: int) -> None:
    """Set pending tool position"""
    types.pending_x = x
    types.pending_y = y


def get_displays() -> str:
    """Get displays information"""
    return types.displays or ""


def get_multi_player_mode() -> bool:
    """Get multiplayer mode setting"""
    return _multi_player_mode


def get_sugar_mode() -> bool:
    """Get Sugar mode setting"""
    return _sugar_mode


def get_need_rest() -> bool:
    """Get need rest flag"""
    return _need_rest


def set_need_rest(need_rest: bool) -> None:
    """Set need rest flag"""
    global _need_rest
    _need_rest = need_rest
    types.need_rest = need_rest


def get_platform() -> str:
    """Get platform string"""
    import platform

    system = platform.system().lower()
    if system == "windows":
        return "msdos"  # For compatibility
    else:
        return "unix"


def get_version() -> str:
    """Get Micropolis version"""
    return types.micropolis_version


def get_random_number(max_val: int | None = None) -> int:
    """Get random number"""
    if max_val is not None:
        return sim_random.Rand(max_val)
    else:
        return sim_random.Rand16()


def format_dollars(amount: int) -> str:
    """Format dollar amount as string"""
    # Simple implementation - could be enhanced
    return f"${amount:,}"


def update_simulation() -> None:
    """Update simulation state"""
    engine.sim_update()


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
    types.Kick()


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
    evaluation.UpdateBudget()
    kick()


def update_budget_window() -> None:
    """Update budget window"""
    # drawBudgetWindow() equivalent
    kick()


def do_budget() -> None:
    """Execute budget calculations"""
    evaluation.DoBudget(context)
    kick()


def do_budget_from_menu() -> None:
    """Execute budget from menu"""
    evaluation.DoBudgetFromMenu(context)
    kick()


# ============================================================================
# Terrain Generation Parameters
# ============================================================================


def get_lake_level() -> int:
    """Get lake level for city generation"""
    return types.lake_level


def set_lake_level(level: int) -> None:
    """Set lake level for city generation"""
    types.lake_level = level


def get_tree_level() -> int:
    """Get tree level for city generation"""
    return types.tree_level


def set_tree_level(level: int) -> None:
    """Set tree level for city generation"""
    types.tree_level = level


def get_curve_level() -> int:
    """Get curve level for city generation"""
    return types.curve_level


def set_curve_level(level: int) -> None:
    """Set curve level for city generation"""
    types.curve_level = level


def get_create_island() -> int:
    """Get create island setting"""
    return types.create_island


def set_create_island(island: int) -> None:
    """Set create island setting"""
    types.create_island = island


# ============================================================================
# Display and Rendering Options
# ============================================================================


def get_do_overlay() -> int:
    """Get overlay display setting"""
    return types.do_overlay


def set_do_overlay(overlay: int) -> None:
    """Set overlay display setting"""
    types.do_overlay = overlay


def get_don_dither() -> int:
    """Get dithering setting"""
    return types.don_dither


def set_don_dither(dither: int) -> None:
    """Set dithering setting"""
    types.don_dither = dither


def get_flush_style() -> int:
    """Get flush style setting"""
    return types.FlushStyle


def set_flush_style(style: int) -> None:
    """Set flush style setting"""
    types.FlushStyle = style


def get_collapse_motion() -> int:
    """Get collapse motion setting"""
    return types.tkCollapseMotion


def set_collapse_motion(motion: int) -> None:
    """Set collapse motion setting"""
    types.tkCollapseMotion = motion


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


def initialize_sim_control() -> None:
    """Initialize simulation control module"""
    # Set default values
    global _sim_speed, _sim_paused, _sim_delay, _sim_skips, _sim_skip
    global _game_started, _need_rest, _performance_timing, _flush_time
    global _auto_budget, _auto_goto, _auto_bulldoze, _no_disasters
    global _user_sound_on, _do_animation, _do_messages, _do_notices
    global _multi_player_mode, _sugar_mode

    _sim_speed = 3
    _sim_paused = False
    _sim_delay = 10
    _sim_skips = 0
    _sim_skip = 0

    _game_started = False
    _need_rest = False
    _performance_timing = False
    _flush_time = 0.0

    _auto_budget = True
    _auto_goto = True
    _auto_bulldoze = True
    _no_disasters = False
    _user_sound_on = True
    _do_animation = True
    _do_messages = True
    _do_notices = True

    _multi_player_mode = False
    _sugar_mode = False
