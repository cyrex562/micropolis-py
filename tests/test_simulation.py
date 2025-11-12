"""
test_simulation.py - Integration tests for core simulation logic

This module tests the simulation.py module to ensure it produces
the same outputs as the original C version for given inputs.
"""

import micropolis.constants
import pytest
from unittest.mock import patch

from src.micropolis import types, simulation


class TestSimulationIntegration:
    """Integration tests for simulation step logic"""

    def setup_method(self):
        """Set up test environment before each test"""
        # Initialize basic simulation state
        types.sim_speed = 2
        types.city_time = 0
        types.total_pop = 1
        types.do_initial_eval = 0

        # Initialize map with some basic tiles
        for x in range(micropolis.constants.WORLD_X):
            for y in range(micropolis.constants.WORLD_Y):
                types.map_data[x][y] = 0

        # Reset simulation counters
        simulation.fcycle = 0
        simulation.scycle = 0
        simulation.spdcycle = 0

    def test_simulate_phase_0_initialization(self):
        """Test phase 0: time increment, valve setting, census clearing"""
        # Set up initial state
        initial_time = types.city_time
        types.sim_speed = 2

        # Run phase 0
        simulation.simulate(context, 0)

        # Verify time incremented
        assert types.city_time == initial_time + 1

        # Verify Scycle incremented
        assert simulation.scycle == 1

        # Verify census was cleared (check some counters)
        assert types.res_pop == 0
        assert types.com_pop == 0
        assert types.ind_pop == 0

    def test_clear_census_resets_counters(self):
        """Test that ClearCensus resets all population counters"""
        # Set some non-zero values
        types.res_pop = 100
        types.com_pop = 50
        types.fire_pop = 10
        types.road_total = 200

        # Clear census
        simulation.clear_census(context)

        # Verify all counters reset to 0
        assert types.res_pop == 0
        assert types.com_pop == 0
        assert types.ind_pop == 0
        assert types.fire_pop == 0
        assert types.road_total == 0
        assert types.rail_total == 0

    def test_dec_traffic_mem_decay(self):
        """Test traffic memory decay over time"""
        # Set up traffic density values
        types.trf_density[0][0] = 50  # Medium density
        types.trf_density[1][1] = 250  # High density
        types.trf_density[2][2] = 10  # Low density

        # Run decay
        simulation.dec_traffic_mem(context)

        assert types.trf_density[0][0] == 50 - 24  # 26-200 range
        assert types.trf_density[1][1] == 250 - 34  # >200 range
        assert types.trf_density[2][2] == 0  # <24 becomes 0
