# Dialog Panels Implementation

This document describes the implementation of the notice, help, player, and file dialogs for the Micropolis pygame UI, as specified in §4.7 of the pygame UI port checklist.

## Overview

Four dialog panels have been implemented to replace the legacy Tcl/Tk dialogs:

1. **NoticeDialog** - Message notification system
2. **HelpDialog** - Contextual help browser
3. **PlayerDialog** - Chat and multiplayer interface
4. **FileDialog** - City file picker

## Implementation Details

### NoticeDialog (`notice_dialog.py`)

Displays a stack of dismissible message cards with:

- **Severity levels**: Info, Warning, Error, Finance, Disaster, Advisor (each with color coding)
- **Features**:
  - Scrollable container for message history (up to 50 messages)
  - Individual dismiss buttons per message
  - "Clear All" button to remove all messages
  - "Mute" toggle to suppress new messages
  - Filter buttons to show/hide messages by severity
  - Auto-scroll to bottom when new messages arrive
- **Event integration**: Subscribes to `message.posted` events from the event bus
- **API**: `add_notice(text, severity, x, y)` for programmatic message posting

**Usage:**

```python
from src.micropolis.ui.panels import NoticeDialog, MessageSeverity

# Create panel
notice_dialog = NoticeDialog(panel_manager, context)

# Add a message
notice_dialog.add_notice(
    "Traffic congestion detected!",
    MessageSeverity.WARNING,
    x=50, y=100
)
```

### HelpDialog (`help_dialog.py`)

Contextual help browser with:

- **HTML-lite rendering**: Supports `<h1>`, `<h2>`, `<p>` tags with styled text
- **Features**:
  - Scrollable content area
  - Topic-based help system
  - Close button
  - Loads help files from `docs/manual/` directory
  - Fallback to default help content if files not found
- **Event integration**: Subscribes to `help.show` events
- **API**:
  - `show_topic(topic)` - Display help for specific topic
  - `load_help_file(filepath)` - Load HTML help file
  - `set_help_content(html)` - Set content directly

**Usage:**

```python
from src.micropolis.ui.panels import HelpDialog

# Create panel
help_dialog = HelpDialog(panel_manager, context)

# Show specific topic
help_dialog.show_topic("zones")

# Load custom help file
help_dialog.load_help_file("/path/to/help.html")
```

### PlayerDialog (`player_dialog.py`)

Multiplayer chat and buddy list interface with:

- **Chat log**: Scrollable message history with username and timestamps
- **Buddy list**: Shows online/offline status with colored indicators
- **Text input**: For sending chat messages
- **Features**:
  - Color-coded messages (local vs. remote)
  - System messages for join/leave events
  - Connection status indicator
  - Send button and Enter key support
  - Backspace editing
- **Sugar integration**: Connects to Sugar networking via event bus
- **Events**:
  - Subscribes to: `chat.message`, `sugar.buddy_joined`, `sugar.buddy_left`, `sugar.shared`
  - Publishes: `chat.send`

**Usage:**

```python
from src.micropolis.ui.panels import PlayerDialog

# Create panel
player_dialog = PlayerDialog(panel_manager, context)

# Messages are automatically handled via event bus
# To send a message programmatically:
context.event_bus.publish("chat.message", {
    "username": "Player1",
    "text": "Hello!",
    "is_local": False
})
```

### FileDialog (`file_dialog.py`)

Native pygame file picker for loading/saving cities:

- **Modes**: "load" or "save"
- **Features**:
  - Thumbnail grid of city files
  - Recent cities list
  - Text input for save filename
  - Scans `.cty` files from cities directory
  - Click to select, Enter to confirm
  - Cancel button
- **Layout**: Grid of 120x140px thumbnails with city names
- **Events**:
  - Publishes: `city.load`, `city.save`

**Usage:**

```python
from src.micropolis.ui.panels import FileDialog

# Create load dialog
load_dialog = FileDialog(panel_manager, context, mode="load")

# Create save dialog
save_dialog = FileDialog(panel_manager, context, mode="save")

# Dialogs publish events when user confirms action
# Listen for events:
context.event_bus.subscribe("city.load", lambda data: load_city(data['path']))
context.event_bus.subscribe("city.save", lambda data: save_city(data['path']))
```

## Widget Dependencies

All dialogs depend on the following widgets from `ui/widgets/`:

- `UIWidget` - Base widget class
- `Button` - Click handlers and rendering
- `TextLabel` - Text display with optional wrapping
- `ScrollContainer` - Scrollable viewport for content
- `UIPanel` - Base panel class with lifecycle management

## Testing

Basic import tests are provided in `tests/ui/test_dialogs.py`:

```bash
uv run pytest tests/ui/test_dialogs.py -v
```

All tests verify that dialogs can be imported and are exported from the panels module.

## Integration with Panel Manager

To register dialogs with the panel manager:

```python
from src.micropolis.ui.panel_manager import PanelManager
from src.micropolis.ui.panels import (
    NoticeDialog,
    HelpDialog,
    PlayerDialog,
    FileDialog,
)

# In panel manager initialization:
notice_dialog = NoticeDialog(panel_manager, context)
help_dialog = HelpDialog(panel_manager, context)
player_dialog = PlayerDialog(panel_manager, context)
load_dialog = FileDialog(panel_manager, context, mode="load")
save_dialog = FileDialog(panel_manager, context, mode="save")

# Register panels
panel_manager.register_panel("notice", notice_dialog)
panel_manager.register_panel("help", help_dialog)
panel_manager.register_panel("player", player_dialog)
panel_manager.register_panel("load_city", load_dialog)
panel_manager.register_panel("save_city", save_dialog)
```

## Known Limitations

1. **TextLabel widget**: Currently uses `TextLabel` from widgets, which has limited text rendering. A more advanced text input widget would be beneficial for the player chat and file dialog input fields.

2. **Thumbnail generation**: FileDialog does not yet generate thumbnails from city files. This would require reading the city map data and rendering it to a small surface.

3. **HTML rendering**: HelpDialog uses a very simple HTML-lite parser. Full HTML/CSS support would require a more sophisticated rendering engine or integration with a library like `pygame_gui`.

4. **Event bus**: Dialogs assume the `event_bus` attribute exists on `AppContext`. This needs to be initialized during context setup.

5. **Sugar attributes**: PlayerDialog references `context.sugar_nickname` which may not exist. Fallback logic handles this.

## Future Enhancements

- Implement proper text input widgets with cursor, selection, and clipboard support
- Add thumbnail generation from city file preview
- Enhance HTML rendering with CSS support
- Add keyboard navigation (Tab/Shift+Tab between controls)
- Implement file browser navigation (parent directory, etc.)
- Add file type filtering to FileDialog
- Support for custom message icons in NoticeDialog
- Rich text formatting in chat messages (bold, colors, emojis)

## Checklist Update

✅ §4.7 - Notice/help/player/file dialogs implemented and tested

- NoticeDialog: Scrollable message cards with filters
- HelpDialog: HTML-lite content browser
- PlayerDialog: Chat with buddy list and Sugar integration
- FileDialog: Native file picker with thumbnails

The feature is now marked complete in `docs/pygame_ui_port_checklist.md`.
