#!/usr/bin/env python3
"""
Basic test for constants.py to verify Macintosh emulation constants are working.
"""

import sys
import os

# Add the src/micropolis directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'micropolis'))

try:
    import constants

    # Test basic type definitions
    assert constants.QUAD is int
    print("✓ QUAD type definition correct")

    # Test ctypes types are defined
    assert hasattr(constants, 'Byte')
    assert hasattr(constants, 'Ptr')
    assert hasattr(constants, 'Handle')
    print("✓ Basic Macintosh types defined")

    # Test Resource class
    resource = constants.Resource(buf=b"test", size=4, name="TEST", id=123)
    assert resource.buf == b"test"
    assert resource.size == 4
    assert resource.name == "TEST"
    assert resource.id == 123
    assert resource.next is None
    print("✓ Resource class works correctly")

    # Test resource management functions (stubs)
    assert constants.NewPtr(100) is None  # Returns None as placeholder
    assert constants.GetResource("TILE", 1) is None  # Returns None as placeholder
    assert constants.ResourceSize(None) == 0
    assert constants.ResourceName(None) == ""
    assert constants.ResourceID(None) == 0
    print("✓ Resource management functions defined")

    # Test constants
    assert 'TILE' in constants.RESOURCE_TYPES
    assert 'SND ' in constants.RESOURCE_TYPES
    assert constants.MAX_RESOURCE_SIZE == 65536
    print("✓ Constants defined correctly")

    print("\n🎉 All tests passed! constants.py is working correctly.")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except AssertionError as e:
    print(f"❌ Test failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)