"""
updates.py - UI Update Management for Micropolis

This module handles updating various UI components in response to
simulation state changes. It replaces the w_update.c functionality
with a Python-based update management system.

Key responsibilities:
- Funds display updates
- Date/time updates
- Valve/demand controls (R, C, I valves)
- Options menu updates
- Graph updates
- Evaluation updates
"""




from collections.abc import Callable


def make_dollar_decimal_str(amount: int) -> str:
    """
    Format a dollar amount with decimal places.
    Equivalent to makeDollarDecimalStr() in w_update.c
    """
    if amount < 0:
        return "0"

    # Format with commas and decimal
    amount_str = f"{amount}"
    if len(amount_str) <= 3:
        return amount_str

    # Add commas for thousands
    result = ""
    for i, char in enumerate(reversed(amount_str)):
        if i > 0 and i % 3 == 0:
            result = "," + result
        result = char + result

    return result


class UIUpdateManager:
    """
    Manages UI updates for various Micropolis components.

    This class centralizes the logic for determining when UI elements
    need to be updated and provides callbacks for the UI to respond
    to state changes.
    """

    def __init__(self):
        # Update flags
        self.must_update_funds = False
        self.must_update_options = False
        self.valve_flag = False

        # Last known values for change detection
        self.last_city_time = -1
        self.last_city_year = -1
        self.last_city_month = -1
        self.last_funds = -1
        self.last_r_valve = -999999.0
        self.last_c_valve = -999999.0
        self.last_i_valve = -999999.0

        # Callbacks for UI updates
        self.callbacks: dict[str, Callable] = {}

        # Simulation state references (will be set externally)
        self.city_time = 0
        self.starting_year = 1900
        self.total_funds = 0
        self.r_valve = 0.0
        self.c_valve = 0.0
        self.i_valve = 0.0

        # Options state
        self.auto_budget = False
        self.auto_go = False
        self.auto_bulldoze = False
        self.no_disasters = True
        self.user_sound_on = True
        self.do_animation = True
        self.do_messages = True
        self.do_notices = True

    def register_callback(self, event_type: str, callback: Callable):
        """
        Register a callback function for a specific update event.

        Args:
            event_type: Type of update event ('funds', 'date', 'valves', 'options', etc.)
            callback: Function to call when the event occurs
        """
        self.callbacks[event_type] = callback

    def unregister_callback(self, event_type: str):
        """Unregister a callback for an event type."""
        self.callbacks.pop(event_type, None)

    def update_heads(self):
        """
        Update all major UI heads (funds, valves, options).
        Equivalent to DoUpdateHeads() in w_update.c
        """
        self.show_valves()
        self.do_time_stuff()
        self.really_update_funds()
        self.update_options()

    def update_editors(self):
        """
        Update editor views.
        Equivalent to UpdateEditors() in w_update.c
        """
        self.invalidate_editors()
        self.update_heads()

    def update_maps(self):
        """
        Update map views.
        Equivalent to UpdateMaps() in w_update.c
        """
        self.invalidate_maps()

    def update_graphs(self):
        """
        Update graph displays.
        Equivalent to UpdateGraphs() in w_update.c
        """
        self.change_census()

    def update_evaluation(self):
        """
        Update evaluation displays.
        Equivalent to UpdateEvaluation() in w_update.c
        """
        self.change_eval()

    def update_heads_full(self):
        """
        Force full update of all heads.
        Equivalent to UpdateHeads() in w_update.c
        """
        self.must_update_funds = True
        self.valve_flag = True
        self.last_city_time = self.last_city_year = self.last_city_month = self.last_funds = self.last_r_valve = -999999
        self.update_heads()

    def update_funds(self):
        """
        Mark funds for update.
        Equivalent to UpdateFunds() in w_update.c
        """
        self.must_update_funds = True

    def really_update_funds(self):
        """
        Actually update the funds display if needed.
        Equivalent to ReallyUpdateFunds() in w_update.c
        """
        if not self.must_update_funds:
            return

        self.must_update_funds = False

        # Ensure funds are not negative
        if self.total_funds < 0:
            self.total_funds = 0

        if self.total_funds != self.last_funds:
            self.last_funds = self.total_funds
            funds_str = make_dollar_decimal_str(self.total_funds)
            local_str = f"Funds: {funds_str}"

            # Call UI update callback
            if 'funds' in self.callbacks:
                self.callbacks['funds'](local_str)

    def do_time_stuff(self):
        """
        Handle time-related updates.
        Equivalent to doTimeStuff() in w_update.c
        """
        self.update_date()

    def update_date(self):
        """
        Update the date display.
        Equivalent to updateDate() in w_update.c
        """
        # Calculate year and month from city time
        # City time is in 1/4 months, so divide by 4 for months
        year = (self.city_time // 48) + self.starting_year
        month = (self.city_time % 48) // 4

        # Handle year overflow
        if year >= 1000000:
            self.set_year(self.starting_year)
            year = self.starting_year
            self.send_message(-40)  # Year overflow message

        self.do_message()

        if self.last_city_year != year or self.last_city_month != month:
            self.last_city_year = year
            self.last_city_month = month

            month_names = [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
            ]

            date_str = f"{month_names[month]} {year}"

            # Call UI update callback
            if 'date' in self.callbacks:
                self.callbacks['date'](date_str, month, year)

    def show_valves(self):
        """
        Update valve displays if needed.
        Equivalent to showValves() in w_update.c
        """
        if self.valve_flag:
            self.draw_valve()
            self.valve_flag = False

    def draw_valve(self):
        """
        Draw/update the valve controls.
        Equivalent to drawValve() in w_update.c
        """
        # Clamp valve values
        r = self.r_valve
        if r < -1500:
            r = -1500
        if r > 1500:
            r = 1500

        c = self.c_valve
        if c < -1500:
            c = -1500
        if c > 1500:
            c = 1500

        i = self.i_valve
        if i < -1500:
            i = -1500
        if i > 1500:
            i = 1500

        if (r != self.last_r_valve or
            c != self.last_c_valve or
            i != self.last_i_valve):
            self.last_r_valve = r
            self.last_c_valve = c
            self.last_i_valve = i
            self.set_demand(r, c, i)

    def set_demand(self, r: float, c: float, i: float):
        """
        Set the demand values for R, C, I.
        Equivalent to SetDemand() in w_update.c
        """
        # Convert to hundredths for display
        r_hundredths = int(r / 100)
        c_hundredths = int(c / 100)
        i_hundredths = int(i / 100)

        # Call UI update callback
        if 'demand' in self.callbacks:
            self.callbacks['demand'](r_hundredths, c_hundredths, i_hundredths)

    def update_options(self):
        """
        Update options menu if needed.
        Equivalent to updateOptions() in w_update.c
        """
        if self.must_update_options:
            options = 0
            if self.auto_budget:
                options |= 1
            if self.auto_go:
                options |= 2
            if self.auto_bulldoze:
                options |= 4
            if not self.no_disasters:
                options |= 8
            if self.user_sound_on:
                options |= 16
            if self.do_animation:
                options |= 32
            if self.do_messages:
                options |= 64
            if self.do_notices:
                options |= 128

            self.must_update_options = False
            self.update_options_menu(options)

    def update_options_menu(self, options: int):
        """
        Update the options menu display.
        Equivalent to UpdateOptionsMenu() in w_update.c
        """
        # Extract individual option flags
        option_flags = [
            (options & 1) != 0,    # auto_budget
            (options & 2) != 0,    # auto_go
            (options & 4) != 0,    # auto_bulldoze
            (options & 8) != 0,    # disasters enabled
            (options & 16) != 0,   # sound on
            (options & 32) != 0,   # animation on
            (options & 64) != 0,   # messages on
            (options & 128) != 0   # notices on
        ]

        # Call UI update callback
        if 'options' in self.callbacks:
            self.callbacks['options'](option_flags)

    # Utility methods

    # Stub methods for functionality that would be implemented elsewhere
    def invalidate_editors(self):
        """Invalidate editor views - stub implementation."""
        pass

    def invalidate_maps(self):
        """Invalidate map views - stub implementation."""
        pass

    def change_census(self):
        """Change census data - stub implementation."""
        pass

    def change_eval(self):
        """Change evaluation data - stub implementation."""
        pass

    def set_year(self, year: int):
        """Set the starting year - stub implementation."""
        self.starting_year = year

    def send_message(self, message_id: int):
        """Send a message - stub implementation."""
        pass

    def do_message(self):
        """Process messages - stub implementation."""
        pass


# Global instance for easy access
update_manager = UIUpdateManager()


# Convenience functions for backward compatibility
def DoUpdateHeads():
    """Update all major UI heads."""
    update_manager.update_heads()


def UpdateEditors():
    """Update editor views."""
    update_manager.update_editors()


def UpdateMaps():
    """Update map views."""
    update_manager.update_maps()


def UpdateGraphs():
    """Update graph displays."""
    update_manager.update_graphs()


def UpdateEvaluation():
    """Update evaluation displays."""
    update_manager.update_evaluation()


def UpdateHeads():
    """Force full update of all heads."""
    update_manager.update_heads_full()


def UpdateFunds():
    """Mark funds for update."""
    update_manager.update_funds()


def ReallyUpdateFunds():
    """Actually update the funds display."""
    update_manager.really_update_funds()


def doTimeStuff():
    """Handle time-related updates."""
    update_manager.do_time_stuff()


def updateDate():
    """Update the date display."""
    update_manager.update_date()


def showValves():
    """Update valve displays."""
    update_manager.show_valves()


def drawValve():
    """Draw/update the valve controls."""
    update_manager.draw_valve()


def SetDemand(r: float, c: float, i: float):
    """Set the demand values."""
    update_manager.set_demand(r, c, i)


def updateOptions():
    """Update options menu."""
    update_manager.update_options()


def UpdateOptionsMenu(options: int):
    """Update the options menu display."""
    update_manager.update_options_menu(options)