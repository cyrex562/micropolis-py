"""Simple in-game overlay for viewing and remapping keybindings."""

from __future__ import annotations

import logging
from typing import Any

import pygame

from .input_bindings import InputAction, InputBindingManager, InputChord

logger = logging.getLogger(__name__)

_OVERLAY_ALPHA = (0, 0, 0, 180)
_PANEL_COLOR = (20, 28, 46, 232)
_PANEL_OUTLINE = (70, 120, 200)
_ROW_BG = (36, 54, 86, 200)
_TEXT_COLOR = (230, 235, 245)
_SUBTLE_TEXT = (160, 170, 185)
_ACCENT_COLOR = (127, 196, 255)
_STATUS_BG = (15, 22, 34, 230)


class KeybindingsOverlay:
    """Modal overlay that lists keybindings and supports remapping."""

    def __init__(self, manager: InputBindingManager) -> None:
        self._manager = manager
        self.visible = False
        self._selected_index = 0
        self._top_index = 0
        self._page_size = 10
        self._row_height = 32
        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._bold_font: pygame.font.Font | None = None
        self._status = "Press Enter to remap, Delete to clear, R to reset."
        self._actions: list[InputAction] = manager.actions()
        self._capturing_action: str | None = None
        manager.register_change_listener(self._handle_binding_change)

    # ------------------------------------------------------------------
    def toggle(self) -> None:
        if self.visible:
            self.hide()
        else:
            self.show()

    def show(self) -> None:
        self.visible = True
        self._status = "Use arrow keys to select an action."
        self._refresh_cache()

    def hide(self) -> None:
        self.visible = False
        self._cancel_capture()

    # ------------------------------------------------------------------
    def handle_event(self, event: Any) -> bool:
        if not self.visible:
            return False
        event_type = getattr(event, "type", None)
        if event_type == pygame.KEYDOWN:
            return self._handle_keydown(event)
        if event_type == pygame.MOUSEWHEEL:
            return self._handle_mousewheel(event)
        if event_type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        self._ensure_fonts()
        width, height = surface.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill(_OVERLAY_ALPHA)
        surface.blit(overlay, (0, 0))
        panel_rect = pygame.Rect(
            int(width * 0.08),
            int(height * 0.08),
            int(width * 0.84),
            int(height * 0.84),
        )
        pygame.draw.rect(surface, _PANEL_COLOR, panel_rect, border_radius=12)
        pygame.draw.rect(surface, _PANEL_OUTLINE, panel_rect, width=2, border_radius=12)

        padding = 24
        header_y = panel_rect.top + padding
        self._draw_text(
            surface,
            "Keybindings",
            (panel_rect.left + padding, header_y),
            bold=True,
        )
        self._draw_text(
            surface,
            "Enter: remap  ·  Delete: clear  ·  R: reset  ·  Esc: close",
            (panel_rect.left + padding, header_y + 28),
            color=_SUBTLE_TEXT,
        )
        list_top = header_y + 56
        list_height = panel_rect.height - (list_top - panel_rect.top) - 100
        self._page_size = max(5, list_height // self._row_height)
        self._ensure_scroll_bounds()
        self._render_list(
            surface,
            pygame.Rect(
                panel_rect.left + padding,
                list_top,
                panel_rect.width - (padding * 2),
                self._page_size * self._row_height,
            ),
        )
        status_rect = pygame.Rect(
            panel_rect.left + padding,
            panel_rect.bottom - padding - 48,
            panel_rect.width - (padding * 2),
            48,
        )
        pygame.draw.rect(surface, _STATUS_BG, status_rect, border_radius=8)
        self._draw_text(
            surface,
            self._status,
            (status_rect.left + 12, status_rect.top + 12),
            color=_ACCENT_COLOR if self._capturing_action else _TEXT_COLOR,
        )

    # ------------------------------------------------------------------
    def _render_list(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        actions = self._actions[self._top_index : self._top_index + self._page_size]
        for idx, action in enumerate(actions):
            row_rect = pygame.Rect(
                rect.left,
                rect.top + idx * self._row_height,
                rect.width,
                self._row_height - 4,
            )
            absolute_index = self._top_index + idx
            if absolute_index == self._selected_index:
                pygame.draw.rect(surface, _ROW_BG, row_rect, border_radius=6)
            label = f"{action.label}"
            binding = (
                ", ".join([self._format_binding(ch) for ch in action.bindings])
                or "Unbound"
            )
            category = action.category.title()
            self._draw_text(
                surface,
                label,
                (row_rect.left + 12, row_rect.top + 4),
                bold=absolute_index == self._selected_index,
            )
            self._draw_text(
                surface,
                category,
                (row_rect.left + 12, row_rect.top + 18),
                color=_SUBTLE_TEXT,
            )
            binding_color = _ACCENT_COLOR if binding != "Unbound" else _SUBTLE_TEXT
            binding_surface = self._get_small_font().render(
                binding,
                True,
                binding_color,
            )
            surface.blit(
                binding_surface,
                (
                    row_rect.right - binding_surface.get_width() - 12,
                    row_rect.top + (self._row_height // 2) - 8,
                ),
            )

    def _draw_text(
        self,
        surface: pygame.Surface,
        text: str,
        position: tuple[int, int],
        *,
        color: tuple[int, int, int] = _TEXT_COLOR,
        bold: bool = False,
    ) -> None:
        font = self._get_font(bold=bold)
        surface.blit(font.render(text, True, color), position)

    # ------------------------------------------------------------------
    def _handle_keydown(self, event: Any) -> bool:
        key = getattr(event, "key", None)
        if key is None:
            return False
        if key == pygame.K_ESCAPE:
            if self._capturing_action:
                self._cancel_capture()
            else:
                self.hide()
            return True
        if self._capturing_action:
            return False  # allow manager to capture keystroke
        if key in (pygame.K_UP, pygame.K_k):
            self._move_selection(-1)
            return True
        if key in (pygame.K_DOWN, pygame.K_j):
            self._move_selection(1)
            return True
        if key == pygame.K_PAGEUP:
            self._move_selection(-self._page_size)
            return True
        if key == pygame.K_PAGEDOWN:
            self._move_selection(self._page_size)
            return True
        if key == pygame.K_HOME:
            self._selected_index = 0
            self._ensure_visible()
            return True
        if key == pygame.K_END:
            self._selected_index = len(self._actions) - 1
            self._ensure_visible()
            return True
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._begin_capture()
            return True
        if key == pygame.K_DELETE:
            self._clear_binding()
            return True
        if key == pygame.K_r:
            self._reset_binding()
            return True
        return False

    def _handle_mousewheel(self, event: Any) -> bool:
        delta = int(getattr(event, "y", 0))
        if not delta:
            return False
        self._top_index = max(0, self._top_index - delta)
        max_top = max(0, len(self._actions) - self._page_size)
        self._top_index = min(self._top_index, max_top)
        return True

    # ------------------------------------------------------------------
    def _begin_capture(self) -> None:
        if not self._actions:
            return
        action = self._actions[self._selected_index]
        self._capturing_action = action.action_id
        self._status = f"Press new binding for {action.label}"
        self._manager.request_capture(action.action_id, self._on_capture_complete)

    def _cancel_capture(self) -> None:
        if self._capturing_action is None:
            return
        self._manager.cancel_capture()
        self._capturing_action = None
        self._status = "Capture cancelled."

    def _on_capture_complete(self, chord: InputChord) -> None:
        action = (
            self._manager.get_action(self._capturing_action)
            if self._capturing_action
            else None
        )
        self._capturing_action = None
        binding = self._format_binding(chord)
        if action:
            self._status = f"Bound {action.label} to {binding}"
        else:
            self._status = f"Bound to {binding}"
        self._refresh_cache()

    def _clear_binding(self) -> None:
        if not self._actions:
            return
        action = self._actions[self._selected_index]
        self._manager.remap_action(action.action_id, [])
        self._status = f"Cleared bindings for {action.label}"

    def _reset_binding(self) -> None:
        if not self._actions:
            return
        action = self._actions[self._selected_index]
        self._manager.restore_defaults(action.action_id)
        self._status = f"Restored defaults for {action.label}"

    # ------------------------------------------------------------------
    def _move_selection(self, delta: int) -> None:
        if not self._actions:
            return
        self._selected_index = max(
            0, min(len(self._actions) - 1, self._selected_index + delta)
        )
        self._ensure_visible()

    def _ensure_visible(self) -> None:
        if self._selected_index < self._top_index:
            self._top_index = self._selected_index
        elif self._selected_index >= self._top_index + self._page_size:
            self._top_index = self._selected_index - self._page_size + 1

    def _handle_binding_change(self, _: InputAction) -> None:
        self._refresh_cache()

    def _refresh_cache(self) -> None:
        self._actions = self._manager.actions()
        if self._selected_index >= len(self._actions):
            self._selected_index = max(0, len(self._actions) - 1)
        self._ensure_visible()

    def _ensure_fonts(self) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        if self._font is None:
            self._font = pygame.font.SysFont("DejaVu Sans", 18)
        if self._bold_font is None:
            self._bold_font = pygame.font.SysFont("DejaVu Sans", 18, bold=True)
        if self._small_font is None:
            self._small_font = pygame.font.SysFont("DejaVu Sans", 14)

    def _get_font(self, *, bold: bool = False) -> pygame.font.Font:
        self._ensure_fonts()
        font = self._bold_font if bold else self._font
        assert font is not None
        return font

    def _get_small_font(self) -> pygame.font.Font:
        self._ensure_fonts()
        assert self._small_font is not None
        return self._small_font

    def _format_binding(self, chord: InputChord) -> str:
        return chord.signature().replace("+", " + ")

    def _ensure_scroll_bounds(self) -> None:
        max_top = max(0, len(self._actions) - self._page_size)
        self._top_index = max(0, min(self._top_index, max_top))

    @property
    def is_capturing(self) -> bool:
        return self._capturing_action is not None


__all__ = ["KeybindingsOverlay"]
