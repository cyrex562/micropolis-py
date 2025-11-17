"""
budget.py - Budget and finance management system for Micropolis Python port

This module implements the budget system ported from w_budget.c,
responsible for managing city funding, budget allocation, and financial
calculations for fire, police, and road services.
"""

from . import messages
from .context import AppContext


def _kick() -> None:
    from micropolis.sim_control import kick as _kick_fn

    _kick_fn()


# ============================================================================
# Budget Global Variables
# ============================================================================

# Budget percentages (0.0 to 1.0)
# road_percent: float = 0.0
# police_percent: float = 0.0
# fire_percent: float = 0.0

# Budget values (allocated amounts)
# road_value: int = 0
# police_value: int = 0
# fire_value: int = 0

# Maximum budget values (requested amounts)
# road_max_value: int = 0
# police_max_value: int = 0
# fire_max_value: int = 0

# Drawing flags
# must_draw_curr_percents: bool = False
# must_draw_budget_window: bool = False


# def _kick() -> None:
#     """Local helper mirroring sim_control.kick without circular import."""
#     types.Kick()


# def kick() -> None:
#     """Backwards-compatible alias expected by legacy callers/tests."""
#     _kick()


def update_heads() -> None:
    """Compatibility shim; historically refreshed header widgets."""
    _kick()


# ============================================================================
# Budget Initialization
# ============================================================================


def init_funding_level(context: AppContext) -> None:
    """
    Initialize funding levels to default values.

    Ported from InitFundingLevel() in w_budget.c.
    Called during game initialization.
    """
    # global fire_percent, fire_value, police_percent, police_value
    # global road_percent, road_value

    context.fire_percent = 1.0  # 1.0
    context.fire_value = 0
    context.police_percent = 1.0  # 1.0
    context.police_value = 0
    context.road_percent = 1.0  # 1.0
    context.road_value = 0

    draw_budget_window(context)
    draw_curr_percents(context)


# ============================================================================
# Budget Calculation Functions
# ============================================================================


def do_budget(context: AppContext) -> None:
    """
    Perform budget calculation for current turn.

    Ported from DoBudget() in w_budget.c.
    Called from simulation loop.
    :param context:
    """
    do_budget_now(context, from_menu=False)


def do_budget_from_menu(context: AppContext) -> None:
    """
    Perform budget calculation when called from menu.

    Ported from DoBudgetFromMenu() in w_budget.c.
    Called when user manually triggers budget dialog.
    :param context:
    """
    do_budget_now(context, from_menu=True)


def do_budget_now(context: AppContext, from_menu: bool) -> None:
    """
    Core budget calculation logic.

    Ported from DoBudgetNow() in w_budget.c.
    Calculates how much funding each department gets based on available funds.

    Args:
        from_menu: Whether this was triggered from the budget menu
        :param from_menu:
        :param context:
    """
    # global fire_value, police_value, road_value
    # global fire_max_value, police_max_value, road_max_value
    # global fire_percent, police_percent, road_percent

    # Calculate requested amounts based on percentages
    fire_int = int(context.fire_fund * context.fire_percent)
    police_int = int(context.police_fund * context.police_percent)
    road_int = int(context.road_fund * context.road_percent)

    total = fire_int + police_int + road_int

    # Available funds
    yum_ducets = context.tax_fund + context.total_funds

    if yum_ducets > total:
        # Enough money for all requests
        context.fire_value = fire_int
        context.police_value = police_int
        context.road_value = road_int
    elif total > 0:
        # Not enough money, allocate proportionally
        if yum_ducets > road_int:
            context.road_value = road_int
            yum_ducets -= road_int

            if yum_ducets > fire_int:
                context.fire_value = fire_int
                yum_ducets -= fire_int

                if yum_ducets > police_int:
                    context.police_value = police_int
                    yum_ducets -= police_int
                else:
                    context.police_value = yum_ducets
                    if yum_ducets > 0:
                        context.police_percent = yum_ducets / context.police_fund
                    else:
                        context.police_percent = 0.0
            else:
                context.fire_value = yum_ducets
                context.police_value = 0
                context.police_percent = 0.0
                if yum_ducets > 0:
                    context.fire_percent = yum_ducets / context.fire_fund
                else:
                    context.fire_percent = 0.0
        else:
            context.road_value = yum_ducets
            if yum_ducets > 0:
                context.road_percent = yum_ducets / context.road_fund
            else:
                context.road_percent = 0.0

            context.fire_value = 0
            context.police_value = 0
            context.fire_percent = 0.0
            context.police_percent = 0.0
    else:
        # No funding requested
        context.fire_value = 0
        context.police_value = 0
        context.road_value = 0
        context.fire_percent = 1.0
        context.police_percent = 1.0
        context.road_percent = 1.0

    # Set maximum values
    context.fire_max_value = context.fire_fund
    context.police_max_value = context.police_fund
    context.road_max_value = context.road_fund

    draw_curr_percents(context)

    # Handle auto-budget vs manual budget
    if (not context.auto_budget) or from_menu:
        if not context.auto_budget:
            # TODO: append current year to budget string in UI
            pass

        show_budget_window_and_start_waiting(context)

        if not from_menu:
            # Apply the budget allocations
            context.fire_spend = context.fire_value
            context.police_spend = context.police_value
            context.road_spend = context.road_value

            total = context.fire_spend + context.police_spend + context.road_spend
            more_dough = context.tax_fund - total
            spend(context, -more_dough)
    else:
        # Auto-budget mode and not from menu
        if yum_ducets > total:
            more_dough = context.tax_fund - total
            spend(context, -more_dough)
            context.fire_spend = context.fire_fund
            context.police_spend = context.police_fund
            context.road_spend = context.road_fund
            draw_budget_window(context)
            draw_curr_percents(context)
            update_heads()
        else:
            # Not enough money for auto-budget, disable it
            context.auto_budget = False  # XXX: force auto-budget off
            context.must_update_options = True
            messages.clear_mes(context)
            messages.send_mes(context, 29)  # "Not enough funds for auto-budget"
            # Go back to manual budget
            do_budget_now(context, from_menu=True)


# ============================================================================
# Budget UI Functions (Adapted for pygame)
# ============================================================================


def draw_budget_window(context: AppContext) -> None:
    """
    Mark budget window for redraw.

    Ported from drawBudgetWindow() in w_budget.c.
    In pygame version, this sets a flag for UI update.
    :param context:
    """
    # global must_draw_budget_window
    context.must_draw_budget_window = True


def really_draw_budget_window(context: AppContext) -> None:
    """
    Actually draw/update the budget window.

    Ported from ReallyDrawBudgetWindow() in w_budget.c.
    In pygame version, this would update the UI display.
    :param context:
    """
    # global must_draw_budget_window

    # Calculate cash flow
    cash_flow = (
        context.tax_fund
        - context.fire_value
        - context.police_value
        - context.road_value
    )
    cash_flow2 = cash_flow

    # Format cash flow string
    if cash_flow < 0:
        cash_flow = -cash_flow
        context.flow_str = f"-${cash_flow:,}"  # For future UI integration
    else:
        context.flow_str = f"+${cash_flow:,}"  # For future UI integration

    # Format other values (for future UI integration)
    context.previous_str = f"${context.total_funds:,}"
    context.current_str = f"${cash_flow2 + context.total_funds:,}"
    context.collected_str = f"${context.tax_fund:,}"

    # In pygame version, this would send data to UI
    # For now, just mark as drawn
    context.must_draw_budget_window = False


def draw_curr_percents(context: AppContext) -> None:
    """
    Mark current percentages for redraw.

    Ported from drawCurrPercents() in w_budget.c.
    :param context:
    """
    # global must_draw_curr_percents
    context.must_draw_curr_percents = True


def really_draw_curr_percents(context: AppContext) -> None:
    """
    Actually draw/update current budget percentages.

    Ported from ReallyDrawCurrPercents() in w_budget.c.
    :param context:
    """
    # global must_draw_curr_percents

    # Format budget values (for future UI integration)
    context.fire_want = f"${context.fire_max_value:,}"
    context.police_want = f"${context.police_max_value:,}"
    context.road_want = f"${context.road_max_value:,}"

    context.fire_got = f"${int(context.fire_max_value * context.fire_percent):,}"
    context.police_got = f"${int(context.police_max_value * context.police_percent):,}"
    context.road_got = f"${int(context.road_max_value * context.road_percent):,}"

    # In pygame version, this would send data to UI
    # For now, just mark as drawn
    context.must_draw_curr_percents = False


def update_budget_window(context: AppContext) -> None:
    """
    Update budget window if needed.

    Ported from UpdateBudgetWindow() in w_budget.c.
    :param context:
    """
    # global must_draw_curr_percents, must_draw_budget_window

    if context.must_draw_curr_percents:
        really_draw_curr_percents(context)
        context.must_draw_curr_percents = False
    if context.must_draw_budget_window:
        really_draw_budget_window(context)
        context.must_draw_budget_window = False


def update_budget(context: AppContext) -> None:
    """
    Update budget display.

    Ported from UpdateBudget() in w_budget.c.
    :param context:
    """
    draw_curr_percents(context)
    draw_budget_window(context)
    # In original, this calls Eval("UIUpdateBudget")
    # In pygame version, this would trigger UI update


def show_budget_window_and_start_waiting(context: AppContext) -> None:
    """
    Show budget window and pause for user input.

    Ported from ShowBudgetWindowAndStartWaiting() in w_budget.c.
    In pygame version, this would show modal dialog.
    :param context:
    """
    # In original, this calls Eval("UIShowBudgetAndWait")
    # In pygame version, this would show budget dialog
    # For now, just pause simulation
    context.sim_paused = True


# ============================================================================
# Budget UI Data Functions
# ============================================================================


def set_budget(
    flow_str: str, previous_str: str, current_str: str, collected_str: str, tax: int
) -> None:
    """
    Set budget display data.

    Ported from SetBudget() in w_budget.c.
    In original, this formats TCL command for UI.
    In pygame version, this would pass data to UI system.
    """
    # In pygame version, store or pass to UI
    pass


def set_budget_values(
    road_got: str,
    road_want: str,
    road_percent_int: int,
    police_got: str,
    police_want: str,
    police_percent_int: int,
    fire_got: str,
    fire_want: str,
    fire_percent_int: int,
) -> None:
    """
    Set budget values display data.

    Ported from SetBudgetValues() in w_budget.c.
    """
    # In pygame version, store or pass to UI
    pass


# ============================================================================
# Utility Functions
# ============================================================================


def spend(context: AppContext, amount: int) -> None:
    """
    Spend money from city funds.

    Ported from Spend() function referenced in w_budget.c.
    :param amount:
    :param context:
    """
    context.total_funds -= amount
    context.must_update_funds = 1
    _kick()


# ============================================================================
# Budget Accessor Functions
# ============================================================================


def get_road_percent(context: AppContext) -> float:
    """Get road funding percentage."""
    return context.road_percent


def set_road_percent(context: AppContext, percent: float) -> None:
    """Set road funding percentage.
    :param percent:
    :param context:
    """
    # global road_percent
    context.road_percent = max(0.0, min(1.0, percent))


def get_police_percent(context: AppContext) -> float:
    """Get police funding percentage.
    :param context:
    """
    return context.police_percent


def set_police_percent(context: AppContext, percent: float) -> None:
    """Set police funding percentage.
    :param percent:
    :param context:
    """
    # global police_percent
    context.police_percent = max(0.0, min(1.0, percent))


def get_fire_percent(context: AppContext) -> float:
    """Get fire funding percentage.
    :param context:
    """
    return context.fire_percent


def set_fire_percent(context: AppContext, percent: float) -> None:
    """Set fire funding percentage."""
    # global fire_percent
    context.fire_percent = max(0.0, min(1.0, percent))


def get_road_value(context: AppContext) -> int:
    """Get allocated road funding.
    :param context:
    """
    return context.road_value


def get_police_value(context: AppContext) -> int:
    """Get allocated police funding.
    :param context:
    """
    return context.police_value


def get_fire_value(context: AppContext) -> int:
    """Get allocated fire funding.
    :param context:
    """
    return context.fire_value


def get_road_max_value(context: AppContext) -> int:
    """Get maximum road funding request.
    :param context:
    """
    return context.road_max_value


def get_police_max_value(context: AppContext) -> int:
    """Get maximum police funding request.
    :param context:
    """
    return context.police_max_value


def get_fire_max_value(context: AppContext) -> int:
    """Get maximum fire funding request.
    :param context:
    """
    return context.fire_max_value


# ============================================================================
# TCL Command Interface Functions
# ============================================================================


def auto_budget(context: AppContext, enabled: bool | None = None) -> int:
    """
    Get or set auto-budget mode.

    Ported from SimCmdAutoBudget in w_sim.c.
    :param enabled:
    :param context:
    """
    if enabled is not None:
        context.auto_budget = enabled
        context.must_update_options = True
        _kick()
        update_budget(context)

    return context.auto_budget


def do_budget_command(context: AppContext) -> None:
    """
    Execute budget calculation.

    Ported from SimCmdDoBudget in w_sim.c.
    :param context:
    """
    do_budget(context)
    _kick()


def do_budget_from_menu_command(context: AppContext) -> None:
    """
    Execute budget calculation from menu.

    Ported from SimCmdDoBudgetFromMenu in w_sim.c.
    :param context:
    """
    do_budget_from_menu(context)
    _kick()


def update_budget_command(context: AppContext) -> None:
    """
    Update budget display.

    Ported from SimCmdUpdateBudget in w_sim.c.
    :param context:
    """
    update_budget(context)
    _kick()


def update_budget_window_command(context: AppContext) -> None:
    """
    Update budget window display.

    Ported from SimCmdUpdateBudgetWindow in w_sim.c.
    :param context:
    """
    update_budget_window(context)
    _kick()
