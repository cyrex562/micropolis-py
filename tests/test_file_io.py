#!/usr/bin/env python3
"""
Test for the file I/O system implementation.
Tests city file loading and saving functionality.
"""

import os
import tempfile
import sys

from micropolis.file_io import loadFile, saveFile, validateCityFile, getCityFileInfo
from micropolis import types, allocation, initialization

def test_file_io():
    """Test basic file I/O functionality"""

    # Initialize simulation state
    allocation.initMapArrays()
    initialization.InitWillStuff()
    types.ScenarioID = 0
    types.InitSimLoad = 1
    types.DoInitialEval = 0

    print("Testing file I/O system...")

    # Test loading an existing city file
    test_city = "cities/bluebird.cty"
    if os.path.exists(test_city):
        print(f"Testing load of existing city file: {test_city}")
        result = loadFile(test_city)
        if result:
            print("✓ Successfully loaded existing city file")
            print(f"  City name: {types.CityName}")
            print(f"  Total funds: {types.TotalFunds}")
            print(f"  City time: {types.CityTime}")
            print(f"  City tax: {types.CityTax}")
        else:
            print("✗ Failed to load existing city file")
            return False
    else:
        print(f"Test city file not found: {test_city}")
        return False

    # Test saving to a temporary file
    with tempfile.NamedTemporaryFile(suffix='.cty', delete=False) as tmp:
        temp_filename = tmp.name

    try:
        print(f"Testing save to temporary file: {temp_filename}")
        result = saveFile(temp_filename)
        if result:
            print("✓ Successfully saved city file")

            # Validate the saved file
            is_valid, error_msg = validateCityFile(temp_filename)
            if is_valid:
                print("✓ Saved file is valid")

                # Get file info
                info = getCityFileInfo(temp_filename)
                if info:
                    print("✓ File info retrieved successfully")
                    print(f"  File type: {info['type']}")
                    print(f"  City tax: {info['city_tax']}")
                    print(f"  Sim speed: {info['sim_speed']}")
                else:
                    print("✗ Failed to get file info")
                    return False
            else:
                print(f"✗ Saved file is invalid: {error_msg}")
                return False
        else:
            print("✗ Failed to save city file")
            return False

    finally:
        # Clean up temporary file
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)

    # Test loading and saving round-trip
    print("Testing load/save round-trip...")

    # Load original file again
    result1 = loadFile(test_city)
    if not result1:
        print("✗ Failed to reload original file")
        return False

    # Save to another temp file
    with tempfile.NamedTemporaryFile(suffix='.cty', delete=False) as tmp:
        temp_filename2 = tmp.name

    try:
        result2 = saveFile(temp_filename2)
        if not result2:
            print("✗ Failed to save in round-trip test")
            return False

        # Load the saved file back
        result3 = loadFile(temp_filename2)
        if not result3:
            print("✗ Failed to load saved file in round-trip test")
            return False

        print("✓ Load/save round-trip successful")

    finally:
        if os.path.exists(temp_filename2):
            os.unlink(temp_filename2)

    print("All file I/O tests passed!")
    return True
