"""
player_dialog.py - Player/chat dialog panel for Micropolis pygame UI

This panel implements the player/chat window with input field, chat log,
buddy list, and connects to Sugar networking via existing IPC channels.
Provides status indicators for connection states.

Ported from wplayer.tcl
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

try:
    import pygame
except ImportError:
    pygame = None  # type: ignore

from micropolis.context import AppContext
from micropolis.ui.uipanel import UIPanel
from micropolis.ui.widgets.base import UIWidget
from micropolis.ui.widgets.button import Button
from micropolis.ui.widgets.label import TextLabel
from micropolis.ui.widgets.scroll import ScrollContainer

if TYPE_CHECKING:
    from micropolis.ui.panel_manager import PanelManager


@dataclass
class ChatMessage:
    """Represents a single chat message."""

    username: str
    text: str
    timestamp: float
    is_local: bool = False


@dataclass
class Buddy:
    """Represents a buddy/player in the session."""

    name: str
    color: tuple[int, int, int]
    is_online: bool = True


class ChatLogRenderer(UIWidget):
    """Widget that renders chat log messages."""

    def __init__(self, rect: tuple[int, int, int, int] = (0, 0, 400, 300)) -> None:
        super().__init__(widget_id="chat_log", rect=rect)
        self._messages: deque[ChatMessage] = deque(maxlen=100)
        self._line_height = 20
        self._padding = 5

    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the chat log."""
        self._messages.append(message)
        self._update_size()
        self.invalidate()

    def _update_size(self) -> None:
        """Update widget size based on message count."""
        content_height = len(self._messages) * self._line_height + 2 * self._padding
        x, y, w, _ = self.rect
        self.set_rect((x, y, w, content_height))

    def clear(self) -> None:
        """Clear all messages."""
        self._messages.clear()
        self._update_size()
        self.invalidate()

    def on_render(self, renderer) -> None:
        """Render the chat log."""
        if not pygame:
            return

        x, y, w, h = self.rect

        # Background
        renderer.draw_rect(self.rect, (20, 20, 20))

        # Render each message
        y_offset = y + self._padding
        try:
            font = pygame.font.Font(None, 18)

            for msg in self._messages:
                # Color code local vs remote messages
                color = (100, 200, 255) if msg.is_local else (255, 255, 255)

                # Format: [username]: text
                text = f"[{msg.username}]: {msg.text}"

                # Render text
                text_surface = font.render(text, True, color)
                text_rect = text_surface.get_rect()
                text_rect.topleft = (x + self._padding, y_offset)

                # Blit text
                if hasattr(renderer, "_surface"):
                    renderer._surface.blit(text_surface, text_rect)

                y_offset += self._line_height

        except Exception:
            pass  # Skip rendering on error


class BuddyListRenderer(UIWidget):
    """Widget that renders the buddy list."""

    def __init__(self, rect: tuple[int, int, int, int] = (0, 0, 200, 300)) -> None:
        super().__init__(widget_id="buddy_list", rect=rect)
        self._buddies: list[Buddy] = []
        self._line_height = 25
        self._padding = 5

    def set_buddies(self, buddies: list[Buddy]) -> None:
        """Set the list of buddies."""
        self._buddies = buddies
        self.invalidate()

    def on_render(self, renderer) -> None:
        """Render the buddy list."""
        if not pygame:
            return

        x, y, w, h = self.rect

        # Background
        renderer.draw_rect(self.rect, (30, 30, 30))

        # Render each buddy
        y_offset = y + self._padding
        try:
            font = pygame.font.Font(None, 18)

            for buddy in self._buddies:
                # Status indicator (online/offline)
                status_color = (0, 255, 0) if buddy.is_online else (128, 128, 128)
                status_rect = (x + self._padding, y_offset + 5, 10, 10)
                if pygame:
                    pygame.draw.circle(
                        renderer._surface if hasattr(renderer, "_surface") else None,
                        status_color,
                        (status_rect[0] + 5, status_rect[1] + 5),
                        5,
                    )

                # Buddy name with color
                text_x = x + self._padding + 20
                text_surface = font.render(buddy.name, True, buddy.color)
                text_rect = text_surface.get_rect()
                text_rect.topleft = (text_x, y_offset)

                # Blit text
                if hasattr(renderer, "_surface"):
                    renderer._surface.blit(text_surface, text_rect)

                y_offset += self._line_height

        except Exception:
            pass  # Skip rendering on error


class PlayerDialog(UIPanel):
    """Player/chat dialog panel."""

    def __init__(self, manager: PanelManager, context: AppContext) -> None:
        super().__init__(manager, context)
        self.panel_id = "player_dialog"
        self.legacy_name = "player"

        # Chat state
        self._chat_log_renderer: ChatLogRenderer | None = None
        self._buddy_list_renderer: BuddyListRenderer | None = None
        self._chat_input_text: str = ""
        self._chat_scroll: ScrollContainer | None = None
        self._buddy_scroll: ScrollContainer | None = None

        # UI components
        self._input_field: UIWidget | None = None
        self._send_btn: Button | None = None
        self._status_label: TextLabel | None = None
        self._connection_status: str = "Disconnected"

        # Subscribe to event bus for chat messages and Sugar events
        if hasattr(context, "event_bus"):
            context.event_bus.subscribe("chat.message", self._on_chat_message)
            context.event_bus.subscribe("sugar.buddy_joined", self._on_buddy_joined)
            context.event_bus.subscribe("sugar.buddy_left", self._on_buddy_left)
            context.event_bus.subscribe("sugar.shared", self._on_shared)

    def did_mount(self) -> None:
        """Initialize UI components when panel mounts."""
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the player dialog UI layout."""
        x, y, w, h = self.rect

        # Split panel: chat log on left, buddy list on right
        buddy_list_width = 200
        chat_width = w - buddy_list_width - 20

        # Status label at top
        self._status_label = TextLabel(
            text=f"Status: {self._connection_status}",
            rect=(x + 10, y + 10, w - 20, 25),
            color=(150, 150, 150, 255),
        )

        # Chat log scroll container
        chat_rect = (x + 10, y + 45, chat_width, h - 100)
        self._chat_scroll = ScrollContainer(rect=chat_rect)
        self._chat_log_renderer = ChatLogRenderer(rect=(0, 0, chat_width - 20, 300))
        self._chat_scroll.set_content(self._chat_log_renderer)

        # Input field and send button at bottom
        input_y = y + h - 45
        self._input_field = TextLabel(
            text="",
            rect=(x + 10, input_y, chat_width - 90, 35),
            color=(255, 255, 255, 255),
        )

        self._send_btn = Button(
            text="Send",
            rect=(x + chat_width - 70, input_y, 80, 35),
            on_click=self._handle_send_message,
        )

        # Buddy list scroll container
        buddy_x = x + chat_width + 20
        buddy_rect = (buddy_x, y + 45, buddy_list_width, h - 55)
        self._buddy_scroll = ScrollContainer(rect=buddy_rect)
        self._buddy_list_renderer = BuddyListRenderer(
            rect=(0, 0, buddy_list_width - 20, 300)
        )
        self._buddy_scroll.set_content(self._buddy_list_renderer)

    def _on_chat_message(self, event_data: dict) -> None:
        """Handle incoming chat message."""
        username = event_data.get("username", "Unknown")
        text = event_data.get("text", "")
        is_local = event_data.get("is_local", False)

        if self._chat_log_renderer:
            import time

            message = ChatMessage(
                username=username, text=text, timestamp=time.time(), is_local=is_local
            )
            self._chat_log_renderer.add_message(message)

            # Auto-scroll to bottom
            if self._chat_scroll:
                max_x, max_y = self._chat_scroll._max_scroll()
                self._chat_scroll.scroll_to(0, max_y)

    def _on_buddy_joined(self, event_data: dict) -> None:
        """Handle buddy joined event."""
        buddy_name = event_data.get("name", "Unknown")
        buddy_color = event_data.get("color", (255, 255, 255))

        # Update buddy list
        if self._buddy_list_renderer:
            buddies = self._buddy_list_renderer._buddies
            # Check if buddy already exists
            existing = next((b for b in buddies if b.name == buddy_name), None)
            if existing:
                existing.is_online = True
            else:
                buddies.append(
                    Buddy(name=buddy_name, color=buddy_color, is_online=True)
                )
            self._buddy_list_renderer.set_buddies(buddies)

        # Add system message
        if self._chat_log_renderer:
            import time

            msg = ChatMessage(
                username="System",
                text=f"{buddy_name} joined",
                timestamp=time.time(),
                is_local=False,
            )
            self._chat_log_renderer.add_message(msg)

    def _on_buddy_left(self, event_data: dict) -> None:
        """Handle buddy left event."""
        buddy_name = event_data.get("name", "Unknown")

        # Update buddy list
        if self._buddy_list_renderer:
            buddies = self._buddy_list_renderer._buddies
            for buddy in buddies:
                if buddy.name == buddy_name:
                    buddy.is_online = False
            self._buddy_list_renderer.set_buddies(buddies)

        # Add system message
        if self._chat_log_renderer:
            import time

            msg = ChatMessage(
                username="System",
                text=f"{buddy_name} left",
                timestamp=time.time(),
                is_local=False,
            )
            self._chat_log_renderer.add_message(msg)

    def _on_shared(self, event_data: dict) -> None:
        """Handle Sugar shared event."""
        self._connection_status = "Connected (Shared)"
        if self._status_label:
            self._status_label.text = f"Status: {self._connection_status}"
            self._status_label.invalidate()

    def _handle_send_message(self) -> None:
        """Handle send button click."""
        if not self._input_field or not self._chat_input_text.strip():
            return

        # Get local username
        username = self.context.sugar_nickname or "Player"

        # Send message through event bus
        if hasattr(self.context, "event_bus"):
            self.context.event_bus.publish(
                "chat.send",
                {"username": username, "text": self._chat_input_text, "is_local": True},
            )

        # Add to local chat log
        if self._chat_log_renderer:
            import time

            message = ChatMessage(
                username=username,
                text=self._chat_input_text,
                timestamp=time.time(),
                is_local=True,
            )
            self._chat_log_renderer.add_message(message)

        # Clear input
        self._chat_input_text = ""
        if self._input_field:
            self._input_field.text = ""
            self._input_field.invalidate()

    def handle_text_input(self, text: str) -> None:
        """Handle text input for chat field."""
        self._chat_input_text += text
        if self._input_field:
            self._input_field.text = self._chat_input_text
            self._input_field.invalidate()

    def handle_backspace(self) -> None:
        """Handle backspace in chat field."""
        if self._chat_input_text:
            self._chat_input_text = self._chat_input_text[:-1]
            if self._input_field:
                self._input_field.text = self._chat_input_text
                self._input_field.invalidate()

    def draw(self, surface) -> None:
        """Render the player dialog."""
        if not self.visible:
            return

        # Render background
        if pygame:
            bg_color = (40, 40, 40)
            pygame.draw.rect(surface, bg_color, self.rect)
            pygame.draw.rect(surface, (100, 100, 100), self.rect, 2)

        # Render status label
        if self._status_label:
            self._status_label.render(surface)

        # Render chat scroll container
        if self._chat_scroll:
            self._chat_scroll.render(surface)

        # Render input field and send button
        if self._input_field:
            self._input_field.render(surface)
        if self._send_btn:
            self._send_btn.render(surface)

        # Render buddy list scroll container
        if self._buddy_scroll:
            self._buddy_scroll.render(surface)

    def handle_panel_event(self, event) -> bool:
        """Handle panel-specific events."""
        # Handle text input for chat field
        if pygame and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                self._handle_send_message()
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.handle_backspace()
                return True
            elif event.unicode and event.unicode.isprintable():
                self.handle_text_input(event.unicode)
                return True

        # Forward to send button
        if self._send_btn and self._send_btn.handle_event(event):
            return True

        # Forward to scroll containers
        if self._chat_scroll and self._chat_scroll.handle_event(event):
            return True
        if self._buddy_scroll and self._buddy_scroll.handle_event(event):
            return True

        return False


__all__ = ["PlayerDialog", "ChatMessage", "Buddy"]
