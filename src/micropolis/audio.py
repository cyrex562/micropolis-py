"""
audio.py - Sound effect management for Micropolis Python port using pygame mixer
"""

import logging
import os
from dataclasses import dataclass
from typing import Any
from result import Result, Err, Ok

import pygame.mixer

# Import simulation modules
from . import types

logger = logging.getLogger(__name__)

# ============================================================================
# Type Definitions and Constants
# ============================================================================

# Sound channel constants (matching original TCL interface)
SOUND_CHANNELS = {
    "city": 0,  # City-wide sound effects
    "edit": 1,  # Editor/bulldozer sounds
    "sprite": 2,  # Sprite/moving object sounds
}

# Maximum number of sound channels
MAX_CHANNELS = 8

# Sound file extensions to try
SOUND_EXTENSIONS = [".wav", ".ogg", ".mp3"]


# ============================================================================
# Data Structures
# ============================================================================


@dataclass
class SoundInfo:
    """
    Information about a loaded sound.
    """

    sound: pygame.mixer.Sound | None = None
    channel: pygame.mixer.Channel | None = None
    is_looping: bool = False
    resource_id: str | None = None


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


def initialize_sound() -> Result[None, Exception]:
    """
    Initialize the sound system.

    Ported from InitializeSound() in w_sound.c.
    Initializes pygame mixer and sets up sound channels.
    """
    global SoundInitialized

    if SoundInitialized:
        return Ok(None)

    if not types.UserSoundOn:
        return Ok(None)

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
        logger.info("Sound system initialized")

    except Exception as e:
        logger.exception(f"Failed to initialize sound system: {e}")
        SoundInitialized = False
        return Err(e)
    return Ok(None)


def shutdown_sound() -> Result[None, Exception]:
    """
    Shut down the sound system.

    Ported from ShutDownSound() in w_sound.c.
    Stops all sounds and cleans up resources.
    """
    global SoundInitialized, Dozing

    if not SoundInitialized:
        return Ok(None)

    try:
        _stop_all_channels()

        # Clear caches
        sound_cache.clear()
        active_channels.clear()

        SoundInitialized = False
        Dozing = False
        logger.info("Sound system shut down")

    except Exception as e:
        logger.exception(f"Error shutting down sound system: {e}")
        return Err(e)

    return Ok(None)


def make_sound(channel: str, sound_id: str) -> Result[None, Exception]:
    """
    Play a sound on a specific channel.

    Ported from MakeSound() in w_sound.c.
    Plays a one-shot sound effect.

    Args:
        channel: Sound channel name (e.g., "city", "edit")
        sound_id: Sound identifier
    """
    if not types.UserSoundOn or not SoundInitialized:
        return Ok(None)

    try:
        # Get or load the sound
        sound_info = get_sound(sound_id)
        if sound_info.is_err():
            return Err(ValueError(f"failed to get sound by sound_id {sound_id}"))
        sound_info = sound_info.unwrap()

        # Get channel number
        channel_num = SOUND_CHANNELS.get(channel, 0)

        # Play the sound
        sound_info.channel = pygame.mixer.Channel(channel_num)
        if sound_info.sound is None:
            return Err(ValueError("sound_info sound is None"))
        sound_info.channel.play(sound_info.sound)

    except Exception as e:
        logger.exception(f"Error playing sound {sound_id} on channel {channel}: {e}")
        return Err(e)

    return Ok(None)


def make_sound_on(view: Any, channel: str, sound_id: str) -> Result[None, Exception]:
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
    return make_sound(channel, sound_id)


def start_bulldozer() -> Result[None, Exception]:
    """
    Start the bulldozer sound loop.

    Ported from StartBulldozer() in w_sound.c.
    Starts looping bulldozer sound when bulldozing begins.
    """
    global Dozing

    if not types.UserSoundOn or not SoundInitialized:
        return Ok(None)

    if Dozing:
        return Ok(None)  # Already playing

    try:
        # Get bulldozer sound
        sound_info = get_sound("bulldozer")
        if sound_info.is_err():
            return Err(ValueError("failed to get bulldozer sound"))
        sound_info = sound_info.unwrap()

        if sound_info.sound is None:
            return Err(ValueError("sound_info.sound is None"))

        # Get edit channel
        channel_num = SOUND_CHANNELS.get("edit", 1)
        sound_info.channel = pygame.mixer.Channel(channel_num)

        # Start looping
        sound_info.channel.play(sound_info.sound, loops=-1)  # -1 = loop forever
        sound_info.is_looping = True

        Dozing = True

    except Exception as e:
        logger.exception(f"Error starting bulldozer sound: {e}")
        return Err(e)

    return Ok(None)


def stop_bulldozer() -> Result[None, Exception]:
    """
    Stop the bulldozer sound loop.

    Ported from StopBulldozer() in w_sound.c.
    Stops the looping bulldozer sound.
    """
    global Dozing

    if not SoundInitialized:
        return Ok(None)

    try:
        # Stop bulldozer sound on edit channel
        channel_num = SOUND_CHANNELS.get("edit", 1)
        channel = pygame.mixer.Channel(channel_num)
        channel.stop()

        Dozing = False

    except Exception as e:
        logger.exception(f"Error stopping bulldozer sound: {e}")
        return Err(e)

    return Ok(None)


def sound_off() -> Result[None, Exception]:
    """
    Turn off all sounds.

    Ported from SoundOff() in w_sound.c.
    Stops all playing sounds and resets bulldozer state.
    """
    global Dozing

    if not SoundInitialized:
        return Ok(None)

    try:
        _stop_all_channels()

    except Exception as e:
        logger.exception(f"Error turning sound off: {e}")
        return Err(e)

    return Ok(None)


def do_start_sound(channel: str, sound_id: str) -> Result[None, Exception]:
    """
    Start a sound (internal function).

    Ported from DoStartSound() in w_sound.c.
    Internal function for starting sounds.
    """
    return make_sound(channel, sound_id)


def do_stop_sound(sound_id: str) -> Result[None, Exception]:
    """
    Stop a specific sound (internal function).

    Ported from DoStopSound() in w_sound.c.
    Internal function for stopping sounds by ID.
    """
    if not SoundInitialized:
        return Ok(None)

    try:
        # Find and stop the sound by ID
        for sound_info in sound_cache.values():
            if sound_info.resource_id == sound_id and sound_info.channel:
                sound_info.channel.stop()
                sound_info.is_looping = False
                break

    except Exception as e:
        logger.exception(f"Error stopping sound {sound_id}: {e}")
        return Err(e)

    return Ok(None)


# ============================================================================
# Sound Resource Management
# ============================================================================


def get_sound(sound_name: str) -> Result[SoundInfo, Exception]:
    """
    Get or load a sound by name.

    Args:
        sound_name: Name of the sound file (without extension)

    Returns:
        SoundInfo object, or None if not found
    """
    # Check cache first
    if sound_name in sound_cache:
        # result = sound_cache[sound_name]
        result = sound_cache.get(sound_name, None)
        if result is None:
            return Err(ValueError(f"failed to get sound {sound_name} from sound_cache"))

    # Try to load the sound
    sound_info = load_sound(sound_name)
    if sound_info is None:
        return Err(ValueError(f"failed to load sound {sound_name}"))
    sound_info = sound_info.unwrap()

    sound_cache[sound_name] = sound_info

    return Ok(sound_info)


def load_sound(sound_name: str) -> Result[SoundInfo, Exception]:
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
                result = SoundInfo(sound=sound, resource_id=sound_name)
                return Ok(result)
            except Exception as e:
                logger.exception(f"Error loading sound {sound_path}: {e}")
                return Err(e)

    # Try alternative naming (some sounds have -hi, -low, etc. suffixes)
    # Handle special cases like "HonkHonk-Med" -> "honkhonk-med.wav"
    alt_name = sound_name.lower().replace("-", "")
    for ext in SOUND_EXTENSIONS:
        sound_path = os.path.join(sound_dir, f"{alt_name}{ext}")
        if os.path.exists(sound_path):
            try:
                sound = pygame.mixer.Sound(sound_path)
                result = SoundInfo(sound=sound, resource_id=sound_name)
                return Ok(result)
            except Exception as e:
                logger.exception(f"Error loading sound {sound_path}: {e}")
                return Err(e)

    return Err(ValueError(f"failed to load sound {sound_name}"))


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


def _stop_all_channels() -> Result[None, Exception]:
    """
    Stop playback on every mixer channel and reset cached state.
    """
    global Dozing

    if not SoundInitialized:
        return Err(RuntimeError("sound not initialized"))

    pygame.mixer.stop()

    for info in sound_cache.values():
        if info.channel:
            try:
                info.channel.stop()
            except Exception as e:
                return Err(e)
            info.is_looping = False

    for info in active_channels.values():
        channel = info.channel
        if channel:
            try:
                channel.stop()
            except Exception as e:
                return Err(e)
            info.is_looping = False

    Dozing = False
    return Ok(None)


# ============================================================================
# TCL Command Interface (for compatibility)
# ============================================================================


class AudioCommand:
    """
    TCL command interface for audio functions (for compatibility).
    """

    @staticmethod
    def handle_command(command: str, *args: str) -> Result[str, Exception]:
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
            return Ok("")

        elif command == "shutdown_sound":
            shutdown_sound()
            return Ok("")

        elif command == "make_sound":
            if len(args) != 2:
                return Err(ValueError("Usage: make_sound <channel> <sound_id>"))
            make_sound(args[0], args[1])
            return Ok("")

        elif command == "start_bulldozer":
            start_bulldozer()
            return Ok("")

        elif command == "stop_bulldozer":
            stop_bulldozer()
            return Ok("")

        elif command == "sound_off":
            sound_off()
            return Ok("")

        else:
            return Err(ValueError(f"Unknown audio command: {command}"))


# ============================================================================
# Initialization
# ============================================================================


# Initialize sound system when module is imported
# (This will be called later by the main application)
def _init_module():
    """Initialize module-level state."""
    logger.debug("initializing sound system")
    return Ok(None)


_init_module()
