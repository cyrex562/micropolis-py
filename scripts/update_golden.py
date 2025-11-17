#!/usr/bin/env python3
"""
Update golden reference images for snapshot tests.

This script runs snapshot tests with UPDATE_GOLDEN=1 to regenerate
all golden reference images. Use this when visual changes are intentional
and you want to update the baseline.

Usage:
    python scripts/update_golden.py [test_pattern]

Examples:
    python scripts/update_golden.py                    # Update all
    python scripts/update_golden.py test_editor        # Update editor tests
    python scripts/update_golden.py test_snapshots.py  # Update specific file
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Run snapshot tests with UPDATE_GOLDEN=1."""
    # Get project root (parent of scripts/)
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Build pytest command
    test_pattern = sys.argv[1] if len(sys.argv) > 1 else "tests/"

    # Set environment to update golden images
    env = os.environ.copy()
    env["UPDATE_GOLDEN"] = "1"
    env["SDL_VIDEODRIVER"] = "dummy"  # Headless mode for CI

    # Run pytest
    cmd = ["pytest", "-v", test_pattern, "-k", "snapshot"]

    print(f"Running: {' '.join(cmd)}")
    print(f"Environment: UPDATE_GOLDEN=1, SDL_VIDEODRIVER=dummy")
    print(f"Working directory: {project_root}")
    print("-" * 70)

    result = subprocess.run(cmd, env=env, check=False)

    if result.returncode == 0:
        print("-" * 70)
        print("✓ Golden images updated successfully!")
        print("\nNext steps:")
        print("  1. Review changes: git diff tests/golden/")
        print("  2. Commit if changes are intentional")
        print("  3. Run tests normally to verify: pytest tests/")
    else:
        print("-" * 70)
        print("✗ Some tests failed during update")
        print("\nCheck test output above for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
