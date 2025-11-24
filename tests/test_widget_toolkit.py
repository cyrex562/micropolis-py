from __future__ import annotations

import math
import pygame

from micropolis.ui.widgets import (
    Button,
    Checkbox,
    ModalDialog,
    PaletteGrid,
    PaletteItem,
    RecordingRenderer,
    ScrollContainer,
    Slider,
    TextLabel,
    Theme,
    ThemeMetrics,
    ThemePalette,
    ToggleButton,
    Tooltip,
    UIEvent,
    UIWidget,
)


class DummyWidget(UIWidget):
    def __init__(self, rect=(0, 0, 100, 100)) -> None:
        super().__init__(rect=rect)
        self.received: list[str] = []

    def on_event(self, event: UIEvent) -> bool:
        self.received.append(event.type)
        return True


def mouse_event(event_type: str, x: int, y: int, button: int | None = None) -> UIEvent:
    return UIEvent(type=event_type, position=(x, y), button=button)


def key_event(event_type: str, key: int) -> UIEvent:
    return UIEvent(type=event_type, key=key)


def test_button_click_and_hover_state() -> None:
    clicks: list[str] = []
    button = Button(
        label="Save",
        rect=(0, 0, 100, 30),
        on_click=lambda _: clicks.append("clicked"),
    )

    assert button.handle_event(mouse_event("mouse_move", 10, 10)) is True
    assert button.handle_event(mouse_event("mouse_down", 10, 10, button=1)) is True
    assert button.handle_event(mouse_event("mouse_up", 10, 10, button=1)) is True

    assert clicks == ["clicked"]

    renderer = RecordingRenderer()
    button.render(renderer)
    assert any(
        cmd.name == "text" and cmd.payload["text"] == "Save"
        for cmd in renderer.commands
    )


def test_toggle_button_and_checkbox_emit_toggle_events() -> None:
    toggles: list[bool] = []
    toggle = ToggleButton(
        label="Auto",
        rect=(0, 0, 80, 24),
        on_toggle=lambda _, state: toggles.append(state),
    )

    toggle.handle_event(mouse_event("mouse_down", 5, 5, button=1))
    toggle.handle_event(mouse_event("mouse_up", 5, 5, button=1))
    toggle.handle_event(mouse_event("mouse_down", 5, 5, button=1))
    toggle.handle_event(mouse_event("mouse_up", 5, 5, button=1))

    assert toggles == [True, False]

    checkbox_state: list[bool] = []
    checkbox = Checkbox(
        "Power",
        rect=(0, 0, 160, 32),
        on_toggle=lambda _, state: checkbox_state.append(state),
    )
    checkbox.handle_event(mouse_event("mouse_down", 10, 10, button=1))
    checkbox.handle_event(mouse_event("mouse_up", 10, 10, button=1))
    assert checkbox_state == [True]


def test_slider_changes_value_with_mouse_and_keys() -> None:
    values: list[float] = []
    slider = Slider(
        rect=(0, 0, 200, 20),
        min_value=0.0,
        max_value=100.0,
        step=5.0,
        on_change=lambda _, value: values.append(value),
    )

    slider.handle_event(mouse_event("mouse_down", 150, 10, button=1))
    slider.handle_event(mouse_event("mouse_move", 190, 10, button=1))
    slider.handle_event(mouse_event("mouse_up", 190, 10, button=1))
    slider.handle_event(key_event("key_down", pygame.K_LEFT))  # left arrow

    assert math.isclose(slider.value, 90.0)
    assert values  # at least one change recorded


def test_scroll_container_clamps_and_moves_content() -> None:
    viewport = ScrollContainer(rect=(0, 0, 100, 100))
    content = DummyWidget(rect=(0, 0, 300, 200))
    viewport.set_content(content)

    viewport.scroll_by(150, 80)
    assert viewport.content.rect[0] == -150
    assert viewport.content.rect[1] == -80

    viewport.handle_event(UIEvent(type="scroll", scroll_delta=(0, -40)))
    assert viewport.content.rect[1] <= -40


def test_modal_dialog_dismiss_on_background_click() -> None:
    modal = ModalDialog(rect=(0, 0, 400, 300))
    modal.set_content(TextLabel("Hello", rect=(0, 0, 100, 40)))
    modal.open()
    assert modal.is_open is True

    modal.handle_event(mouse_event("mouse_down", 399, 10, button=1))
    assert modal.is_open is False


def test_palette_grid_selection_skips_disabled_items() -> None:
    selected: list[str] = []
    grid = PaletteGrid(
        rect=(0, 0, 200, 200),
        columns=2,
        items=[
            PaletteItem("road", "Road"),
            PaletteItem("rail", "Rail", enabled=False),
            PaletteItem("wire", "Wire"),
        ],
        on_select=lambda item: selected.append(item.item_id),
    )

    grid.handle_event(mouse_event("mouse_down", 20, 20, button=1))
    grid.handle_event(mouse_event("mouse_down", 90, 20, button=1))  # disabled slot
    grid.handle_event(mouse_event("mouse_down", 20, 80, button=1))

    assert selected == ["road", "wire"]
    assert grid.selected_id == "wire"


def test_tooltip_delay_controls_visibility() -> None:
    tooltip = Tooltip(delay_ms=200)
    tooltip.queue("Funds", (0, 0, 40, 20))
    tooltip.update(0.05)
    assert tooltip.is_visible is False
    tooltip.update(0.20)
    assert tooltip.is_visible is True


def test_theme_can_be_overridden_per_widget() -> None:
    custom_theme = Theme(
        name="Test",
        palette=ThemePalette(accent=(255, 0, 0, 255)),
        metrics=ThemeMetrics(font_name="Fira", font_size=12),
    )
    button = Button(label="Apply")
    button.set_theme(custom_theme)
    renderer = RecordingRenderer()
    button.render(renderer)
    assert renderer.commands  # ensure render occurred without errors
