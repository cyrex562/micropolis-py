"""
test_simulation.py - Integration tests for core simulation logic

This module tests the simulation.py module to ensure it produces
the same outputs as the original C version for given inputs.
"""

import pytest
from unittest.mock import patch

from src.micropolis import types, simulation


class TestSimulationIntegration:
    """Integration tests for simulation step logic"""

    def setup_method(self):
        """Set up test environment before each test"""
        # Initialize basic simulation state
        types.SimSpeed = 2
        types.CityTime = 0
        types.TotalPop = 1
        types.DoInitialEval = 0

        # Initialize map with some basic tiles
        for x in range(types.WORLD_X):
            for y in range(types.WORLD_Y):
                types.Map[x][y] = 0

        # Reset simulation counters
        simulation.Fcycle = 0
        simulation.Scycle = 0
        simulation.Spdcycle = 0

    def test_simulate_phase_0_initialization(self):
        """Test phase 0: time increment, valve setting, census clearing"""
        # Set up initial state
        initial_time = types.CityTime
        types.SimSpeed = 2

        # Run phase 0
        simulation.Simulate(0)

        # Verify time incremented
        assert types.CityTime == initial_time + 1

        # Verify Scycle incremented
        assert simulation.Scycle == 1

        # Verify census was cleared (check some counters)
        assert types.ResPop == 0
        assert types.ComPop == 0
        assert types.IndPop == 0

    def test_clear_census_resets_counters(self):
        """Test that ClearCensus resets all population counters"""
        # Set some non-zero values
        types.ResPop = 100
        types.ComPop = 50
        types.FirePop = 10
        types.RoadTotal = 200

        # Clear census
        simulation.ClearCensus()

        # Verify all counters reset to 0
        assert types.ResPop == 0
        assert types.ComPop == 0
        assert types.IndPop == 0
        assert types.FirePop == 0
        assert types.RoadTotal == 0
        assert types.RailTotal == 0

    def test_dec_traffic_mem_decay(self):
        """Test traffic memory decay over time"""
        # Set up traffic density values
        types.TrfDensity[0][0] = 50   # Medium density
        types.TrfDensity[1][1] = 250  # High density
        types.TrfDensity[2][2] = 10   # Low density

        # Run decay
        simulation.DecTrafficMem()

        assert types.TrfDensity[0][0] == 50 - 24  # 26-200 range
        assert types.TrfDensity[1][1] == 250 - 34  # >200 range
        assert types.TrfDensity[2][2] == 0         # <24 becomes 0