# Tests package shim to expose the real sprite_manager module
# Allows tests to use 'from . import sprite_manager' (relative import)
from micropolis import sprite_manager as sprite_manager

__all__ = ["sprite_manager"]
