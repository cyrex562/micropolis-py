"""
test_stubs.py - Tests for stub implementations

Tests the stub functions and global variables from stubs.py.
These tests ensure that the stub implementations work correctly
and maintain API compatibility with the original C code.
"""

import time
import pytest
from unittest.mock import patch

from src.micropolis import stubs


class TestFinancialFunctions:
    """Test financial functions."""

    def test_spend(self):
        """Test spending money."""
        # Reset funds
        stubs.SetFunds(1000)
        assert stubs.total_funds == 1000

        # Spend some money
        stubs.Spend(context, 200)
        assert stubs.total_funds == 800

    def test_set_funds(self):
        """Test setting funds directly."""
        stubs.SetFunds(500)
        assert stubs.total_funds == 500

        stubs.SetFunds(0)
        assert stubs.total_funds == 0


class TestMacCompatibility:
    """Test Mac compatibility functions."""

    def test_tick_count(self):
        """Test tick count function."""
        tick1 = stubs.TickCount()
        time.sleep(0.01)  # Small delay
        tick2 = stubs.TickCount()

        # Should be monotonically increasing
        assert tick2 >= tick1
        assert isinstance(tick1, int)
        assert isinstance(tick2, int)

    def test_new_ptr(self):
        """Test memory allocation function."""
        # Valid allocation
        ptr = stubs.NewPtr(100)
        assert ptr is not None
        assert len(ptr) == 100
        assert isinstance(ptr, bytes)

        # Zero size
        ptr_zero = stubs.NewPtr(0)
        assert ptr_zero is not None
        assert len(ptr_zero) == 0

        # Large allocation (should still work in Python)
        ptr_large = stubs.NewPtr(1000000)
        assert ptr_large is not None
        assert len(ptr_large) == 1000000


class TestGameLifecycle:
    """Test game lifecycle functions."""

    def test_game_started_new_city(self):
        """Test game started with new city."""
        # Setup
        stubs.SetStartupMode(-1)
        stubs.SetStartupName("TestCity")

        # Mock the types module
        with patch("src.micropolis.stubs.types") as mock_types:
            stubs.GameStarted()

            # Check that maps and editors were invalidated
            # Check that city name was set
            mock_types.setCityName.assert_called_once_with("TestCity")

    def test_game_started_scenario(self):
        """Test game started with scenario."""
        # Setup
        stubs.SetStartupMode(5)  # Scenario 5

        stubs.GameStarted()

    def test_do_play_new_city(self):
        """Test playing new city."""
        stubs.DoPlayNewCity()

    def test_do_really_start_game(self):
        """Test really starting game."""
        stubs.DoReallyStartGame()

    def test_do_start_load(self):
        """Test starting load."""
        stubs.DoStartLoad()

    def test_do_start_scenario(self):
        """Test starting scenario."""
        stubs.DoStartScenario(3)

    def test_drop_fire_bombs(self):
        """Test dropping fire bombs."""
        stubs.DropFireBombs()

    @patch("src.micropolis.engine.sim_exit")
    def test_really_quit(self, mock_exit):
        """Test really quitting."""
        stubs.ReallyQuit()
        mock_exit.assert_called_once_with(0)


class TestGameState:
    """Test game state management."""

    def test_game_level(self):
        """Test game level getter/setter."""
        stubs.SetGameLevel(2)
        assert stubs.GetGameLevel() == 2

        stubs.SetGameLevel(0)
        assert stubs.GetGameLevel() == 0

    def test_sim_speed(self):
        """Test simulation speed getter/setter."""
        stubs.SetSimSpeed(3)
        assert stubs.GetSimSpeed(context) == 3

        stubs.SetSimSpeed(0)
        assert stubs.GetSimSpeed(context) == 0

    def test_no_disasters(self):
        """Test no disasters getter/setter."""
        stubs.SetNoDisasters(True)
        assert stubs.GetNoDisasters() is True

        stubs.SetNoDisasters(False)
        assert stubs.GetNoDisasters() is False

    def test_auto_bulldoze(self):
        """Test auto bulldoze getter/setter."""
        stubs.SetAutoBulldoze(True)
        assert stubs.GetAutoBulldoze() is True

        stubs.SetAutoBulldoze(False)
        assert stubs.GetAutoBulldoze() is False

    def test_auto_budget(self):
        """Test auto budget getter/setter."""
        stubs.SetAutoBudget(True)
        assert stubs.GetAutoBudget() is True

        stubs.SetAutoBudget(False)
        assert stubs.GetAutoBudget() is False

    def test_user_sound_on(self):
        """Test user sound getter/setter."""
        stubs.SetUserSoundOn(True)
        assert stubs.GetUserSoundOn() is True

        stubs.SetUserSoundOn(False)
        assert stubs.GetUserSoundOn() is False

    def test_city_name(self):
        """Test city name getter/setter."""
        stubs.SetCityName("TestCity")
        assert stubs.GetCityName() == "TestCity"

        stubs.SetCityName("")
        assert stubs.GetCityName() == ""

    def test_scenario_id(self):
        """Test scenario ID getter/setter."""
        stubs.SetScenarioID(context, 7)
        assert stubs.GetScenarioID() == 7

        stubs.SetScenarioID(context, 0)
        assert stubs.GetScenarioID() == 0

    def test_startup_mode(self):
        """Test startup mode getter/setter."""
        stubs.SetStartupMode(-1)
        assert stubs.GetStartupMode() == -1

        stubs.SetStartupMode(0)
        assert stubs.GetStartupMode() == 0

    def test_startup_name(self):
        """Test startup name getter/setter."""
        stubs.SetStartupName("TestCity")
        assert stubs.GetStartupName() == "TestCity"

        stubs.SetStartupName(None)
        assert stubs.GetStartupName() is None


class TestInitialization:
    """Test initialization and cleanup."""

    def test_init_game(self):
        """Test game initialization."""
        # Set some non-zero values first
        stubs.sim_skips = 5
        stubs.sim_skip = 2
        stubs.sim_paused = 1
        stubs.sim_paused_speed = 3
        stubs.heat_steps = 10

        with patch("src.micropolis.stubs.types") as mock_types:
            stubs.InitGame()

            # Check that simulation variables were reset
            assert stubs.sim_skips == 0
            assert stubs.sim_skip == 0
            assert stubs.sim_paused == 0
            assert stubs.sim_paused_speed == 0
            assert stubs.heat_steps == 0

            # Check that speed was set
            mock_types.setSpeed.assert_called_once_with(0)

    def test_initialize_stubs(self):
        """Test stub initialization."""
        old_time = stubs.start_time
        stubs.initialize_stubs()

        # Should set start_time to current time
        assert stubs.start_time is not None
        assert stubs.start_time != old_time

    def test_cleanup_stubs(self):
        """Test stub cleanup."""
        # Cleanup should not raise any exceptions
        stubs.cleanup_stubs()


class TestGlobalVariables:
    """Test global variable initialization."""

    def test_global_variables_exist(self):
        """Test that all global variables are properly initialized."""
        # Financial
        assert hasattr(stubs, "TotalFunds")
        assert isinstance(stubs.total_funds, int)

        # Game state
        assert hasattr(stubs, "PunishCnt")
        assert hasattr(stubs, "autoBulldoze")
        assert hasattr(stubs, "autoBudget")
        assert hasattr(stubs, "LastMesTime")
        assert hasattr(stubs, "GameLevel")
        assert hasattr(stubs, "InitSimLoad")
        assert hasattr(stubs, "ScenarioID")
        assert hasattr(stubs, "SimSpeed")
        assert hasattr(stubs, "SimMetaSpeed")
        assert hasattr(stubs, "UserSoundOn")
        assert hasattr(stubs, "CityName")
        assert hasattr(stubs, "NoDisasters")
        assert hasattr(stubs, "MesNum")
        assert hasattr(stubs, "EvalChanged")
        assert hasattr(stubs, "flagBlink")

        # Game startup
        assert hasattr(stubs, "Startup")
        assert hasattr(stubs, "StartupName")

        # Timing
        assert hasattr(stubs, "start_time")

        # Simulation control
        assert hasattr(stubs, "sim_skips")
        assert hasattr(stubs, "sim_skip")
        assert hasattr(stubs, "sim_paused")
        assert hasattr(stubs, "sim_paused_speed")
        assert hasattr(stubs, "heat_steps")
