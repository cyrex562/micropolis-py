"""
Test suite for updates.py - UI Update Management

Tests the UI update management system that handles funds, date, valves, and options updates.
"""

from unittest.mock import Mock
from src.micropolis.updates import (
    UIUpdateManager, update_manager,
    DoUpdateHeads, UpdateEditors, UpdateMaps, UpdateGraphs, UpdateEvaluation,
    UpdateHeads, UpdateFunds, ReallyUpdateFunds, doTimeStuff, updateDate,
    showValves, drawValve, SetDemand, updateOptions, UpdateOptionsMenu
)


class TestUIUpdateManager:
    """Test the UIUpdateManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = UIUpdateManager()
        # Reset to clean state
        self.manager.must_update_funds = False
        self.manager.must_update_options = False
        self.manager.valve_flag = False
        self.manager.callbacks = {}

    def test_initialization(self):
        """Test manager initialization."""
        assert not self.manager.must_update_funds
        assert not self.manager.must_update_options
        assert not self.manager.valve_flag
        assert self.manager.callbacks == {}
        assert self.manager.city_time == 0
        assert self.manager.starting_year == 1900
        assert self.manager.total_funds == 0

    def test_register_callback(self):
        """Test registering callbacks."""
        callback = Mock()
        self.manager.register_callback('funds', callback)

        assert 'funds' in self.manager.callbacks
        assert self.manager.callbacks['funds'] == callback

    def test_unregister_callback(self):
        """Test unregistering callbacks."""
        callback = Mock()
        self.manager.register_callback('funds', callback)
        assert 'funds' in self.manager.callbacks

        self.manager.unregister_callback('funds')
        assert 'funds' not in self.manager.callbacks

    def test_update_heads(self):
        """Test update_heads method."""
        # Mock the individual update methods
        self.manager.show_valves = Mock()
        self.manager.do_time_stuff = Mock()
        self.manager.really_update_funds = Mock()
        self.manager.update_options = Mock()

        self.manager.update_heads()

        self.manager.show_valves.assert_called_once()
        self.manager.do_time_stuff.assert_called_once()
        self.manager.really_update_funds.assert_called_once()
        self.manager.update_options.assert_called_once()

    def test_update_editors(self):
        """Test update_editors method."""
        self.manager.invalidate_editors = Mock()
        self.manager.update_heads = Mock()

        self.manager.update_editors()

        self.manager.invalidate_editors.assert_called_once()
        self.manager.update_heads.assert_called_once()

    def test_update_maps(self):
        """Test update_maps method."""
        self.manager.invalidate_maps = Mock()

        self.manager.update_maps()

        self.manager.invalidate_maps.assert_called_once()

    def test_update_graphs(self):
        """Test update_graphs method."""
        self.manager.change_census = Mock()

        self.manager.update_graphs()

        self.manager.change_census.assert_called_once()

    def test_update_evaluation(self):
        """Test update_evaluation method."""
        self.manager.change_eval = Mock()

        self.manager.update_evaluation()

        self.manager.change_eval.assert_called_once()

    def test_update_heads_full(self):
        """Test update_heads_full method."""
        self.manager.update_heads = Mock()

        # Set some initial values
        self.manager.last_city_time = 100
        self.manager.last_funds = 500
        self.manager.last_r_valve = 100.0

        self.manager.update_heads_full()

        # Check flags are set
        assert self.manager.must_update_funds
        assert self.manager.valve_flag

        # Check values are reset
        assert self.manager.last_city_time == -999999
        assert self.manager.last_city_year == -999999
        assert self.manager.last_city_month == -999999
        assert self.manager.last_funds == -999999
        assert self.manager.last_r_valve == -999999.0

        self.manager.update_heads.assert_called_once()

    def test_update_funds(self):
        """Test update_funds method."""
        assert not self.manager.must_update_funds

        self.manager.update_funds()

        assert self.manager.must_update_funds

    def test_really_update_funds_no_update_needed(self):
        """Test really_update_funds when no update is needed."""
        self.manager.must_update_funds = False
        callback = Mock()
        self.manager.register_callback('funds', callback)

        self.manager.really_update_funds()

        callback.assert_not_called()

    def test_really_update_funds_with_callback(self):
        """Test really_update_funds with callback."""
        self.manager.must_update_funds = True
        self.manager.total_funds = 1234
        self.manager.last_funds = 999  # Different from current

        callback = Mock()
        self.manager.register_callback('funds', callback)

        self.manager.really_update_funds()

        # Should call callback with formatted funds string
        callback.assert_called_once()
        args = callback.call_args[0]
        assert "Funds:" in args[0]
        assert "1,234" in args[0]  # Formatted with comma

        # Should reset flag
        assert not self.manager.must_update_funds
        # Should update last_funds
        assert self.manager.last_funds == 1234

    def test_really_update_funds_negative(self):
        """Test really_update_funds with negative funds."""
        self.manager.must_update_funds = True
        self.manager.total_funds = -100

        self.manager.really_update_funds()

        # Should set funds to 0
        assert self.manager.total_funds == 0

    def test_make_dollar_decimal_str(self):
        """Test dollar formatting."""
        assert make_dollar_decimal_str(0) == "0"
        assert make_dollar_decimal_str(123) == "123"
        assert make_dollar_decimal_str(1234) == "1,234"
        assert make_dollar_decimal_str(1234567) == "1,234,567"

    def test_do_time_stuff(self):
        """Test do_time_stuff method."""
        self.manager.update_date = Mock()

        self.manager.do_time_stuff()

        self.manager.update_date.assert_called_once()

    def test_update_date(self):
        """Test update_date method."""
        self.manager.city_time = 100  # Some time value
        self.manager.starting_year = 1900

        callback = Mock()
        self.manager.register_callback('date', callback)

        self.manager.update_date()

        # Should call callback with date string, month, year
        callback.assert_called_once()
        args = callback.call_args[0]
        date_str, month, year = args

        assert isinstance(date_str, str)
        assert "1902" in date_str  # Should contain the year (100//48 + 1900 = 2 + 1900 = 1902)
        assert isinstance(month, int)
        assert isinstance(year, int)
        assert year == 1902  # (100 // 48) + 1900 = 2 + 1900 = 1902

    def test_update_date_year_overflow(self):
        """Test update_date with year overflow."""
        self.manager.city_time = 1000000 * 48  # Very large time
        self.manager.starting_year = 1900
        self.manager.send_message = Mock()

        callback = Mock()
        self.manager.register_callback('date', callback)

        self.manager.update_date()

        # Should handle overflow
        self.manager.send_message.assert_called_once_with(-40)

    def test_show_valves(self):
        """Test show_valves method."""
        self.manager.valve_flag = True
        self.manager.draw_valve = Mock()

        self.manager.show_valves()

        self.manager.draw_valve.assert_called_once()
        assert not self.manager.valve_flag

    def test_draw_valve(self):
        """Test draw_valve method."""
        self.manager.r_valve = 100.0
        self.manager.c_valve = 200.0
        self.manager.i_valve = 300.0
        self.manager.last_r_valve = 50.0  # Different values
        self.manager.last_c_valve = 60.0
        self.manager.last_i_valve = 70.0

        callback = Mock()
        self.manager.register_callback('demand', callback)

        self.manager.draw_valve()

        # Should call callback with clamped values divided by 100
        callback.assert_called_once_with(1, 2, 3)  # 100/100, 200/100, 300/100

        # Should update last values
        assert self.manager.last_r_valve == 100.0
        assert self.manager.last_c_valve == 200.0
        assert self.manager.last_i_valve == 300.0

    def test_draw_valve_clamping(self):
        """Test draw_valve with value clamping."""
        self.manager.r_valve = 2000.0  # Over max
        self.manager.c_valve = -2000.0  # Under min
        self.manager.i_valve = 100.0  # Normal

        callback = Mock()
        self.manager.register_callback('demand', callback)

        self.manager.draw_valve()

        # Should clamp values
        callback.assert_called_once_with(15, -15, 1)  # Clamped to ±1500, divided by 100

    def test_set_demand(self):
        """Test set_demand method."""
        callback = Mock()
        self.manager.register_callback('demand', callback)

        self.manager.set_demand(100.0, 200.0, 300.0)

        callback.assert_called_once_with(1, 2, 3)  # Divided by 100

    def test_update_options(self):
        """Test update_options method."""
        self.manager.must_update_options = True
        self.manager.auto_budget = True
        self.manager.auto_go = False
        self.manager.auto_bulldoze = True
        self.manager.no_disasters = False
        self.manager.user_sound_on = True
        self.manager.do_animation = False
        self.manager.do_messages = True
        self.manager.do_notices = False

        self.manager.update_options_menu = Mock()

        self.manager.update_options()

        # Should call update_options_menu with correct bitmask
        expected_options = 1 | 4 | 8 | 16 | 64  # auto_budget, auto_bulldoze, disasters, sound, messages
        self.manager.update_options_menu.assert_called_once_with(expected_options)
        assert not self.manager.must_update_options

    def test_update_options_menu(self):
        """Test update_options_menu method."""
        callback = Mock()
        self.manager.register_callback('options', callback)

        # Test with some options set
        options = 1 | 4 | 16  # auto_budget, auto_bulldoze, sound
        self.manager.update_options_menu(options)

        callback.assert_called_once_with([True, False, True, False, True, False, False, False])


class TestConvenienceFunctions:
    """Test the convenience functions that wrap the global manager."""

    def setup_method(self):
        """Set up test fixtures."""
        # Reset global manager
        update_manager.must_update_funds = False
        update_manager.must_update_options = False
        update_manager.valve_flag = False
        update_manager.callbacks = {}

    def test_do_update_heads(self):
        """Test DoUpdateHeads convenience function."""
        update_manager.update_heads = Mock()

        DoUpdateHeads()

        update_manager.update_heads.assert_called_once()

    def test_update_editors_convenience(self):
        """Test UpdateEditors convenience function."""
        update_manager.update_editors = Mock()

        UpdateEditors()

        update_manager.update_editors.assert_called_once()

    def test_update_maps_convenience(self):
        """Test UpdateMaps convenience function."""
        update_manager.update_maps = Mock()

        UpdateMaps()

        update_manager.update_maps.assert_called_once()

    def test_update_graphs_convenience(self):
        """Test UpdateGraphs convenience function."""
        update_manager.update_graphs = Mock()

        UpdateGraphs()

        update_manager.update_graphs.assert_called_once()

    def test_update_evaluation_convenience(self):
        """Test UpdateEvaluation convenience function."""
        update_manager.update_evaluation = Mock()

        UpdateEvaluation()

        update_manager.update_evaluation.assert_called_once()

    def test_update_heads_convenience(self):
        """Test UpdateHeads convenience function."""
        update_manager.update_heads_full = Mock()

        UpdateHeads()

        update_manager.update_heads_full.assert_called_once()

    def test_update_funds_convenience(self):
        """Test UpdateFunds convenience function."""
        UpdateFunds()

        assert update_manager.must_update_funds

    def test_really_update_funds_convenience(self):
        """Test ReallyUpdateFunds convenience function."""
        update_manager.really_update_funds = Mock()

        ReallyUpdateFunds()

        update_manager.really_update_funds.assert_called_once()

    def test_do_time_stuff_convenience(self):
        """Test doTimeStuff convenience function."""
        update_manager.do_time_stuff = Mock()

        doTimeStuff()

        update_manager.do_time_stuff.assert_called_once()

    def test_update_date_convenience(self):
        """Test updateDate convenience function."""
        update_manager.update_date = Mock()

        updateDate()

        update_manager.update_date.assert_called_once()

    def test_show_valves_convenience(self):
        """Test showValves convenience function."""
        update_manager.show_valves = Mock()

        showValves()

        update_manager.show_valves.assert_called_once()

    def test_draw_valve_convenience(self):
        """Test drawValve convenience function."""
        update_manager.draw_valve = Mock()

        drawValve()

        update_manager.draw_valve.assert_called_once()

    def test_set_demand_convenience(self):
        """Test SetDemand convenience function."""
        update_manager.set_demand = Mock()

        SetDemand(100.0, 200.0, 300.0)

        update_manager.set_demand.assert_called_once_with(100.0, 200.0, 300.0)

    def test_update_options_convenience(self):
        """Test updateOptions convenience function."""
        update_manager.update_options = Mock()

        updateOptions()

        update_manager.update_options.assert_called_once()

    def test_update_options_menu_convenience(self):
        """Test UpdateOptionsMenu convenience function."""
        update_manager.update_options_menu = Mock()

        UpdateOptionsMenu(42)

        update_manager.update_options_menu.assert_called_once_with(42)