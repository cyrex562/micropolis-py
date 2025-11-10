#!/usr/bin/env python3
"""
Run the pytest suite in manageable chunks so each invocation stays under the
automation timeout enforced by the Codex CLI harness.

Usage:
    python scripts/run_pytest_chunks.py [--chunk-size 120] [extra pytest args...]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List


def chunked(items: List[str], size: int) -> Iterable[List[str]]:
    """Yield lists of at most `size` items."""
    for idx in range(0, len(items), size):
        yield items[idx : idx + size]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run pytest suites in batches to avoid watchdog timeouts."
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=120,
        help="Number of test files per pytest invocation (default: 120)",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Additional arguments forwarded to each pytest run",
    )
    args = parser.parse_args()

    test_files = sorted(str(path) for path in Path("tests").glob("test_*.py"))
    if not test_files:
        print("No tests/ test_*.py files were found.", file=sys.stderr)
        return 1

    for idx, chunk in enumerate(chunked(test_files, max(1, args.chunk_size)), start=1):
        print(f"\n=== Pytest chunk {idx} ({len(chunk)} files) ===")
        cmd = ["uv", "run", "pytest", *chunk, *args.pytest_args]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            return result.returncode

    print("\nAll pytest chunks completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
