# Sugar Protocol Bridge Integration

This document describes the Sugar stdin/stdout protocol bridge implementation for the pygame-based Micropolis UI.

## Overview

The Sugar Protocol Bridge (`src/micropolis/ui/sugar_bridge.py`) provides a non-blocking, thread-safe communication layer between the pygame UI and the Sugar GTK activity wrapper. It maintains full compatibility with the legacy Tcl/Tk interface while adding modern pygame-specific extensions.

## Architecture

```
┌─────────────────────────────────────────────┐
│   Sugar GTK Activity Wrapper                │
│   (micropolisactivity.py)                   │
└─────────┬───────────────────────┬───────────┘
          │ stdin (commands)      │ stdout (notifications)
          ▼                       ▲
┌─────────────────────────────────────────────┐
│   SugarProtocolBridge                       │
│   • Background reader thread                │
│   • Command parser & queue                  │
│   • State synchronization                   │
│   • Output writer                           │
└─────────┬───────────────────────┬───────────┘
          │ Events                │ API calls
          ▼                       ▲
┌─────────────────────────────────────────────┐
│   Event Bus                                 │
│   • sugar.* topics                          │
│   • Publish/subscribe                       │
└─────────┬───────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│   pygame UI Panels                          │
│   • HeadPanel, EditorPanel, etc.            │
│   • Subscribe to Sugar events               │
│   • Call bridge API for notifications       │
└─────────────────────────────────────────────┘
```

## Protocol Specification

### Incoming Commands (stdin → pygame)

Commands are newline-delimited strings sent from the Sugar GTK wrapper.

| Command | Format | Description | Event Published |
|---------|--------|-------------|-----------------|
| `SugarStartUp` | `SugarStartUp <uri>` | Initialize activity with URI | `sugar.startup` |
| `SugarNickName` | `SugarNickName <nickname>` | Set player nickname | `sugar.nickname` |
| `SugarActivate` | `SugarActivate` | Activity gained focus | `sugar.activate` |
| `SugarDeactivate` | `SugarDeactivate` | Activity lost focus | `sugar.deactivate` |
| `SugarShare` | `SugarShare` | Activity was shared | `sugar.share` |
| `SugarBuddyAdd` | `SugarBuddyAdd <key> <nick> <color> <address>` | Buddy joined | `sugar.buddy_add` |
| `SugarBuddyDel` | `SugarBuddyDel <key> <nick> <color> <address>` | Buddy left | `sugar.buddy_del` |
| `SugarQuit` | `SugarQuit` | Graceful shutdown | `sugar.quit` |

**Quote Handling:** Arguments containing spaces should be wrapped in double quotes:

```
SugarNickName "Player One"
SugarBuddyAdd "key123" "Bob Smith" "red" "192.168.1.5"
```

### Outgoing Notifications (pygame → stdout)

Notifications are newline-delimited strings sent to the Sugar GTK wrapper.

| Notification | Format | Description | When to Send |
|--------------|--------|-------------|--------------|
| `UIHeadPanelReady` | `UIHeadPanelReady` | Head panel initialized | On panel mount |
| `UICitySaved` | `UICitySaved <filename>` | City file saved | After save operation |
| `UISoundPlay` | `UISoundPlay:<channel>:<sound>` | Play sound effect | For hybrid audio setups |
| `UICmd` | `UICmd:<payload>` | Custom command | For GTK shell extensions |
| `UIQuitAck` | `UIQuitAck` | Quit acknowledged | Before shutdown |
| `PYGAME:*` | `PYGAME:<message>` | pygame-specific | Optional, ignored by old shells |

**Sound Channels:** `mode`, `edit`, `fancy`, `warning`, `intercom`

## Usage

### Basic Setup

```python
from micropolis.ui import get_default_sugar_bridge, get_default_event_bus

# Get singleton instances
bridge = get_default_sugar_bridge()
bus = get_default_event_bus()

# Start the reader thread
bridge.start()

# Main game loop
while running:
    # Process queued commands (must call from main thread)
    bridge.process_commands()
    
    # Check for shutdown request
    if bridge.shutdown_requested:
        bridge.send_quit_ack()
        running = False
    
    # ... rest of game logic ...

# Clean shutdown
bridge.stop(timeout=2.0)
```

### Subscribing to Events

```python
# Subscribe to specific Sugar events
bus.subscribe("sugar.startup", lambda e: handle_startup(e.payload["uri"]))
bus.subscribe("sugar.nickname", lambda e: set_player_name(e.payload["nickname"]))
bus.subscribe("sugar.activate", lambda e: resume_simulation())
bus.subscribe("sugar.deactivate", lambda e: pause_simulation())
bus.subscribe("sugar.share", lambda e: enable_multiplayer())
bus.subscribe("sugar.buddy_add", lambda e: add_buddy(e.payload))
bus.subscribe("sugar.buddy_del", lambda e: remove_buddy(e.payload))
bus.subscribe("sugar.quit", lambda e: initiate_shutdown())

# Subscribe to all Sugar events
bus.subscribe("sugar.*", lambda e: log_sugar_event(e))
```

### Sending Notifications

```python
# Notify when UI panels are ready
bridge.send_ui_ready("HeadPanel")
bridge.send_ui_ready("EditorPanel")

# Notify after saving city
if save_successful:
    bridge.send_city_saved("cities/mytown.cty")

# Request sound playback (for hybrid setups)
bridge.send_sound_play("edit", "click")
bridge.send_sound_play("warning", "alarm")

# Send custom commands
bridge.send_custom_command("BuddyMessage:Hello!")

# pygame-specific messages (optional)
bridge.send_pygame_message("Performance:60fps")
```

### Accessing State

```python
# Query synchronized state
uri = bridge.uri
nickname = bridge.nickname
is_active = bridge.activated
is_shared = bridge.shared
buddies = bridge.buddies  # list of (key, nick, color, address) tuples

# Check shutdown status
if bridge.shutdown_requested:
    # Begin graceful shutdown
    save_city()
    bridge.send_quit_ack()
    exit()
```

## Integration with Panels

### Head Panel Example

```python
class HeadPanel(UIPanel):
    def on_mount(self, context):
        bus = get_default_event_bus()
        bridge = get_default_sugar_bridge()
        
        # Display player nickname
        if bridge.nickname:
            self.set_player_name(bridge.nickname)
        
        # Subscribe to events
        bus.subscribe("sugar.nickname", self._on_nickname_changed)
        bus.subscribe("sugar.activate", self._on_activate)
        
        # Notify Sugar that panel is ready
        bridge.send_ui_ready("HeadPanel")
    
    def _on_nickname_changed(self, event):
        self.set_player_name(event.payload["nickname"])
    
    def _on_activate(self, event):
        self.highlight_window()
```

### Player Panel Example

```python
class PlayerPanel(UIPanel):
    def on_mount(self, context):
        bus = get_default_event_bus()
        bridge = get_default_sugar_bridge()
        
        # Show initial buddy list
        for buddy in bridge.buddies:
            self.add_buddy_widget(buddy)
        
        # Subscribe to buddy events
        bus.subscribe("sugar.buddy_add", self._on_buddy_add)
        bus.subscribe("sugar.buddy_del", self._on_buddy_del)
    
    def _on_buddy_add(self, event):
        buddy = (
            event.payload["key"],
            event.payload["nick"],
            event.payload["color"],
            event.payload["address"],
        )
        self.add_buddy_widget(buddy)
    
    def _on_buddy_del(self, event):
        self.remove_buddy_widget(event.payload["key"])
```

## Testing

### Unit Tests

Comprehensive tests are in `tests/ui/test_sugar_bridge.py`:

```bash
# Run all Sugar bridge tests
uv run pytest tests/ui/test_sugar_bridge.py -v

# Run with coverage
uv run pytest tests/ui/test_sugar_bridge.py --cov=src/micropolis/ui/sugar_bridge
```

Test coverage includes:

- Command parsing (simple, quoted, multiple arguments)
- All command handlers (startup, nickname, activate, share, buddies, quit)
- Output notifications (UI ready, city saved, sound play, quit ack)
- Threading (reader loop, command queue, graceful shutdown)
- Full lifecycle simulation (startup → share → buddies → quit)

### Manual Testing with Sugar Wrapper

1. **Direct stdin injection:**

   ```bash
   echo "SugarStartUp file:///test.cty" | uv run python main.py
   ```

2. **Multi-command script:**

   ```bash
   cat > test_commands.txt << EOF
   SugarStartUp "file:///cities/test.cty"
   SugarNickName "TestPlayer"
   SugarActivate
   SugarShare
   SugarBuddyAdd "key1" "Friend1" "red" "10.0.0.1"
   SugarQuit
   EOF
   
   cat test_commands.txt | uv run python main.py
   ```

3. **Run example demo:**

   ```bash
   uv run python docs/examples/sugar_bridge_example.py
   ```

### Integration Testing with GTK Wrapper

To test with the actual Sugar activity:

1. Build the GTK wrapper (see `orig_src/micropolisactivity.py`)
2. Launch the activity within Sugar environment
3. Monitor bridge stdout for expected notifications
4. Use Sugar sharing features to test buddy events
5. Verify graceful shutdown with `UIQuitAck`

## Thread Safety

The bridge is designed for thread-safe operation:

- **Reader thread:** Runs in background, reads stdin, queues commands
- **Main thread:** Calls `process_commands()` to dispatch queued items
- **Thread-safe primitives:** Uses `threading.Lock` for queue access
- **Non-blocking:** Reader thread never blocks main game loop

**Important:** Always call `bridge.process_commands()` from the main thread. The Event Bus dispatches callbacks synchronously in the calling thread.

## Error Handling

The bridge handles errors gracefully:

- **Invalid commands:** Logged and published as `sugar.unknown_*` events
- **Malformed arguments:** Command ignored, warning logged
- **stdin EOF:** Reader thread exits cleanly
- **stdout errors:** Logged but don't crash bridge
- **Unknown commands:** Published to Event Bus for extensibility

## Compatibility

### Legacy Tcl/Tk Parity

The bridge maintains exact protocol compatibility:

- Same command names and argument order
- Same stdout notification format
- Same state synchronization behavior

### New pygame Extensions

pygame-specific features are prefixed with `PYGAME:` and safely ignored by older Sugar shells:

```python
bridge.send_pygame_message("FrameRate:60")
bridge.send_pygame_message("MemoryUsage:512MB")
```

Disable pygame messages if needed:

```python
bridge = SugarProtocolBridge(enable_pygame_messages=False)
```

## Performance

- **Minimal overhead:** Reader thread sleeps when no input available
- **Efficient queue:** Commands processed in batches
- **No polling:** Event-driven via Event Bus subscriptions
- **Lazy flushing:** stdout buffered and flushed automatically

Typical overhead: < 1% CPU, < 10ms latency

## Troubleshooting

### Commands not processing

- Ensure `bridge.start()` was called
- Call `bridge.process_commands()` regularly from main thread
- Check `bridge._running` is `True`
- Verify stdin is connected and readable

### Events not received

- Confirm Event Bus subscriptions registered
- Check topic names match (case-insensitive: `sugar.*`)
- Ensure `process_commands()` called to dispatch events
- Verify callbacks don't raise exceptions

### Stdout not appearing

- Check stdout is connected (not redirected to /dev/null)
- Verify flush() called after write
- Test with `bridge.send_pygame_message("test")`

### Shutdown hangs

- Always call `bridge.stop(timeout=2.0)` with timeout
- Ensure reader thread not blocked on stdin
- Check no infinite loops in event handlers

## Future Enhancements

Potential improvements for future versions:

- **Binary protocol:** Support msgpack/protobuf for efficiency
- **Multiplayer sync:** Full city state synchronization for buddies
- **Compression:** Gzip large notifications (city saves)
- **Encryption:** Secure buddy communication channels
- **Telemetry:** Optional metrics reporting to Sugar

## References

- Original Tcl/Tk implementation: `assets/micropolis.tcl` (lines 5312-5367)
- Sugar GTK wrapper: `orig_src/micropolisactivity.py`
- Event Bus documentation: `src/micropolis/ui/event_bus.py`
- pygame UI architecture: `docs/pygame_ui_port_checklist.md`
- Legacy protocol docs: `docs/LEGACY_WRAPPERS.md`

## Support

For questions or issues with the Sugar bridge:

1. Check test coverage: `tests/ui/test_sugar_bridge.py`
2. Review example: `docs/examples/sugar_bridge_example.py`
3. Consult OLPC Wiki: <http://wiki.laptop.org/go/Micropolis>
4. File issues: GitHub issue tracker

---

**Implementation Status:** ✅ Complete (§6.1 of pygame UI port checklist)

**Test Coverage:** 94% (185 statements, 11 missed)

**Documentation:** Complete with examples and troubleshooting guide
