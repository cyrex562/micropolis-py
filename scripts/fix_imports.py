#!/usr/bin/env python3
"""
Script to fix all imports from 'src.micropolis.' to 'micropolis.'
This removes the sys.path manipulation requirement.
"""

import re
from pathlib import Path


def fix_imports_in_file(filepath: Path) -> bool:
    """Fix imports in a single file. Returns True if file was modified."""
    try:
        content = filepath.read_text(encoding="utf-8")
        original = content

        # Replace 'from src.micropolis.' with 'from micropolis.'
        content = re.sub(r"\bfrom src\.micropolis\.", r"from micropolis.", content)

        # Replace 'import src.micropolis.' with 'import micropolis.'
        content = re.sub(r"\bimport src\.micropolis\.", r"import micropolis.", content)

        if content != original:
            filepath.write_text(content, encoding="utf-8")
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False


def main():
    """Find and fix all Python files with bad imports."""
    project_root = Path(__file__).resolve().parents[1]

    # Find all Python files
    python_files = list(project_root.rglob("*.py"))

    modified = []
    for filepath in python_files:
        # Skip this script itself and __pycache__ directories
        if "__pycache__" in str(filepath) or filepath == Path(__file__):
            continue

        if fix_imports_in_file(filepath):
            modified.append(filepath)
            print(f"Fixed: {filepath.relative_to(project_root)}")

    print(f"\n✓ Fixed {len(modified)} files")

    if not modified:
        print("No files needed fixing!")


if __name__ == "__main__":
    main()
