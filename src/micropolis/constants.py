# mac.py: Macintosh emulation constants and types for Micropolis Python port
#
# This module provides Macintosh-style constants and type definitions
# for the Micropolis city simulation game. These emulate the original
# C Macintosh API used in the classic version.
#
# Original C header: headers/mac.h
# Ported to maintain compatibility with Micropolis simulation logic

import ctypes

# Platform-specific type definitions
# In the original C code, QUAD was defined differently for OSF1 vs other systems
# For Python, we'll use int which is equivalent to long in modern C
QUAD = int

# Basic Macintosh types
Byte = ctypes.c_uint8  # unsigned char
Ptr = ctypes.POINTER(Byte)  # Byte *
Handle = ctypes.POINTER(ctypes.POINTER(ctypes.c_char))  # char **

# Resource management constants
# These would typically be used for loading game assets
# In the Python port, these will be adapted for pygame resource loading


# Resource management functions
# These are stubs that will be implemented to work with pygame/file system


# Constants that might be used throughout the codebase
# These are common Macintosh resource type codes
RESOURCE_TYPES = {
    "TILE": b"TILE",  # Tile graphics
    "SND ": b"SND ",  # Sound resources
    "STR ": b"STR ",  # String resources
    "PICT": b"PICT",  # Picture resources
    "ICON": b"ICON",  # Icon resources
}

# Memory management constants
# These might be used for allocating game data structures
MAX_RESOURCE_SIZE = 65536  # 64KB max resource size (classic Mac limit)
DEFAULT_RESOURCE_CHAIN_SIZE = 100  # Default number of resources in chain
# Import view_types for graphics structures

# ============================================================================
# Basic Constants
# ============================================================================

# Boolean values
TRUE = 1
FALSE = 0
# World dimensions
WORLD_X = 120
WORLD_Y = 100
HWLDX = WORLD_X // 2  # 60
HWLDY = WORLD_Y // 2  # 50
QWX = WORLD_X // 4  # 30
QWY = WORLD_Y // 4  # 25
SM_X = WORLD_X // 8  # 15
SM_Y = (WORLD_Y + 7) // 8  # 13
# Editor and Map dimensions (pixels)
EDITOR_W = WORLD_X * 16  # 1920
EDITOR_H = WORLD_Y * 16  # 1600
MAP_W = WORLD_X * 3  # 360
MAP_H = WORLD_Y * 3  # 300
# Direction constants
NIL = 0
HORIZ = 1
VERT = 0
# Problem tracking
PROBNUM = 10

# History lengths
HISTLEN = 480
MISCHISTLEN = 240
POWERMAPROW = (WORLD_X + 15) // 16  # 8
PWRMAPSIZE = POWERMAPROW * WORLD_Y  # 800
POWERMAPLEN = 1700  # Hardcoded value from C (non-MEGA case)
PWRSTKSIZE = (WORLD_X * WORLD_Y) // 4  # 3000
# ============================================================================
# Map Type Constants
# ============================================================================

ALMAP = 0  # all
REMAP = 1  # residential
COMAP = 2  # commercial
INMAP = 3  # industrial
PRMAP = 4  # power
RDMAP = 5  # road
PDMAP = 6  # population density
RGMAP = 7  # rate of growth
TDMAP = 8  # traffic density
PLMAP = 9  # pollution
CRMAP = 10  # crime
LVMAP = 11  # land value
FIMAP = 12  # fire radius
POMAP = 13  # police radius
DYMAP = 14  # dynamic
NMAPS = 15
PROBNUM = 10
# ============================================================================
# Problem Tracking Constants
# ============================================================================


# ============================================================================
# Simulation Rate Constants
# ============================================================================

VALVERATE = 2
CENSUSRATE = 4
TAXFREQ = 48
# ============================================================================
# Color Constants
# ============================================================================

COLOR_WHITE = 0
COLOR_YELLOW = 1
COLOR_ORANGE = 2
COLOR_RED = 3
COLOR_DARKRED = 4
COLOR_DARKBLUE = 5
COLOR_LIGHTBLUE = 6
COLOR_BROWN = 7
COLOR_LIGHTGREEN = 8
COLOR_DARKGREEN = 9
COLOR_OLIVE = 10
COLOR_LIGHTBROWN = 11
COLOR_LIGHTGRAY = 12
COLOR_MEDIUMGRAY = 13
COLOR_DARKGRAY = 14
COLOR_BLACK = 15


# ============================================================================
# Status Bits (16-bit tile encoding)
# ============================================================================

PWRBIT = 32768  # 0x8000 - bit 15 - power
CONDBIT = 16384  # 0x4000 - bit 14 - conductive
BURNBIT = 8192  # 0x2000 - bit 13 - burning
BULLBIT = 4096  # 0x1000 - bit 12 - bulldozed
ANIMBIT = 2048  # 0x0800 - bit 11 - animated
ZONEBIT = 1024  # 0x0400 - bit 10 - zoned

ALLBITS = 64512  # 0xFC00 - mask for upper 6 bits
LOMASK = 1023  # 0x03FF - mask for low 10 bits

# Combined status bit masks
BLBNBIT = BULLBIT + BURNBIT
BLBNCNBIT = BULLBIT + BURNBIT + CONDBIT
BNCNBIT = BURNBIT + CONDBIT
ASCBIT = ANIMBIT | CONDBIT | BURNBIT  # Animation + conductive + burning
REGBIT = CONDBIT | BURNBIT  # Conductive + burning

# ============================================================================
# Object and Sound Numbers
# ============================================================================

TRA = 1  # Train
COP = 2  # Police helicopter
AIR = 3  # Airplanes
SHI = 4  # Ships
GOD = 5  # God (disaster control)
TOR = 6  # Tornado
EXP = 7  # Explosion
BUS = 8  # Bus

OBJN = 9  # Max number of objects

# ============================================================================
# Graph History Constants
# ============================================================================

RES_HIST = 0
COM_HIST = 1
IND_HIST = 2
MONEY_HIST = 3
CRIME_HIST = 4
POLLUTION_HIST = 5
HISTORIES = 6
ALL_HISTORIES = (1 << HISTORIES) - 1

# ============================================================================
# Tile Mapping Constants
# ============================================================================

# Terrain tiles
DIRT = 0
RIVER = 2
REDGE = 3
CHANNEL = 4
FIRSTRIVEDGE = 5
LASTRIVEDGE = 20
TREEBASE = 21
LASTTREE = 36
WOODS = 37
WOODS2 = 40
WOODS3 = 41
WOODS4 = 42
WOODS5 = 43
RUBBLE = 44
LASTRUBBLE = 47
FLOOD = 48
LASTFLOOD = 51
RADTILE = 52
FIRE = 56
FIREBASE = 56
LASTFIRE = 63

# Road tiles
ROADBASE = 64
HBRIDGE = 64
VBRIDGE = 65
ROADS = 66
INTERSECTION = 76
HROADPOWER = 77
VROADPOWER = 78
BRWH = 79
LTRFBASE = 80
BRWV = 95
HTRFBASE = 144
LASTROAD = 206

# Power tiles
POWERBASE = 208
HPOWER = 208
VPOWER = 209
LHPOWER = 210
LVPOWER = 211
RAILHPOWERV = 221
RAILVPOWERH = 222
LASTPOWER = 222

# Rail tiles
RAILBASE = 224
HRAIL = 224
VRAIL = 225
LHRAIL = 226
LVRAIL = 227
HRAILROAD = 237
VRAILROAD = 238
LASTRAIL = 238

# Residential tiles
RESBASE = 240
FREEZ = 244
HOUSE = 249
LHTHR = 249
HHTHR = 260
RZB = 265
HOSPITAL = 409
CHURCH = 418

# Commercial tiles
COMBASE = 423
COMCLR = 427
CZB = 436

# Industrial tiles
INDBASE = 612
INDCLR = 616
LASTIND = 620
IND1 = 621
IZB = 625
IND2 = 641
IND3 = 644
IND4 = 649
IND5 = 650
IND6 = 676
IND7 = 677
IND8 = 686
IND9 = 689

# Port tiles
PORTBASE = 693
PORT = 698
LASTPORT = 708

# Airport tiles
AIRPORTBASE = 709
RADAR = 711
AIRPORT = 716

# Power plant tiles
COALBASE = 745
POWERPLANT = 750
LASTPOWERPLANT = 760

# Service tiles
FIRESTBASE = 761
FIRESTATION = 765
POLICESTBASE = 770
POLICESTATION = 774
STADIUMBASE = 779
STADIUM = 784
FULLSTADIUM = 800

# Nuclear tiles
NUCLEARBASE = 811
NUCLEAR = 816
LASTZONE = 826

# Special effect tiles
LIGHTNINGBOLT = 827
HBRDG0 = 828
HBRDG1 = 829
HBRDG2 = 830
HBRDG3 = 831
RADAR0 = 832
RADAR1 = 833
RADAR2 = 834
RADAR3 = 835
RADAR4 = 836
RADAR5 = 837
RADAR6 = 838
RADAR7 = 839
FOUNTAIN = 840

# Industrial extensions
INDBASE2 = 844
TELEBASE = 844
TELELAST = 851
SMOKEBASE = 852
TINYEXP = 860
SOMETINYEXP = 864
LASTTINYEXP = 867

# Smoke effects
COALSMOKE1 = 916
COALSMOKE2 = 920
COALSMOKE3 = 924
COALSMOKE4 = 928

# Stadium effects
FOOTBALLGAME1 = 932
FOOTBALLGAME2 = 940

# Bridge tiles
VBRDG0 = 948
VBRDG1 = 949
VBRDG2 = 950
VBRDG3 = 951

# Bridge extension tiles (for nuke cheat)
BRWXXX1 = 111
BRWXXX2 = 127
BRWXXX3 = 143
BRWXXX4 = 159
BRWXXX5 = 175
BRWXXX6 = 191
BRWXXX7 = 207

TILE_COUNT = 960

# ============================================================================
# Tool State Constants
# ============================================================================

residentialState = 0
commercialState = 1
industrialState = 2
fireState = 3
queryState = 4
policeState = 5
wireState = 6
DOZE_STATE = 7
rrState = 8
roadState = 9
chalkState = 10
eraserState = 11
stadiumState = 12
parkState = 13
seaportState = 14
powerState = 15
nuclearState = 16
airportState = 17
networkState = 18


STATE_CMD = 0
STATE_TILES = 1
STATE_OVERLAYS = 2
STATE_GRAPHS = 3
DEFAULT_STARTING_FUNDS = 20000
