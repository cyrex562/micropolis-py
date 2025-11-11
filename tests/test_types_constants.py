#!/usr/bin/env python3
"""
test_types_constants.py - Integration tests for types.py constants verification

This module verifies that Python constants in types.py match the original C implementation
from sim.h, macros.h, and mac.h headers. Ensures algorithmic fidelity by
validating all constants used in simulation logic.
"""

from micropolis.constants import (
    ALMAP,
    CENSUSRATE,
    COLOR_BLACK,
    COLOR_BROWN,
    COLOR_DARKBLUE,
    COLOR_DARKGRAY,
    COLOR_DARKGREEN,
    COLOR_DARKRED,
    COLOR_LIGHTBLUE,
    COLOR_LIGHTBROWN,
    COLOR_LIGHTGRAY,
    COLOR_LIGHTGREEN,
    COLOR_MEDIUMGRAY,
    COLOR_OLIVE,
    COLOR_ORANGE,
    COLOR_RED,
    COLOR_WHITE,
    COLOR_YELLOW,
    COMAP,
    CRMAP,
    DYMAP,
    FIMAP,
    HWLDX,
    HWLDY,
    INMAP,
    LVMAP,
    NMAPS,
    PDMAP,
    PLMAP,
    POMAP,
    PRMAP,
    QWX,
    QWY,
    RDMAP,
    REMAP,
    RGMAP,
    SM_X,
    SM_Y,
    TAXFREQ,
    TDMAP,
    VALVERATE,
    WORLD_X,
    WORLD_Y,
)
import pytest
from src.micropolis.types import (
    # World dimensions
    PWRMAPSIZE,
    POWERMAPLEN,
    # Colors
    PWRBIT,
    CONDBIT,
    BURNBIT,
    BULLBIT,
    ANIMBIT,
    ZONEBIT,
    ALLBITS,
    LOMASK,
    BLBNBIT,
    BLBNCNBIT,
    BNCNBIT,
    ASCBIT,
    REGBIT,
    # Objects
    TRA,
    COP,
    AIR,
    SHI,
    GOD,
    TOR,
    EXP,
    BUS,
    OBJN,
    # Graph histories
    RES_HIST,
    COM_HIST,
    IND_HIST,
    MONEY_HIST,
    CRIME_HIST,
    POLLUTION_HIST,
    HISTORIES,
    ALL_HISTORIES,
    # Terrain tiles
    DIRT,
    RIVER,
    REDGE,
    CHANNEL,
    FIRSTRIVEDGE,
    LASTRIVEDGE,
    TREEBASE,
    LASTTREE,
    WOODS,
    WOODS2,
    WOODS3,
    WOODS4,
    WOODS5,
    RUBBLE,
    LASTRUBBLE,
    FLOOD,
    LASTFLOOD,
    RADTILE,
    FIRE,
    FIREBASE,
    LASTFIRE,
    # Road tiles
    ROADBASE,
    HBRIDGE,
    VBRIDGE,
    ROADS,
    INTERSECTION,
    HROADPOWER,
    VROADPOWER,
    BRWH,
    LTRFBASE,
    BRWV,
    HTRFBASE,
    LASTROAD,
    # Bridge extension tiles
    BRWXXX1,
    BRWXXX2,
    BRWXXX3,
    BRWXXX4,
    BRWXXX5,
    BRWXXX6,
    BRWXXX7,
    # Power tiles
    POWERBASE,
    HPOWER,
    VPOWER,
    LHPOWER,
    LVPOWER,
    RAILHPOWERV,
    RAILVPOWERH,
    LASTPOWER,
    # Rail tiles
    RAILBASE,
    HRAIL,
    VRAIL,
    LHRAIL,
    LVRAIL,
    HRAILROAD,
    VRAILROAD,
    LASTRAIL,
    # Residential tiles
    RESBASE,
    FREEZ,
    HOUSE,
    LHTHR,
    HHTHR,
    RZB,
    HOSPITAL,
    CHURCH,
    # Commercial tiles
    COMBASE,
    COMCLR,
    CZB,
    # Industrial tiles
    INDBASE,
    INDCLR,
    LASTIND,
    IND1,
    IZB,
    IND2,
    IND3,
    IND4,
    IND5,
    IND6,
    IND7,
    IND8,
    IND9,
    # Port tiles
    PORTBASE,
    PORT,
    LASTPORT,
    # Airport tiles
    AIRPORTBASE,
    RADAR,
    AIRPORT,
    # Power plant tiles
    COALBASE,
    POWERPLANT,
    LASTPOWERPLANT,
    # Service tiles
    FIRESTBASE,
    FIRESTATION,
    POLICESTBASE,
    POLICESTATION,
    STADIUMBASE,
    STADIUM,
    FULLSTADIUM,
    # Nuclear tiles
    NUCLEARBASE,
    NUCLEAR,
    LASTZONE,
    # Special effect tiles
    LIGHTNINGBOLT,
    HBRDG0,
    HBRDG1,
    HBRDG2,
    HBRDG3,
    RADAR0,
    RADAR1,
    RADAR2,
    RADAR3,
    RADAR4,
    RADAR5,
    RADAR6,
    RADAR7,
    FOUNTAIN,
    # Industrial extensions
    INDBASE2,
    TELEBASE,
    TELELAST,
    SMOKEBASE,
    TINYEXP,
    SOMETINYEXP,
    LASTTINYEXP,
    # Smoke effects
    COALSMOKE1,
    COALSMOKE2,
    COALSMOKE3,
    COALSMOKE4,
    # Stadium effects
    FOOTBALLGAME1,
    FOOTBALLGAME2,
    # Bridge tiles
    VBRDG0,
    VBRDG1,
    VBRDG2,
    VBRDG3,
    # Total tile count
    TILE_COUNT,
    # Tool states
    residentialState,
    commercialState,
    industrialState,
    fireState,
    queryState,
    policeState,
    wireState,
    DOZE_STATE,
    rrState,
    roadState,
    chalkState,
    eraserState,
    stadiumState,
    parkState,
    seaportState,
    powerState,
    nuclearState,
    airportState,
    networkState,
    firstState,
    lastState,
    # State categories
    STATE_CMD,
    STATE_TILES,
    STATE_OVERLAYS,
    STATE_GRAPHS,
    # Map types
    PROBNUM,
)


class TestWorldDimensions:
    """Test world and derived dimension constants"""

    def test_world_dimensions(self):
        """Verify world dimensions match C version"""
        assert WORLD_X == 120, f"WORLD_X should be 120, got {WORLD_X}"
        assert WORLD_Y == 100, f"WORLD_Y should be 100, got {WORLD_Y}"

    def test_half_dimensions(self):
        """Verify half-world dimensions"""
        assert HWLDX == WORLD_X // 2, f"HWLDX should be {WORLD_X // 2}, got {HWLDX}"
        assert HWLDY == WORLD_Y // 2, f"HWLDY should be {WORLD_Y // 2}, got {HWLDY}"
        assert HWLDX == 60, f"HWLDX should be 60, got {HWLDX}"
        assert HWLDY == 50, f"HWLDY should be 50, got {HWLDY}"

    def test_quarter_dimensions(self):
        """Verify quarter-world dimensions"""
        assert QWX == WORLD_X // 4, f"QWX should be {WORLD_X // 4}, got {QWX}"
        assert QWY == WORLD_Y // 4, f"QWY should be {WORLD_Y // 4}, got {QWY}"
        assert QWX == 30, f"QWX should be 30, got {QWX}"
        assert QWY == 25, f"QWY should be 25, got {QWY}"

    def test_small_dimensions(self):
        """Verify small map dimensions (8x8 blocks)"""
        assert SM_X == WORLD_X // 8, f"SmX should be {WORLD_X // 8}, got {SM_X}"
        assert SM_Y == (WORLD_Y + 7) // 8, (
            f"SmY should be {(WORLD_Y + 7) // 8}, got {SM_Y}"
        )
        assert SM_X == 15, f"SmX should be 15, got {SM_X}"
        assert SM_Y == 13, f"SmY should be 13, got {SM_Y}"


class TestPowerGridConstants:
    """Test power grid calculation constants"""

    def test_power_map_size(self):
        """Verify power map size calculations"""
        # POWERMAPROW = (WORLD_X + 15) // 16
        power_map_row = (WORLD_X + 15) // 16
        expected_pwrmapsize = power_map_row * WORLD_Y

        assert PWRMAPSIZE == expected_pwrmapsize, (
            f"PWRMAPSIZE should be {expected_pwrmapsize}, got {PWRMAPSIZE}"
        )
        assert PWRMAPSIZE == 800, (
            f"PWRMAPSIZE should be 800, got {PWRMAPSIZE}"
        )  # (120+15)//16 * 100 = 8*100 = 800

        # Actually, let me recalculate: (120 + 15) // 16 = 135 // 16 = 8, 8 * 100 = 800
        # But the C code shows PWRMAPSIZE = (POWERMAPROW * WORLD_Y) and POWERMAPLEN = 1700
        # Let me check the C calculation again...

    def test_power_map_length(self):
        """Verify power map length"""
        # From C code: POWERMAPLEN = 1700
        # This seems to be a hardcoded value, possibly for compatibility
        assert POWERMAPLEN == 1700, f"POWERMAPLEN should be 1700, got {POWERMAPLEN}"


class TestColorConstants:
    """Test color index constants"""

    def test_color_values(self):
        """Verify color constants match C version"""
        assert COLOR_WHITE == 0
        assert COLOR_YELLOW == 1
        assert COLOR_ORANGE == 2
        assert COLOR_RED == 3
        assert COLOR_DARKRED == 4
        assert COLOR_DARKBLUE == 5
        assert COLOR_LIGHTBLUE == 6
        assert COLOR_BROWN == 7
        assert COLOR_LIGHTGREEN == 8
        assert COLOR_DARKGREEN == 9
        assert COLOR_OLIVE == 10
        assert COLOR_LIGHTBROWN == 11
        assert COLOR_LIGHTGRAY == 12
        assert COLOR_MEDIUMGRAY == 13
        assert COLOR_DARKGRAY == 14
        assert COLOR_BLACK == 15


class TestStatusBits:
    """Test tile status bit constants"""

    def test_individual_bits(self):
        """Verify individual status bits"""
        assert PWRBIT == 32768  # 0x8000, bit 15
        assert CONDBIT == 16384  # 0x4000, bit 14
        assert BURNBIT == 8192  # 0x2000, bit 13
        assert BULLBIT == 4096  # 0x1000, bit 12
        assert ANIMBIT == 2048  # 0x0800, bit 11
        assert ZONEBIT == 1024  # 0x0400, bit 10

    def test_bit_masks(self):
        """Verify bit mask constants"""
        assert ALLBITS == 64512  # 0xFC00 - mask for upper 6 bits
        assert LOMASK == 1023  # 0x03FF - mask for low 10 bits

    def test_combined_bits(self):
        """Verify combined status bit constants"""
        assert BLBNBIT == (BULLBIT + BURNBIT)
        assert BLBNCNBIT == (BULLBIT + BURNBIT + CONDBIT)
        assert BNCNBIT == (BURNBIT + CONDBIT)
        assert ASCBIT == (
            ANIMBIT | CONDBIT | BURNBIT
        )  # Animation + conductive + burning
        assert REGBIT == (CONDBIT | BURNBIT)  # Conductive + burning


class TestObjectConstants:
    """Test object and sound number constants"""

    def test_object_numbers(self):
        """Verify object number constants"""
        assert TRA == 1  # Train
        assert COP == 2  # Police helicopter
        assert AIR == 3  # Airplanes
        assert SHI == 4  # Ships
        assert GOD == 5  # God (disaster control)
        assert TOR == 6  # Tornado
        assert EXP == 7  # Explosion
        assert BUS == 8  # Bus

    def test_object_count(self):
        """Verify maximum object count"""
        assert OBJN == 9  # Max number of objects


class TestGraphHistoryConstants:
    """Test graph history constants"""

    def test_history_indices(self):
        """Verify history indices"""
        assert RES_HIST == 0
        assert COM_HIST == 1
        assert IND_HIST == 2
        assert MONEY_HIST == 3
        assert CRIME_HIST == 4
        assert POLLUTION_HIST == 5

    def test_history_count(self):
        """Verify history count and mask"""
        assert HISTORIES == 6
        assert ALL_HISTORIES == ((1 << HISTORIES) - 1)
        assert ALL_HISTORIES == 63  # 2^6 - 1 = 63


class TestTileConstants:
    """Test tile value constants"""

    def test_terrain_tiles(self):
        """Verify terrain tile constants"""
        assert DIRT == 0
        assert RIVER == 2
        assert REDGE == 3
        assert CHANNEL == 4
        assert FIRSTRIVEDGE == 5
        assert LASTRIVEDGE == 20
        assert TREEBASE == 21
        assert LASTTREE == 36
        assert WOODS == 37
        assert WOODS2 == 40
        assert WOODS3 == 41
        assert WOODS4 == 42
        assert WOODS5 == 43
        assert RUBBLE == 44
        assert LASTRUBBLE == 47
        assert FLOOD == 48
        assert LASTFLOOD == 51
        assert RADTILE == 52
        assert FIRE == 56
        assert FIREBASE == 56
        assert LASTFIRE == 63

    def test_road_tiles(self):
        """Verify road tile constants"""
        assert ROADBASE == 64
        assert HBRIDGE == 64
        assert VBRIDGE == 65
        assert ROADS == 66
        assert INTERSECTION == 76
        assert HROADPOWER == 77
        assert VROADPOWER == 78
        assert BRWH == 79
        assert LTRFBASE == 80
        assert BRWV == 95
        assert HTRFBASE == 144
        assert LASTROAD == 206

    def test_bridge_extensions(self):
        """Verify bridge extension tiles"""
        assert BRWXXX1 == 111
        assert BRWXXX2 == 127
        assert BRWXXX3 == 143
        assert BRWXXX4 == 159
        assert BRWXXX5 == 175
        assert BRWXXX6 == 191
        assert BRWXXX7 == 207

    def test_power_tiles(self):
        """Verify power tile constants"""
        assert POWERBASE == 208
        assert HPOWER == 208
        assert VPOWER == 209
        assert LHPOWER == 210
        assert LVPOWER == 211
        assert RAILHPOWERV == 221
        assert RAILVPOWERH == 222
        assert LASTPOWER == 222

    def test_rail_tiles(self):
        """Verify rail tile constants"""
        assert RAILBASE == 224
        assert HRAIL == 224
        assert VRAIL == 225
        assert LHRAIL == 226
        assert LVRAIL == 227
        assert HRAILROAD == 237
        assert VRAILROAD == 238
        assert LASTRAIL == 238

    def test_residential_tiles(self):
        """Verify residential tile constants"""
        assert RESBASE == 240
        assert FREEZ == 244
        assert HOUSE == 249
        assert LHTHR == 249
        assert HHTHR == 260
        assert RZB == 265
        assert HOSPITAL == 409
        assert CHURCH == 418

    def test_commercial_tiles(self):
        """Verify commercial tile constants"""
        assert COMBASE == 423
        assert COMCLR == 427
        assert CZB == 436

    def test_industrial_tiles(self):
        """Verify industrial tile constants"""
        assert INDBASE == 612
        assert INDCLR == 616
        assert LASTIND == 620
        assert IND1 == 621
        assert IZB == 625
        assert IND2 == 641
        assert IND3 == 644
        assert IND4 == 649
        assert IND5 == 650
        assert IND6 == 676
        assert IND7 == 677
        assert IND8 == 686
        assert IND9 == 689

    def test_port_tiles(self):
        """Verify port tile constants"""
        assert PORTBASE == 693
        assert PORT == 698
        assert LASTPORT == 708

    def test_airport_tiles(self):
        """Verify airport tile constants"""
        assert AIRPORTBASE == 709
        assert RADAR == 711
        assert AIRPORT == 716

    def test_power_plant_tiles(self):
        """Verify power plant tile constants"""
        assert COALBASE == 745
        assert POWERPLANT == 750
        assert LASTPOWERPLANT == 760

    def test_service_tiles(self):
        """Verify service tile constants"""
        assert FIRESTBASE == 761
        assert FIRESTATION == 765
        assert POLICESTBASE == 770
        assert POLICESTATION == 774
        assert STADIUMBASE == 779
        assert STADIUM == 784
        assert FULLSTADIUM == 800

    def test_nuclear_tiles(self):
        """Verify nuclear tile constants"""
        assert NUCLEARBASE == 811
        assert NUCLEAR == 816
        assert LASTZONE == 826

    def test_special_effect_tiles(self):
        """Verify special effect tile constants"""
        assert LIGHTNINGBOLT == 827
        assert HBRDG0 == 828
        assert HBRDG1 == 829
        assert HBRDG2 == 830
        assert HBRDG3 == 831
        assert RADAR0 == 832
        assert RADAR1 == 833
        assert RADAR2 == 834
        assert RADAR3 == 835
        assert RADAR4 == 836
        assert RADAR5 == 837
        assert RADAR6 == 838
        assert RADAR7 == 839
        assert FOUNTAIN == 840

    def test_industrial_extensions(self):
        """Verify industrial extension tiles"""
        assert INDBASE2 == 844
        assert TELEBASE == 844
        assert TELELAST == 851
        assert SMOKEBASE == 852
        assert TINYEXP == 860
        assert SOMETINYEXP == 864
        assert LASTTINYEXP == 867

    def test_smoke_effects(self):
        """Verify smoke effect tiles"""
        assert COALSMOKE1 == 916
        assert COALSMOKE2 == 920
        assert COALSMOKE3 == 924
        assert COALSMOKE4 == 928

    def test_stadium_effects(self):
        """Verify stadium effect tiles"""
        assert FOOTBALLGAME1 == 932
        assert FOOTBALLGAME2 == 940

    def test_bridge_tiles(self):
        """Verify bridge tiles"""
        assert VBRDG0 == 948
        assert VBRDG1 == 949
        assert VBRDG2 == 950
        assert VBRDG3 == 951

    def test_tile_count(self):
        """Verify total tile count"""
        assert TILE_COUNT == 960


class TestToolStateConstants:
    """Test tool state constants"""

    def test_tool_states(self):
        """Verify tool state constants"""
        assert residentialState == 0
        assert commercialState == 1
        assert industrialState == 2
        assert fireState == 3
        assert queryState == 4
        assert policeState == 5
        assert wireState == 6
        assert DOZE_STATE == 7
        assert rrState == 8
        assert roadState == 9
        assert chalkState == 10
        assert eraserState == 11
        assert stadiumState == 12
        assert parkState == 13
        assert seaportState == 14
        assert powerState == 15
        assert nuclearState == 16
        assert airportState == 17
        assert networkState == 18

    def test_state_ranges(self):
        """Verify state range constants"""
        assert firstState == residentialState
        assert lastState == networkState


class TestStateCategoryConstants:
    """Test state category constants"""

    def test_state_categories(self):
        """Verify state category constants"""
        assert STATE_CMD == 0
        assert STATE_TILES == 1
        assert STATE_OVERLAYS == 2
        assert STATE_GRAPHS == 3


class TestMapTypeConstants:
    """Test map type constants"""

    def test_map_types(self):
        """Verify map type constants"""
        assert ALMAP == 0  # all
        assert REMAP == 1  # residential
        assert COMAP == 2  # commercial
        assert INMAP == 3  # industrial
        assert PRMAP == 4  # power
        assert RDMAP == 5  # road
        assert PDMAP == 6  # population density
        assert RGMAP == 7  # rate of growth
        assert TDMAP == 8  # traffic density
        assert PLMAP == 9  # pollution
        assert CRMAP == 10  # crime
        assert LVMAP == 11  # land value
        assert FIMAP == 12  # fire radius
        assert POMAP == 13  # police radius
        assert DYMAP == 14  # dynamic

    def test_map_count(self):
        """Verify total map count"""
        assert NMAPS == 15


class TestSimulationRateConstants:
    """Test simulation rate constants"""

    def test_simulation_rates(self):
        """Verify simulation rate constants"""
        assert VALVERATE == 2
        assert CENSUSRATE == 4
        assert TAXFREQ == 48


class TestProblemConstants:
    """Test problem tracking constants"""

    def test_problem_count(self):
        """Verify problem count constant"""
        assert PROBNUM == 10


class TestBitOperations:
    """Test bit operation utilities"""

    def test_bit_calculations(self):
        """Verify bit calculations work correctly"""
        # Test that status bits are powers of 2
        assert PWRBIT == 2**15
        assert CONDBIT == 2**14
        assert BURNBIT == 2**13
        assert BULLBIT == 2**12
        assert ANIMBIT == 2**11
        assert ZONEBIT == 2**10

        # Test mask calculations
        expected_allbits = PWRBIT | CONDBIT | BURNBIT | BULLBIT | ANIMBIT | ZONEBIT
        assert ALLBITS == expected_allbits
        assert LOMASK == (2**10) - 1  # 0x03FF


class TestTileRanges:
    """Test tile range validations"""

    def test_tile_ranges(self):
        """Verify tile ranges are consistent"""
        # Terrain ranges
        assert FIRSTRIVEDGE < LASTRIVEDGE
        assert TREEBASE < LASTTREE
        assert RUBBLE < LASTRUBBLE
        assert FLOOD < LASTFLOOD
        assert FIREBASE == FIRE
        assert FIRE < LASTFIRE

        # Infrastructure ranges
        assert ROADBASE < LASTROAD
        assert POWERBASE < LASTPOWER
        assert RAILBASE < LASTRAIL
        assert RESBASE < HOSPITAL  # Residential range
        assert COMBASE < CZB  # Commercial range
        assert INDBASE < LASTIND  # Industrial range
        assert PORTBASE < LASTPORT
        assert AIRPORTBASE < AIRPORT
        assert COALBASE < LASTPOWERPLANT
        assert FIRESTBASE < FIRESTATION
        assert POLICESTBASE < POLICESTATION
        assert STADIUMBASE < FULLSTADIUM
        assert NUCLEARBASE < LASTZONE

        # Special effects
        assert TELEBASE < TELELAST
        assert SMOKEBASE < TINYEXP
        assert TINYEXP < LASTTINYEXP
