#!/usr/bin/env python3
"""
Basic test for the disaster system implementation.
Tests that disaster functions can be called without errors.
"""

import sys
import os

from micropolis.disasters import DoDisasters, MakeEarthquake, MakeFlood, MakeMonster, MakeTornado, MakeMeltdown

def test_disaster_system():
    """Test basic disaster system functionality"""

    print("Testing disaster system...")

    # Test DoDisasters function (main disaster dispatcher)
    try:
        DoDisasters()
        print("✓ DoDisasters() executed successfully")
    except Exception as e:
        print(f"✗ DoDisasters() failed: {e}")
        return False

    # Test individual disaster functions
    disaster_tests = [
        ("MakeEarthquake", MakeEarthquake),
        ("MakeFlood", MakeFlood),
        ("MakeMonster", MakeMonster),
        ("MakeTornado", MakeTornado),
        ("MakeMeltdown", MakeMeltdown),
    ]

    for name, func in disaster_tests:
        try:
            func()
            print(f"✓ {name}() executed successfully")
        except Exception as e:
            print(f"✗ {name}() failed: {e}")
            return False

    print("All disaster system tests passed!")
    return True
