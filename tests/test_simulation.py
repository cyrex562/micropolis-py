"""
test_simulation.py - Integration tests for core simulation logic

This module tests the simulation.py module to ensure it produces
the same outputs as the original C version for given inputs.
"""

import micropolis.constants
from micropolis.context import AppContext
from micropolis import simulation

context: AppContext


class TestSimulationIntegration:
    """Integration tests for simulation step logic"""

    def setup_method(self):
        """Set up test environment before each test"""
        # Initialize basic simulation state
        context.sim_speed = 2
        context.city_time = 0
        context.total_pop = 1
        context.do_initial_eval = 0

        # Initialize map with some basic tiles
        for x in range(micropolis.constants.WORLD_X):
            for y in range(micropolis.constants.WORLD_Y):
                context.map_data[x][y] = 0

        # Reset simulation counters
        simulation.fcycle = 0
        simulation.scycle = 0
        simulation.spdcycle = 0

    def test_simulate_phase_0_initialization(self):
        """Test phase 0: time increment, valve setting, census clearing"""
        # Set up initial state
        initial_time = context.city_time
        context.sim_speed = 2

        # Run phase 0
        simulation.simulate(context, 0)

        # Verify time incremented
        assert context.city_time == initial_time + 1

        # Verify Scycle incremented
        assert simulation.scycle == 1

        # Verify census was cleared (check some counters)
        assert context.res_pop == 0
        assert context.com_pop == 0
        assert context.ind_pop == 0

    def test_clear_census_resets_counters(self):
        """Test that ClearCensus resets all population counters"""
        # Set some non-zero values
        context.res_pop = 100
        context.com_pop = 50
        context.fire_pop = 10
        context.road_total = 200

        # Clear census
        simulation.clear_census(context)

        # Verify all counters reset to 0
        assert context.res_pop == 0
        assert context.com_pop == 0
        assert context.ind_pop == 0
        assert context.fire_pop == 0
        assert context.road_total == 0
        assert context.rail_total == 0

    def test_dec_traffic_mem_decay(self):
        """Test traffic memory decay over time"""
        # Set up traffic density values
        context.trf_density[0][0] = 50  # Medium density
        context.trf_density[1][1] = 250  # High density
        context.trf_density[2][2] = 10  # Low density

        # Run decay
        simulation.dec_traffic_mem(context)

        assert context.trf_density[0][0] == 50 - 24  # 26-200 range
        assert context.trf_density[1][1] == 250 - 34  # >200 range
        assert context.trf_density[2][2] == 0  # <24 becomes 0
