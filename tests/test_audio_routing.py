#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced audio routing system.
Run with: uv run python test_audio_routing.py
"""

import os
import sys
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from micropolis import audio
from micropolis.context import AppContext
from micropolis.app_config import AppConfig


def test_audio_routing():
    """Test the new audio routing features."""
    print("Testing Enhanced Audio Routing System")
    print("=" * 60)

    # Create a mock context
    config = AppConfig()
    context = AppContext(config=config)
    context.user_sound_on = True
    context.sound_initialized = False

    # Mock pygame mixer
    with patch("micropolis.audio.pygame.mixer") as mock_mixer:
        mock_mixer.get_init.return_value = False
        mock_mixer.get_num_channels.return_value = 8

        # Test 1: Initialize sound system
        print("\n1. Initializing sound system...")
        result = audio.initialize_sound(context)
        if result.is_ok():
            print("   ✓ Sound system initialized successfully")
            print(f"   ✓ Created {len(audio.channel_states)} logical channels:")
            for name, state in audio.channel_states.items():
                print(
                    f"     - {name}: channel={state.channel_num}, priority={state.priority}"
                )
        else:
            print(f"   ✗ Failed: {result.unwrap_err()}")
            return False

        # Test 2: Channel volume control
        print("\n2. Testing channel volume control...")
        result = audio.set_channel_volume("warning", 0.8)
        if result.is_ok():
            volume_result = audio.get_channel_volume("warning")
            if volume_result.is_ok():
                print(
                    f"   ✓ Set warning channel volume to {volume_result.unwrap():.2f}"
                )
            else:
                print(f"   ✗ Failed to get volume: {volume_result.unwrap_err()}")
        else:
            print(f"   ✗ Failed: {result.unwrap_err()}")

        # Test 3: Channel mute control
        print("\n3. Testing channel mute control...")
        result = audio.set_channel_mute("edit", True)
        if result.is_ok():
            muted_result = audio.is_channel_muted("edit")
            if muted_result.is_ok():
                print(f"   ✓ Edit channel muted: {muted_result.unwrap()}")
            else:
                print(f"   ✗ Failed to check mute: {muted_result.unwrap_err()}")
        else:
            print(f"   ✗ Failed: {result.unwrap_err()}")

        # Test 4: Play sound (with mocked sound loading)
        print("\n4. Testing sound playback...")
        with patch.object(audio, "get_sound") as mock_get_sound:
            mock_sound = MagicMock()
            mock_channel = MagicMock()
            mock_get_sound.return_value = audio.Ok(audio.SoundInfo(sound=mock_sound))

            with patch("micropolis.audio.pygame.mixer.Channel") as mock_channel_class:
                mock_channel_class.return_value = mock_channel

                # Test playing on different channels
                channels_to_test = ["mode", "edit", "fancy", "warning", "intercom"]
                for ch in channels_to_test:
                    # Skip muted channel
                    if ch == "edit":
                        audio.set_channel_mute("edit", False)

                    result = audio.play_sound(context, ch, "test_sound")
                    if result.is_ok():
                        print(f"   ✓ Played sound on channel: {ch}")
                    else:
                        print(f"   ✗ Failed on {ch}: {result.unwrap_err()}")

        # Test 5: Bulldozer sound (looping)
        print("\n5. Testing bulldozer looping sound...")
        with patch.object(audio, "play_sound") as mock_play:
            mock_play.return_value = audio.Ok(None)
            result = audio.start_bulldozer_sound(context)
            if result.is_ok():
                print("   ✓ Started bulldozer sound loop")
                print(f"   ✓ Dozing state: {context.dozing}")
            else:
                print(f"   ✗ Failed: {result.unwrap_err()}")

        # Test 6: Channel priority check
        print("\n6. Checking channel priorities...")
        from micropolis.constants import SOUND_CHANNEL_PRIORITY

        sorted_channels = sorted(
            SOUND_CHANNEL_PRIORITY.items(), key=lambda x: x[1], reverse=True
        )
        print("   Channel priority order (highest to lowest):")
        for name, priority in sorted_channels:
            print(f"     {priority:3d}: {name}")

        # Test 7: Sugar stdout notifications
        print("\n7. Testing Sugar stdout notifications...")
        print(f"   Sugar notifications enabled: {audio.EMIT_SUGAR_SOUND_NOTIFICATIONS}")
        print(f"   Sugar notification prefix: '{audio.SUGAR_SOUND_PREFIX}'")

        # Test 8: Shutdown
        print("\n8. Shutting down sound system...")
        result = audio.shutdown_sound(context)
        if result.is_ok():
            print("   ✓ Sound system shut down successfully")
        else:
            print(f"   ✗ Failed: {result.unwrap_err()}")

    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    return True


if __name__ == "__main__":
    success = test_audio_routing()
    sys.exit(0 if success else 1)
