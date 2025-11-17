"""
file_dialog.py - File picker dialog panel for Micropolis pygame UI

This panel implements the pygame-native file picker with recent cities list,
thumbnails (generated from city snapshots), and quick scenario load buttons.
Provides text entry for city name and location.

Ported from wfile.tcl
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

try:
    import pygame
except ImportError:
    pygame = None  # type: ignore

from micropolis.context import AppContext
from micropolis.ui.uipanel import UIPanel
from micropolis.ui.widgets.base import UIWidget
from micropolis.ui.widgets.button import Button
from micropolis.ui.widgets.scroll import ScrollContainer

if TYPE_CHECKING:
    from micropolis.ui.panel_manager import PanelManager


@dataclass
class CityFile:
    """Represents a city file entry."""

    name: str
    path: str
    last_modified: float
    thumbnail: pygame.Surface | None = None


class CityThumbnail(UIWidget):
    """Widget that displays a city thumbnail."""

    def __init__(
        self,
        city_file: CityFile,
        on_select: callable | None = None,
        rect: tuple[int, int, int, int] = (0, 0, 120, 140),
    ) -> None:
        super().__init__(widget_id=f"thumb_{city_file.name}", rect=rect)
        self.city_file = city_file
        self.on_select_callback = on_select
        self._is_selected = False

    def on_render(self, renderer) -> None:
        """Render the thumbnail."""
        if not pygame:
            return

        x, y, w, h = self.rect

        # Background
        bg_color = (80, 80, 150) if self._is_selected else (50, 50, 50)
        renderer.draw_rect(
            self.rect, bg_color, border=True, border_color=(100, 100, 100)
        )

        # Thumbnail image
        if self.city_file.thumbnail:
            thumb_rect = (x + 10, y + 10, w - 20, h - 40)
            try:
                if hasattr(renderer, "_surface"):
                    scaled_thumb = pygame.transform.scale(
                        self.city_file.thumbnail, (thumb_rect[2], thumb_rect[3])
                    )
                    renderer._surface.blit(scaled_thumb, thumb_rect[:2])
            except Exception:
                pass

        # City name label
        try:
            font = pygame.font.Font(None, 16)
            text = self.city_file.name
            if len(text) > 12:
                text = text[:9] + "..."

            text_surface = font.render(text, True, (255, 255, 255))
            text_rect = text_surface.get_rect()
            text_rect.centerx = x + w // 2
            text_rect.bottom = y + h - 5

            if hasattr(renderer, "_surface"):
                renderer._surface.blit(text_surface, text_rect)
        except Exception:
            pass

    def handle_event(self, event) -> bool:
        """Handle thumbnail click."""
        if pygame and event.type == pygame.MOUSEBUTTONDOWN:
            if self._is_inside(event.pos):
                self._is_selected = True
                if self.on_select_callback:
                    self.on_select_callback(self.city_file)
                self.invalidate()
                return True
        return False

    def _is_inside(self, pos: tuple[int, int]) -> bool:
        """Check if position is inside widget."""
        x, y, w, h = self.rect
        px, py = pos
        return x <= px <= x + w and y <= py <= y + h

    def set_selected(self, selected: bool) -> None:
        """Set selection state."""
        if self._is_selected != selected:
            self._is_selected = selected
            self.invalidate()


class FileDialog(UIPanel):
    """File picker dialog panel."""

    def __init__(
        self,
        manager: PanelManager,
        context: AppContext,
        mode: str = "load",  # "load" or "save"
    ) -> None:
        super().__init__(manager, context)
        self.panel_id = f"file_dialog_{mode}"
        self.legacy_name = "file"
        self.mode = mode

        # File state
        self._city_files: list[CityFile] = []
        self._selected_file: CityFile | None = None
        self._current_directory: Path = self._get_default_city_dir()

        # UI components
        self._scroll_container: ScrollContainer | None = None
        self._thumbnail_container: UIWidget | None = None
        self._filename_input: UIWidget | None = None
        self._load_btn: Button | None = None
        self._cancel_btn: Button | None = None
        self._recent_btn: Button | None = None

        # Input state
        self._filename_text: str = ""

    def _get_default_city_dir(self) -> Path:
        """Get the default cities directory."""
        # Try context first
        if hasattr(self.context, "city_dir") and self.context.city_dir:
            return Path(self.context.city_dir)

        # Fallback to cities/ directory
        base_dir = Path(__file__).parent.parent.parent.parent.parent
        cities_dir = base_dir / "cities"
        if cities_dir.exists():
            return cities_dir

        # Last resort: current directory
        return Path.cwd()

    def did_mount(self) -> None:
        """Initialize UI components when panel mounts."""
        self._setup_ui()
        self._scan_city_files()

    def _setup_ui(self) -> None:
        """Set up the file dialog UI layout."""
        x, y, w, h = self.rect

        # Title
        title_text = "Load City" if self.mode == "load" else "Save City"

        # Buttons at bottom
        button_height = 40
        button_width = 120
        button_y = y + h - button_height - 10

        self._cancel_btn = Button(
            text="Cancel",
            rect=(x + w - button_width - 10, button_y, button_width, 35),
            on_click=self._handle_cancel,
        )

        action_text = "Load" if self.mode == "load" else "Save"
        self._load_btn = Button(
            text=action_text,
            rect=(x + w - 2 * button_width - 20, button_y, button_width, 35),
            on_click=self._handle_action,
        )

        # Recent cities button
        self._recent_btn = Button(
            text="Recent",
            rect=(x + 10, button_y, button_width, 35),
            on_click=self._handle_show_recent,
        )

        # Filename input for save mode
        if self.mode == "save":
            input_y = button_y - 50
            # Create a simple input widget (would need proper text input widget)
            from micropolis.ui.widgets.label import TextLabel

            self._filename_input = TextLabel(
                text=self._filename_text,
                rect=(x + 10, input_y, w - 20, 35),
                color=(255, 255, 255, 255),
            )

        # Scroll container for thumbnails
        scroll_height = h - button_height - (70 if self.mode == "save" else 20) - 40
        scroll_rect = (x + 10, y + 40, w - 20, scroll_height)
        self._scroll_container = ScrollContainer(rect=scroll_rect)

        # Container for thumbnail grid
        self._thumbnail_container = UIWidget(
            widget_id="thumbnail_container", rect=(0, 0, w - 40, 200)
        )
        self._scroll_container.set_content(self._thumbnail_container)

    def _scan_city_files(self) -> None:
        """Scan the cities directory for .cty files."""
        self._city_files.clear()

        if not self._current_directory.exists():
            return

        # Find all .cty files
        for cty_file in self._current_directory.glob("*.cty"):
            city_file = CityFile(
                name=cty_file.stem,
                path=str(cty_file),
                last_modified=cty_file.stat().st_mtime,
                thumbnail=None,
            )
            # TODO: Generate thumbnail from city file
            # city_file.thumbnail = self._generate_thumbnail(cty_file)
            self._city_files.append(city_file)

        # Sort by last modified (newest first)
        self._city_files.sort(key=lambda f: f.last_modified, reverse=True)

        self._layout_thumbnails()

    def _layout_thumbnails(self) -> None:
        """Layout thumbnail grid."""
        if not self._thumbnail_container:
            return

        # Clear existing thumbnails
        for child in list(self._thumbnail_container.children):
            self._thumbnail_container.remove_child(child)

        # Grid layout
        thumb_width = 120
        thumb_height = 140
        thumb_spacing = 10
        columns = max(1, (self.rect[2] - 40) // (thumb_width + thumb_spacing))

        row = 0
        col = 0

        for city_file in self._city_files:
            x = col * (thumb_width + thumb_spacing)
            y = row * (thumb_height + thumb_spacing)

            thumbnail = CityThumbnail(
                city_file=city_file,
                on_select=self._handle_thumbnail_select,
                rect=(x, y, thumb_width, thumb_height),
            )
            self._thumbnail_container.add_child(thumbnail)

            col += 1
            if col >= columns:
                col = 0
                row += 1

        # Update container height
        total_rows = (len(self._city_files) + columns - 1) // columns
        container_height = total_rows * (thumb_height + thumb_spacing) + thumb_spacing
        self._thumbnail_container.resize_to(self.rect[2] - 40, container_height)
        self.invalidate()

    def _handle_thumbnail_select(self, city_file: CityFile) -> None:
        """Handle thumbnail selection."""
        # Deselect all other thumbnails
        if self._thumbnail_container:
            for child in self._thumbnail_container.children:
                if isinstance(child, CityThumbnail):
                    child.set_selected(child.city_file == city_file)

        self._selected_file = city_file

        # Update filename input for save mode
        if self.mode == "save" and self._filename_input:
            self._filename_text = city_file.name
            self._filename_input.text = self._filename_text
            self._filename_input.invalidate()

    def _handle_action(self) -> None:
        """Handle Load/Save button click."""
        if self.mode == "load":
            if self._selected_file:
                # Trigger load city event
                if hasattr(self.context, "event_bus"):
                    self.context.event_bus.publish(
                        "city.load", {"path": self._selected_file.path}
                    )
                self.hide()
        else:  # save mode
            if self._filename_text.strip():
                # Construct save path
                filename = self._filename_text.strip()
                if not filename.endswith(".cty"):
                    filename += ".cty"
                save_path = self._current_directory / filename

                # Trigger save city event
                if hasattr(self.context, "event_bus"):
                    self.context.event_bus.publish(
                        "city.save", {"path": str(save_path)}
                    )
                self.hide()

    def _handle_cancel(self) -> None:
        """Handle Cancel button click."""
        self.hide()

    def _handle_show_recent(self) -> None:
        """Handle Recent button click."""
        # Show only recently modified files
        self._city_files = [f for f in self._city_files[:10]]
        self._layout_thumbnails()

    def handle_text_input(self, text: str) -> None:
        """Handle text input for filename field (save mode)."""
        if self.mode == "save":
            self._filename_text += text
            if self._filename_input:
                self._filename_input.text = self._filename_text
                self._filename_input.invalidate()

    def handle_backspace(self) -> None:
        """Handle backspace in filename field."""
        if self.mode == "save" and self._filename_text:
            self._filename_text = self._filename_text[:-1]
            if self._filename_input:
                self._filename_input.text = self._filename_text
                self._filename_input.invalidate()

    def draw(self, surface) -> None:
        """Render the file dialog."""
        if not self.visible:
            return

        # Render background
        if pygame:
            bg_color = (40, 40, 40)
            pygame.draw.rect(surface, bg_color, self.rect)
            pygame.draw.rect(surface, (100, 100, 100), self.rect, 2)

        # Title
        try:
            font = pygame.font.Font(None, 32)
            title_text = "Load City" if self.mode == "load" else "Save City"
            text_surface = font.render(title_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect()
            text_rect.topleft = (self.rect[0] + 10, self.rect[1] + 10)
            surface.blit(text_surface, text_rect)
        except Exception:
            pass

        # Render scroll container
        if self._scroll_container:
            self._scroll_container.render(surface)

        # Render filename input (save mode)
        if self.mode == "save" and self._filename_input:
            self._filename_input.render(surface)

        # Render buttons
        if self._load_btn:
            self._load_btn.render(surface)
        if self._cancel_btn:
            self._cancel_btn.render(surface)
        if self._recent_btn:
            self._recent_btn.render(surface)

    def handle_panel_event(self, event) -> bool:
        """Handle panel-specific events."""
        # Handle text input for filename field (save mode)
        if self.mode == "save" and pygame and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                self._handle_action()
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.handle_backspace()
                return True
            elif event.unicode and event.unicode.isprintable():
                self.handle_text_input(event.unicode)
                return True

        # Forward to buttons
        if self._load_btn and self._load_btn.handle_event(event):
            return True
        if self._cancel_btn and self._cancel_btn.handle_event(event):
            return True
        if self._recent_btn and self._recent_btn.handle_event(event):
            return True

        # Forward to scroll container
        if self._scroll_container and self._scroll_container.handle_event(event):
            return True

        # Forward to thumbnails
        if self._thumbnail_container:
            for child in self._thumbnail_container.children:
                if child.handle_event(event):
                    return True

        return False


__all__ = ["FileDialog", "CityFile"]
