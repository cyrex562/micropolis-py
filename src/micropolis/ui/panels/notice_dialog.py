"""
notice_dialog.py - Notice/message dialog panel for Micropolis pygame UI

This panel implements the notice window that displays dismissible message cards
with severity colors, auto-scroll for long text, Clear All and Mute buttons,
and filters for finance, disasters, and advisor messages.

Ported from wnotice.tcl
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum
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


class MessageSeverity(Enum):
    """Message severity levels with associated colors."""

    INFO = ("info", (100, 150, 200))
    WARNING = ("warning", (200, 150, 50))
    ERROR = ("error", (200, 50, 50))
    FINANCE = ("finance", (50, 200, 100))
    DISASTER = ("disaster", (255, 100, 0))
    ADVISOR = ("advisor", (150, 100, 200))


@dataclass
class NoticeMessage:
    """Represents a single notice message."""

    text: str
    severity: MessageSeverity
    timestamp: float
    x: int = 0
    y: int = 0
    dismissible: bool = True


class MessageCard(UIWidget):
    """Single dismissible message card widget."""

    def __init__(
        self,
        message: NoticeMessage,
        on_dismiss: callable | None = None,
        rect: tuple[int, int, int, int] = (0, 0, 400, 60),
    ) -> None:
        super().__init__(widget_id=f"card_{id(message)}", rect=rect)
        self.message = message
        self.on_dismiss_callback = on_dismiss

        # Create label for message text
        self.label = TextLabel(
            text=message.text,
            rect=(10, 10, rect[2] - 80, rect[3] - 20),
            color=(255, 255, 255),
            wrap_width=rect[2] - 80,
        )
        self.add_child(self.label)

        # Create dismiss button if message is dismissible
        if message.dismissible:
            self.dismiss_btn = Button(
                text="✕",
                rect=(rect[2] - 60, 10, 50, rect[3] - 20),
                on_click=self._handle_dismiss,
            )
            self.add_child(self.dismiss_btn)
        else:
            self.dismiss_btn = None

        # Set background color based on severity
        self.bg_color = message.severity.value[1]

    def _handle_dismiss(self) -> None:
        """Handle dismiss button click."""
        if self.on_dismiss_callback:
            self.on_dismiss_callback(self.message)

    def on_render(self, renderer) -> None:
        """Render the message card with colored background."""
        # Draw card background
        x, y, w, h = self.rect
        if pygame:
            # Add alpha for slight transparency
            color = (*self.bg_color, 200)
            renderer.draw_rect(self.rect, color, border=True, border_color=(0, 0, 0))


class NoticeDialog(UIPanel):
    """Notice window panel displaying message cards."""

    def __init__(self, manager: PanelManager, context: AppContext) -> None:
        super().__init__(manager, context)
        self.panel_id = "notice_dialog"
        self.legacy_name = "notice"

        # Message queue
        self._messages: deque[NoticeMessage] = deque(maxlen=50)
        self._active_filters: set[MessageSeverity] = set()
        self._muted = False

        # UI components
        self._scroll_container: ScrollContainer | None = None
        self._message_container: UIWidget | None = None
        self._clear_btn: Button | None = None
        self._mute_btn: Button | None = None
        self._filter_buttons: dict[MessageSeverity, Button] = {}

        # Subscribe to event bus for messages
        if hasattr(context, "event_bus"):
            context.event_bus.subscribe("message.posted", self._on_message_posted)

    def did_mount(self) -> None:
        """Initialize UI components when panel mounts."""
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the notice dialog UI layout."""
        x, y, w, h = self.rect

        # Top control bar with buttons
        control_bar_height = 40
        button_width = 100
        button_spacing = 10

        # Clear All button
        self._clear_btn = Button(
            text="Clear All",
            rect=(x + 10, y + 10, button_width, 30),
            on_click=self._handle_clear_all,
        )

        # Mute button
        self._mute_btn = Button(
            text="Mute",
            rect=(x + button_width + 20, y + 10, button_width, 30),
            on_click=self._handle_toggle_mute,
        )

        # Filter buttons
        filter_x = x + 2 * button_width + 40
        for severity in MessageSeverity:
            btn = Button(
                text=severity.value[0].title(),
                rect=(filter_x, y + 10, 80, 30),
                on_click=lambda s=severity: self._toggle_filter(s),
                toggle=True,
            )
            self._filter_buttons[severity] = btn
            filter_x += 90

        # Scroll container for messages
        scroll_rect = (x, y + control_bar_height, w, h - control_bar_height)
        self._scroll_container = ScrollContainer(rect=scroll_rect)

        # Container widget to hold all message cards
        self._message_container = UIWidget(
            widget_id="message_container", rect=(0, 0, w - 20, 100)
        )
        self._scroll_container.set_content(self._message_container)

        self._relayout_messages()

    def _relayout_messages(self) -> None:
        """Relayout all message cards in the container."""
        if not self._message_container:
            return

        # Clear existing cards
        for child in list(self._message_container.children):
            self._message_container.remove_child(child)

        # Add cards for visible messages
        y_offset = 0
        card_width = self.rect[2] - 40
        card_height = 60
        card_spacing = 10

        for message in self._messages:
            # Apply filters
            if self._active_filters and message.severity not in self._active_filters:
                continue

            card = MessageCard(
                message=message,
                on_dismiss=self._handle_dismiss_message,
                rect=(10, y_offset, card_width, card_height),
            )
            self._message_container.add_child(card)
            y_offset += card_height + card_spacing

        # Update container height
        container_height = max(y_offset, self.rect[3] - 40)
        self._message_container.resize_to(card_width + 20, container_height)
        self.invalidate()

    def _on_message_posted(self, event_data: dict) -> None:
        """Handle new message posted to event bus."""
        if self._muted:
            return

        # Extract message data
        text = event_data.get("text", "")
        severity_name = event_data.get("severity", "info")
        x = event_data.get("x", 0)
        y = event_data.get("y", 0)

        # Map severity string to enum
        severity = MessageSeverity.INFO
        for sev in MessageSeverity:
            if sev.value[0] == severity_name:
                severity = sev
                break

        # Create and add message
        import time

        message = NoticeMessage(
            text=text, severity=severity, timestamp=time.time(), x=x, y=y
        )
        self._messages.append(message)
        self._relayout_messages()

        # Auto-scroll to bottom for new messages
        if self._scroll_container:
            max_x, max_y = self._scroll_container._max_scroll()
            self._scroll_container.scroll_to(0, max_y)

    def add_notice(
        self,
        text: str,
        severity: MessageSeverity = MessageSeverity.INFO,
        x: int = 0,
        y: int = 0,
    ) -> None:
        """
        Add a notice message to the dialog.

        Args:
            text: Message text
            severity: Message severity level
            x: Optional X coordinate for location-based messages
            y: Optional Y coordinate for location-based messages
        """
        if self._muted:
            return

        import time

        message = NoticeMessage(
            text=text, severity=severity, timestamp=time.time(), x=x, y=y
        )
        self._messages.append(message)
        self._relayout_messages()

    def _handle_dismiss_message(self, message: NoticeMessage) -> None:
        """Handle dismissing a single message."""
        if message in self._messages:
            self._messages.remove(message)
            self._relayout_messages()

    def _handle_clear_all(self) -> None:
        """Handle Clear All button click."""
        self._messages.clear()
        self._relayout_messages()

    def _handle_toggle_mute(self) -> None:
        """Handle Mute button toggle."""
        self._muted = not self._muted
        if self._mute_btn:
            self._mute_btn.text = "Unmute" if self._muted else "Mute"

    def _toggle_filter(self, severity: MessageSeverity) -> None:
        """Toggle visibility filter for a severity level."""
        if severity in self._active_filters:
            self._active_filters.remove(severity)
        else:
            self._active_filters.add(severity)
        self._relayout_messages()

    def draw(self, surface) -> None:
        """Render the notice dialog."""
        if not self.visible:
            return

        # Render background
        if pygame:
            bg_color = (40, 40, 40)
            pygame.draw.rect(surface, bg_color, self.rect)

        # Render buttons
        if self._clear_btn:
            self._clear_btn.render(surface)
        if self._mute_btn:
            self._mute_btn.render(surface)
        for btn in self._filter_buttons.values():
            btn.render(surface)

        # Render scroll container
        if self._scroll_container:
            self._scroll_container.render(surface)

    def handle_panel_event(self, event) -> bool:
        """Handle panel-specific events."""
        # Forward to buttons
        if self._clear_btn and self._clear_btn.handle_event(event):
            return True
        if self._mute_btn and self._mute_btn.handle_event(event):
            return True
        for btn in self._filter_buttons.values():
            if btn.handle_event(event):
                return True

        # Forward to scroll container
        if self._scroll_container and self._scroll_container.handle_event(event):
            return True

        return False


__all__ = ["NoticeDialog", "NoticeMessage", "MessageSeverity"]
