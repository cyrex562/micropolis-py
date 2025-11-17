# Audio Routing Implementation Summary

## Overview

This document summarizes the implementation of the enhanced audio routing system for Micropolis, as specified in §6.3 of the pygame UI port checklist. The implementation recreates the audio routing from the legacy Tcl/Tk interface (`sound.tcl`) using `pygame.mixer` with comprehensive channel management, priority-based preemption, and Sugar GTK shell compatibility.

## Implementation Date

November 15, 2025

## Key Features Implemented

### 1. Logical Audio Channels

Expanded from 3 basic channels to 7 logical channels matching legacy Tcl interface:

| Channel   | Number | Priority | Purpose                              |
|-----------|--------|----------|--------------------------------------|
| mode      | 0      | 10       | Background/ambient sounds            |
| edit      | 1      | 30       | Editor/UI clicks (bulldozer, tools)  |
| fancy     | 2      | 50       | Event sounds (construction, etc.)    |
| warning   | 3      | 100      | Disaster warnings (highest priority) |
| intercom  | 4      | 80       | Notification messages                |
| sprite    | 5      | 20       | Sprite/moving object sounds          |
| city      | 6      | 10       | City-wide effects (legacy compat)    |

### 2. Channel Management API

#### Volume Control

```python
# Set channel volume (0.0 to 1.0)
set_channel_volume(channel: str, volume: float) -> Result[None, Exception]

# Get current volume
get_channel_volume(channel: str) -> Result[float, Exception]
```

#### Mute Control

```python
# Mute or unmute a channel
set_channel_mute(channel: str, muted: bool) -> Result[None, Exception]

# Check if channel is muted
is_channel_muted(channel: str) -> Result[bool, Exception]
```

### 3. Enhanced Sound Playback API

New `play_sound()` function as the main audio playback API:

```python
def play_sound(
    context: AppContext,
    channel: str,
    sound_name: str,
    loop: bool = False,
    fade_ms: int = DEFAULT_FADE_MS,
) -> Result[None, Exception]:
    """
    Play a sound on a logical channel with priority and fade support.
    
    Features:
    - Channel volume/mute control
    - Priority-based preemption
    - Fade-in support (default 50ms)
    - Optional looping
    - Sugar stdout notifications
    """
```

### 4. Priority-Based Preemption

Higher priority sounds can interrupt lower priority sounds:

- **Warning sounds (priority 100)** preempt all other channels
- **Intercom (priority 80)** preempts events and ambient sounds
- **Events (priority 50)** preempt UI feedback
- **UI feedback (priority 30)** preempts sprites and ambient
- **Sprites and ambient (priority 10-20)** lowest priority

### 5. Fade Support

All sound playback supports configurable fade-in (default 50ms) to avoid clipping when sounds overlap:

```python
# Play with custom fade
play_sound(context, "edit", "bulldozer", fade_ms=100)
```

### 6. Sugar GTK Shell Compatibility

#### Stdout Notifications

When `EMIT_SUGAR_SOUND_NOTIFICATIONS = True` (default), the system emits stdout messages for Sugar GTK shell audio compatibility:

```python
# Format: "Sound <sound_name>"
Sound bulldozer
Sound Explosion-High
Sound HonkHonk-Med
```

This allows the GTK wrapper to optionally handle audio if pygame audio is disabled or for compatibility with older Sugar shells.

#### Configuration

```python
# In audio.py module-level constants:
EMIT_SUGAR_SOUND_NOTIFICATIONS = True  # Set to False to disable
SUGAR_SOUND_PREFIX = "Sound "  # Format prefix
```

### 7. Channel State Tracking

Each logical channel maintains comprehensive state:

```python
@dataclass
class ChannelState:
    name: str                    # Channel name
    channel_num: int             # pygame channel number
    volume: float = 1.0          # 0.0 to 1.0
    muted: bool = False          # Mute state
    priority: int = 0            # Preemption priority
    current_sound: str | None    # Currently playing sound
    is_looping: bool = False     # Loop state
```

### 8. Updated Legacy Functions

All existing audio functions updated to use the new routing:

- `make_sound()` → delegates to `play_sound()`
- `make_sound_on()` → delegates to `play_sound()`
- `start_bulldozer_sound()` → uses `play_sound()` with `loop=True`
- `stop_bulldozer_sound()` → channel-aware stop
- `sound_off()` → stops all channels properly

### 9. Improved Initialization

Enhanced `initialize_sound()` now:

- Creates all 7 logical channel states
- Sets up priority mappings
- Initializes per-channel volume/mute controls
- Validates channel configuration

### 10. Comprehensive Shutdown

Enhanced `shutdown_sound()` now:

- Stops all active channels
- Clears channel states
- Resets global state (including legacy `Dozing`)
- Cleans up all caches

## Code Changes

### Modified Files

1. **`src/micropolis/constants.py`**
   - Expanded `SOUND_CHANNELS` dictionary (7 channels)
   - Added `SOUND_CHANNEL_PRIORITY` mapping
   - Updated channel constants

2. **`src/micropolis/audio.py`**
   - Added `ChannelState` dataclass
   - Implemented `play_sound()` main API
   - Added volume/mute control functions
   - Enhanced initialization and shutdown
   - Added Sugar notification support
   - Updated legacy functions to use new routing

### New Data Structures

```python
# Channel state tracking
channel_states: dict[str, ChannelState] = {}

# Configuration constants
EMIT_SUGAR_SOUND_NOTIFICATIONS = True
SUGAR_SOUND_PREFIX = "Sound "
DEFAULT_FADE_MS = 50
```

## Testing

### Verification Script

Created `test_audio_routing.py` demonstrating:

- ✓ Sound system initialization with 7 channels
- ✓ Channel volume control (set/get)
- ✓ Channel mute control (set/check)
- ✓ Sound playback on all channels
- ✓ Bulldozer looping sound
- ✓ Priority ordering validation
- ✓ Sugar stdout notifications
- ✓ Proper shutdown cleanup

### Test Results

All features verified working:

```
Testing Enhanced Audio Routing System
============================================================
✓ Sound system initialized successfully
✓ Created 7 logical channels
✓ Channel volume control working
✓ Channel mute control working
✓ Sound playback on all channels
✓ Bulldozer looping sound
✓ Channel priorities validated
✓ Sugar notifications enabled
✓ Shutdown successful
```

## Usage Examples

### Basic Sound Playback

```python
from micropolis import audio
from micropolis.context import AppContext

# Initialize
context = AppContext(config=config)
audio.initialize_sound(context)

# Play UI feedback sound
audio.play_sound(context, "edit", "beep")

# Play disaster warning (high priority)
audio.play_sound(context, "warning", "Siren")

# Play ambient background sound with loop
audio.play_sound(context, "mode", "traffic", loop=True)
```

### Channel Control

```python
# Adjust warning channel volume
audio.set_channel_volume("warning", 0.8)

# Mute UI sounds during cutscene
audio.set_channel_mute("edit", True)

# Unmute after cutscene
audio.set_channel_mute("edit", False)

# Check if channel is muted
if audio.is_channel_muted("edit").unwrap():
    print("Edit channel is muted")
```

### Bulldozer (Looping) Sound

```python
# Start bulldozer sound loop
audio.start_bulldozer_sound(context)

# Stop bulldozer sound
audio.stop_bulldozer_sound(context)
```

### Advanced: Custom Fade

```python
# Play with 200ms fade-in for smooth transition
audio.play_sound(context, "fancy", "build", fade_ms=200)
```

## Compatibility

### Legacy API

All existing code using the old API continues to work:

- `make_sound(context, channel, sound_id)` → unchanged interface
- `make_sound_on(context, view, channel, sound_id)` → unchanged interface
- `start_bulldozer_sound(context)` → unchanged interface
- `stop_bulldozer_sound(context)` → unchanged interface

### Sugar Integration

- Stdout notifications maintain GTK shell compatibility
- Can be disabled via `EMIT_SUGAR_SOUND_NOTIFICATIONS = False`
- Format: `Sound <sound_name>` matches legacy behavior

### Global State

Legacy CamelCase global `Dozing` maintained for compatibility:

```python
global Dozing  # noqa: N806  # Legacy CamelCase global variable
Dozing = True  # noqa: F841  # Legacy global, kept for compatibility
```

## Performance Considerations

1. **Channel Caching**: Sound files loaded once and cached
2. **Efficient Preemption**: Priority checks prevent unnecessary stops
3. **Fade Optimization**: Default 50ms fade balances smoothness vs latency
4. **State Tracking**: Minimal overhead per channel

## Future Enhancements

Potential improvements for future iterations:

1. **Spatial Audio**: Position sounds based on view coordinates
2. **Dynamic Volume**: Adjust based on game state (e.g., disaster proximity)
3. **Sound Groups**: Manage related sounds collectively
4. **Priority Queuing**: Queue lower-priority sounds instead of dropping
5. **Analytics**: Track sound playback for debugging/tuning

## Dependencies

- `pygame.mixer`: Core audio playback
- `result`: Error handling with `Result` types
- `pydantic`: Context validation

## References

- Original spec: `docs/pygame_ui_port_checklist.md` §6.3
- Legacy Tcl: `assets/sound.tcl`
- Test script: `test_audio_routing.py`

## Checklist Status

✅ **Completed**: Section 9, checklist item:

- [x] Recreate the audio routing from §6.3 using `audio.py`/`pygame.mixer`, matching channel semantics and optional stdout notifications.

## Notes

- All lint warnings addressed (legacy globals marked with `noqa` comments)
- Type hints maintained throughout
- Result types used for error handling consistency
- Documentation strings follow project conventions
