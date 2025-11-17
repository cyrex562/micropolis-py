# mac.py: Macintosh emulation constants and types for Micropolis Python port
#
# This module provides Macintosh-style constants and type definitions
# for the Micropolis city simulation game. These emulate the original
# C Macintosh API used in the classic version.
#
# Original C header: headers/mac.h
# Ported to maintain compatibility with Micropolis simulation logic

import ctypes

import pygame

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
# PROBNUM = 10
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

MICROPOLIS_VERSION = "2025.11.11"

WATER_LOW = RIVER  # 2
WATER_HIGH = LASTRIVEDGE  # 20
WOODS_LOW = TREEBASE  # 21
WOODS_HIGH = 39  # UNUSED_TRASH2 (woods tile range end)

# Tile constants
SIM_SMTILE = 385
SIM_BWTILE = 386
SIM_GSMTILE = 388
SIM_LGTILE = 544

# Stipple pattern dimensions
STIPPLE_WIDTH = 16
STIPPLE_HEIGHT = 16

# Stipple pattern bitmaps (from g_setup.c)
GRAY25_BITS = bytes(
    [
        0x77,
        0x77,
        0xDD,
        0xDD,
        0x77,
        0x77,
        0xDD,
        0xDD,
        0x77,
        0x77,
        0xDD,
        0xDD,
        0x77,
        0x77,
        0xDD,
        0xDD,
        0x77,
        0x77,
        0xDD,
        0xDD,
        0x77,
        0x77,
        0xDD,
        0xDD,
        0x77,
        0x77,
        0xDD,
        0xDD,
        0x77,
        0x77,
        0xDD,
        0xDD,
    ]
)

GRAY50_BITS = bytes(
    [
        0x55,
        0x55,
        0xAA,
        0xAA,
        0x55,
        0x55,
        0xAA,
        0xAA,
        0x55,
        0x55,
        0xAA,
        0xAA,
        0x55,
        0x55,
        0xAA,
        0xAA,
        0x55,
        0x55,
        0xAA,
        0xAA,
        0x55,
        0x55,
        0xAA,
        0xAA,
        0x55,
        0x55,
        0xAA,
        0xAA,
        0x55,
        0x55,
        0xAA,
        0xAA,
    ]
)

GRAY75_BITS = bytes(
    [
        0x88,
        0x88,
        0x22,
        0x22,
        0x88,
        0x88,
        0x22,
        0x22,
        0x88,
        0x88,
        0x22,
        0x22,
        0x88,
        0x88,
        0x22,
        0x22,
        0x88,
        0x88,
        0x22,
        0x22,
        0x88,
        0x88,
        0x22,
        0x22,
        0x88,
        0x88,
        0x22,
        0x22,
        0x88,
        0x88,
        0x22,
        0x22,
    ]
)

VERT_BITS = bytes(
    [
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
        0xAA,
    ]
)

HORIZ_BITS = bytes(
    [
        0xFF,
        0xFF,
        0x00,
        0x00,
        0xFF,
        0xFF,
        0x00,
        0x00,
        0xFF,
        0xFF,
        0x00,
        0x00,
        0xFF,
        0xFF,
        0x00,
        0x00,
        0xFF,
        0xFF,
        0x00,
        0x00,
        0xFF,
        0xFF,
        0x00,
        0x00,
        0xFF,
        0xFF,
        0x00,
        0x00,
        0xFF,
        0xFF,
        0x00,
        0x00,
    ]
)

DIAG_BITS = bytes(
    [
        0x55,
        0x55,
        0xEE,
        0xEE,
        0x55,
        0x55,
        0xBA,
        0xBB,
        0x55,
        0x55,
        0xEE,
        0xEE,
        0x55,
        0x55,
        0xBA,
        0xBB,
        0x55,
        0x55,
        0xEE,
        0xEE,
        0x55,
        0x55,
        0xBA,
        0xBB,
        0x55,
        0x55,
        0xEE,
        0xEE,
        0x55,
        0x55,
        0xBA,
        0xBB,
    ]
)

# History names and colors (for pygame rendering)
HIST_NAMES = [
    "Residential",
    "Commercial",
    "Industrial",
    "Cash Flow",
    "Crime",
    "Pollution",
]

HIST_COLORS = [
    (144, 238, 144),  # Light green for residential
    (0, 0, 139),  # Dark blue for commercial
    (255, 255, 0),  # Yellow for industrial
    (0, 100, 0),  # Dark green for cash flow
    (255, 0, 0),  # Red for crime
    (128, 128, 0),  # Olive for pollution
]

# Sprite types for disasters
# GOD = 5  # Monster/Godzilla sprite
# TOR = 6  # Tornado sprite
# COP = 2  # Police helicopter sprite
# AIR = 3  # Airplane sprite
# SHI = 4  # Ship sprite
# EXP = 7  # Explosion sprite

# ============================================================================
# Value Mapping Constants
# ============================================================================

VAL_NONE = 0
VAL_LOW = 1
VAL_MEDIUM = 2
VAL_HIGH = 3
VAL_VERYHIGH = 4
VAL_PLUS = 5
VAL_VERYPLUS = 6
VAL_MINUS = 7
VAL_VERYMINUS = 8

# Color mapping arrays (pygame color indices)
valMap: list[int] = [
    -1,  # VAL_NONE
    COLOR_LIGHTGRAY,  # VAL_LOW
    COLOR_YELLOW,  # VAL_MEDIUM
    COLOR_ORANGE,  # VAL_HIGH
    COLOR_RED,  # VAL_VERYHIGH
    COLOR_DARKGREEN,  # VAL_PLUS
    COLOR_LIGHTGREEN,  # VAL_VERYPLUS
    COLOR_ORANGE,  # VAL_MINUS
    COLOR_YELLOW,  # VAL_VERYMINUS
]

# Grayscale mapping for monochrome displays
valGrayMap: list[int] = [
    -1,  # VAL_NONE
    31,  # VAL_LOW
    127,  # VAL_MEDIUM
    191,  # VAL_HIGH
    255,  # VAL_VERYHIGH
    223,  # VAL_PLUS
    255,  # VAL_VERYPLUS
    31,  # VAL_MINUS
    0,  # VAL_VERYMINUS
]

# Color definitions for power view
UNPOWERED = COLOR_LIGHTBLUE
POWERED = COLOR_RED
CONDUCTIVE = COLOR_LIGHTGRAY

# Constants (ported from w_piem.c)
PI = 3.1415926535897932
TWO_PI = 6.2831853071795865
PIE_SPOKE_INSET = 6
PIE_BG_COLOR = "#bfbfbf"
PIE_ACTIVE_FG_COLOR = "black"
PIE_ACTIVE_BG_COLOR = "#bfbfbf"
PIE_FG = "black"
PIE_ACTIVE_BORDER_WIDTH = 2
PIE_INACTIVE_RADIUS = 8
PIE_MIN_RADIUS = 16
PIE_EXTRA_RADIUS = 2
PIE_BORDER_WIDTH = 2
PIE_POPUP_DELAY = 250

# Color intensity mapping (from original X implementation)
COLOR_INTENSITIES = [
    255,  # COLOR_WHITE
    170,  # COLOR_YELLOW
    127,  # COLOR_ORANGE
    85,  # COLOR_RED
    63,  # COLOR_DARKRED
    76,  # COLOR_DARKBLUE
    144,  # COLOR_LIGHTBLUE
    118,  # COLOR_BROWN
    76,  # COLOR_LIGHTGREEN
    42,  # COLOR_DARKGREEN
    118,  # COLOR_OLIVE
    144,  # COLOR_LIGHTBROWN
    191,  # COLOR_LIGHTGRAY
    127,  # COLOR_MEDIUMGRAY
    63,  # COLOR_DARKGRAY
    0,  # COLOR_BLACK
]


# Power grid constants
POWERMAPROW = (WORLD_X + 15) // 16  # ((WORLD_X + 15) / 16)
# PWRMAPSIZE = POWERMAPROW * WORLD_Y
# PWRSTKSIZE = (
#     WORLD_X * WORLD_Y
# ) // 4  # ((WORLD_X * WORLD_Y) / 4)

# Power-related bit constants
# PWRBIT = 32768  # 0x8000 - bit 15
# CONDBIT = 16384  # 0x4000 - bit 14

# TILE_COUNT = 960  # From sim.h

SIM_RAND_MAX = 0xFFFF  # Maximum value returned by sim_rand()

# Generator types
TYPE_0 = 0  # linear congruential
TYPE_1 = 1  # x**7 + x**3 + 1
TYPE_2 = 2  # x**15 + x + 1
TYPE_3 = 3  # x**31 + x**3 + 1
TYPE_4 = 4  # x**63 + x + 1

# Break values (minimum state size for each type)
BREAK_0 = 8
BREAK_1 = 32
BREAK_2 = 64
BREAK_3 = 128
BREAK_4 = 256

# Degrees for each polynomial
DEG_0 = 0
DEG_1 = 7
DEG_2 = 15
DEG_3 = 31
DEG_4 = 63

# Separations between coefficients
SEP_0 = 0
SEP_1 = 3
SEP_2 = 1
SEP_3 = 3
SEP_4 = 1

MAX_TYPES = 5

# Arrays of degrees and separations
degrees = [DEG_0, DEG_1, DEG_2, DEG_3, DEG_4]
seps = [SEP_0, SEP_1, SEP_2, SEP_3, SEP_4]

# Default state table (from random.c)
randtbl = [
    TYPE_3,
    0x9A319039,
    0x32D9C024,
    0x9B663182,
    0x5DA1F342,
    0xDE3B81E0,
    0xDF0A6FB5,
    0xF103BC02,
    0x48F340FB,
    0x7449E56B,
    0xBEB1DBB0,
    0xAB5C5918,
    0x946554FD,
    0x8C2E680F,
    0xEB3D799F,
    0xB11EE0B7,
    0x2D436B86,
    0xDA672E2A,
    0x1588CA88,
    0xE369735D,
    0x904F35F7,
    0xD7158FD6,
    0x6FA6F051,
    0x616E6B96,
    0xAC94EFDC,
    0x36413F93,
    0xC622C298,
    0xF5A42AB8,
    0x8A88D77B,
    0xF5AD9D0E,
    0x8999220B,
    0x27FB47B9,
]

# Sprite groove offsets (from w_sprite.c)
TRA_GROOVE_X = -39
TRA_GROOVE_Y = 6
BUS_GROOVE_X = -39
BUS_GROOVE_Y = 6

# Sprite directions (8-directional movement)
DIR_NORTH = 0
DIR_NORTHEAST = 1
DIR_EAST = 2
DIR_SOUTHEAST = 3
DIR_SOUTH = 4
DIR_SOUTHWEST = 5
DIR_WEST = 6
DIR_NORTHWEST = 7

# Constants from the original C code
WORLD_X = 120
WORLD_Y = 100
RIVER = 2
REDGE = 3
CHANNEL = 4
WOODS = 37
BL = 4096  # Burned land bit
BN = 8192  # Tree bit
BLN = BL + BN  # Burned tree bit

# River smoothing lookup table
RED_TAB = [
    13 + BL,
    13 + BL,
    17 + BL,
    15 + BL,
    5 + BL,
    2,
    19 + BL,
    17 + BL,
    9 + BL,
    11 + BL,
    2,
    13 + BL,
    7 + BL,
    9 + BL,
    5 + BL,
    2,
]

# Tree smoothing lookup table
TED_TAB = [0, 0, 0, 34, 0, 0, 36, 35, 0, 32, 0, 33, 30, 31, 29, 37]

# Direction movement tables
DIR_TAB_X = [0, 1, 1, 1, 0, -1, -1, -1]
DIR_TAB_Y = [-1, -1, 0, 1, 1, 1, 0, -1]

# River placement matrices
BR_MATRIX = [
    [0, 0, 0, 3, 3, 3, 0, 0, 0],
    [0, 0, 3, 2, 2, 2, 3, 0, 0],
    [0, 3, 2, 2, 2, 2, 2, 3, 0],
    [3, 2, 2, 2, 2, 2, 2, 2, 3],
    [3, 2, 2, 2, 4, 2, 2, 2, 3],
    [3, 2, 2, 2, 2, 2, 2, 2, 3],
    [0, 3, 2, 2, 2, 2, 2, 3, 0],
    [0, 0, 3, 2, 2, 2, 3, 0, 0],
    [0, 0, 0, 3, 3, 3, 0, 0, 0],
]

SR_MATRIX = [
    [0, 0, 3, 3, 0, 0],
    [0, 3, 2, 2, 3, 0],
    [3, 2, 2, 2, 2, 3],
    [3, 2, 2, 2, 2, 3],
    [0, 3, 2, 2, 3, 0],
    [0, 0, 3, 3, 0, 0],
]

SIM_TIMER_EVENT = pygame.USEREVENT + 2
EARTHQUAKE_TIMER_EVENT = pygame.USEREVENT + 3
UPDATE_EVENT = pygame.USEREVENT + 4

# Tool state enumeration
# residentialState = 0
# commercialState = 1
# industrialState = 2
# fireState = 3
# queryState = 4
# policeState = 5
# wireState = 6
# dozeState = 7
# rrState = 8
# roadState = 9
# chalkState = 10
# eraserState = 11
# stadiumState = 12
# parkState = 13
# seaportState = 14
# powerState = 15
# nuclearState = 16
# airportState = 17
# networkState = 18

# Tool state range
firstState = residentialState
lastState = networkState

# Cost of each tool
CostOf: list[int] = [
    100,
    100,
    100,
    500,  # residential, commercial, industrial, fire
    0,
    500,
    5,
    1,  # query, police, wire, bulldoze
    20,
    10,
    0,
    0,  # rail, road, chalk, eraser
    5000,
    10,
    3000,
    3000,  # stadium, park, seaport, coal power
    5000,
    10000,
    100,  # nuclear, airport, network
]

# Size of each tool (radius from center)
toolSize: list[int] = [
    3,
    3,
    3,
    3,  # residential, commercial, industrial, fire (3x3)
    1,
    3,
    1,
    1,  # query, police, wire, bulldoze (1x1 or 3x3)
    1,
    1,
    0,
    0,  # rail, road, chalk, eraser (1x1 or freeform)
    4,
    1,
    4,
    4,  # stadium, park, seaport, coal power (4x4)
    4,
    6,
    1,
    0,  # nuclear, airport, network (4x4, 6x6, 1x1)
]

# Offset from map coordinates to tool center
toolOffset: list[int] = [
    1,
    1,
    1,
    1,  # residential, commercial, industrial, fire
    0,
    1,
    0,
    0,  # query, police, wire, bulldoze
    0,
    0,
    0,
    0,  # rail, road, chalk, eraser
    1,
    0,
    1,
    1,  # stadium, park, seaport, coal power
    1,
    1,
    0,
    0,  # nuclear, airport, network
]

# Tool colors for overlay display (RGB pairs)
toolColors: list[int] = [
    0x00FF00,
    0x00FFFF,
    0xFFFF00,
    0x00FF00,  # residential (green), commercial (cyan), industrial (yellow), fire (green/red)
    0xFF8000,
    0x00FF00,
    0x808080,
    0x808080,  # query (orange), police (green/cyan), wire (gray/yellow), bulldoze (brown/gray)
    0x808080,
    0xFFFFFF,
    0xC0C0C0,
    0x808080,  # rail (gray/olive), road (gray/white), chalk (gray/gray), eraser (gray/gray)
    0xC0C0FF,
    0x806040,
    0xC0C0FF,
    0xC0C0FF,  # stadium (gray/green), park (brown/green), seaport (gray/blue), power (gray/yellow)
    0xC0C0FF,
    0xC0C0FF,
    0xC0C0FF,
    0xFF0000,  # nuclear (gray/yellow), airport (gray/brown), network (gray/red), (unused)
]

MAXDIS = 30  # Maximum distance to try driving

# aniTile: Animation tile lookup table
# Maps animation indices to actual tile IDs for rendering animated elements
ANI_TILE_SIZE = 1024

ani_tile: list[int] = [
    # Base tiles (0-55)
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,
    29,
    30,
    31,
    32,
    33,
    34,
    35,
    36,
    37,
    38,
    39,
    40,
    41,
    42,
    43,
    44,
    45,
    46,
    47,
    48,
    49,
    50,
    51,
    52,
    53,
    54,
    55,
    # Fire animation (56-63)
    57,
    58,
    59,
    60,
    61,
    62,
    63,
    56,
    # No Traffic (64-79)
    64,
    65,
    66,
    67,
    68,
    69,
    70,
    71,
    72,
    73,
    74,
    75,
    76,
    77,
    78,
    79,
    # Light Traffic (80-143) - reordered version from #else branch
    128,
    129,
    130,
    131,
    132,
    133,
    134,
    135,
    136,
    137,
    138,
    139,
    140,
    141,
    142,
    143,
    80,
    81,
    82,
    83,
    84,
    85,
    86,
    87,
    88,
    89,
    90,
    91,
    92,
    93,
    94,
    95,
    96,
    97,
    98,
    99,
    100,
    101,
    102,
    103,
    104,
    105,
    106,
    107,
    108,
    109,
    110,
    111,
    112,
    113,
    114,
    115,
    116,
    117,
    118,
    119,
    120,
    121,
    122,
    123,
    124,
    125,
    126,
    127,
    # Heavy Traffic (144-207) - reordered version from #else branch
    192,
    193,
    194,
    195,
    196,
    197,
    198,
    199,
    200,
    201,
    202,
    203,
    204,
    205,
    206,
    207,
    144,
    145,
    146,
    147,
    148,
    149,
    150,
    151,
    152,
    153,
    154,
    155,
    156,
    157,
    158,
    159,
    160,
    161,
    162,
    163,
    164,
    165,
    166,
    167,
    168,
    169,
    170,
    171,
    172,
    173,
    174,
    175,
    176,
    177,
    178,
    179,
    180,
    181,
    182,
    183,
    184,
    185,
    186,
    187,
    188,
    189,
    190,
    191,
    # Wires & Rails (208-239)
    208,
    209,
    210,
    211,
    212,
    213,
    214,
    215,
    216,
    217,
    218,
    219,
    220,
    221,
    222,
    223,
    224,
    225,
    226,
    227,
    228,
    229,
    230,
    231,
    232,
    233,
    234,
    235,
    236,
    237,
    238,
    239,
    # Residential (240-422)
    240,
    241,
    242,
    243,
    244,
    245,
    246,
    247,
    248,
    249,
    250,
    251,
    252,
    253,
    254,
    255,
    256,
    257,
    258,
    259,
    260,
    261,
    262,
    263,
    264,
    265,
    266,
    267,
    268,
    269,
    270,
    271,
    272,
    273,
    274,
    275,
    276,
    277,
    278,
    279,
    280,
    281,
    282,
    283,
    284,
    285,
    286,
    287,
    288,
    289,
    290,
    291,
    292,
    293,
    294,
    295,
    296,
    297,
    298,
    299,
    300,
    301,
    302,
    303,
    304,
    305,
    306,
    307,
    308,
    309,
    310,
    311,
    312,
    313,
    314,
    315,
    316,
    317,
    318,
    319,
    320,
    321,
    322,
    323,
    324,
    325,
    326,
    327,
    328,
    329,
    330,
    331,
    332,
    333,
    334,
    335,
    336,
    337,
    338,
    339,
    340,
    341,
    342,
    343,
    344,
    345,
    346,
    347,
    348,
    349,
    350,
    351,
    352,
    353,
    354,
    355,
    356,
    357,
    358,
    359,
    360,
    361,
    362,
    363,
    364,
    365,
    366,
    367,
    368,
    369,
    370,
    371,
    372,
    373,
    374,
    375,
    376,
    377,
    378,
    379,
    380,
    381,
    382,
    383,
    384,
    385,
    386,
    387,
    388,
    389,
    390,
    391,
    392,
    393,
    394,
    395,
    396,
    397,
    398,
    399,
    400,
    401,
    402,
    403,
    404,
    405,
    406,
    407,
    408,
    409,
    410,
    411,
    412,
    413,
    414,
    415,
    416,
    417,
    418,
    419,
    420,
    421,
    422,
    # Commercial (423-611)
    423,
    424,
    425,
    426,
    427,
    428,
    429,
    430,
    431,
    432,
    433,
    434,
    435,
    436,
    437,
    438,
    439,
    440,
    441,
    442,
    443,
    444,
    445,
    446,
    447,
    448,
    449,
    450,
    451,
    452,
    453,
    454,
    455,
    456,
    457,
    458,
    459,
    460,
    461,
    462,
    463,
    464,
    465,
    466,
    467,
    468,
    469,
    470,
    471,
    472,
    473,
    474,
    475,
    476,
    477,
    478,
    479,
    480,
    481,
    482,
    483,
    484,
    485,
    486,
    487,
    488,
    489,
    490,
    491,
    492,
    493,
    494,
    495,
    496,
    497,
    498,
    499,
    500,
    501,
    502,
    503,
    504,
    505,
    506,
    507,
    508,
    509,
    510,
    511,
    512,
    513,
    514,
    515,
    516,
    517,
    518,
    519,
    520,
    521,
    522,
    523,
    524,
    525,
    526,
    527,
    528,
    529,
    530,
    531,
    532,
    533,
    534,
    535,
    536,
    537,
    538,
    539,
    540,
    541,
    542,
    543,
    544,
    545,
    546,
    547,
    548,
    549,
    550,
    551,
    552,
    553,
    554,
    555,
    556,
    557,
    558,
    559,
    560,
    561,
    562,
    563,
    564,
    565,
    566,
    567,
    568,
    569,
    570,
    571,
    572,
    573,
    574,
    575,
    576,
    577,
    578,
    579,
    580,
    581,
    582,
    583,
    584,
    585,
    586,
    587,
    588,
    589,
    590,
    591,
    592,
    593,
    594,
    595,
    596,
    597,
    598,
    599,
    600,
    601,
    602,
    603,
    604,
    605,
    606,
    607,
    608,
    609,
    610,
    611,
    # Industrial (612-692)
    612,
    613,
    614,
    615,
    616,
    617,
    618,
    619,
    852,
    621,
    622,
    623,
    624,
    625,
    626,
    627,
    628,
    629,
    630,
    631,
    632,
    633,
    634,
    635,
    636,
    637,
    638,
    639,
    640,
    884,
    642,
    643,
    888,
    645,
    646,
    647,
    648,
    892,
    896,
    651,
    652,
    653,
    654,
    655,
    656,
    657,
    658,
    659,
    660,
    661,
    662,
    663,
    664,
    665,
    666,
    667,
    668,
    669,
    670,
    671,
    672,
    673,
    674,
    675,
    900,
    904,
    678,
    679,
    680,
    681,
    682,
    683,
    684,
    685,
    908,
    687,
    688,
    912,
    690,
    691,
    692,
    # SeaPort (693-708)
    693,
    694,
    695,
    696,
    697,
    698,
    699,
    700,
    701,
    702,
    703,
    704,
    705,
    706,
    707,
    708,
    # AirPort (709-744)
    709,
    710,
    832,
    712,
    713,
    714,
    715,
    716,
    717,
    718,
    719,
    720,
    721,
    722,
    723,
    724,
    725,
    726,
    727,
    728,
    729,
    730,
    731,
    732,
    733,
    734,
    735,
    736,
    737,
    738,
    739,
    740,
    741,
    742,
    743,
    744,
    # Coal power (745-760)
    745,
    746,
    916,
    920,
    749,
    750,
    924,
    928,
    753,
    754,
    755,
    756,
    757,
    758,
    759,
    760,
    # Fire Dept (761-778)
    761,
    762,
    763,
    764,
    765,
    766,
    767,
    768,
    769,
    770,
    771,
    772,
    773,
    774,
    775,
    776,
    777,
    778,
    # Stadium (779-794)
    779,
    780,
    781,
    782,
    783,
    784,
    785,
    786,
    787,
    788,
    789,
    790,
    791,
    792,
    793,
    794,
    # Stadium Anims (795-810)
    795,
    796,
    797,
    798,
    799,
    800,
    801,
    802,
    803,
    804,
    805,
    806,
    807,
    808,
    809,
    810,
    # Nuclear Power (811-826)
    811,
    812,
    813,
    814,
    815,
    816,
    817,
    818,
    819,
    952,
    821,
    822,
    823,
    824,
    825,
    826,
    # Power out + Bridges (827-831)
    827,
    828,
    829,
    830,
    831,
    # Radar dish (833-840)
    833,
    834,
    835,
    836,
    837,
    838,
    839,
    832,
    # Fountain / Flag (841-860)
    841,
    842,
    843,
    840,
    845,
    846,
    847,
    848,
    849,
    850,
    851,
    844,
    853,
    854,
    855,
    856,
    857,
    858,
    859,
    852,
    # zone destruct & rubblize (861-868)
    861,
    862,
    863,
    864,
    865,
    866,
    867,
    867,
    # totally unsure (868-883)
    868,
    869,
    870,
    871,
    872,
    873,
    874,
    875,
    876,
    877,
    878,
    879,
    880,
    881,
    882,
    883,
    # Smoke stacks (885-932)
    885,
    886,
    887,
    884,
    889,
    890,
    891,
    888,
    893,
    894,
    895,
    892,
    897,
    898,
    899,
    896,
    901,
    902,
    903,
    900,
    905,
    906,
    907,
    904,
    909,
    910,
    911,
    908,
    913,
    914,
    915,
    912,
    917,
    918,
    919,
    916,
    921,
    922,
    923,
    920,
    925,
    926,
    927,
    924,
    929,
    930,
    931,
    928,
    # Stadium Playfield (933-948)
    933,
    934,
    935,
    936,
    937,
    938,
    939,
    932,
    941,
    942,
    943,
    944,
    945,
    946,
    947,
    940,
    # Bridge up chars (948-951)
    948,
    949,
    950,
    951,
    # Nuclear swirl (953-956)
    953,
    954,
    955,
    952,
    # Pad to 1024 elements with 0s (invalid/empty tiles)
] + [0] * (1024 - 956)


# aniSynch: Animation synchronization values
# Controls timing and synchronization of animated tiles
# 0xff = no animation, other values control animation speed/phasing
ani_synch: list[int] = [
    # Base tiles (0-55) - no animation
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    # Fire (56-63) - no animation sync
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    # No Traffic (64-79) - no animation
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    # Light Traffic (80-143) - animated with different phases
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    # Heavy Traffic (144-207) - animated with different phases
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x11,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x22,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x44,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    0x88,
    # Wires and Rails (208-239) - no animation
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    # Residential (240-422) - no animation
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    # Commercial (423-611) - no animation
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    # Industrial (612-692) - some animated elements
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0x01,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0x11,
    0xFF,
    0xFF,
    0x11,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0x11,
    0x11,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0x11,
    0x11,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0x11,
    0xFF,
    0xFF,
    0x11,
    0xFF,
    0xFF,
    0xFF,
    # SeaPort (693-708) - no animation
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    # AirPort (709-744) - some animation
    0xFF,
    0xFF,
    0x01,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    # Coal Power (745-760) - animated
    0xFF,
    0xFF,
    0x11,
    0x11,
    0xFF,
    0xFF,
    0x11,
    0x11,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    # Fire/Police Department (761-778) - no animation
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    # Stadium (779-794) - no animation
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    # Full Stadium (795-810) - no animation
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    # Nuclear Power (811-826) - some animation
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0x11,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    # Power out/Bridges (827-831) - no animation
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    # Radar Dish (833-840) - animated
    0x01,
    0x02,
    0x04,
    0x08,
    0x10,
    0x20,
    0x40,
    0x80,
    # Fountain/Flag (841-860) - animated
    0x11,
    0x22,
    0x44,
    0x88,
    0x01,
    0x02,
    0x04,
    0x08,
    0x10,
    0x20,
    0x40,
    0x80,
    0x01,
    0x02,
    0x04,
    0x08,
    0x10,
    0x20,
    0x40,
    0x80,
    # Zone Destruct + Rubblize (861-868) - no animation
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    # Totally Unsure (869-884) - no animation
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    # Smoke Stacks (885-932) - animated
    0x11,
    0x22,
    0x44,
    0x88,
    0x11,
    0x22,
    0x44,
    0x88,
    0x11,
    0x22,
    0x44,
    0x88,
    0x11,
    0x22,
    0x44,
    0x88,
    0x11,
    0x22,
    0x44,
    0x88,
    0x11,
    0x22,
    0x44,
    0x88,
    0x11,
    0x22,
    0x44,
    0x88,
    0x11,
    0x22,
    0x44,
    0x88,
    0x11,
    0x22,
    0x44,
    0x88,
    0x11,
    0x22,
    0x44,
    0x88,
    0x11,
    0x22,
    0x44,
    0x88,
    0x11,
    0x22,
    0x44,
    0x88,
    # Stadium Playfield (933-948) - animated
    0x01,
    0x02,
    0x04,
    0x08,
    0x10,
    0x20,
    0x40,
    0x80,
    0x01,
    0x02,
    0x04,
    0x08,
    0x10,
    0x20,
    0x40,
    0x80,
    # Bridge Up (949-952) - no animation
    0xFF,
    0xFF,
    0xFF,
    0xFF,
    # Nuclear swirl (953-956) - animated
    0x11,
    0x22,
    0x44,
    0x88,
    # Pad to 1024 elements
]

if len(ani_tile) < ANI_TILE_SIZE:
    ani_tile.extend([0] * (ANI_TILE_SIZE - len(ani_tile)))
else:
    ani_tile = ani_tile[:ANI_TILE_SIZE]

# Sound channel constants (matching original TCL interface)
# Legacy Tcl used: mode (background), edit (UI clicks), fancy (events),
# warning (disasters), intercom (notifications)
SOUND_CHANNELS = {
    "mode": 6,  # Background/ambient sounds
    "edit": 1,  # Editor/UI clicks (bulldozer, tool selection)
    "fancy": 2,  # Event sounds (building construction, etc.)
    "warning": 3,  # Disaster warnings (fire, monster, etc.)
    "intercom": 4,  # Notification messages
    "sprite": 5,  # Sprite/moving object sounds
    "city": 0,  # City-wide sound effects (legacy compatibility)
}

# Channel priorities (higher number = higher priority)
SOUND_CHANNEL_PRIORITY = {
    "warning": 100,  # Disasters must be heard
    "intercom": 80,  # Notifications are important
    "fancy": 50,  # Events are moderately important
    "edit": 30,  # UI feedback is useful
    "sprite": 20,  # Sprites are ambient
    "mode": 10,  # Background is lowest priority
    "city": 10,  # Legacy channel, low priority
}

# Maximum number of sound channels
MAX_CHANNELS = 8

# Sound file extensions to try
SOUND_EXTENSIONS = [".wav", ".ogg", ".mp3"]
