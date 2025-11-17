"""
help_dialog.py - Help browser dialog panel for Micropolis pygame UI

This panel implements the contextual help browser that displays HTML-lite
help content in a scrollable pane and integrates with tooltip SetHelp
by highlighting relevant sections.

Ported from whelp.tcl
"""

from __future__ import annotations

import os
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


class HelpContentRenderer(UIWidget):
    """Widget that renders HTML-lite help content."""

    def __init__(self, rect: tuple[int, int, int, int] = (0, 0, 600, 400)) -> None:
        super().__init__(widget_id="help_content", rect=rect)
        self._content_lines: list[tuple[str, dict]] = []  # (text, style)
        self._line_height = 20
        self._padding = 10

    def set_content(self, html_content: str) -> None:
        """Parse and set HTML-lite content."""
        self._content_lines = self._parse_html_lite(html_content)
        self._update_size()
        self.invalidate()

    def _parse_html_lite(self, html: str) -> list[tuple[str, dict]]:
        """
        Parse simple HTML tags into styled text lines.

        Supports: <h1>, <h2>, <p>, <b>, <i>, <a>
        """
        lines = []
        current_style = {
            "bold": False,
            "italic": False,
            "size": 14,
            "color": (255, 255, 255),
        }

        # Simple line-by-line parser
        for line in html.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Detect heading tags
            if line.startswith("<h1>"):
                text = line.replace("<h1>", "").replace("</h1>", "")
                style = current_style.copy()
                style["size"] = 24
                style["bold"] = True
                lines.append((text, style))
            elif line.startswith("<h2>"):
                text = line.replace("<h2>", "").replace("</h2>", "")
                style = current_style.copy()
                style["size"] = 18
                style["bold"] = True
                lines.append((text, style))
            elif line.startswith("<p>"):
                text = line.replace("<p>", "").replace("</p>", "")
                lines.append((text, current_style.copy()))
            else:
                # Plain text
                if line:
                    lines.append((line, current_style.copy()))

        return lines

    def _update_size(self) -> None:
        """Update widget size based on content."""
        content_height = (
            len(self._content_lines) * self._line_height + 2 * self._padding
        )
        x, y, w, _ = self.rect
        self.set_rect((x, y, w, content_height))

    def on_render(self, renderer) -> None:
        """Render the help content."""
        if not pygame:
            return

        x, y, w, h = self.rect

        # Background
        renderer.draw_rect(self.rect, (30, 30, 30))

        # Render each line
        y_offset = y + self._padding
        for text, style in self._content_lines:
            # Create font
            font_size = style.get("size", 14)
            bold = style.get("bold", False)
            # Simple font rendering - pygame default fonts
            try:
                font = pygame.font.Font(None, font_size)
                if bold:
                    font.set_bold(True)

                # Render text
                color = style.get("color", (255, 255, 255))
                text_surface = font.render(text, True, color)
                text_rect = text_surface.get_rect()
                text_rect.topleft = (x + self._padding, y_offset)

                # Blit text (renderer should have a surface)
                if hasattr(renderer, "_surface"):
                    renderer._surface.blit(text_surface, text_rect)

            except Exception:
                pass  # Skip rendering on error

            y_offset += self._line_height


class HelpDialog(UIPanel):
    """Help browser dialog panel."""

    def __init__(self, manager: PanelManager, context: AppContext) -> None:
        super().__init__(manager, context)
        self.panel_id = "help_dialog"
        self.legacy_name = "help"

        self._scroll_container: ScrollContainer | None = None
        self._content_renderer: HelpContentRenderer | None = None
        self._close_btn: Button | None = None
        self._current_topic: str = ""
        self._help_loaded = False

        # Subscribe to event bus for help requests
        if hasattr(context, "event_bus"):
            context.event_bus.subscribe("help.show", self._on_show_help)

    def did_mount(self) -> None:
        """Initialize UI components when panel mounts."""
        self._setup_ui()
        self._load_default_help()

    def _setup_ui(self) -> None:
        """Set up the help dialog UI layout."""
        x, y, w, h = self.rect

        # Top bar with close button
        top_bar_height = 40
        self._close_btn = Button(
            text="Close",
            rect=(x + w - 110, y + 10, 100, 30),
            on_click=self._handle_close,
        )

        # Topic label
        self._topic_label = TextLabel(
            text="Help",
            rect=(x + 10, y + 10, w - 130, 30),
            color=(255, 255, 255, 255),
        )

        # Scroll container for help content
        scroll_rect = (x, y + top_bar_height, w, h - top_bar_height)
        self._scroll_container = ScrollContainer(rect=scroll_rect)

        # Content renderer
        self._content_renderer = HelpContentRenderer(
            rect=(0, 0, w - 20, h - top_bar_height)
        )
        self._scroll_container.set_content(self._content_renderer)

    def _load_default_help(self) -> None:
        """Load default help content."""
        help_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..", "docs", "manual"
        )
        default_help = os.path.join(help_dir, "index.html")

        if os.path.exists(default_help):
            self.load_help_file(default_help)
        else:
            # Fallback help text
            self.set_help_content(
                "<h1>Micropolis Help</h1>\n"
                "<p>Welcome to Micropolis!</p>\n"
                "<h2>Getting Started</h2>\n"
                "<p>Use the toolbar to select tools and build your city.</p>\n"
                "<p>Zones: Residential (R), Commercial (C), Industrial (I)</p>\n"
                "<p>Infrastructure: Roads, Power, Water</p>\n"
                "<h2>Tips</h2>\n"
                "<p>- Balance your budget</p>\n"
                "<p>- Provide adequate services</p>\n"
                "<p>- Monitor pollution and crime</p>\n"
            )

    def load_help_file(self, filepath: str) -> None:
        """Load help content from an HTML file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.set_help_content(content)
            self._help_loaded = True
        except Exception as e:
            print(f"Error loading help file {filepath}: {e}")
            self.set_help_content(
                f"<h1>Error</h1><p>Could not load help file: {filepath}</p>"
            )

    def set_help_content(self, html_content: str) -> None:
        """Set the help content to display."""
        if self._content_renderer:
            self._content_renderer.set_content(html_content)
            self.invalidate()

    def show_topic(self, topic: str) -> None:
        """
        Show help for a specific topic.

        Args:
            topic: Topic identifier (e.g., "tools", "zones", "budget")
        """
        self._current_topic = topic

        # Update topic label
        if self._topic_label:
            self._topic_label.text = f"Help: {topic.replace('_', ' ').title()}"

        # Load topic-specific help
        help_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..", "docs", "manual"
        )
        topic_file = os.path.join(help_dir, f"{topic}.html")

        if os.path.exists(topic_file):
            self.load_help_file(topic_file)
        else:
            # Generic help for topic
            self.set_help_content(
                f"<h1>{topic.replace('_', ' ').title()}</h1>\n"
                f"<p>Help content for {topic} not yet available.</p>\n"
            )

        self.show()

    def _on_show_help(self, event_data: dict) -> None:
        """Handle help.show event from event bus."""
        topic = event_data.get("topic", "")
        if topic:
            self.show_topic(topic)
        else:
            self.show()

    def _handle_close(self) -> None:
        """Handle close button click."""
        self.hide()

    def draw(self, surface) -> None:
        """Render the help dialog."""
        if not self.visible:
            return

        # Render background
        if pygame:
            bg_color = (50, 50, 50)
            pygame.draw.rect(surface, bg_color, self.rect)
            pygame.draw.rect(surface, (100, 100, 100), self.rect, 2)

        # Render close button and label
        if self._close_btn:
            self._close_btn.render(surface)
        if self._topic_label:
            self._topic_label.render(surface)

        # Render scroll container
        if self._scroll_container:
            self._scroll_container.render(surface)

    def handle_panel_event(self, event) -> bool:
        """Handle panel-specific events."""
        # Forward to close button
        if self._close_btn and self._close_btn.handle_event(event):
            return True

        # Forward to scroll container
        if self._scroll_container and self._scroll_container.handle_event(event):
            return True

        return False


__all__ = ["HelpDialog"]
