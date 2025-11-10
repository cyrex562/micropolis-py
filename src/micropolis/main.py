#!/usr/bin/env python3
"""
Micropolis Python Binary

This script serves as the main executable for the Python port of Micropolis.
It replaces the original C binary and provides the same stdin/stdout interface
expected by the Sugar activity wrapper.

Usage:
    python Micropolis.py [options]

The script initializes the Micropolis simulation engine and runs the main pygame loop.
"""

import sys
import os

# Add the src directory to Python path so we can import micropolis
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from micropolis.engine import main
except ImportError as e:
    print(f"Error importing micropolis engine: {e}", file=sys.stderr)
    print("Make sure the micropolis package is properly installed.", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    # Run the main function and exit with its return code
    sys.exit(main())