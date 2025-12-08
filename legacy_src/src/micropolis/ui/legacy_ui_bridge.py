"""
ui/legacy_ui_bridge.py - UI-specific legacy global synchronization bridge

This module provides wrapper functions that update both the modern AppContext
and the legacy sim_control.types namespace to maintain compatibility with
tests and legacy code that depend on CamelCase globals.

As specified in §6.2 of the pygame UI port checklist, these wrappers ensure:
1. AppContext properties are updated for modern pygame UI panels
2. sim_control.types globals are updated for test observability
3. Both contexts remain synchronized during UI operations
4. Legacy TCL/TK-style callbacks are triggered when needed

Each function here is designed to be called by pygame UI components (panels,
widgets, event handlers) to maintain full compatibility with the existing
test suite and legacy integration points.
"""

from typing import Any

from micropolis.context import AppContext
from src.micropolis import sim_control


# ============================================================================
# UI Toggle and Option Wrappers
# ============================================================================


def ui_set_auto_budget(context: AppContext, enabled: bool) -> None:
    """
    Set auto-budget toggle from UI.

    Updates both AppContext.auto_budget and sim_control.types.AutoBudget
    so tests patching micropolis.sim_control.types continue to work.

    :param context: Application context
    :param enabled: Whether auto-budget is enabled
    """
    context.auto_budget = bool(enabled)
    sim_control._legacy_set("AutoBudget", bool(enabled))
    context.must_update_options = True
    sim_control._legacy_set("MustUpdateOptions", 1)
    sim_control.kick()


def ui_get_auto_budget(context: AppContext) -> bool:
    """
    Get auto-budget toggle state.

    Reads from legacy types first for test compatibility, falls back to context.

    :param context: Application context
    :return: Current auto-budget state
    """
    return sim_control._legacy_bool("AutoBudget", bool(context.auto_budget))


def ui_set_auto_goto(context: AppContext, enabled: bool) -> None:
    """
    Set auto-goto toggle from UI.

    Updates both AppContext and legacy AutoGoto/AutoGo globals.

    :param context: Application context
    :param enabled: Whether auto-goto is enabled
    """
    context.auto_goto = bool(enabled)
    context.auto_go = bool(enabled)
    sim_control._legacy_set("AutoGoto", bool(enabled))
    sim_control._legacy_set("AutoGo", bool(enabled))
    context.must_update_options = True
    sim_control._legacy_set("MustUpdateOptions", 1)
    sim_control.kick()


def ui_get_auto_goto(context: AppContext) -> bool:
    """
    Get auto-goto toggle state.

    :param context: Application context
    :return: Current auto-goto state
    """
    return sim_control._legacy_bool("AutoGoto", bool(context.auto_goto))


def ui_set_auto_bulldoze(context: AppContext, enabled: bool) -> None:
    """
    Set auto-bulldoze toggle from UI.

    Updates both AppContext.auto_bulldoze and legacy AutoBulldoze global.

    :param context: Application context
    :param enabled: Whether auto-bulldoze is enabled
    """
    context.auto_bulldoze = bool(enabled)
    sim_control._legacy_set("AutoBulldoze", bool(enabled))
    context.must_update_options = True
    sim_control._legacy_set("MustUpdateOptions", 1)
    sim_control.kick()


def ui_get_auto_bulldoze(context: AppContext) -> bool:
    """
    Get auto-bulldoze toggle state.

    :param context: Application context
    :return: Current auto-bulldoze state
    """
    return sim_control._legacy_bool("AutoBulldoze", bool(context.auto_bulldoze))


def ui_set_disasters_enabled(context: AppContext, enabled: bool) -> None:
    """
    Set disasters enabled toggle from UI.

    Updates both AppContext.no_disasters and legacy noDisasters global
    (note the inverted logic).

    :param context: Application context
    :param enabled: Whether disasters are enabled (True = disasters on)
    """
    context.no_disasters = not enabled
    sim_control._legacy_set("noDisasters", not enabled)
    context.must_update_options = True
    sim_control._legacy_set("MustUpdateOptions", 1)
    sim_control.kick()


def ui_get_disasters_enabled(context: AppContext) -> bool:
    """
    Get disasters enabled state.

    :param context: Application context
    :return: True if disasters are enabled
    """
    no_disasters = sim_control._legacy_bool("noDisasters", bool(context.no_disasters))
    return not no_disasters


def ui_set_sound_enabled(context: AppContext, enabled: bool) -> None:
    """
    Set sound enabled toggle from UI.

    Updates both AppContext.user_sound_on and legacy UserSoundOn global.

    :param context: Application context
    :param enabled: Whether sound is enabled
    """
    context.user_sound_on = bool(enabled)
    sim_control._legacy_set("UserSoundOn", bool(enabled))
    context.must_update_options = True
    sim_control._legacy_set("MustUpdateOptions", 1)
    sim_control.kick()


def ui_get_sound_enabled(context: AppContext) -> bool:
    """
    Get sound enabled state.

    :param context: Application context
    :return: Current sound enabled state
    """
    return sim_control._legacy_bool("UserSoundOn", bool(context.user_sound_on))


def ui_set_do_animation(context: AppContext, enabled: bool) -> None:
    """
    Set animation enabled toggle from UI.

    Updates both AppContext.do_animation and legacy doAnimation global.

    :param context: Application context
    :param enabled: Whether animations are enabled
    """
    context.do_animation = bool(enabled)
    sim_control._legacy_set("doAnimation", bool(enabled))
    context.must_update_options = True
    sim_control._legacy_set("MustUpdateOptions", 1)
    sim_control.kick()


def ui_get_do_animation(context: AppContext) -> bool:
    """
    Get animation enabled state.

    :param context: Application context
    :return: Current animation enabled state
    """
    return sim_control._legacy_bool("doAnimation", bool(context.do_animation))


def ui_set_do_messages(context: AppContext, enabled: bool) -> None:
    """
    Set messages enabled toggle from UI.

    Updates both AppContext.do_messages and legacy doMessages global.

    :param context: Application context
    :param enabled: Whether messages are enabled
    """
    context.do_messages = bool(enabled)
    sim_control._legacy_set("doMessages", bool(enabled))
    context.must_update_options = True
    sim_control._legacy_set("MustUpdateOptions", 1)
    sim_control.kick()


def ui_get_do_messages(context: AppContext) -> bool:
    """
    Get messages enabled state.

    :param context: Application context
    :return: Current messages enabled state
    """
    return sim_control._legacy_bool("doMessages", bool(context.do_messages))


def ui_set_do_notices(context: AppContext, enabled: bool) -> None:
    """
    Set notices enabled toggle from UI.

    Updates both AppContext.do_notices and legacy doNotices global.

    :param context: Application context
    :param enabled: Whether notices are enabled
    """
    context.do_notices = bool(enabled)
    sim_control._legacy_set("doNotices", bool(enabled))
    context.must_update_options = True
    sim_control._legacy_set("MustUpdateOptions", 1)
    sim_control.kick()


def ui_get_do_notices(context: AppContext) -> bool:
    """
    Get notices enabled state.

    :param context: Application context
    :return: Current notices enabled state
    """
    return sim_control._legacy_bool("doNotices", bool(context.do_notices))


# ============================================================================
# City Metadata Wrappers
# ============================================================================


def ui_set_city_name(context: AppContext, name: str) -> None:
    """
    Set city name from UI.

    Updates both AppContext.city_name and legacy CityName global,
    and calls legacy setCityName callback if registered.

    :param context: Application context
    :param name: New city name
    """
    normalized = name.strip() or "New City"
    context.city_name = normalized
    sim_control._legacy_set("CityName", normalized)
    sim_control._legacy_call("setCityName", normalized, prefer_legacy=True)
    sim_control.kick()


def ui_get_city_name(context: AppContext) -> str:
    """
    Get city name.

    Reads from legacy types first for test compatibility.

    :param context: Application context
    :return: Current city name
    """
    city_name = sim_control._legacy_get("CityName", context.city_name or "Micropolis")
    if not city_name or not str(city_name).strip():
        city_name = "Micropolis"
    return str(city_name)


def ui_set_game_level(context: AppContext, level: int) -> None:
    """
    Set game difficulty level from UI.

    Updates legacy GameLevel and calls SetGameLevelFunds to adjust starting funds.

    :param context: Application context
    :param level: Difficulty level (0=Easy, 1=Medium, 2=Hard)
    """
    if 0 <= level <= 2:
        sim_control._legacy_set("GameLevel", level)
        # Import engine here to avoid circular imports
        from src.micropolis import engine

        sim_control._legacy_call(
            "SetGameLevelFunds",
            context,
            level,
            fallback=engine.SetGameLevelFunds,
            legacy_args=(level,),
            prefer_legacy=True,
        )
        sim_control.kick()


def ui_get_game_level(context: AppContext) -> int:
    """
    Get game difficulty level.

    :param context: Application context
    :return: Current difficulty level (0-2)
    """
    return sim_control._legacy_int("GameLevel", context.game_level)


# ============================================================================
# Simulation Speed Wrappers
# ============================================================================


def ui_set_sim_speed(context: AppContext, speed: int) -> None:
    """
    Set simulation speed from UI.

    Updates both AppContext.sim_speed and legacy SimSpeed global.

    :param context: Application context
    :param speed: Speed setting (0=Paused, 1-7=speeds)
    """
    if 0 <= speed <= 7:
        context.sim_speed = speed
        sim_control._legacy_set("SimSpeed", speed)
        sim_control.kick()


def ui_get_sim_speed(context: AppContext) -> int:
    """
    Get simulation speed.

    :param context: Application context
    :return: Current speed setting (0-7)
    """
    return sim_control._legacy_int("SimSpeed", context.sim_speed)


def ui_pause_simulation(context: AppContext) -> None:
    """
    Pause the simulation from UI.

    :param context: Application context
    """
    context.sim_paused = True
    sim_control.kick()


def ui_resume_simulation(context: AppContext) -> None:
    """
    Resume the simulation from UI.

    :param context: Application context
    """
    context.sim_paused = False
    sim_control.kick()


def ui_is_sim_paused(context: AppContext) -> bool:
    """
    Check if simulation is paused.

    :param context: Application context
    :return: True if paused
    """
    return bool(context.sim_paused)


# ============================================================================
# Budget and Finance Wrappers
# ============================================================================


def ui_set_total_funds(context: AppContext, funds: int) -> None:
    """
    Set total city funds from UI.

    Updates both AppContext and legacy TotalFunds global, triggers fund update flag.

    :param context: Application context
    :param funds: New total funds
    """
    if funds >= 0:
        context.total_funds = funds
        context.must_update_funds = True
        sim_control._legacy_set("TotalFunds", funds)
        sim_control._legacy_set("MustUpdateFunds", 1)
        sim_control.kick()


def ui_get_total_funds(context: AppContext) -> int:
    """
    Get total city funds.

    :param context: Application context
    :return: Current total funds
    """
    return int(sim_control._legacy_get("TotalFunds", context.total_funds) or 0)


def ui_set_tax_rate(context: AppContext, tax: int) -> None:
    """
    Set tax rate from UI.

    Updates both AppContext.city_tax and legacy CityTax global.

    :param context: Application context
    :param tax: Tax rate (0-20)
    """
    if 0 <= tax <= 20:
        context.city_tax = tax
        sim_control._legacy_set("CityTax", tax)
        sim_control.kick()


def ui_get_tax_rate(context: AppContext) -> int:
    """
    Get tax rate.

    :param context: Application context
    :return: Current tax rate (0-20)
    """
    return sim_control._legacy_int("CityTax", context.city_tax)


def ui_set_fire_fund_percentage(context: AppContext, percent: int) -> None:
    """
    Set fire department funding percentage from UI.

    :param context: Application context
    :param percent: Funding percentage (0-100)
    """
    if 0 <= percent <= 100:
        context.fire_percent = percent / 100.0
        context.fire_spend = (context.fire_max_value * percent) // 100
        sim_control._legacy_set("firePercent", context.fire_percent)
        sim_control._legacy_set("fireSpend", context.fire_spend)

        from src.micropolis import simulation

        sim_control._legacy_call(
            "UpdateFundEffects",
            context,
            fallback=simulation.update_fund_effects,
            legacy_args=(),
            prefer_legacy=True,
        )
        sim_control.kick()


def ui_get_fire_fund_percentage(context: AppContext) -> int:
    """
    Get fire department funding percentage.

    :param context: Application context
    :return: Funding percentage (0-100)
    """
    percent = sim_control._legacy_get("firePercent", context.fire_percent)
    if percent is None:
        percent = context.fire_percent
    return int(round(float(percent) * 100.0))


def ui_set_police_fund_percentage(context: AppContext, percent: int) -> None:
    """
    Set police department funding percentage from UI.

    :param context: Application context
    :param percent: Funding percentage (0-100)
    """
    if 0 <= percent <= 100:
        context.police_percent = percent / 100.0
        context.police_spend = (context.police_max_value * percent) // 100
        sim_control._legacy_set("policePercent", context.police_percent)
        sim_control._legacy_set("policeSpend", context.police_spend)

        from src.micropolis import simulation

        sim_control._legacy_call(
            "UpdateFundEffects",
            context,
            fallback=simulation.update_fund_effects,
            legacy_args=(),
            prefer_legacy=True,
        )
        sim_control.kick()


def ui_get_police_fund_percentage(context: AppContext) -> int:
    """
    Get police department funding percentage.

    :param context: Application context
    :return: Funding percentage (0-100)
    """
    percent = sim_control._legacy_get("policePercent", context.police_percent)
    if percent is None:
        percent = context.police_percent
    return int(round(float(percent) * 100.0))


def ui_set_road_fund_percentage(context: AppContext, percent: int) -> None:
    """
    Set road department funding percentage from UI.

    :param context: Application context
    :param percent: Funding percentage (0-100)
    """
    if 0 <= percent <= 100:
        context.road_percent = percent / 100.0
        context.road_spend = (context.road_max_value * percent) // 100
        sim_control._legacy_set("roadPercent", context.road_percent)
        sim_control._legacy_set("roadSpend", context.road_spend)

        from src.micropolis import simulation

        sim_control._legacy_call(
            "UpdateFundEffects",
            context,
            fallback=simulation.update_fund_effects,
            legacy_args=(),
            prefer_legacy=True,
        )
        sim_control.kick()


def ui_get_road_fund_percentage(context: AppContext) -> int:
    """
    Get road department funding percentage.

    :param context: Application context
    :return: Funding percentage (0-100)
    """
    percent = sim_control._legacy_get("roadPercent", context.road_percent)
    if percent is None:
        percent = context.road_percent
    return int(round(float(percent) * 100.0))


# ============================================================================
# Overlay and Display Wrappers
# ============================================================================


def ui_set_overlay(context: AppContext, overlay_id: int) -> None:
    """
    Set current overlay display from UI.

    Updates both AppContext.do_overlay and legacy DoOverlay global.

    :param context: Application context
    :param overlay_id: Overlay identifier (0=None, 1=Population, 2=Pollution, etc.)
    """
    context.do_overlay = overlay_id
    sim_control._legacy_set("DoOverlay", overlay_id)
    sim_control.kick()


def ui_get_overlay(context: AppContext) -> int:
    """
    Get current overlay display.

    :param context: Application context
    :return: Current overlay identifier
    """
    return sim_control._legacy_int("DoOverlay", context.do_overlay)


# ============================================================================
# Initialization and Seeding
# ============================================================================


def ui_seed_from_legacy_types(context: AppContext) -> None:
    """
    Seed pygame UI state from sim_control.types namespace.

    This is called during initialization to synchronize the pygame UI with
    any values set by headless tests or legacy code that modified types
    before the UI was created.

    Should be called once after context is created but before panels mount.

    :param context: Application context to seed
    """
    # Toggles
    context.auto_budget = sim_control._legacy_bool("AutoBudget", context.auto_budget)
    context.auto_goto = sim_control._legacy_bool("AutoGoto", context.auto_goto)
    context.auto_go = sim_control._legacy_bool("AutoGo", context.auto_go)
    context.auto_bulldoze = sim_control._legacy_bool(
        "AutoBulldoze", context.auto_bulldoze
    )
    context.no_disasters = sim_control._legacy_bool("noDisasters", context.no_disasters)
    context.user_sound_on = sim_control._legacy_bool(
        "UserSoundOn", context.user_sound_on
    )
    context.do_animation = sim_control._legacy_bool("doAnimation", context.do_animation)
    context.do_messages = sim_control._legacy_bool("doMessages", context.do_messages)
    context.do_notices = sim_control._legacy_bool("doNotices", context.do_notices)

    # City metadata
    city_name = sim_control._legacy_get("CityName", context.city_name)
    if city_name:
        context.city_name = str(city_name)

    # Game level
    game_level = sim_control._legacy_get("GameLevel", context.game_level)
    if game_level is not None:
        context.game_level = int(game_level)

    # Simulation speed
    sim_speed = sim_control._legacy_get("SimSpeed", context.sim_speed)
    if sim_speed is not None:
        context.sim_speed = int(sim_speed)

    # Funds
    total_funds = sim_control._legacy_get("TotalFunds", context.total_funds)
    if total_funds is not None:
        context.total_funds = int(total_funds)

    # Tax rate
    city_tax = sim_control._legacy_get("CityTax", context.city_tax)
    if city_tax is not None:
        context.city_tax = int(city_tax)

    # Budget percentages
    fire_percent = sim_control._legacy_get("firePercent", None)
    if fire_percent is not None:
        context.fire_percent = float(fire_percent)

    police_percent = sim_control._legacy_get("policePercent", None)
    if police_percent is not None:
        context.police_percent = float(police_percent)

    road_percent = sim_control._legacy_get("roadPercent", None)
    if road_percent is not None:
        context.road_percent = float(road_percent)

    # Overlay
    do_overlay = sim_control._legacy_get("DoOverlay", context.do_overlay)
    if do_overlay is not None:
        context.do_overlay = int(do_overlay)


# ============================================================================
# Data Contract Documentation
# ============================================================================


# Crosswalk table between AppContext properties and legacy CamelCase globals:
#
# | AppContext Property      | Legacy Global (types)  | UI Component              |
# |--------------------------|------------------------|---------------------------|
# | auto_budget              | AutoBudget             | Head panel toggle         |
# | auto_goto                | AutoGoto, AutoGo       | Editor panel toggle       |
# | auto_bulldoze            | AutoBulldoze           | Editor panel toggle       |
# | no_disasters             | noDisasters            | Options panel toggle      |
# | user_sound_on            | UserSoundOn            | Options panel toggle      |
# | do_animation             | doAnimation            | Options panel toggle      |
# | do_messages              | doMessages             | Head panel toggle         |
# | do_notices               | doNotices              | Notice panel toggle       |
# | city_name                | CityName               | Head panel editable label |
# | game_level               | GameLevel              | Scenario picker           |
# | sim_speed                | SimSpeed               | Head panel speed controls |
# | total_funds              | TotalFunds             | Head panel counter        |
# | city_tax                 | CityTax                | Budget panel slider       |
# | fire_percent             | firePercent            | Budget panel slider       |
# | police_percent           | policePercent          | Budget panel slider       |
# | road_percent             | roadPercent            | Budget panel slider       |
# | do_overlay               | DoOverlay              | Map/editor overlay select |
# | must_update_funds        | MustUpdateFunds        | Event flag                |
# | must_update_options      | MustUpdateOptions      | Event flag                |
