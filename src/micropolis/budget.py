"""
budget.py - Budget and finance management system for Micropolis Python port

This module implements the budget system ported from w_budget.c,
responsible for managing city funding, budget allocation, and financial
calculations for fire, police, and road services.
"""

from . import messages, types

# ============================================================================
# Budget Global Variables
# ============================================================================

# Budget percentages (0.0 to 1.0)
road_percent: float = 0.0
police_percent: float = 0.0
fire_percent: float = 0.0

# Budget values (allocated amounts)
road_value: int = 0
police_value: int = 0
fire_value: int = 0

# Maximum budget values (requested amounts)
road_max_value: int = 0
police_max_value: int = 0
fire_max_value: int = 0

# Drawing flags
must_draw_curr_percents: bool = False
must_draw_budget_window: bool = False


def _kick() -> None:
    """Local helper mirroring sim_control.kick without circular import."""
    types.Kick()


def kick() -> None:
    """Backwards-compatible alias expected by legacy callers/tests."""
    _kick()


def update_heads() -> None:
    """Compatibility shim; historically refreshed header widgets."""
    _kick()


# ============================================================================
# Budget Initialization
# ============================================================================


def init_funding_level() -> None:
    """
    Initialize funding levels to default values.

    Ported from InitFundingLevel() in w_budget.c.
    Called during game initialization.
    """
    global fire_percent, fire_value, police_percent, police_value
    global road_percent, road_value

    fire_percent = 1.0  # 1.0
    fire_value = 0
    police_percent = 1.0  # 1.0
    police_value = 0
    road_percent = 1.0  # 1.0
    road_value = 0

    draw_budget_window()
    draw_curr_percents()


# ============================================================================
# Budget Calculation Functions
# ============================================================================


def do_budget() -> None:
    """
    Perform budget calculation for current turn.

    Ported from DoBudget() in w_budget.c.
    Called from simulation loop.
    """
    do_budget_now(from_menu=False)


def do_budget_from_menu() -> None:
    """
    Perform budget calculation when called from menu.

    Ported from DoBudgetFromMenu() in w_budget.c.
    Called when user manually triggers budget dialog.
    """
    do_budget_now(from_menu=True)


def do_budget_now(from_menu: bool) -> None:
    """
    Core budget calculation logic.

    Ported from DoBudgetNow() in w_budget.c.
    Calculates how much funding each department gets based on available funds.

    Args:
        from_menu: Whether this was triggered from the budget menu
    """
    global fire_value, police_value, road_value
    global fire_max_value, police_max_value, road_max_value
    global fire_percent, police_percent, road_percent

    # Calculate requested amounts based on percentages
    fire_int = int(types.fire_fund * fire_percent)
    police_int = int(types.police_fund * police_percent)
    road_int = int(types.road_fund * road_percent)

    total = fire_int + police_int + road_int

    # Available funds
    yum_ducets = types.tax_fund + types.total_funds

    if yum_ducets > total:
        # Enough money for all requests
        fire_value = fire_int
        police_value = police_int
        road_value = road_int
    elif total > 0:
        # Not enough money, allocate proportionally
        if yum_ducets > road_int:
            road_value = road_int
            yum_ducets -= road_int

            if yum_ducets > fire_int:
                fire_value = fire_int
                yum_ducets -= fire_int

                if yum_ducets > police_int:
                    police_value = police_int
                    yum_ducets -= police_int
                else:
                    police_value = yum_ducets
                    if yum_ducets > 0:
                        police_percent = yum_ducets / types.police_fund
                    else:
                        police_percent = 0.0
            else:
                fire_value = yum_ducets
                police_value = 0
                police_percent = 0.0
                if yum_ducets > 0:
                    fire_percent = yum_ducets / types.fire_fund
                else:
                    fire_percent = 0.0
        else:
            road_value = yum_ducets
            if yum_ducets > 0:
                road_percent = yum_ducets / types.road_fund
            else:
                road_percent = 0.0

            fire_value = 0
            police_value = 0
            fire_percent = 0.0
            police_percent = 0.0
    else:
        # No funding requested
        fire_value = 0
        police_value = 0
        road_value = 0
        fire_percent = 1.0
        police_percent = 1.0
        road_percent = 1.0

    # Set maximum values
    fire_max_value = types.fire_fund
    police_max_value = types.police_fund
    road_max_value = types.road_fund

    draw_curr_percents()

    # Handle auto-budget vs manual budget
    if (not types.auto_budget) or from_menu:
        if not types.auto_budget:
            # TODO: append current year to budget string in UI
            pass

        show_budget_window_and_start_waiting()

        if not from_menu:
            # Apply the budget allocations
            types.fire_spend = fire_value
            types.police_spend = police_value
            types.road_spend = road_value

            total = types.fire_spend + types.police_spend + types.road_spend
            more_dough = types.tax_fund - total
            spend(-more_dough)
    else:
        # Auto-budget mode and not from menu
        if yum_ducets > total:
            more_dough = types.tax_fund - total
            spend(-more_dough)
            types.fire_spend = types.fire_fund
            types.police_spend = types.police_fund
            types.road_spend = types.road_fund
            draw_budget_window()
            draw_curr_percents()
            update_heads()
        else:
            # Not enough money for auto-budget, disable it
            types.auto_budget = 0  # XXX: force auto-budget off
            types.must_update_options = 1
            messages.clear_mes()
            messages.send_mes(29)  # "Not enough funds for auto-budget"
            # Go back to manual budget
            do_budget_now(from_menu=True)


# ============================================================================
# Budget UI Functions (Adapted for pygame)
# ============================================================================


def draw_budget_window() -> None:
    """
    Mark budget window for redraw.

    Ported from drawBudgetWindow() in w_budget.c.
    In pygame version, this sets a flag for UI update.
    """
    global must_draw_budget_window
    must_draw_budget_window = True


def really_draw_budget_window() -> None:
    """
    Actually draw/update the budget window.

    Ported from ReallyDrawBudgetWindow() in w_budget.c.
    In pygame version, this would update the UI display.
    """
    global must_draw_budget_window

    # Calculate cash flow
    cash_flow = types.tax_fund - fire_value - police_value - road_value
    cash_flow2 = cash_flow

    # Format cash flow string
    if cash_flow < 0:
        cash_flow = -cash_flow
        flow_str = f"-${cash_flow:,}"  # For future UI integration
    else:
        flow_str = f"+${cash_flow:,}"  # For future UI integration

    # Format other values (for future UI integration)
    previous_str = f"${types.total_funds:,}"
    current_str = f"${cash_flow2 + types.total_funds:,}"
    collected_str = f"${types.tax_fund:,}"

    # In pygame version, this would send data to UI
    # For now, just mark as drawn
    must_draw_budget_window = False


def draw_curr_percents() -> None:
    """
    Mark current percentages for redraw.

    Ported from drawCurrPercents() in w_budget.c.
    """
    global must_draw_curr_percents
    must_draw_curr_percents = True


def really_draw_curr_percents() -> None:
    """
    Actually draw/update current budget percentages.

    Ported from ReallyDrawCurrPercents() in w_budget.c.
    """
    global must_draw_curr_percents

    # Format budget values (for future UI integration)
    fire_want = f"${fire_max_value:,}"
    police_want = f"${police_max_value:,}"
    road_want = f"${road_max_value:,}"

    fire_got = f"${int(fire_max_value * fire_percent):,}"
    police_got = f"${int(police_max_value * police_percent):,}"
    road_got = f"${int(road_max_value * road_percent):,}"

    # In pygame version, this would send data to UI
    # For now, just mark as drawn
    must_draw_curr_percents = False


def update_budget_window() -> None:
    """
    Update budget window if needed.

    Ported from UpdateBudgetWindow() in w_budget.c.
    """
    global must_draw_curr_percents, must_draw_budget_window

    if must_draw_curr_percents:
        really_draw_curr_percents()
        must_draw_curr_percents = False
    if must_draw_budget_window:
        really_draw_budget_window()
        must_draw_budget_window = False


def update_budget() -> None:
    """
    Update budget display.

    Ported from UpdateBudget() in w_budget.c.
    """
    draw_curr_percents()
    draw_budget_window()
    # In original, this calls Eval("UIUpdateBudget")
    # In pygame version, this would trigger UI update


def show_budget_window_and_start_waiting() -> None:
    """
    Show budget window and pause for user input.

    Ported from ShowBudgetWindowAndStartWaiting() in w_budget.c.
    In pygame version, this would show modal dialog.
    """
    # In original, this calls Eval("UIShowBudgetAndWait")
    # In pygame version, this would show budget dialog
    # For now, just pause simulation
    types.sim_paused = True


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


def spend(amount: int) -> None:
    """
    Spend money from city funds.

    Ported from Spend() function referenced in w_budget.c.
    """
    types.total_funds -= amount
    types.must_update_funds = 1
    kick()


# ============================================================================
# Budget Accessor Functions
# ============================================================================


def get_road_percent() -> float:
    """Get road funding percentage."""
    return road_percent


def set_road_percent(percent: float) -> None:
    """Set road funding percentage."""
    global road_percent
    road_percent = max(0.0, min(1.0, percent))


def get_police_percent() -> float:
    """Get police funding percentage."""
    return police_percent


def set_police_percent(percent: float) -> None:
    """Set police funding percentage."""
    global police_percent
    police_percent = max(0.0, min(1.0, percent))


def get_fire_percent() -> float:
    """Get fire funding percentage."""
    return fire_percent


def set_fire_percent(percent: float) -> None:
    """Set fire funding percentage."""
    global fire_percent
    fire_percent = max(0.0, min(1.0, percent))


def get_road_value() -> int:
    """Get allocated road funding."""
    return road_value


def get_police_value() -> int:
    """Get allocated police funding."""
    return police_value


def get_fire_value() -> int:
    """Get allocated fire funding."""
    return fire_value


def get_road_max_value() -> int:
    """Get maximum road funding request."""
    return road_max_value


def get_police_max_value() -> int:
    """Get maximum police funding request."""
    return police_max_value


def get_fire_max_value() -> int:
    """Get maximum fire funding request."""
    return fire_max_value


# ============================================================================
# TCL Command Interface Functions
# ============================================================================


def auto_budget(enabled: bool | None = None) -> int:
    """
    Get or set auto-budget mode.

    Ported from SimCmdAutoBudget in w_sim.c.
    """
    if enabled is not None:
        types.auto_budget = enabled
        types.must_update_options = 1
        kick()
        update_budget()

    return types.auto_budget


def do_budget_command() -> None:
    """
    Execute budget calculation.

    Ported from SimCmdDoBudget in w_sim.c.
    """
    do_budget()
    kick()


def do_budget_from_menu_command() -> None:
    """
    Execute budget calculation from menu.

    Ported from SimCmdDoBudgetFromMenu in w_sim.c.
    """
    do_budget_from_menu()
    kick()


def update_budget_command() -> None:
    """
    Update budget display.

    Ported from SimCmdUpdateBudget in w_sim.c.
    """
    update_budget()
    kick()


def update_budget_window_command() -> None:
    """
    Update budget window display.

    Ported from SimCmdUpdateBudgetWindow in w_sim.c.
    """
    update_budget_window()
    kick()
