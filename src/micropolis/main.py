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

import logging
import sys
from datetime import datetime
from pathlib import Path

from rich.logging import RichHandler

from micropolis.engine import main


def init_logging():
    console_handler = RichHandler(rich_tracebacks=True, show_time=True, show_level=True)

# Create logs directory at project root (two parents up from this file)
    LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file_path = LOG_DIR / f"micropolis-{timestamp}.log"

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    file_handler.setFormatter(file_formatter)

# Configure root logger to use both handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

# Small startup message
    logging.getLogger(__name__).debug(
    f"Logging initialized. Console -> rich, File -> {log_file_path}"
)

init_logging()


if __name__ == "__main__":
    # Run the main function and exit with its return code
    sys.exit(main())
