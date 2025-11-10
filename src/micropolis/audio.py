"""
audio.py - Sound effect management for Micropolis Python port using pygame mixer
"""

import os
from dataclasses import dataclass
from typing import Any

import pygame.mixer

# Import simulation modules
from . import types

# ============================================================================
# Type Definitions and Constants
# ============================================================================

# Sound channel constants (matching original TCL interface)
SOUND_CHANNELS = {
    'city': 0,      # City-wide sound effects
    'edit': 1,      # Editor/bulldozer sounds
    'sprite': 2,    # Sprite/moving object sounds
}

# Maximum number of sound channels
MAX_CHANNELS = 8

# Sound file extensions to try
SOUND_EXTENSIONS = ['.wav', '.ogg', '.mp3']


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class SoundInfo:
    """
    Information about a loaded sound.
    """
    sound: pygame.mixer.Sound|None = None
    channel: pygame.mixer.Channel|None = None
    is_looping: bool = False
    resource_id: str|None = None
# ============================================================================
# Global Variables
# ============================================================================

# Sound system state
SoundInitialized: bool = False
Dozing: bool = False  # Bulldozer sound state

# Sound cache
sound_cache: dict[str, SoundInfo] = {}

# Active sound channels
active_channels: dict[int, SoundInfo] = {}
# ============================================================================
# Sound System Functions
# ============================================================================

def initialize_sound() -> None:
    """
    Initialize the sound system.

    Ported from InitializeSound() in w_sound.c.
    Initializes pygame mixer and sets up sound channels.
    """
    global SoundInitialized

    if SoundInitialized:
        return

    if not types.UserSoundOn:
        return

    try:
        # Initialize pygame mixer if not already initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        # Set up channels
        pygame.mixer.set_num_channels(MAX_CHANNELS)

        # Reserve channels for specific uses
        for i in range(MAX_CHANNELS):
            channel = pygame.mixer.Channel(i)
            active_channels[i] = SoundInfo(channel=channel)

        SoundInitialized = True
        print("Sound system initialized")

    except Exception as e:
        print(f"Failed to initialize sound system: {e}")
        SoundInitialized = False


def shutdown_sound() -> None:
    """
    Shut down the sound system.

    Ported from ShutDownSound() in w_sound.c.
    Stops all sounds and cleans up resources.
    """
    global SoundInitialized, Dozing

    if not SoundInitialized:
        return

    try:
        _stop_all_channels()

        # Clear caches
        sound_cache.clear()
        active_channels.clear()

        SoundInitialized = False
        Dozing = False
        print("Sound system shut down")

    except Exception as e:
        print(f"Error shutting down sound system: {e}")


def make_sound(channel: str, sound_id: str) -> None:
    """
    Play a sound on a specific channel.

    Ported from MakeSound() in w_sound.c.
    Plays a one-shot sound effect.

    Args:
        channel: Sound channel name (e.g., "city", "edit")
        sound_id: Sound identifier
    """
    if not types.UserSoundOn or not SoundInitialized:
        return

    try:
        # Get or load the sound
        sound_info = get_sound(sound_id)
        if not sound_info or not sound_info.sound:
            print(f"Sound not found: {sound_id}")
            return

        # Get channel number
        channel_num = SOUND_CHANNELS.get(channel, 0)

        # Play the sound
        sound_info.channel = pygame.mixer.Channel(channel_num)
        sound_info.channel.play(sound_info.sound)

    except Exception as e:
        print(f"Error playing sound {sound_id} on channel {channel}: {e}")


def make_sound_on(view: Any, channel: str, sound_id: str) -> None:
    """
    Play a sound on a specific channel associated with a view.

    Ported from MakeSoundOn() in w_sound.c.
    Currently simplified - just calls make_sound.

    Args:
        view: View object (currently unused)
        channel: Sound channel name
        sound_id: Sound identifier
    """
    # For now, just delegate to make_sound
    # In full implementation, this would position sound based on view
    make_sound(channel, sound_id)


def start_bulldozer() -> None:
    """
    Start the bulldozer sound loop.

    Ported from StartBulldozer() in w_sound.c.
    Starts looping bulldozer sound when bulldozing begins.
    """
    global Dozing

    if not types.UserSoundOn or not SoundInitialized:
        return

    if Dozing:
        return  # Already playing

    try:
        # Get bulldozer sound
        sound_info = get_sound("bulldozer")
        if not sound_info or not sound_info.sound:
            print("Bulldozer sound not found")
            return

        # Get edit channel
        channel_num = SOUND_CHANNELS.get('edit', 1)
        sound_info.channel = pygame.mixer.Channel(channel_num)

        # Start looping
        sound_info.channel.play(sound_info.sound, loops=-1)  # -1 = loop forever
        sound_info.is_looping = True

        Dozing = True

    except Exception as e:
        print(f"Error starting bulldozer sound: {e}")


def stop_bulldozer() -> None:
    """
    Stop the bulldozer sound loop.

    Ported from StopBulldozer() in w_sound.c.
    Stops the looping bulldozer sound.
    """
    global Dozing

    if not SoundInitialized:
        return

    try:
        # Stop bulldozer sound on edit channel
        channel_num = SOUND_CHANNELS.get('edit', 1)
        channel = pygame.mixer.Channel(channel_num)
        channel.stop()

        Dozing = False

    except Exception as e:
        print(f"Error stopping bulldozer sound: {e}")


def sound_off() -> None:
    """
    Turn off all sounds.

    Ported from SoundOff() in w_sound.c.
    Stops all playing sounds and resets bulldozer state.
    """
    global Dozing

    if not SoundInitialized:
        return

    try:
        _stop_all_channels()

    except Exception as e:
        print(f"Error turning sound off: {e}")


def do_start_sound(channel: str, sound_id: str) -> None:
    """
    Start a sound (internal function).

    Ported from DoStartSound() in w_sound.c.
    Internal function for starting sounds.
    """
    make_sound(channel, sound_id)


def do_stop_sound(sound_id: str) -> None:
    """
    Stop a specific sound (internal function).

    Ported from DoStopSound() in w_sound.c.
    Internal function for stopping sounds by ID.
    """
    if not SoundInitialized:
        return

    try:
        # Find and stop the sound by ID
        for sound_info in sound_cache.values():
            if sound_info.resource_id == sound_id and sound_info.channel:
                sound_info.channel.stop()
                sound_info.is_looping = False
                break

    except Exception as e:
        print(f"Error stopping sound {sound_id}: {e}")


# ============================================================================
# Sound Resource Management
# ============================================================================

def get_sound(sound_name: str) -> SoundInfo|None:
    """
    Get or load a sound by name.

    Args:
        sound_name: Name of the sound file (without extension)

    Returns:
        SoundInfo object, or None if not found
    """
    # Check cache first
    if sound_name in sound_cache:
        return sound_cache[sound_name]

    # Try to load the sound
    sound_info = load_sound(sound_name)
    if sound_info:
        sound_cache[sound_name] = sound_info

    return sound_info


def load_sound(sound_name: str) -> SoundInfo|None:
    """
    Load a sound file from the sounds directory.

    Args:
        sound_name: Name of the sound file (without extension)

    Returns:
        SoundInfo object if loaded successfully, None otherwise
    """
    # Determine sound directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sound_dir = os.path.join(script_dir, "..", "..", "assets", "sounds")

    # Try different extensions
    for ext in SOUND_EXTENSIONS:
        sound_path = os.path.join(sound_dir, f"{sound_name}{ext}")
        if os.path.exists(sound_path):
            try:
                sound = pygame.mixer.Sound(sound_path)
                return SoundInfo(sound=sound, resource_id=sound_name)
            except Exception as e:
                print(f"Error loading sound {sound_path}: {e}")
                continue

    # Try alternative naming (some sounds have -hi, -low, etc. suffixes)
    # Handle special cases like "HonkHonk-Med" -> "honkhonk-med.wav"
    alt_name = sound_name.lower().replace('-', '')
    for ext in SOUND_EXTENSIONS:
        sound_path = os.path.join(sound_dir, f"{alt_name}{ext}")
        if os.path.exists(sound_path):
            try:
                sound = pygame.mixer.Sound(sound_path)
                return SoundInfo(sound=sound, resource_id=sound_name)
            except Exception as e:
                print(f"Error loading sound {sound_path}: {e}")
                continue

    return None


# ============================================================================
# Utility Functions
# ============================================================================

def is_sound_enabled() -> bool:
    """
    Check if sound is enabled.

    Returns:
        True if sound is enabled and initialized
    """
    return SoundInitialized and bool(types.UserSoundOn)


def get_channel_count() -> int:
    """
    Get the number of available sound channels.

    Returns:
        Number of mixer channels
    """
    if not SoundInitialized:
        return 0
    return pygame.mixer.get_num_channels()


def preload_sounds(sound_names: list[str]) -> None:
    """
    Preload a list of sounds into cache.

    Args:
        sound_names: List of sound names to preload
    """
    if not SoundInitialized:
        return

    for sound_name in sound_names:
        get_sound(sound_name)  # This will load and cache the sound


def _stop_all_channels() -> None:
    """
    Stop playback on every mixer channel and reset cached state.
    """
    global Dozing

    if not SoundInitialized:
        return

    pygame.mixer.stop()

    for info in sound_cache.values():
        if info.channel:
            try:
                info.channel.stop()
            except Exception:
                pass
            info.is_looping = False

    for info in active_channels.values():
        channel = info.channel
        if channel:
            try:
                channel.stop()
            except Exception:
                pass
            info.is_looping = False

    Dozing = False


# ============================================================================
# TCL Command Interface (for compatibility)
# ============================================================================

class AudioCommand:
    """
    TCL command interface for audio functions (for compatibility).
    """

    @staticmethod
    def handle_command(command: str, *args: str) -> str:
        """
        Handle TCL audio commands.

        Args:
            command: TCL command name
            *args: Command arguments

        Returns:
            TCL command result
        """
        if command == "initialize_sound":
            initialize_sound()
            return ""

        elif command == "shutdown_sound":
            shutdown_sound()
            return ""

        elif command == "make_sound":
            if len(args) != 2:
                raise ValueError("Usage: make_sound <channel> <sound_id>")
            make_sound(args[0], args[1])
            return ""

        elif command == "start_bulldozer":
            start_bulldozer()
            return ""

        elif command == "stop_bulldozer":
            stop_bulldozer()
            return ""

        elif command == "sound_off":
            sound_off()
            return ""

        else:
            raise ValueError(f"Unknown audio command: {command}")


# ============================================================================
# Initialization
# ============================================================================

# Initialize sound system when module is imported
# (This will be called later by the main application)
def _init_module():
    """Initialize module-level state."""
    pass

_init_module()
