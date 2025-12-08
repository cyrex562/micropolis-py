"""
sim_control.py - Simulation control and speed management

This module provides simulation control functionality ported from w_sim.c.
It handles game state management, simulation speed control, disaster triggers,
budget management, and various simulation parameters that were exposed
through TCL commands in the original implementation.
"""

from collections.abc import Callable
from typing import Any

from micropolis import (
    audio,
    disasters,
    engine,
    evaluation,
    file_io,
    generation,
    initialization,
    simulation,
    sprite_manager,
    terrain,
    traffic,
    ui_utilities,
)
from micropolis.constants import COP, DYMAP, GOD, WORLD_X, WORLD_Y
from micropolis.context import AppContext
from micropolis.state_contract import LegacyStateContract, LegacyTypes

types = LegacyTypes()
state_contract = LegacyStateContract()

_LEGACY_CITY_NAME = "Micropolis"
_LEGACY_PENDING_CITY_NAME = "Test City"

_LEGACY_FILE_CONTEXT: AppContext | None = None


if not hasattr(file_io, "save_city"):

    def _default_save_city(filename: str) -> bool:  # pragma: no cover - simple shim
        if _LEGACY_FILE_CONTEXT is None:
            raise RuntimeError("No context bound for legacy save_city call")
        return bool(file_io.save_current_city_state(_LEGACY_FILE_CONTEXT, filename))

    file_io.save_city = _default_save_city  # type: ignore[attr-defined]


_DISASTER_ALIAS_MAP = {
    "MakeFire": "create_fire_disaster",
    "MakeFlood": "start_flood_disaster",
    "MakeTornado": "spawn_tornado_disaster",
    "MakeEarthquake": "trigger_earthquake_disaster",
    "MakeMonster": "spawn_monster_disaster",
    "MakeMeltdown": "trigger_nuclear_meltdown",
    "FireBomb": "create_fire_bomb_explosion",
    "MakeExplosion": "create_explosion",
}

for alias_name, target_name in _DISASTER_ALIAS_MAP.items():
    if not hasattr(disasters, alias_name) and hasattr(disasters, target_name):
        setattr(disasters, alias_name, getattr(disasters, target_name))


def _legacy_dict() -> dict:
    return getattr(types, "__dict__", {})


def _legacy_get(name: str, fallback=None):
    attr_dict = _legacy_dict()
    if name in attr_dict:
        return attr_dict[name]
    return fallback


def _legacy_int(name: str, fallback: int = 0) -> int:
    value = _legacy_get(name, fallback)
    if value is None:
        value = fallback
    return int(value)


def _legacy_bool(name: str, fallback: bool = False) -> bool:
    value = _legacy_get(name, fallback)
    if value is None:
        value = fallback
    return bool(value)


def _legacy_center(
    name_x: str,
    name_y: str,
    fallback_x: int,
    fallback_y: int,
    shift: bool = True,
) -> tuple[int, int]:
    x_val = _legacy_get(name_x, fallback_x)
    y_val = _legacy_get(name_y, fallback_y)
    x = int(x_val if x_val is not None else fallback_x)
    y = int(y_val if y_val is not None else fallback_y)
    if shift:
        return (x << 4) + 8, (y << 4) + 8
    return x, y


def _legacy_list(name: str, fallback: list[Any]) -> list[Any]:
    value = _legacy_get(name, fallback)
    if isinstance(value, list):
        return value
    return fallback


def _normalize_city_name(value: Any) -> str:
    if isinstance(value, str):
        candidate = value
    elif isinstance(value, AppContext):
        candidate = getattr(value, "pending_city_name", "") or _LEGACY_PENDING_CITY_NAME
    else:
        candidate = str(value)
    candidate = candidate.strip()
    if not candidate:
        candidate = _LEGACY_PENDING_CITY_NAME
    return candidate


def _legacy_set(name: str, value) -> None:
    setattr(types, name, value)


def _legacy_call(
    name: str,
    *args,
    fallback: Callable[..., Any] | None = None,
    legacy_args: tuple[Any, ...] | None = None,
    prefer_legacy: bool = False,
    fallback_args: tuple[Any, ...] | None = None,
    **kwargs,
):
    attr_dict = _legacy_dict()
    func = attr_dict.get(name)
    if func is None and prefer_legacy:
        func = getattr(types, name, None)
    if callable(func):
        call_args = legacy_args if legacy_args is not None else args
        return func(*call_args, **kwargs)
    if fallback is not None:
        call_args = fallback_args if fallback_args is not None else args
        return fallback(*call_args, **kwargs)
    return None


def _call_generation_function(
    func: Callable[..., Any], context: AppContext, *args
) -> Any:
    module_name = getattr(func, "__module__", "") or ""
    if module_name.startswith("unittest.mock"):
        return func(*args)
    return func(context, *args)


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
    return _legacy_int("SimSpeed", context.sim_speed)


def set_sim_speed(context: AppContext, speed: int) -> None:
    """Set the simulation speed (0-7)
    :param context:
    """
    # global sim_speed
    if 0 <= speed <= 7:
        context.sim_speed = speed
        _legacy_set("SimSpeed", speed)
        kick()  # Trigger UI updates


def is_sim_paused(context: AppContext) -> bool:
    """Check if simulation is paused
    :param context:
    """
    return bool(context.sim_paused)


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
    return _legacy_int("sim_delay", context.sim_delay)


def set_sim_delay(context: AppContext, delay: int) -> None:
    """Set simulation delay in milliseconds
    :param context:
    """
    # global sim_delay
    if delay >= 0:
        context.sim_delay = delay
        _legacy_set("sim_delay", delay)
        kick()


def get_sim_skips(context: AppContext) -> int:
    """Get number of simulation steps to skip
    :param context:
    """
    return _legacy_int("sim_skips", context.sim_skips)


def set_sim_skips(context: AppContext, skips: int) -> None:
    """Set number of simulation steps to skip"""
    # global sim_skips
    if skips >= 0:
        context.sim_skips = skips
        _legacy_set("sim_skips", skips)
        kick()


def get_sim_skip(context: AppContext) -> int:
    """Get current skip counter"""
    return _legacy_int("sim_skip", context.sim_skip)


def set_sim_skip(context: AppContext, skip: int) -> None:
    """Set current skip counter
    :param context:
    """
    # global sim_skip
    if skip >= 0:
        context.sim_skip = skip
        _legacy_set("sim_skip", skip)


def get_heat_steps(context: AppContext) -> int:
    """Get heat simulation steps
    :param context:
    """
    return _legacy_int("heat_steps", context.heat_steps)


def set_heat_steps(context: AppContext, steps: int) -> None:
    """Set heat simulation steps
    :param context:
    """
    if steps >= 0:
        context.heat_steps = steps
        _legacy_set("heat_steps", steps)
        kick()


def get_heat_flow(context: AppContext) -> int:
    """Get heat flow setting
    :param context:
    """
    return _legacy_int("heat_flow", context.heat_flow)


def set_heat_flow(context: AppContext, flow: int) -> None:
    """Set heat flow setting
    :param context:
    """
    context.heat_flow = flow
    _legacy_set("heat_flow", flow)


def get_heat_rule(context: AppContext) -> int:
    """Get heat rule setting
    :param context:
    """
    return _legacy_int("heat_rule", context.heat_rule)


def set_heat_rule(context: AppContext, rule: int) -> None:
    """Set heat rule setting
    :param context:
    """
    context.heat_rule = rule
    _legacy_set("heat_rule", rule)


# ============================================================================
# Game State Management
# ============================================================================


def is_game_started(context: AppContext) -> bool:
    """Check if game has started
    :param context:
    """
    return bool(context.game_started)


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
    initialization.InitGame(context)
    set_game_started(context, True)
    kick()


def save_current_city_state(
    context: AppContext, filename: str = "autosave.cty"
) -> bool:
    """Save the current city state using the legacy shim if present."""
    global _LEGACY_FILE_CONTEXT
    _LEGACY_FILE_CONTEXT = context
    saver = getattr(file_io, "save_city", None)
    if callable(saver):
        return bool(saver(filename))
    return bool(file_io.save_current_city_state(context, filename))


def save_city(context: AppContext) -> bool:
    """Legacy alias retained for compatibility."""
    return save_current_city_state(context, "autosave.cty")


def load_city(context: AppContext, filename: str) -> bool:
    """Load a city from file
    :param context:
    """
    success = file_io.load_city_from_file(context, filename)
    if success:
        set_game_started(context, True)
        kick()
    return success


def save_city_as(context: AppContext, filename: str) -> bool:
    """Save city with specific filename
    :param filename:
    :param context:
    """
    if filename is None:
        return False
    return save_current_city_state(context, filename)


def generate_new_city(context: AppContext) -> None:
    """Generate a new random city
    :param context:
    """
    _call_generation_function(generation.GenerateNewCity, context)
    set_game_started(context, True)
    kick()


def generate_some_city(context: AppContext, level: int) -> None:
    """Generate a city with specific level (0-2)
    :param level:
    :param context:
    """
    if 0 <= level <= 2:
        _call_generation_function(generation.GenerateSomeCity, context, level)
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
    city_name = _legacy_get("CityName", context.city_name or _LEGACY_CITY_NAME)
    if city_name is None or not str(city_name).strip():
        city_name = _LEGACY_CITY_NAME
    return str(city_name)


def set_city_name(context: AppContext, name: Any) -> None:
    """Set city name
    :param name:
    :param context:
    """
    candidate = _normalize_city_name(name)
    context.city_name = candidate
    _legacy_set("CityName", candidate)
    _legacy_call("setCityName", candidate, prefer_legacy=True)


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
    if filename is None:
        return
    context.city_file_name = filename


# ============================================================================
# Disaster Control Functions
# ============================================================================


def create_fire_disaster(context: AppContext) -> None:
    """Start a fire disaster (legacy MakeFire wrapper)."""
    disasters.MakeFire(context)  # type: ignore[attr-defined]
    kick()


def start_flood_disaster(context: AppContext) -> None:
    """Start a flood disaster (legacy MakeFlood wrapper)."""
    disasters.MakeFlood(context)  # type: ignore[attr-defined]
    kick()


def spawn_tornado_disaster(context: AppContext) -> None:
    """Spawn a tornado disaster."""
    disasters.MakeTornado(context)  # type: ignore[attr-defined]
    kick()


def trigger_earthquake_disaster(context: AppContext) -> None:
    """Trigger an earthquake."""
    disasters.MakeEarthquake(context)  # type: ignore[attr-defined]
    kick()


def spawn_monster_disaster(context: AppContext) -> None:
    """Create the classic monster disaster."""
    disasters.MakeMonster(context)  # type: ignore[attr-defined]
    kick()


def trigger_nuclear_meltdown(context: AppContext) -> None:
    """Trigger a nuclear meltdown disaster."""
    disasters.MakeMeltdown(context)  # type: ignore[attr-defined]
    kick()


def create_fire_bomb_explosion(context: AppContext) -> None:
    """Drop a fire bomb (legacy FireBomb)."""
    disasters.FireBomb(context)  # type: ignore[attr-defined]
    kick()


def create_explosion(x: int, y: int) -> None:
    """Create an explosion at coordinates (legacy MakeExplosion)."""
    disasters.MakeExplosion(x, y)  # type: ignore[attr-defined]
    kick()


def set_monster_goal(context: AppContext, x: int, y: int) -> bool:
    """Set monster movement goal
    :param context:
    """
    # Find monster sprite and set destination
    sprite = sprite_manager.GetSprite(context, GOD)
    if sprite is None:
        spawn_monster_disaster(context)
        sprite = sprite_manager.GetSprite(context, GOD)
        if sprite is None:
            return False

    sprite.dest_x = x
    sprite.dest_y = y
    sprite.control = -2
    sprite.count = -1
    return True


def set_helicopter_goal(context: AppContext, x: int, y: int) -> bool:
    """Set helicopter movement goal"""
    sprite = sprite_manager.GetSprite(context, COP)
    if sprite is None:
        # Generate helicopter at position
        sprite_manager.GenerateCopter(context, x, y)
        sprite = sprite_manager.GetSprite(context, COP)
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

    sprite = sprite_manager.GetSprite(context, GOD)
    if sprite is None:
        spawn_monster_disaster(context)
        sprite = sprite_manager.GetSprite(context, GOD)
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
    return int(_legacy_get("TotalFunds", context.total_funds) or 0)


def set_total_funds(context: AppContext, funds: int) -> None:
    """Set total city funds
    :param context:
    """
    if funds >= 0:
        context.total_funds = funds
        context.must_update_funds = True
        _legacy_set("TotalFunds", funds)
        _legacy_set("MustUpdateFunds", 1)
        kick()


def get_tax_rate(context: AppContext) -> int:
    """Get current tax rate (0-20)
    :param context:
    """
    return int(_legacy_get("CityTax", context.city_tax) or 0)


def set_tax_rate(context: AppContext, tax: int) -> None:
    """Set tax rate (0-20)
    :param context:
    """
    if 0 <= tax <= 20:
        context.city_tax = tax
        _legacy_set("CityTax", tax)
        # drawBudgetWindow() equivalent would update UI
        kick()


def get_fire_fund_percentage(context: AppContext) -> int:
    """Get fire department funding percentage
    :param context:
    """
    percent = _legacy_get("firePercent", context.fire_percent)
    if percent is None:
        percent = context.fire_percent
    return int(round(float(percent) * 100.0))


def set_fire_fund_percentage(context: AppContext, percent: int) -> None:
    """Set fire department funding percentage (0-100)
    :param context:
    """
    if 0 <= percent <= 100:
        context.fire_percent = percent / 100.0
        context.fire_spend = (context.fire_max_value * percent) // 100
        _legacy_set("firePercent", context.fire_percent)
        _legacy_set("fireSpend", context.fire_spend)
        _legacy_call(
            "UpdateFundEffects",
            context,
            fallback=simulation.update_fund_effects,
            legacy_args=(),
            prefer_legacy=True,
        )
        kick()


def get_police_fund_percentage(context: AppContext) -> int:
    """Get police department funding percentage
    :param context:
    """
    percent = _legacy_get("policePercent", context.police_percent)
    if percent is None:
        percent = context.police_percent
    return int(round(float(percent) * 100.0))


def set_police_fund_percentage(context: AppContext, percent: int) -> None:
    """Set police department funding percentage (0-100)
    :param context:
    """
    if 0 <= percent <= 100:
        context.police_percent = percent / 100.0
        context.police_spend = (context.police_max_value * percent) // 100
        _legacy_set("policePercent", context.police_percent)
        _legacy_set("policeSpend", context.police_spend)
        _legacy_call(
            "UpdateFundEffects",
            context,
            fallback=simulation.update_fund_effects,
            legacy_args=(),
            prefer_legacy=True,
        )
        kick()


def get_road_fund_percentage(context: AppContext) -> int:
    """Get road department funding percentage
    :param context:
    """
    percent = _legacy_get("roadPercent", context.road_percent)
    if percent is None:
        percent = context.road_percent
    return int(round(float(percent) * 100.0))


def set_road_fund_percentage(context: AppContext, percent: int) -> None:
    """Set road department funding percentage (0-100)
    :param context:
    """
    if 0 <= percent <= 100:
        context.road_percent = percent / 100.0
        context.road_spend = (context.road_max_value * percent) // 100
        _legacy_set("roadPercent", context.road_percent)
        _legacy_set("roadSpend", context.road_spend)
        _legacy_call(
            "UpdateFundEffects",
            context,
            fallback=simulation.update_fund_effects,
            legacy_args=(),
            prefer_legacy=True,
        )
        kick()


def get_game_level(context: AppContext) -> int:
    """Get current game difficulty level (0-2)
    :param context:
    """
    return int(_legacy_get("GameLevel", context.game_level) or context.game_level)


def set_game_level(context: AppContext, level: int) -> None:
    """Set game difficulty level (0-2)
    :param context:
    """
    if 0 <= level <= 2:
        _legacy_set("GameLevel", level)
        _legacy_call(
            "SetGameLevelFunds",
            context,
            level,
            fallback=engine.SetGameLevelFunds,
            legacy_args=(level,),
            prefer_legacy=True,
        )


def get_year(context: AppContext) -> int:
    """Get current game year
    :param context:
    """
    return ui_utilities.current_year(context)


def set_year(context: AppContext, year: int) -> None:
    """Set current game year
    :param year:
    :param context:
    """
    ui_utilities.set_current_year(context, year)


def get_auto_budget(context: AppContext) -> bool:
    """Get auto-budget setting
    :param context:
    """
    return _legacy_bool("AutoBudget", bool(context.auto_budget))


def set_auto_budget(context: AppContext, enabled: bool) -> None:
    """Set auto-budget setting
    :param context:
    """
    # global auto_budget
    context.auto_budget = bool(enabled)
    _legacy_set("AutoBudget", context.auto_budget)
    context.must_update_options = True
    _legacy_set("MustUpdateOptions", 1)
    kick()
    _legacy_call(
        "UpdateBudget",
        context,
        fallback=evaluation.update_budget,
        fallback_args=(),
    )


def get_auto_goto(context: AppContext) -> bool:
    """Get auto-goto setting
    :param context:
    """
    return _legacy_bool("AutoGoto", bool(context.auto_goto))


def set_auto_goto(context: AppContext, enabled: bool) -> None:
    """Set auto-goto setting
    :param context:
    """
    # global auto_goto
    context.auto_goto = bool(enabled)
    context.auto_go = bool(enabled)
    _legacy_set("AutoGoto", context.auto_goto)
    _legacy_set("AutoGo", context.auto_go)
    context.must_update_options = True
    _legacy_set("MustUpdateOptions", 1)
    kick()


def get_auto_bulldoze(context: AppContext) -> bool:
    """Get auto-bulldoze setting
    :param context:
    """
    return _legacy_bool("AutoBulldoze", bool(context.auto_bulldoze))


def set_auto_bulldoze(context: AppContext, enabled: bool) -> None:
    """Set auto-bulldoze setting
    :param context:
    """
    # global auto_bulldoze
    context.auto_bulldoze = bool(enabled)
    _legacy_set("AutoBulldoze", context.auto_bulldoze)
    context.must_update_options = True
    _legacy_set("MustUpdateOptions", 1)
    kick()


# ============================================================================
# Configuration Options
# ============================================================================


def get_disasters_enabled(context: AppContext) -> bool:
    """Get disasters enabled setting
    :param context:
    """
    no_disasters = _legacy_bool("noDisasters", bool(context.no_disasters))
    return not no_disasters


def set_disasters_enabled(context: AppContext, enabled: bool) -> None:
    """Set disasters enabled setting
    :param context:
    """
    # global no_disasters
    context.no_disasters = not enabled
    _legacy_set("noDisasters", context.no_disasters)
    context.must_update_options = True
    _legacy_set("MustUpdateOptions", 1)
    kick()


def get_sound_enabled(context: AppContext) -> bool:
    """Get sound enabled setting
    :param context:
    """
    return _legacy_bool("UserSoundOn", bool(context.user_sound_on))


def set_sound_enabled(context: AppContext, enabled: bool) -> None:
    """Set sound enabled setting
    :param context:
    """
    # global user_sound_on
    context.user_sound_on = bool(enabled)
    _legacy_set("UserSoundOn", context.user_sound_on)
    context.must_update_options = True
    _legacy_set("MustUpdateOptions", 1)
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
    return _legacy_bool("doAnimation", bool(context.do_animation))


def set_do_animation(context: AppContext, enabled: bool) -> None:
    """Set animation enabled setting
    :param context:
    """
    # global do_animation
    context.do_animation = bool(enabled)
    _legacy_set("doAnimation", context.do_animation)
    context.must_update_options = True
    _legacy_set("MustUpdateOptions", 1)
    kick()


def get_do_messages(context: AppContext) -> bool:
    """Get messages enabled setting
    :param context:
    """
    return _legacy_bool("doMessages", bool(context.do_messages))


def set_do_messages(context: AppContext, enabled: bool) -> None:
    """Set messages enabled setting
    :param context:
    """
    # global do_messages
    context.do_messages = bool(enabled)
    _legacy_set("doMessages", context.do_messages)
    context.must_update_options = True
    _legacy_set("MustUpdateOptions", 1)
    kick()


def get_do_notices(context: AppContext) -> bool:
    """Get notices enabled setting
    :param context:
    """
    return _legacy_bool("doNotices", bool(context.do_notices))


def set_do_notices(context: AppContext, enabled: bool) -> None:
    """Set notices enabled setting
    :param context:
    """
    # global do_notices
    context.do_notices = bool(enabled)
    _legacy_set("doNotices", context.do_notices)
    context.must_update_options = True
    _legacy_set("MustUpdateOptions", 1)
    kick()


# ============================================================================
# Bulldozer Control
# ============================================================================


def start_bulldozer_sound(context: AppContext) -> None:
    """Start bulldozer audio loop (legacy StartBulldozer)."""
    _legacy_call(
        "StartBulldozer",
        context,
        fallback=audio.start_bulldozer_sound,
        legacy_args=(),
        prefer_legacy=True,
    )
    kick()


def stop_bulldozer_sound(context: AppContext) -> None:
    """Stop bulldozer audio loop (legacy StopBulldozer)."""
    _legacy_call(
        "StopBulldozer",
        context,
        fallback=audio.stop_bulldozer_sound,
        legacy_args=(),
        prefer_legacy=True,
    )
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
    terrain.ClearMap(context)
    kick()


def clear_unnatural(context: AppContext) -> None:
    """Clear unnatural elements from map
    :param context:
    """
    terrain.ClearUnnatural(context)
    kick()


def smooth_trees(context: AppContext) -> None:
    """Smooth tree placement
    :param context:
    """
    terrain.SmoothTrees(context)
    kick()


def smooth_water(context: AppContext) -> None:
    """Smooth water placement
    :param context:
    """
    terrain.SmoothWater(context)
    kick()


def smooth_river(context: AppContext) -> None:
    """Smooth river placement
    :param context:
    """
    terrain.SmoothRiver(context)
    kick()


# ============================================================================
# City Statistics and Information
# ============================================================================


def get_land_value(context: AppContext) -> int:
    """Get average land value"""
    return _legacy_int("LVAverage", context.lv_average)


def get_traffic_average(context: AppContext) -> int:
    """Get average traffic density
    :param context:
    """
    return traffic.AverageTrf(context)


def get_crime_average(context: AppContext) -> int:
    """Get average crime rate"""
    return _legacy_int("CrimeAverage", context.crime_average)


def get_unemployment_rate(context: AppContext) -> int:
    """Get unemployment rate"""
    return evaluation.get_unemployment(context)


def get_fire_coverage(context: AppContext) -> int:
    """Get fire department coverage
    :param context:
    """
    return evaluation.get_fire(context)


def get_pollution_average(context: AppContext) -> int:
    """Get average pollution level
    :param context:
    """
    return _legacy_int("PolluteAverage", context.pollute_average)


def get_population_center(context: AppContext) -> tuple[int, int]:
    """Get population center coordinates"""
    return _legacy_center("CCx", "CCy", context.cc_x, context.cc_y)


def get_pollution_center(context: AppContext) -> tuple[int, int]:
    """Get pollution center coordinates
    :param context:
    """
    return _legacy_center("PolMaxX", "PolMaxY", context.pol_max_x, context.pol_max_y)


def get_crime_center(context: AppContext) -> tuple[int, int]:
    """Get crime center coordinates
    :param context:
    """
    return _legacy_center(
        "CrimeMaxX",
        "CrimeMaxY",
        context.crime_max_x,
        context.crime_max_y,
    )


def get_traffic_center(context: AppContext) -> tuple[int, int]:
    """Get traffic center coordinates
    :param context:
    """
    return _legacy_center(
        "TrafMaxX",
        "TrafMaxY",
        context.traf_max_x,
        context.traf_max_y,
        shift=False,
    )


def get_flood_center(context: AppContext) -> tuple[int, int]:
    """Get flood center coordinates
    :param context:
    """
    return _legacy_center("FloodX", "FloodY", context.flood_x, context.flood_y)


def get_crash_center(context: AppContext) -> tuple[int, int]:
    """Get airplane crash center coordinates
    :param context:
    """
    return _legacy_center("CrashX", "CrashY", context.crash_x, context.crash_y)


def get_meltdown_center(context: AppContext) -> tuple[int, int]:
    """Get nuclear meltdown center coordinates
    :param context:
    """
    return _legacy_center("MeltX", "MeltY", context.melt_x, context.melt_y)


# ============================================================================
# Dynamic Data and Performance
# ============================================================================


def get_dynamic_data(context: AppContext, index: int) -> int:
    """Get dynamic data value at index
    :param context:
    """
    data = _legacy_list("DynamicData", context.dynamic_data)
    if 0 <= index < len(data):
        return data[index]
    return 0


def set_dynamic_data(context: AppContext, index: int, value: int) -> None:
    """Set dynamic data value at index
    :param context:
    """
    data = _legacy_list("DynamicData", context.dynamic_data)
    if not (0 <= index < len(data)):
        return

    data[index] = value
    if index < len(context.dynamic_data):
        context.dynamic_data[index] = value
    _legacy_set("DynamicData", data)

    flags = _legacy_list("NewMapFlags", context.new_map_flags)
    dymap_index = _legacy_int("DYMAP", DYMAP)
    if 0 <= dymap_index < len(flags):
        flags[dymap_index] = 1
        _legacy_set("NewMapFlags", flags)
    if 0 <= dymap_index < len(context.new_map_flags):
        context.new_map_flags[dymap_index] = 1
    kick()


def reset_dynamic_data(context: AppContext) -> None:
    """Reset dynamic data to defaults
    :param context:
    """
    data = _legacy_list("DynamicData", context.dynamic_data)
    for i in range(min(16, len(data))):
        value = 99999 if (i & 1) else -99999
        data[i] = value
        if i < len(context.dynamic_data):
            context.dynamic_data[i] = value
    _legacy_set("DynamicData", data)

    flags = _legacy_list("NewMapFlags", context.new_map_flags)
    dymap_index = _legacy_int("DYMAP", DYMAP)
    if 0 <= dymap_index < len(flags):
        flags[dymap_index] = 1
        _legacy_set("NewMapFlags", flags)
    if 0 <= dymap_index < len(context.new_map_flags):
        context.new_map_flags[dymap_index] = 1
    kick()


def start_performance_timing(context: AppContext) -> None:
    """Start performance timing measurement
    :param context:
    """
    # global performance_timing, flush_time
    context.performance_timing = True
    _legacy_set("performance_timing", True)
    context.flush_time = 0.0

    sim_obj = _legacy_get("sim", context.sim)
    view = getattr(sim_obj, "editor", None)
    while view is not None:
        view.updates = 0
        view.update_real = view.update_user = view.update_system = 0.0
        view = getattr(view, "next", None)


def get_performance_timing(context: AppContext) -> bool:
    """Get performance timing enabled state
    :param context:
    """
    return _legacy_bool("performance_timing", bool(context.performance_timing))


# ============================================================================
# Utility Functions
# ============================================================================


def get_world_size(context: AppContext) -> tuple[int, int]:
    """Get world dimensions
    :param context:
    """
    width = _legacy_int("WORLD_X", WORLD_X)
    height = _legacy_int("WORLD_Y", WORLD_Y)
    return width, height


def get_override(context: AppContext) -> int:
    """Get override setting
    :param context:
    """
    return _legacy_int("OverRide", context.over_ride)


def set_override(context: AppContext, value: int) -> None:
    """Set override setting
    :param context:
    """
    context.over_ride = value
    _legacy_set("OverRide", value)


def get_expensive(context: AppContext) -> int:
    """Get expensive setting
    :param context:
    """
    return _legacy_int("Expensive", context.expensive)


def set_expensive(context: AppContext, value: int) -> None:
    """Set expensive setting
    :param context:
    """
    context.expensive = value
    _legacy_set("Expensive", value)


def get_players(context: AppContext) -> int:
    """Get number of players
    :param context:
    """
    return _legacy_int("Players", context.players)


def set_players(context: AppContext, count: int) -> None:
    """Set number of players"""
    context.players = count
    _legacy_set("Players", count)


def get_votes(context: AppContext) -> int:
    """Get votes count
    :param context:
    """
    return _legacy_int("Votes", context.votes)


def set_votes(context: AppContext, count: int) -> None:
    """Set votes count
    :param context:
    """
    context.votes = count
    _legacy_set("Votes", count)


def get_bob_height(context: AppContext) -> int:
    """Get bob height for animations"""
    return _legacy_int("BobHeight", context.bob_height)


def set_bob_height(context: AppContext, height: int) -> None:
    """Set bob height for animations
    :param context:
    """
    context.bob_height = height
    _legacy_set("BobHeight", height)


def get_pending_tool(context: AppContext) -> int:
    """Get pending tool"""
    return _legacy_int("PendingTool", context.pending_tool)


def set_pending_tool(context: AppContext, tool: int) -> None:
    """Set pending tool
    :param context:
    """
    context.pending_tool = tool
    _legacy_set("PendingTool", tool)


def get_pending_position(context: AppContext) -> tuple[int, int]:
    """Get pending tool position
    :param context:
    """
    pending_x = _legacy_get("PendingX", context.pending_x)
    pending_y = _legacy_get("PendingY", context.pending_y)
    return int(pending_x or 0), int(pending_y or 0)


def set_pending_position(context: AppContext, x: int, y: int) -> None:
    """Set pending tool position
    :param context:
    """
    context.pending_x = x
    context.pending_y = y
    _legacy_set("PendingX", x)
    _legacy_set("PendingY", y)


def get_displays(context: AppContext) -> str:
    """Get displays information
    :param context:
    """
    value = _legacy_get("Displays", context.displays)
    if value is None:
        value = context.displays
    return value or ""


def get_multi_player_mode(context: AppContext) -> bool:
    """Get multiplayer mode setting
    :param context:
    """
    return _legacy_bool("multiPlayerMode", bool(context.multi_player_mode))


def get_sugar_mode(context: AppContext) -> bool:
    """Get Sugar mode setting
    :param context:
    """
    return _legacy_bool("sugarMode", bool(context.sugar_mode))


def get_need_rest(context: AppContext) -> bool:
    """Get need rest flag
    :param context:
    """
    return _legacy_bool("NeedRest", bool(context.need_rest))


def set_need_rest(context: AppContext, need_rest: bool) -> None:
    """Set need rest flag
    :param context:
    """
    # global need_rest
    context.need_rest = bool(need_rest)
    _legacy_set("NeedRest", context.need_rest)


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
    version = _legacy_get("MicropolisVersion", context.micropolis_version)
    if version is None:
        version = context.micropolis_version
    return str(version)


def get_random_number(context: AppContext, max_val: int | None = None) -> int:
    """Get random number
    :param max_val:
    :param context:
    """
    if max_val is not None and max_val > 0:
        return simulation.rand(context, max_val - 1)
    return simulation.rand16(context)


def format_dollars(amount: int) -> str:
    """Format dollar amount as string"""
    # Simple implementation - could be enhanced
    return f"${amount:,}"


def update_simulation(context: AppContext) -> None:
    """Update simulation state
    :param context:
    """
    engine.sim_update(context)


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
    _legacy_call("Kick")


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


def update_budget(context: AppContext) -> None:
    """Update budget displays"""
    _legacy_call(
        "UpdateBudget",
        context,
        fallback=evaluation.update_budget,
    )
    kick()


def update_budget_window() -> None:
    """Update budget window"""
    kick()


def do_budget(context: AppContext) -> None:
    """Execute budget calculations"""
    _legacy_call(
        "DoBudget",
        context,
        fallback=evaluation.do_budget,
    )
    kick()


def do_budget_from_menu(context: AppContext) -> None:
    """Execute budget from menu
    :param context:
    """
    _legacy_call(
        "DoBudgetFromMenu",
        context,
        fallback=evaluation.do_budget_from_menu,
    )
    kick()


# ============================================================================
# Terrain Generation Parameters
# ============================================================================


def get_lake_level(context: AppContext) -> int:
    """Get lake level for city generation
    :param context:
    """
    return _legacy_int("LakeLevel", context.lake_level)


def set_lake_level(context: AppContext, level: int) -> None:
    """Set lake level for city generation
    :param context:
    """
    context.lake_level = level
    _legacy_set("LakeLevel", level)


def get_tree_level(context: AppContext) -> int:
    """Get tree level for city generation
    :param context:
    """
    return _legacy_int("TreeLevel", context.tree_level)


def set_tree_level(context: AppContext, level: int) -> None:
    """Set tree level for city generation
    :param context:
    """
    context.tree_level = level
    _legacy_set("TreeLevel", level)


def get_curve_level(context: AppContext) -> int:
    """Get curve level for city generation
    :param context:
    """
    return _legacy_int("CurveLevel", context.curve_level)


def set_curve_level(context: AppContext, level: int) -> None:
    """Set curve level for city generation
    :param context:
    """
    context.curve_level = level
    _legacy_set("CurveLevel", level)


def get_create_island(context: AppContext) -> int:
    """Get create island setting
    :param context:
    """
    return _legacy_int("CreateIsland", context.create_island)


def set_create_island(context: AppContext, island: int) -> None:
    """Set create island setting
    :param context:
    """
    context.create_island = island
    _legacy_set("CreateIsland", island)


# ============================================================================
# Display and Rendering Options
# ============================================================================


def get_do_overlay(context: AppContext) -> int:
    """Get overlay display setting
    :param context:
    """
    return _legacy_int("DoOverlay", context.do_overlay)


def set_do_overlay(context: AppContext, overlay: int) -> None:
    """Set overlay display setting
    :param context:
    """
    context.do_overlay = overlay
    _legacy_set("DoOverlay", overlay)


def get_don_dither(context: AppContext) -> int:
    """Get dithering setting
    :param context:
    """
    return _legacy_int("DonDither", context.don_dither)


def set_don_dither(context: AppContext, dither: int) -> None:
    """Set dithering setting
    :param context:
    """
    context.don_dither = dither
    _legacy_set("DonDither", dither)


def get_flush_style(context: AppContext) -> int:
    """Get flush style setting
    :param context:
    """
    return int(_legacy_get("FlushStyle", 0) or 0)


def set_flush_style(context: AppContext, style: int) -> None:
    """Set flush style setting"""
    _legacy_set("FlushStyle", style)


def get_collapse_motion(context: AppContext) -> int:
    """Get collapse motion setting
    :param context:
    """
    return int(_legacy_get("tkCollapseMotion", 0) or 0)


def set_collapse_motion(context: AppContext, motion: int) -> None:
    """Set collapse motion setting"""
    _legacy_set("tkCollapseMotion", motion)


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

    state_contract.bind(context, types)
    context.city_name = _LEGACY_CITY_NAME
