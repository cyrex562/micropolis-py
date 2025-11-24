"""
test_audio.py - Test suite for audio.py module
"""

import os
from unittest.mock import patch, MagicMock
import pygame.mixer

from tests.assertions import Assertions

# Import the module to test
import sys
import os
import micropolis
from micropolis import audio
from micropolis.context import AppContext
from micropolis.app_config import AppConfig

# Provide a simple test context so legacy-style calls that reference a
# module-level `context` name resolve during the tests.
context = AppContext(config=AppConfig())


class TestAudio(Assertions):
    """Test cases for audio.py module"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reset global state
        audio.SoundInitialized = False
        audio.Dozing = False
        audio.sound_cache.clear()
        audio.active_channels.clear()

        # Reset the test context's sound_initialized
        ctx = getattr(micropolis, "_AUTO_TEST_CONTEXT", None)
        if ctx is not None:
            ctx.sound_initialized = False
            ctx.user_sound_on = True

        # Set up sound enabled (legacy)
        context.user_sound_on = True
        context.sound = 1

        # Mock pygame mixer to avoid actual audio initialization
        self.pygame_mixer_patcher = patch("pygame.mixer")
        self.mock_mixer = self.pygame_mixer_patcher.start()

        # Configure mock mixer
        self.mock_mixer.get_init.return_value = False
        self.mock_mixer.get_num_channels.return_value = 8

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        self.pygame_mixer_patcher.stop()

        # Reset global state
        audio.SoundInitialized = False
        audio.Dozing = False
        audio.sound_cache.clear()
        audio.active_channels.clear()

        context.user_sound_on = False
        context.sound = 0

    def test_initialize_sound_success(self):
        """Test successful sound initialization."""
        # Mock successful initialization
        self.mock_mixer.init.return_value = None
        self.mock_mixer.set_num_channels.return_value = None

        audio.initialize_sound()

        self.assertTrue(audio.SoundInitialized)
        self.mock_mixer.init.assert_called_once()
        self.mock_mixer.set_num_channels.assert_called_once_with(audio.MAX_CHANNELS)

    def test_initialize_sound_disabled(self):
        """Test sound initialization when sound is disabled."""
        # Get the test context and set user_sound_on to False
        ctx = getattr(micropolis, "_AUTO_TEST_CONTEXT", None)
        context.user_sound_on = False

        audio.initialize_sound()

        self.assertFalse(audio.SoundInitialized)
        self.mock_mixer.init.assert_not_called()

    def test_initialize_sound_already_initialized(self):
        """Test sound initialization when already initialized."""
        audio.SoundInitialized = True
        # Also set on test context
        ctx = getattr(micropolis, "_AUTO_TEST_CONTEXT", None)
        context.sound_initialized = True

        audio.initialize_sound()

        # Should not re-initialize
        self.mock_mixer.init.assert_not_called()

    def test_initialize_sound_failure(self):
        """Test sound initialization failure."""
        self.mock_mixer.init.side_effect = Exception("Init failed")

        audio.initialize_sound()

        self.assertFalse(audio.SoundInitialized)

    def test_shutdown_sound(self):
        """Test sound shutdown."""
        audio.SoundInitialized = True
        audio.Dozing = True
        # Also set on test context
        ctx = getattr(micropolis, "_AUTO_TEST_CONTEXT", None)
        context.sound_initialized = True

        audio.shutdown_sound()

        self.assertFalse(audio.SoundInitialized)
        self.assertFalse(audio.Dozing)
        self.mock_mixer.stop.assert_called_once()

    def test_make_sound_success(self):
        """Test successful sound playback."""
        audio.SoundInitialized = True

        # Mock sound loading
        mock_sound = MagicMock()
        mock_channel = MagicMock()

        with patch.object(audio, "get_sound") as mock_get_sound:
            mock_get_sound.return_value = audio.SoundInfo(sound=mock_sound)

            with patch("micropolis.audio.pygame.mixer.Channel") as mock_channel_class:
                mock_channel_class.return_value = mock_channel

                audio.make_sound(context, "city", "test")

                mock_get_sound.assert_called_once_with("test")
                mock_channel_class.assert_called_once_with(0)  # city channel
                mock_channel.play.assert_called_once_with(mock_sound)

    def test_make_sound_disabled(self):
        """Test sound playback when sound is disabled."""
        context.user_sound_on = False

        with patch.object(audio, "get_sound") as mock_get_sound:
            audio.make_sound(context, "city", "test")

            mock_get_sound.assert_not_called()

    def test_make_sound_not_initialized(self):
        """Test sound playback when not initialized."""
        audio.SoundInitialized = False

        with patch.object(audio, "get_sound") as mock_get_sound:
            audio.make_sound(context, "city", "test")

            mock_get_sound.assert_not_called()

    def test_make_sound_not_found(self):
        """Test sound playback when sound not found."""
        audio.SoundInitialized = True

        with patch.object(audio, "get_sound") as mock_get_sound:
            mock_get_sound.return_value = None

            audio.make_sound(context, "city", "nonexistent")

            mock_get_sound.assert_called_once_with("nonexistent")

    def test_make_sound_on(self):
        """Test MakeSoundOn function."""
        audio.SoundInitialized = True

        with patch.object(audio, "make_sound") as mock_make_sound:
            mock_view = MagicMock()
            audio.make_sound_on(mock_view, "city", "test")

            mock_make_sound.assert_called_once_with("city", "test")

    def test_start_bulldozer_success(self):
        """Test successful bulldozer sound start."""
        audio.SoundInitialized = True

        # Mock sound loading
        mock_sound = MagicMock()
        mock_channel = MagicMock()

        with patch.object(audio, "get_sound") as mock_get_sound:
            mock_get_sound.return_value = audio.SoundInfo(sound=mock_sound)

            with patch("micropolis.audio.pygame.mixer.Channel") as mock_channel_class:
                mock_channel_class.return_value = mock_channel

                audio.start_bulldozer_sound()

                self.assertTrue(audio.Dozing)
                mock_get_sound.assert_called_once_with("bulldozer")
                mock_channel_class.assert_called_once_with(1)  # edit channel
                mock_channel.play.assert_called_once_with(mock_sound, loops=-1)

    def test_start_bulldozer_already_playing(self):
        """Test bulldozer sound start when already playing."""
        audio.Dozing = True

        with patch.object(audio, "get_sound") as mock_get_sound:
            audio.start_bulldozer_sound()

            mock_get_sound.assert_not_called()

    def test_stop_bulldozer(self):
        """Test bulldozer sound stop."""
        audio.SoundInitialized = True
        audio.Dozing = True
        # Also set on test context
        ctx = getattr(micropolis, "_AUTO_TEST_CONTEXT", None)
        if ctx is not None:
            ctx.sound_initialized = True

        with patch("micropolis.audio.pygame.mixer.Channel") as mock_channel_class:
            mock_channel = MagicMock()
            mock_channel_class.return_value = mock_channel

            audio.stop_bulldozer_sound()

            self.assertFalse(audio.Dozing)
            mock_channel_class.assert_called_once_with(1)  # edit channel
            mock_channel.stop.assert_called_once()

    def test_sound_off(self):
        """Test sound off function."""
        audio.SoundInitialized = True
        audio.Dozing = True

        audio.sound_off(context)

        self.assertFalse(audio.Dozing)
        self.mock_mixer.stop.assert_called_once()

    def test_do_start_sound(self):
        """Test DoStartSound function."""
        with patch.object(audio, "make_sound") as mock_make_sound:
            audio.do_start_sound("city", "test")

            mock_make_sound.assert_called_once_with("city", "test")

    def test_do_stop_sound(self):
        """Test DoStopSound function."""
        audio.SoundInitialized = True

        # Set up a cached sound
        mock_channel = MagicMock()
        sound_info = audio.SoundInfo(channel=mock_channel, resource_id="test")
        audio.sound_cache["test"] = sound_info

        audio.do_stop_sound("test")

        mock_channel.stop.assert_called_once()

    def test_get_sound_cached(self):
        """Test getting a cached sound."""
        sound_info = audio.SoundInfo(sound=MagicMock(), resource_id="test")
        audio.sound_cache["test"] = sound_info

        result = audio.get_sound("test")

        self.assertEqual(result, sound_info)

    def test_get_sound_load_new(self):
        """Test loading a new sound."""
        with patch.object(audio, "load_sound") as mock_load_sound:
            sound_info = audio.SoundInfo(sound=MagicMock(), resource_id="test")
            mock_load_sound.return_value = sound_info

            result = audio.get_sound("test")

            self.assertEqual(result, sound_info)
            self.assertEqual(audio.sound_cache["test"], sound_info)

    def test_load_sound_success(self):
        """Test successful sound loading."""
        # Create a temporary sound file path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sound_dir = os.path.join(script_dir, "..", "..", "assets", "sounds")
        test_sound_path = os.path.join(sound_dir, "beep.wav")

        # Mock pygame.mixer.Sound to avoid actual file loading
        with patch("micropolis.audio.pygame.mixer.Sound") as mock_sound_class:
            mock_sound = MagicMock()
            mock_sound_class.return_value = mock_sound

            # Mock os.path.exists to return True for our test file
            with patch("os.path.exists") as mock_exists:
                mock_exists.return_value = True

                result = audio.load_sound("beep")

                self.assertIsNotNone(result)
                self.assertEqual(result.sound, mock_sound)
                self.assertEqual(result.resource_id, "beep")

    def test_load_sound_not_found(self):
        """Test sound loading when file not found."""
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False

            result = audio.load_sound("nonexistent")

            self.assertIsNone(result)

    def test_is_sound_enabled(self):
        """Test is_sound_enabled function."""
        ctx = getattr(micropolis, "_AUTO_TEST_CONTEXT", None)

        # Not initialized
        self.assertFalse(audio.is_sound_enabled())

        # Initialized but disabled
        audio.SoundInitialized = True
        context.sound_initialized = True
        context.user_sound_on = False
        self.assertFalse(audio.is_sound_enabled())

        # Enabled
        context.user_sound_on = True
        self.assertTrue(audio.is_sound_enabled())

    def test_get_channel_count(self):
        """Test get_channel_count function."""
        # Not initialized
        self.assertEqual(audio.get_channel_count(), 0)

        # Initialized
        audio.SoundInitialized = True
        self.mock_mixer.get_num_channels.return_value = 8
        self.assertEqual(audio.get_channel_count(), 8)

    def test_preload_sounds(self):
        """Test preloading sounds."""
        audio.SoundInitialized = True

        with patch.object(audio, "get_sound") as mock_get_sound:
            audio.preload_sounds(["sound1", "sound2"])

            self.assertEqual(mock_get_sound.call_count, 2)
            mock_get_sound.assert_any_call("sound1")
            mock_get_sound.assert_any_call("sound2")

    def test_preload_sounds_not_initialized(self):
        """Test preloading sounds when not initialized."""
        with patch.object(audio, "get_sound") as mock_get_sound:
            audio.preload_sounds(["sound1"])

            mock_get_sound.assert_not_called()

    def test_tcl_commands_initialize_sound(self):
        """Test TCL initialize_sound command."""
        with patch.object(audio, "initialize_sound") as mock_init:
            result = audio.AudioCommand.handle_command(
                context, context, "initialize_sound"
            )

            self.assertEqual(result, "")
            mock_init.assert_called_once()

    def test_tcl_commands_make_sound(self):
        """Test TCL make_sound command."""
        with patch.object(audio, "make_sound") as mock_make:
            result = audio.AudioCommand.handle_command(
                context, context, "make_sound", "city", "test"
            )

            self.assertEqual(result, "")
            mock_make.assert_called_once_with("city", "test")

    def test_tcl_commands_start_bulldozer(self):
        """Test TCL start_bulldozer command."""
        with patch.object(audio, "start_bulldozer") as mock_start:
            result = audio.AudioCommand.handle_command(
                context, context, "start_bulldozer"
            )

            self.assertEqual(result, "")
            mock_start.assert_called_once()

    def test_tcl_commands_stop_bulldozer(self):
        """Test TCL stop_bulldozer command."""
        with patch.object(audio, "stop_bulldozer") as mock_stop:
            result = audio.AudioCommand.handle_command(
                context, context, "stop_bulldozer"
            )

            self.assertEqual(result, "")
            mock_stop.assert_called_once()

    def test_tcl_commands_sound_off(self):
        """Test TCL sound_off command."""
        with patch.object(audio, "sound_off") as mock_off:
            result = audio.AudioCommand.handle_command(context, context, "sound_off")

            self.assertEqual(result, "")
            mock_off.assert_called_once()

    def test_tcl_commands_invalid(self):
        """Test invalid TCL command."""
        with self.assertRaises(ValueError):
            audio.AudioCommand.handle_command(context, context, "invalid_command")

    def test_tcl_commands_make_sound_wrong_args(self):
        """Test TCL make_sound command with wrong number of args."""
        with self.assertRaises(ValueError):
            audio.AudioCommand.handle_command(
                context, context, "make_sound", "onlyonearg"
            )
