#!/usr/bin/env python3
"""
file_io.py - City save/load functionality for Micropolis Python port

This module implements the .cty file format loading and saving, ported from s_fileio.c.
It handles the binary city file format with proper endianness conversion and data validation.
"""

import os
import struct
import sys

from micropolis.constants import HISTLEN, MISCHISTLEN, WORLD_X, WORLD_Y
from micropolis.context import AppContext
from micropolis.engine import (
    InitFundingLevel,
    invalidate_errors,
    invalidate_maps,
    setSkips,
    setSpeed,
)
from micropolis.initialization import InitWillStuff
from micropolis.simulation import do_sim_init
from micropolis.ui_utilities import eval_cmd_str, set_city_name, set_funds, set_game_level
from micropolis.updates import UpdateFunds


# ============================================================================
# Endianness Handling
# ============================================================================


def _swap_shorts(buf: list, length: int) -> None:
    """
    Swap bytes in each short for endianness conversion.

    Args:
        buf: List of shorts to swap
        length: Number of shorts to process
    """
    for i in range(length):
        # Flip bytes in each short: 0xABCD -> 0xCDAB
        buf[i] = ((buf[i] & 0xFF) << 8) | ((buf[i] & 0xFF00) >> 8)


def _swap_longs(buf: list, length: int) -> None:
    """
    Swap bytes in each long for endianness conversion.

    Args:
        buf: List of longs to swap
        length: Number of longs to process
    """
    for i in range(length):
        # Flip bytes in each long: 0xABCDEFGH -> 0xGHEFCDAB
        long_val = buf[i]
        buf[i] = (
            ((long_val & 0x000000FF) << 24)
            | ((long_val & 0x0000FF00) << 8)
            | ((long_val & 0x00FF0000) >> 8)
            | ((long_val & 0xFF000000) >> 24)
        )


def _half_swap_longs(buf: list, length: int) -> None:
    """
    Swap 16-bit halves in each long for endianness conversion.

    Args:
        buf: List of longs to swap
        length: Number of longs to process
    """
    for i in range(length):
        # Flip 16-bit halves: 0xABCDEFGH -> 0xEFCDABGH
        long_val = buf[i]
        buf[i] = ((long_val & 0x0000FFFF) << 16) | ((long_val & 0xFFFF0000) >> 16)


# ============================================================================
# File I/O Helper Functions
# ============================================================================


def _load_short(buf: list, length: int, file_obj) -> bool:
    """
    Load shorts from file with endianness conversion.

    Args:
        buf: Buffer to store loaded shorts
        length: Number of shorts to load
        file_obj: Open file object

    Returns:
        True on success, False on failure
    """
    try:
        # Read raw bytes
        data = file_obj.read(length * 2)  # 2 bytes per short
        if len(data) != length * 2:
            return False

        # Unpack as little-endian unsigned shorts
        unpacked = struct.unpack(f"<{length}H", data)
        buf[:length] = unpacked

        # Convert to Mac endianness (big-endian)
        _swap_shorts(buf, length)

        return True
    except (struct.error, OSError):
        return False


def _load_long(buf: list, length: int, file_obj) -> bool:
    """
    Load longs from file with endianness conversion.

    Args:
        buf: Buffer to store loaded longs
        length: Number of longs to load
        file_obj: Open file object

    Returns:
        True on success, False on failure
    """
    try:
        # Read raw bytes
        data = file_obj.read(length * 4)  # 4 bytes per long
        if len(data) != length * 4:
            return False

        # Unpack as little-endian longs
        buf[:] = struct.unpack(f"<{length}l", data)

        # Convert to Mac endianness (big-endian)
        _swap_longs(buf, length)

        return True
    except (struct.error, OSError):
        return False


def _save_short(buf: list, length: int, file_obj) -> bool:
    """
    Save shorts to file with endianness conversion.

    Args:
        buf: Buffer containing shorts to save
        length: Number of shorts to save
        file_obj: Open file object

    Returns:
        True on success, False on failure
    """
    try:
        # Convert to Mac endianness (big-endian)
        _swap_shorts(buf, length)

        # Pack as big-endian unsigned shorts
        data = struct.pack(f">{length}H", *buf[:length])

        # Write to file
        if file_obj.write(data) != len(data):
            print(f"_save_short: write failed, expected {len(data)} bytes")
            return False

        # Convert back to intel endianness
        _swap_shorts(buf, length)

        return True
    except (struct.error, OSError):
        return False


def _save_long(buf: list, length: int, file_obj) -> bool:
    """
    Save longs to file with endianness conversion.

    Args:
        buf: Buffer containing longs to save
        length: Number of longs to save
        file_obj: Open file object

    Returns:
        True on success, False on failure
    """
    try:
        # Convert to Mac endianness (big-endian)
        _swap_longs(buf, length)

        # Pack as big-endian longs
        data = struct.pack(f">{length}l", *buf)

        # Write to file
        if file_obj.write(data) != len(data):
            return False

        # Convert back to intel endianness
        _swap_longs(buf, length)

        return True
    except (struct.error, OSError):
        return False


# ============================================================================
# City File Loading
# ============================================================================


def _load_file(context: AppContext, filename: str, directory: str | None = None) -> bool:
    """
    Load city data from a .cty file.

    Args:
        filename: Name of the city file
        directory: Optional directory path

    Returns:
        True on success, False on failure
        :param context:
    """
    filepath = filename
    if directory:
        filepath = os.path.join(directory, filename)

    try:
        with open(filepath, "rb") as f:
            # Check file size to determine city type
            f.seek(0, 2)  # Seek to end
            size = f.tell()
            f.seek(0)  # Seek back to beginning

            if size not in [27120, 99120, 219120]:
                return False  # Invalid file size

            # Load history data
            if not _load_short(context.res_his, HISTLEN // 2, f):
                return False
            if not _load_short(context.com_his, HISTLEN // 2, f):
                return False
            if not _load_short(context.ind_his, HISTLEN // 2, f):
                return False
            if not _load_short(context.crime_his, HISTLEN // 2, f):
                return False
            if not _load_short(context.pollution_his, HISTLEN // 2, f):
                return False
            if not _load_short(context.money_his, HISTLEN // 2, f):
                return False
            if not _load_short(context.misc_his, MISCHISTLEN // 2, f):
                return False

            # Load main map data
            map_data = []
            if not _load_short(
                map_data, WORLD_X * WORLD_Y, f
            ):
                return False

            # Convert flat array to 2D map
            for x in range(WORLD_X):
                for y in range(WORLD_Y):
                    context.map_data[x][y] = map_data[
                        x * WORLD_Y + y
                    ]

            return True

    except (OSError, IOError):
        return False


def loadFile(context: AppContext, filename: str) -> int:
    """
    Load a city file and initialize the simulation state.

    Args:
        filename: Path to the city file

    Returns:
        1 on success, 0 on failure
        :param context:
    """
    if not _load_file(context, filename, None):
        return 0

    # Extract total funds from MiscHis (stored as two shorts at positions 50-51)
    total_funds = context.misc_his[50] | (context.misc_his[51] << 16)
    total_funds_buf = [total_funds]
    _half_swap_longs(total_funds_buf, 1)
    context.total_funds = total_funds_buf[0]

    # Extract city time from MiscHis (position 8)
    city_time = context.misc_his[8]
    city_time_buf = [city_time]
    _half_swap_longs(city_time_buf, 1)
    context.city_time = city_time_buf[0]

    # Extract game settings from MiscHis
    context.auto_bulldoze = context.misc_his[52]  # Auto bulldoze flag
    context.auto_budget = context.misc_his[53]  # Auto budget flag
    context.auto_go = context.misc_his[54]  # Auto go flag
    context.user_sound_on = context.misc_his[55]  # Sound on/off flag
    context.city_tax = context.misc_his[56]  # City tax rate
    context.sim_speed = context.misc_his[57]  # Simulation speed

    # Extract budget percentages (stored as fixed-point values)
    police_pct = context.misc_his[58] | (context.misc_his[59] << 16)
    police_pct_buf = [police_pct]
    _half_swap_longs(police_pct_buf, 1)
    context.police_percent = police_pct_buf[0] / 65536.0

    fire_pct = context.misc_his[60] | (context.misc_his[61] << 16)
    fire_pct_buf = [fire_pct]
    _half_swap_longs(fire_pct_buf, 1)
    context.fire_percent = fire_pct_buf[0] / 65536.0

    road_pct = context.misc_his[62] | (context.misc_his[63] << 16)
    road_pct_buf = [road_pct]
    _half_swap_longs(road_pct_buf, 1)
    context.road_percent = road_pct_buf[0] / 65536.0

    # Validate and clamp values
    if context.city_time < 0:
        context.city_time = 0
    if context.city_tax > 20 or context.city_tax < 0:
        context.city_tax = 7
    if context.sim_speed < 0 or context.sim_speed > 3:
        context.sim_speed = 3

    # Update simulation state
    setSpeed(context, context.sim_speed)
    setSkips(context, 0)

    # Initialize funding and evaluation
    InitFundingLevel(context)
    InitWillStuff(context)
    context.scenario_id = 0
    context.init_sim_load = 1
    context.do_initial_eval = 0
    do_sim_init(context)
    invalidate_errors(context.sim)
    invalidate_maps(context.sim)

    return 1


# ============================================================================
# City File Saving
# ============================================================================


def saveFile(context: AppContext, filename: str) -> int:
    """
    Save the current city state to a .cty file.

    Args:
        filename: Path where to save the city file

    Returns:
        1 on success, 0 on failure
        :param context:
    """
    try:
        with open(filename, "wb") as f:
            # Store total funds in MiscHis (positions 50-51)
            total_funds = context.total_funds
            _half_swap_longs([total_funds], 1)
            context.misc_his[50] = total_funds & 0xFFFF
            context.misc_his[51] = (total_funds >> 16) & 0xFFFF

            # Store city time in MiscHis (position 8)
            city_time = context.city_time
            _half_swap_longs([city_time], 1)
            context.misc_his[8] = city_time & 0xFFFF

            # Store game settings in MiscHis
            context.misc_his[52] = context.auto_bulldoze
            context.misc_his[53] = context.auto_budget
            context.misc_his[54] = context.auto_go
            context.misc_his[55] = context.user_sound_on
            context.misc_his[57] = context.sim_speed
            context.misc_his[56] = context.city_tax

            # Store budget percentages as fixed-point values
            police_pct = int(context.police_percent * 65536)
            _half_swap_longs([police_pct], 1)
            context.misc_his[58] = police_pct & 0xFFFF
            context.misc_his[59] = (police_pct >> 16) & 0xFFFF

            fire_pct = int(context.fire_percent * 65536)
            _half_swap_longs([fire_pct], 1)
            context.misc_his[60] = fire_pct & 0xFFFF
            context.misc_his[61] = (fire_pct >> 16) & 0xFFFF

            road_pct = int(context.road_percent * 65536)
            _half_swap_longs([road_pct], 1)
            context.misc_his[62] = road_pct & 0xFFFF
            context.misc_his[63] = (road_pct >> 16) & 0xFFFF

            # Convert 2D map to flat array for saving
            map_data = []
            for x in range(WORLD_X):
                for y in range(WORLD_Y):
                    map_data.append(context.map_data[x][y])

            # Save all data sections
            if not _save_short(context.res_his, HISTLEN // 2, f):
                return 0
            if not _save_short(context.com_his, HISTLEN // 2, f):
                return 0
            if not _save_short(context.ind_his, HISTLEN // 2, f):
                return 0
            if not _save_short(context.crime_his, HISTLEN // 2, f):
                return 0
            if not _save_short(context.pollution_his, HISTLEN // 2, f):
                return 0
            if not _save_short(context.money_his, HISTLEN // 2, f):
                return 0
            if not _save_short(context.misc_his, MISCHISTLEN // 2, f):
                return 0
            if not _save_short(
                map_data, WORLD_X * WORLD_Y, f
            ):
                return 0

            return 1

    except (OSError, IOError):
        return 0


# ============================================================================
# Scenario Loading
# ============================================================================


def LoadScenario(context: AppContext, scenario_id: int) -> None:
    """
    Load a predefined scenario city.

    Args:
        scenario_id: Scenario number (1-8)
        :param context:
    """
    # Clear current city file name
    if context.city_file_name:
        context.city_file_name = ""

    # Set game level to 0 (scenarios override difficulty)
    set_game_level(context, 0)

    # Validate scenario ID
    if scenario_id < 1 or scenario_id > 8:
        scenario_id = 1

    # Scenario definitions
    scenarios = {
        1: ("Dullsville", "snro.111", 1900, 2, 5000),
        2: ("San Francisco", "snro.222", 1906, 2, 20000),
        3: ("Hamburg", "snro.333", 1944, 2, 20000),
        4: ("Bern", "snro.444", 1965, 2, 20000),
        5: ("Tokyo", "snro.555", 1957, 2, 20000),
        6: ("Detroit", "snro.666", 1972, 2, 20000),
        7: ("Boston", "snro.777", 2010, 2, 20000),
        8: ("Rio de Janeiro", "snro.888", 2047, 2, 20000),
    }

    name, fname, year, month, funds = scenarios[scenario_id]

    # Set scenario parameters
    context.scenario_id = scenario_id
    context.city_time = ((year - 1900) * 48) + month
    set_funds(context, funds)

    # Set city name
    set_city_name(context, name)

    # Reset simulation state
    setSkips(context, 0)
    invalidate_maps(context.sim)
    invalidate_errors(context.sim)
    setSpeed(context, 3)
    context.city_tax = 7

    # Load scenario file
    _load_file(context, fname, context.resource_dir)

    # Initialize simulation
    InitWillStuff(context)
    InitFundingLevel(context)
    UpdateFunds()
    invalidate_errors(context.sim)
    invalidate_maps(context.sim)
    context.init_sim_load = 1
    context.do_initial_eval = 0
    do_sim_init(context)
    context.DidLoadScenario()
    context.Kick()


# ============================================================================
# High-Level City Management
# ============================================================================


def LoadCity(context: AppContext, filename: str) -> int:
    """
    Load a city file with proper error handling and UI updates.

    Args:
        filename: Path to the city file

    Returns:
        1 on success, 0 on failure
        :param context:
    """
    if loadFile(context, filename):
        # Store filename
        if context.city_file_name:
            context.city_file_name = ""
        context.city_file_name = filename

        # Extract city name from filename
        base_name = os.path.basename(filename)
        if "." in base_name:
            base_name = base_name.rsplit(".", 1)[0]

        # Handle path separators for cross-platform compatibility
        if "\\" in base_name:
            base_name = base_name.rsplit("\\", 1)[1]
        elif "/" in base_name:
            base_name = base_name.rsplit("/", 1)[1]

        set_city_name(context, base_name)

        # Update UI and simulation state
        invalidate_maps(context.sim)
        invalidate_errors(context.sim)
        context.DidLoadCity()
        return 1
    else:
        # Handle load failure
        context.DidntLoadCity(f"Unable to load city from file: {filename}")
        return 0


def SaveCity(context: AppContext) -> None:
    """
    Save the current city, prompting for filename if needed.
    :param context:
    """
    if not context.city_file_name:
        context.DoSaveCityAs()
    else:
        if saveFile(context, context.city_file_name):
            context.DidSaveCity()
        else:
            msg = f"Unable to save city to file: {context.city_file_name}"
            context.DidntSaveCity(msg)


def DoSaveCityAs(context: AppContext) -> None:
    """
    Prompt user to choose a save filename.
    :param context:
    """
    # This would be implemented when UI is available
    # For now, delegate to TCL/Tk interface
    context.Eval("UISaveCityAs")


def SaveCityAs(context: AppContext, filename: str) -> None:
    """
    Save city to a specific filename.

    Args:
        filename: Target filename
        :param context:
    """
    # Store filename
    if context.city_file_name:
        context.city_file_name = ""
    context.city_file_name = filename

    # Extract city name from filename
    base_name = os.path.basename(filename)
    if "." in base_name:
        base_name = base_name.rsplit(".", 1)[0]

    # Handle path separators
    if "\\" in base_name:
        base_name = base_name.rsplit("\\", 1)[1]
    elif "/" in base_name:
        base_name = base_name.rsplit("/", 1)[1]

        if saveFile(context, context.city_file_name):
            set_city_name(context, base_name)
        context.DidSaveCity()
    else:
        msg = f"Unable to save city to file: {context.city_file_name}"
        context.DidntSaveCity(msg)


# ============================================================================
# UI Callback Stubs (to be implemented when UI is available)
# ============================================================================


def DidLoadScenario(context: AppContext) -> None:
    """Callback when scenario is loaded.
    :param context:
    """
    eval_cmd_str(context, "UIDidLoadScenario")


def DidLoadCity(context: AppContext) -> None:
    """Callback when city is loaded.
    :param context:
    """
    eval_cmd_str(context, "UIDidLoadCity")


def DidntLoadCity(context: AppContext, msg: str) -> None:
    """Callback when city load fails.
    :param context:
    """
    eval_cmd_str(context, f"UIDidntLoadCity {{{msg}}}")


def DidSaveCity(context: AppContext) -> None:
    """Callback when city is saved.
    :param context:
    """
    eval_cmd_str(context, "UIDidSaveCity")


def DidntSaveCity(context: AppContext, msg: str) -> None:
    """Callback when city save fails.
    :param context:
    """
    eval_cmd_str(context, f"UIDidntSaveCity {{{msg}}}")


# ============================================================================
# Modern API wrappers
# ============================================================================


def save_current_city_state(context: AppContext, filename: str) -> bool:
    """
    Save the current city state (Pythonic helper used by higher-level modules).
    :param filename:
    :param context:
    """
    return bool(saveFile(context, filename))


def load_city_from_file(context: AppContext, filename: str) -> bool:
    """
    Load a city file with success/failure semantics.
    :param filename:
    :param context:
    """
    return bool(LoadCity(context, filename))


# ============================================================================
# Utility Functions
# ============================================================================


def validateCityFile(filename: str) -> tuple[bool, str]:
    """
    Validate that a file is a proper .cty file.

    Args:
        filename: Path to the file to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check file size
        size = os.path.getsize(filename)
        if size not in [27120, 99120, 219120]:
            return (
                False,
                f"Invalid file size: {size} bytes. Expected 27120, 99120, or 219120.",
            )

        # Try to read the file header to validate format
        with open(filename, "rb") as f:
            # Read first few shorts to check if they're valid
            header_data = f.read(20)  # First 10 shorts
            if len(header_data) != 20:
                return False, "File too short to be a valid city file."

            # Unpack and check for reasonable values
            header_shorts = struct.unpack("<10H", header_data)
            # Basic sanity check - history values should be non-negative
            if any(x < 0 for x in header_shorts[:6]):  # First 6 history arrays
                return False, "Invalid history data in file."

        return True, ""

    except (OSError, IOError, struct.error) as e:
        return False, f"Error reading file: {e}"


def getCityFileInfo(filename: str) -> dict | None:
    """
    Get information about a city file without fully loading it.

    Args:
        filename: Path to the city file

    Returns:
        Dictionary with city info, or None if invalid
    """
    try:
        with open(filename, "rb") as f:
            # Check file size to determine city type
            f.seek(0, 2)
            size = f.tell()
            f.seek(0)

            city_type = "Unknown"
            if size == 27120:
                city_type = "Normal City"
            elif size == 99120:
                city_type = "2x2 City"
            elif size == 219120:
                city_type = "3x3 City"
            else:
                return None

            # Read some basic info from MiscHis
            f.seek(6 * (HISTLEN // 2) * 2)  # Skip history arrays
            misc_data = f.read(MISCHISTLEN * 2)
            misc_shorts = struct.unpack(f"<{MISCHISTLEN}H", misc_data)

            # Extract basic info
            city_tax = misc_shorts[56]
            sim_speed = misc_shorts[57]

            return {
                "filename": filename,
                "size": size,
                "type": city_type,
                "city_tax": city_tax,
                "sim_speed": sim_speed,
            }

    except (OSError, IOError, struct.error):
        return None


try:
    from micropolis import compat_shims
except ImportError:
    compat_shims = None

if compat_shims is not None:
    compat_shims.inject_legacy_wrappers(
        sys.modules[__name__],
        ["loadFile", "saveFile", "LoadCity", "SaveCity", "DoSaveCityAs"],
    )
