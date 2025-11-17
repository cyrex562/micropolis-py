# Micropolis Python Port - AI Coding Guidelines

## Project Context

This is a port of the open source version of SimCity (Micropolis) from C/TCL/TK to Python 3 and Pygame. The original codebase is written in C for the simulation engine, with a TCL/Tk GUI, and wrapped as a Sugar activity for OLPC laptops.

## Development Standards

- Follow PEP 8 style guidelines for Python code
- Use type hints everywhere consistent with Python 3.13 and later.
  - Instead of `List` use `list[type]`
  - Instead of `Dict` use `dict[key_type, value_type]`
  - Instead of `Optional[type]` use `type | None`
- Use f-strings for string formatting
- Write unit tests for all code using pytest
- Write property-based tests for all code using hypothesis
- Use rich and logging to provide verbose logging of function behavior
- Run all python code with `uv`
- When addding new dependencies, use `uv add <package>` to add them to the virtual environment
- Use pydantic base models for all data structures where appropriate
- Prefer pure functions (no side-effects) and immutable data structures. Avoid in-place mutation of arguments
- Do not use global variables
- parse command-line arguments with argparse
- store settings in a TOML file and parse with tomli or pydantic
- Avoid initializing or setting variables to None as a placeholder or initial value. Prefer initializing with a meaningful default value. Use `type | None` only for variables that can legitimately be None.
- Access fields and methods directly. Do not use `getattr` or `setattr`
- Use classes instead of dictionaries where appropriate
- Write docstrings for all modules, classes, and functions
- Use type aliases for complex types
- Use enums for sets of related constants
- Use ruff for all linting and auto-formatting. Run `ruff check .` to check for issues and `ruff fix .` to auto-fix them.
- Use the Result type from the `result` library for functions that can fail instead of raising exceptions. in functions that call these funtions, check the result and handle errors by propagating them up.
- Use `pathlib.Path` for all file and directory paths instead of strings
- Do not use insecure functions like `eval` or `exec`
- Do not use pickle
- All constants and globals should use ALL_CAPS_WITH_UNDERSCORES naming convention
- do not use the `global` keyword
- break long function definitions, function calls, lists, and dictionaries into multiple lines for readability

## Project Structure

- assets/: Game assets like graphics, sounds, scenarios
  - dejavu-lgc/: Font files
  - images/: All graphics used in the game
  - sounds/: Sound effects and music
  - asset_manifest.json: Manifest of all assets with metadata
  - *.tcl: TCL/Tk GUI code
  - hexa.*: Hexadecimal data files
  - snro.*: Scenario files
  - stri.*: String resource files
- cities/: Example city save files (.cty)
- config/: Configuration files
  - keybindings.json: Keybinding configuration
  - themes.json: Theme configuration
- docs/: Documentation
- logs/: Log files
- orig_src/: Original C source code from Micropolis
- src/micropolis/:
  - constants.py: Game constants
  - context.py: Game context and state management
  - main.py: Main entry point
- tests/:
  - test_*.py: Unit and integration tests
- pyproject.toml: Project configuration
- README.md: Project overview and instructions
