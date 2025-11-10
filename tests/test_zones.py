"""
test_zones.py - Integration tests for zone processing and growth mechanics

Tests zone growth algorithms, population calculations, and building placement
to ensure outputs match the original C version behavior.
"""

import unittest.mock
from src.micropolis.zones import (
    DoZone, DoHospChur, DoResidential, DoCommercial, DoIndustrial,
    RZPop, CZPop, IZPop, GetCRVal, EvalRes, EvalCom, EvalInd,
    ZonePlop, ResPlop, ComPlop, IndPlop, SetZPower, DoFreePop, EvalLot
)
from src.micropolis import types, macros


from tests.assertions import Assertions

class TestZoneIntegration(Assertions):
    """Integration tests for zone processing functions."""

    def setUp(self):
        """Set up test fixtures with mock simulation state."""
        # Initialize basic simulation state
        types.Map = [[0 for _ in range(types.WORLD_Y)] for _ in range(types.WORLD_X)]
        types.PowerMap = bytearray(types.PWRMAPSIZE)
        types.LandValueMem = [[100 for _ in range(types.WORLD_Y // 2)] for _ in range(types.WORLD_X // 2)]
        types.PollutionMem = [[10 for _ in range(types.WORLD_Y // 2)] for _ in range(types.WORLD_X // 2)]
        types.PopDensity = [[32 for _ in range(types.WORLD_Y // 2)] for _ in range(types.WORLD_X // 2)]
        types.ComRate = [[1000 for _ in range(types.WORLD_Y // 8)] for _ in range(types.WORLD_X // 8)]
        types.RateOGMem = [[0 for _ in range(types.WORLD_Y // 8)] for _ in range(types.WORLD_X // 8)]

        # Reset counters
        types.ResPop = 0
        types.ComPop = 0
        types.IndPop = 0
        types.HospPop = 0
        types.ChurchPop = 0
        types.PwrdZCnt = 0
        types.unPwrdZCnt = 0
        types.NeedHosp = 0
        types.NeedChurch = 0

        # Set valve values
        types.RValve = 0
        types.CValve = 0
        types.IValve = 0

        # Set current position
        types.SMapX = 60
        types.SMapY = 50
        types.CChr9 = types.RZB  # Default to residential zone base
        types.CChr = types.CChr9

        # Mock random functions to return predictable values
        self.rand_patcher = unittest.mock.patch('src.micropolis.simulation.Rand', return_value=5)
        self.rand16_patcher = unittest.mock.patch('src.micropolis.simulation.Rand16', return_value=1000)
        self.rand16_signed_patcher = unittest.mock.patch('src.micropolis.simulation.Rand16Signed', return_value=0)
        self.rand_patcher.start()
        self.rand16_patcher.start()
        self.rand16_signed_patcher.start()

    def tearDown(self):
        """Clean up patches."""
        self.rand_patcher.stop()
        self.rand16_patcher.stop()
        self.rand16_signed_patcher.stop()

    def test_population_calculations_residential(self):
        """Test residential zone population calculations match C version."""
        # Test various residential zone densities
        test_cases = [
            (types.RZB, 16),      # Empty residential zone
            (types.RZB + 9, 24),  # Low density
            (types.RZB + 18, 32), # Medium density
            (types.RZB + 27, 40), # High density
            (types.RZB + 36, 16), # Wraps around (density % 4 = 0)
        ]

        for tile_value, expected_pop in test_cases:
            with self.subTest(tile_value=tile_value):
                result = RZPop(tile_value)
                self.assertEqual(result, expected_pop,
                    f"RZPop({tile_value}) should be {expected_pop}, got {result}")

    def test_population_calculations_commercial(self):
        """Test commercial zone population calculations match C version."""
        test_cases = [
            (types.COMCLR, 0),    # Commercial clear
            (types.CZB, 1),       # Base commercial
            (types.CZB + 9, 2),   # Low density
            (types.CZB + 18, 3),  # Medium density
            (types.CZB + 27, 4),  # High density
            (types.CZB + 36, 5),  # Max density
            (types.CZB + 45, 1),  # Wraps around (density % 5 = 0)
        ]

        for tile_value, expected_pop in test_cases:
            with self.subTest(tile_value=tile_value):
                result = CZPop(tile_value)
                self.assertEqual(result, expected_pop,
                    f"CZPop({tile_value}) should be {expected_pop}, got {result}")

    def test_population_calculations_industrial(self):
        """Test industrial zone population calculations match C version."""
        test_cases = [
            (types.INDCLR, 0),    # Industrial clear
            (types.IZB, 1),       # Base industrial
            (types.IZB + 9, 2),   # Low density
            (types.IZB + 18, 3),  # Medium density
            (types.IZB + 27, 4),  # High density
            (types.IZB + 36, 1),  # Wraps around (density % 4 = 0)
        ]

        for tile_value, expected_pop in test_cases:
            with self.subTest(tile_value=tile_value):
                result = IZPop(tile_value)
                self.assertEqual(result, expected_pop,
                    f"IZPop({tile_value}) should be {expected_pop}, got {result}")

    def test_get_cr_val_land_value_rating(self):
        """Test GetCRVal produces correct land value ratings."""
        test_cases = [
            # (land_value, pollution, expected_rating)
            (20, 0, 0),    # Low land value
            (50, 10, 1),   # Land value - pollution = 40, which is >=30 and <80
            (100, 10, 2),  # Land value - pollution = 90, which is >=80 and <150
            (140, 20, 2),  # 120, still <150
            (160, 30, 2),  # 130, still <150
            (170, 10, 3),  # 160, >=150
        ]

        for land_val, pollution, expected in test_cases:
            with self.subTest(land_val=land_val, pollution=pollution):
                types.LandValueMem[types.SMapX >> 1][types.SMapY >> 1] = land_val
                types.PollutionMem[types.SMapX >> 1][types.SMapY >> 1] = pollution
                result = GetCRVal()
                self.assertEqual(result, expected,
                    f"GetCRVal with land_value={land_val}, pollution={pollution} should be {expected}, got {result}")

    def test_zone_power_detection(self):
        """Test SetZPower correctly detects powered zones."""
        # Test nuclear power plant (always powered)
        types.CChr9 = types.NUCLEAR
        types.CChr = types.NUCLEAR
        result = SetZPower()
        self.assertEqual(result, 1)
        self.assertTrue(types.Map[types.SMapX][types.SMapY] & types.PWRBIT)

        # Test power plant (always powered)
        types.CChr9 = types.POWERPLANT
        types.CChr = types.POWERPLANT
        result = SetZPower()
        self.assertEqual(result, 1)
        self.assertTrue(types.Map[types.SMapX][types.SMapY] & types.PWRBIT)

        # Test regular zone without power
        types.CChr9 = types.RZB
        types.CChr = types.RZB
        result = SetZPower()
        self.assertEqual(result, 0)
        self.assertFalse(types.Map[types.SMapX][types.SMapY] & types.PWRBIT)

    def test_zone_type_routing(self):
        """Test DoZone routes to correct processing function based on tile type."""
        # Test residential zone routing
        types.CChr9 = types.RZB
        with unittest.mock.patch('src.micropolis.zones.DoResidential') as mock_res:
            DoZone()
            mock_res.assert_called_once()

        # Test commercial zone routing
        types.CChr9 = types.CZB
        with unittest.mock.patch('src.micropolis.zones.DoCommercial') as mock_com:
            DoZone()
            mock_com.assert_called_once()

        # Test industrial zone routing
        types.CChr9 = types.IZB
        with unittest.mock.patch('src.micropolis.zones.DoIndustrial') as mock_ind:
            DoZone()
            mock_ind.assert_called_once()

        # Test hospital routing
        types.CChr9 = types.HOSPITAL
        with unittest.mock.patch('src.micropolis.zones.DoHospChur') as mock_hosp:
            DoZone()
            mock_hosp.assert_called_once()

    def test_hospital_church_processing(self):
        """Test hospital and church zone processing."""
        # Test hospital processing
        types.CChr9 = types.HOSPITAL
        types.CityTime = 0  # Will trigger repair
        initial_hosp_pop = types.HospPop

        with unittest.mock.patch('src.micropolis.simulation.RepairZone') as mock_repair:
            DoHospChur()
            self.assertEqual(types.HospPop, initial_hosp_pop + 1)
            mock_repair.assert_called_once_with(types.HOSPITAL, 3)

        # Test church processing
        types.CChr9 = types.CHURCH
        types.CityTime = 0  # Will trigger repair
        initial_church_pop = types.ChurchPop

        with unittest.mock.patch('src.micropolis.simulation.RepairZone') as mock_repair:
            DoHospChur()
            self.assertEqual(types.ChurchPop, initial_church_pop + 1)
            mock_repair.assert_called_once_with(types.CHURCH, 3)

    def test_evaluation_functions(self):
        """Test zone evaluation functions produce correct desirability scores."""
        # Test residential evaluation
        traf_good = 1
        result = EvalRes(traf_good)
        # Land value 100 - pollution 10 = 90, shifted to 90*32=2880, then -3000 = -120
        expected = (100 - 10) * 32 - 3000  # 2880 - 3000 = -120
        self.assertEqual(result, expected)

        # Test commercial evaluation
        result = EvalCom(traf_good)
        self.assertEqual(result, 1000)  # ComRate value

        # Test industrial evaluation
        result = EvalInd(traf_good)
        self.assertEqual(result, 0)  # Always returns 0 for good traffic

        # Test bad traffic cases
        traf_bad = -1
        self.assertEqual(EvalRes(traf_bad), -3000)
        self.assertEqual(EvalCom(traf_bad), -3000)
        self.assertEqual(EvalInd(traf_bad), -1000)

    def test_zone_placement_residential(self):
        """Test residential zone placement calculations."""
        test_cases = [
            # (density, value, expected_base)
            (0, 0, ((0 * 4 + 0) * 9) + types.RZB - 4),  # Empty zone
            (1, 1, ((1 * 4 + 1) * 9) + types.RZB - 4),  # Low density, low value
            (2, 2, ((2 * 4 + 2) * 9) + types.RZB - 4),  # Medium density, medium value
        ]

        for density, value, expected_base in test_cases:
            with self.subTest(density=density, value=value):
                with unittest.mock.patch('src.micropolis.zones.ZonePlop') as mock_plop:
                    ResPlop(density, value)
                    mock_plop.assert_called_once_with(expected_base)

    def test_zone_placement_commercial(self):
        """Test commercial zone placement calculations."""
        test_cases = [
            # (density, value, expected_base)
            (0, 0, ((0 * 5 + 0) * 9) + types.CZB - 4),  # Empty zone
            (1, 1, ((1 * 5 + 1) * 9) + types.CZB - 4),  # Low density, low value
            (2, 2, ((2 * 5 + 2) * 9) + types.CZB - 4),  # Medium density, medium value
        ]

        for density, value, expected_base in test_cases:
            with self.subTest(density=density, value=value):
                with unittest.mock.patch('src.micropolis.zones.ZonePlop') as mock_plop:
                    ComPlop(density, value)
                    mock_plop.assert_called_once_with(expected_base)

    def test_zone_placement_industrial(self):
        """Test industrial zone placement calculations."""
        test_cases = [
            # (density, value, expected_base)
            (0, 0, ((0 * 4 + 0) * 9) + types.IZB - 4),  # Empty zone
            (1, 1, ((1 * 4 + 1) * 9) + types.IZB - 4),  # Low density, low value
            (2, 2, ((2 * 4 + 2) * 9) + types.IZB - 4),  # Medium density, medium value
        ]

        for density, value, expected_base in test_cases:
            with self.subTest(density=density, value=value):
                with unittest.mock.patch('src.micropolis.zones.ZonePlop') as mock_plop:
                    IndPlop(density, value)
                    mock_plop.assert_called_once_with(expected_base)

    def test_free_zone_population_counting(self):
        """Test DoFreePop counts houses in free zone area."""
        # Clear the area first
        for x in range(types.SMapX - 1, types.SMapX + 2):
            for y in range(types.SMapY - 1, types.SMapY + 2):
                if macros.TestBounds(x, y):
                    types.Map[x][y] = 0

        # Add some houses (LHTHR to HHTHR range)
        types.Map[types.SMapX - 1][types.SMapY - 1] = types.LHTHR
        types.Map[types.SMapX][types.SMapY] = types.HHTHR
        types.Map[types.SMapX + 1][types.SMapY + 1] = types.LHTHR + 5

        result = DoFreePop()
        self.assertEqual(result, 3)  # Should count 3 houses

    def test_zone_plop_blocked_by_disaster(self):
        """Test ZonePlop fails when area contains fire/flood."""
        # Clear area first
        for i in range(9):
            zx = [-1, 0, 1, -1, 0, 1, -1, 0, 1][i]
            zy = [-1, -1, -1, 0, 0, 0, 1, 1, 1][i]
            xx, yy = types.SMapX + zx, types.SMapY + zy
            if macros.TestBounds(xx, yy):
                types.Map[xx][yy] = 0

        # Add fire to one tile (between FLOOD and ROADBASE)
        fire_tile = types.FLOOD + 10  # Some fire tile
        types.Map[types.SMapX][types.SMapY] = fire_tile

        result = ZonePlop(types.RZB)
        self.assertFalse(result)  # Should fail due to fire

    def test_zone_plop_success(self):
        """Test ZonePlop successfully places zone tiles."""
        # Clear area first
        for i in range(9):
            zx = [-1, 0, 1, -1, 0, 1, -1, 0, 1][i]
            zy = [-1, -1, -1, 0, 0, 0, 1, 1, 1][i]
            xx, yy = types.SMapX + zx, types.SMapY + zy
            if macros.TestBounds(xx, yy):
                types.Map[xx][yy] = 0

        result = ZonePlop(types.RZB)
        self.assertTrue(result)  # Should succeed

        # Check center tile has ZONEBIT and BULLBIT set
        center_tile = types.Map[types.SMapX][types.SMapY]
        self.assertTrue(center_tile & types.ZONEBIT)
        self.assertTrue(center_tile & types.BULLBIT)

    def test_eval_lot_scoring(self):
        """Test EvalLot produces correct lot desirability scores."""
        x, y = types.SMapX + 2, types.SMapY + 2  # Use offset to avoid boundary issues

        # Test invalid lot (occupied by non-residential)
        types.Map[x][y] = types.ROADBASE + 10
        result = EvalLot(x, y)
        self.assertEqual(result, -1)

        # Test clear lot with no roads
        types.Map[x][y] = 0
        result = EvalLot(x, y)
        self.assertEqual(result, 1)  # Base score

        # Add roads around the lot
        types.Map[x][y-1] = types.ROADBASE  # North
        types.Map[x+1][y] = types.ROADBASE  # East
        result = EvalLot(x, y)
        self.assertEqual(result, 3)  # Base + 2 roads

    def test_residential_growth_logic(self):
        """Test residential zone growth decision logic."""
        # Mock traffic to be good
        with unittest.mock.patch('src.micropolis.zones.MakeTraf', return_value=1):
            # Set up conditions for growth
            types.RValve = 1000  # High residential valve
            types.CChr9 = types.RZB

            # Mock Rand16Signed to return a value that allows growth
            # For zscore=1000: need Rand16Signed < (1000 - 26380) = -25380
            with unittest.mock.patch('src.micropolis.simulation.Rand16Signed', return_value=-30000):
                with unittest.mock.patch('src.micropolis.zones.DoResIn') as mock_grow:
                    DoResidential(1)  # Powered zone
                    # Should attempt growth due to high valve
                    mock_grow.assert_called_once()

    def test_commercial_growth_logic(self):
        """Test commercial zone growth decision logic."""
        # Mock traffic to be good
        with unittest.mock.patch('src.micropolis.zones.MakeTraf', return_value=1):
            # Set up conditions for growth
            types.CValve = 1000  # High commercial valve
            types.CChr9 = types.CZB

            # Mock Rand16Signed to return a value that allows growth
            with unittest.mock.patch('src.micropolis.simulation.Rand16Signed', return_value=-30000):
                with unittest.mock.patch('src.micropolis.zones.DoComIn') as mock_grow:
                    DoCommercial(1)  # Powered zone
                    # Should attempt growth due to high valve
                    mock_grow.assert_called_once()

    def test_industrial_growth_logic(self):
        """Test industrial zone growth decision logic."""
        # Mock traffic to be good
        with unittest.mock.patch('src.micropolis.zones.MakeTraf', return_value=1):
            # Set up conditions for growth
            types.IValve = 1000  # High industrial valve
            types.CChr9 = types.IZB

            # Mock Rand16Signed to return a value that allows growth
            with unittest.mock.patch('src.micropolis.simulation.Rand16Signed', return_value=-30000):
                with unittest.mock.patch('src.micropolis.zones.DoIndIn') as mock_grow:
                    DoIndustrial(1)  # Powered zone
                    # Should attempt growth due to high valve
                    mock_grow.assert_called_once()

    def test_zone_shrinkage_logic(self):
        """Test zone shrinkage when conditions are poor."""
        # Mock traffic to be good but valves low
        with unittest.mock.patch('src.micropolis.zones.MakeTraf', return_value=1):
            # Set up conditions for shrinkage
            types.RValve = -1000  # Low residential valve
            types.CChr9 = types.RZB + 27  # High density residential

            # Mock Rand16Signed to return a value that allows shrinkage
            # For zscore=-1000: need Rand16Signed > (-1000 + 26380) = 25380
            with unittest.mock.patch('src.micropolis.simulation.Rand16Signed', return_value=30000):
                with unittest.mock.patch('src.micropolis.zones.DoResOut') as mock_shrink:
                    DoResidential(1)  # Powered zone
                    # Should attempt shrinkage due to low valve
                    mock_shrink.assert_called_once()

