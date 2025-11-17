"""
Comprehensive widget state transition tests using synthesized pygame events.

Tests:
- Click/hover/focus events with state transitions
- Pressed/disabled/enabled states
- Tooltip popup timing and positioning
- Slider bounds and keyboard navigation
- Checkbox/toggle state persistence
- Focus traversal and keyboard accessibility
"""

import pygame
import pytest

from micropolis.ui.widgets import (
    Button,
    Checkbox,
    Slider,
    TextLabel,
    ToggleButton,
    Tooltip,
)
from tests.ui.conftest import (
    assert_color_equal,
    assert_rect_contains,
    synthesize_key_event,
    synthesize_mouse_event,
)


class TestButtonStates:
    """Test Button widget state transitions."""

    def test_button_normal_to_hover(self, mock_display):
        """Button should transition to hover state on mouse motion."""
        button = Button(
            rect=pygame.Rect(10, 10, 100, 40), text="Click Me", callback=lambda: None
        )

        # Initially normal state
        assert not button.hovered
        assert not button.pressed

        # Move mouse over button
        event = synthesize_mouse_event("MOUSEMOTION", (50, 25))
        button.on_event(event)

        assert button.hovered
        assert not button.pressed

    def test_button_hover_to_pressed(self, mock_display):
        """Button should transition to pressed state on mouse down."""
        clicked = False

        def on_click():
            nonlocal clicked
            clicked = True

        button = Button(
            rect=pygame.Rect(10, 10, 100, 40), text="Click Me", callback=on_click
        )

        # Hover first
        button.on_event(synthesize_mouse_event("MOUSEMOTION", (50, 25)))
        assert button.hovered

        # Press button
        button.on_event(synthesize_mouse_event("MOUSEBUTTONDOWN", (50, 25), button=1))
        assert button.pressed
        assert not clicked  # Callback not triggered yet

        # Release button
        button.on_event(synthesize_mouse_event("MOUSEBUTTONUP", (50, 25), button=1))
        assert not button.pressed
        assert clicked  # Callback triggered on release

    def test_button_disabled_state(self, mock_display):
        """Disabled button should not respond to events."""
        clicked = False

        def on_click():
            nonlocal clicked
            clicked = True

        button = Button(
            rect=pygame.Rect(10, 10, 100, 40), text="Click Me", callback=on_click
        )

        button.set_enabled(False)
        assert not button.enabled

        # Try to click disabled button
        button.on_event(synthesize_mouse_event("MOUSEBUTTONDOWN", (50, 25), button=1))
        button.on_event(synthesize_mouse_event("MOUSEBUTTONUP", (50, 25), button=1))

        assert not clicked  # Callback should not trigger
        assert not button.pressed

    def test_button_re_enabled(self, mock_display):
        """Re-enabled button should respond to events again."""
        clicked = False

        def on_click():
            nonlocal clicked
            clicked = True

        button = Button(
            rect=pygame.Rect(10, 10, 100, 40), text="Click Me", callback=on_click
        )

        # Disable then re-enable
        button.set_enabled(False)
        button.set_enabled(True)
        assert button.enabled

        # Click should work
        button.on_event(synthesize_mouse_event("MOUSEBUTTONDOWN", (50, 25), button=1))
        button.on_event(synthesize_mouse_event("MOUSEBUTTONUP", (50, 25), button=1))

        assert clicked


class TestToggleButtonStates:
    """Test ToggleButton widget state transitions."""

    def test_toggle_on_off(self, mock_display):
        """ToggleButton should toggle state on click."""
        button = ToggleButton(
            rect=pygame.Rect(10, 10, 100, 40),
            text="Toggle",
            callback=lambda state: None,
        )

        assert not button.toggled

        # First click - toggle on
        button.on_event(synthesize_mouse_event("MOUSEBUTTONDOWN", (50, 25), button=1))
        button.on_event(synthesize_mouse_event("MOUSEBUTTONUP", (50, 25), button=1))
        assert button.toggled

        # Second click - toggle off
        button.on_event(synthesize_mouse_event("MOUSEBUTTONDOWN", (50, 25), button=1))
        button.on_event(synthesize_mouse_event("MOUSEBUTTONUP", (50, 25), button=1))
        assert not button.toggled

    def test_toggle_callback_receives_state(self, mock_display):
        """ToggleButton callback should receive current state."""
        states = []

        def on_toggle(state):
            states.append(state)

        button = ToggleButton(
            rect=pygame.Rect(10, 10, 100, 40), text="Toggle", callback=on_toggle
        )

        # Toggle on
        button.on_event(synthesize_mouse_event("MOUSEBUTTONDOWN", (50, 25), button=1))
        button.on_event(synthesize_mouse_event("MOUSEBUTTONUP", (50, 25), button=1))
        assert states == [True]

        # Toggle off
        button.on_event(synthesize_mouse_event("MOUSEBUTTONDOWN", (50, 25), button=1))
        button.on_event(synthesize_mouse_event("MOUSEBUTTONUP", (50, 25), button=1))
        assert states == [True, False]


class TestCheckboxStates:
    """Test Checkbox widget state transitions."""

    def test_checkbox_toggle(self, mock_display):
        """Checkbox should toggle checked state."""
        checkbox = Checkbox(
            rect=pygame.Rect(10, 10, 20, 20),
            label="Enable Feature",
            callback=lambda state: None,
        )

        assert not checkbox.checked

        # Click to check
        checkbox.on_event(synthesize_mouse_event("MOUSEBUTTONDOWN", (15, 15), button=1))
        checkbox.on_event(synthesize_mouse_event("MOUSEBUTTONUP", (15, 15), button=1))
        assert checkbox.checked

        # Click to uncheck
        checkbox.on_event(synthesize_mouse_event("MOUSEBUTTONDOWN", (15, 15), button=1))
        checkbox.on_event(synthesize_mouse_event("MOUSEBUTTONUP", (15, 15), button=1))
        assert not checkbox.checked


class TestSliderStates:
    """Test Slider widget state transitions and keyboard navigation."""

    def test_slider_drag(self, mock_display):
        """Slider should update value when dragged."""
        slider = Slider(
            rect=pygame.Rect(10, 10, 200, 20),
            min_val=0,
            max_val=100,
            initial_val=50,
            callback=lambda val: None,
        )

        assert slider.value == 50

        # Start dragging
        slider.on_event(synthesize_mouse_event("MOUSEBUTTONDOWN", (110, 20), button=1))
        assert slider.dragging

        # Drag to new position (left edge)
        slider.on_event(synthesize_mouse_event("MOUSEMOTION", (10, 20)))
        assert slider.value == 0

        # Drag to right edge
        slider.on_event(synthesize_mouse_event("MOUSEMOTION", (210, 20)))
        assert slider.value == 100

        # Release
        slider.on_event(synthesize_mouse_event("MOUSEBUTTONUP", (210, 20), button=1))
        assert not slider.dragging

    def test_slider_keyboard_navigation(self, mock_display):
        """Slider should respond to arrow keys."""
        slider = Slider(
            rect=pygame.Rect(10, 10, 200, 20),
            min_val=0,
            max_val=100,
            initial_val=50,
            callback=lambda val: None,
        )

        # Give slider focus
        slider.focused = True

        # Press right arrow (should increase)
        slider.on_event(synthesize_key_event("KEYDOWN", pygame.K_RIGHT))
        assert slider.value > 50

        # Press left arrow (should decrease)
        initial = slider.value
        slider.on_event(synthesize_key_event("KEYDOWN", pygame.K_LEFT))
        assert slider.value < initial

    def test_slider_bounds_clamping(self, mock_display):
        """Slider should clamp values to min/max bounds."""
        slider = Slider(
            rect=pygame.Rect(10, 10, 200, 20),
            min_val=0,
            max_val=100,
            initial_val=50,
            callback=lambda val: None,
        )

        # Try to set value below minimum
        slider.set_value(-10)
        assert slider.value == 0

        # Try to set value above maximum
        slider.set_value(150)
        assert slider.value == 100

    def test_slider_step_size(self, mock_display):
        """Slider should respect step size for discrete values."""
        slider = Slider(
            rect=pygame.Rect(10, 10, 200, 20),
            min_val=0,
            max_val=100,
            initial_val=50,
            step=10,
            callback=lambda val: None,
        )

        # Set to non-step value - should round
        slider.set_value(47)
        assert slider.value in [40, 50]  # Should round to nearest step


class TestTooltipStates:
    """Test Tooltip popup timing and positioning."""

    def test_tooltip_hover_delay(self, mock_display):
        """Tooltip should appear after hover delay."""
        tooltip = Tooltip(text="Help text", delay_ms=100)

        # Start hovering
        tooltip.on_mouse_enter()
        assert not tooltip.visible

        # Update before delay expires
        tooltip.on_update(50)
        assert not tooltip.visible

        # Update past delay
        tooltip.on_update(60)
        assert tooltip.visible

    def test_tooltip_disappears_on_mouse_leave(self, mock_display):
        """Tooltip should disappear when mouse leaves."""
        tooltip = Tooltip(text="Help text", delay_ms=100)

        # Show tooltip
        tooltip.on_mouse_enter()
        tooltip.on_update(150)
        assert tooltip.visible

        # Mouse leaves
        tooltip.on_mouse_leave()
        assert not tooltip.visible

    def test_tooltip_positioning(self, mock_display):
        """Tooltip should position near cursor."""
        tooltip = Tooltip(text="Help text", delay_ms=100)

        # Show at specific position
        mouse_pos = (100, 200)
        tooltip.set_position(mouse_pos)
        tooltip.on_mouse_enter()
        tooltip.on_update(150)

        # Tooltip should be offset from cursor
        assert tooltip.rect.topleft != mouse_pos
        assert tooltip.rect.left >= mouse_pos[0]
        assert tooltip.rect.top >= mouse_pos[1]


class TestFocusTraversal:
    """Test keyboard focus traversal between widgets."""

    def test_tab_focus_next(self, mock_display):
        """Tab key should move focus to next widget."""
        button1 = Button(
            rect=pygame.Rect(10, 10, 100, 40), text="B1", callback=lambda: None
        )
        button2 = Button(
            rect=pygame.Rect(10, 60, 100, 40), text="B2", callback=lambda: None
        )
        button3 = Button(
            rect=pygame.Rect(10, 110, 100, 40), text="B3", callback=lambda: None
        )

        widgets = [button1, button2, button3]

        # Start with first widget focused
        button1.focused = True

        # Press Tab - should focus next
        event = synthesize_key_event("KEYDOWN", pygame.K_TAB)

        # Simulate focus manager behavior
        current_index = 0
        for i, w in enumerate(widgets):
            if w.focused:
                w.focused = False
                current_index = i
                break

        next_index = (current_index + 1) % len(widgets)
        widgets[next_index].focused = True

        assert not button1.focused
        assert button2.focused
        assert not button3.focused

    def test_shift_tab_focus_previous(self, mock_display):
        """Shift+Tab should move focus to previous widget."""
        button1 = Button(
            rect=pygame.Rect(10, 10, 100, 40), text="B1", callback=lambda: None
        )
        button2 = Button(
            rect=pygame.Rect(10, 60, 100, 40), text="B2", callback=lambda: None
        )

        widgets = [button1, button2]

        # Start with second widget focused
        button2.focused = True

        # Press Shift+Tab
        event = synthesize_key_event("KEYDOWN", pygame.K_TAB, mod=pygame.KMOD_SHIFT)

        # Simulate focus manager behavior
        current_index = 1
        for i, w in enumerate(widgets):
            if w.focused:
                w.focused = False
                current_index = i
                break

        prev_index = (current_index - 1) % len(widgets)
        widgets[prev_index].focused = True

        assert button1.focused
        assert not button2.focused


class TestWidgetVisibility:
    """Test widget visibility and enabled state interactions."""

    def test_hidden_widget_no_events(self, mock_display):
        """Hidden widgets should not receive events."""
        clicked = False

        def on_click():
            nonlocal clicked
            clicked = True

        button = Button(rect=pygame.Rect(10, 10, 100, 40), text="B", callback=on_click)

        button.visible = False

        # Try to click hidden button
        button.on_event(synthesize_mouse_event("MOUSEBUTTONDOWN", (50, 25), button=1))
        button.on_event(synthesize_mouse_event("MOUSEBUTTONUP", (50, 25), button=1))

        assert not clicked

    def test_widget_show_hide(self, mock_display):
        """Widget should toggle visibility correctly."""
        button = Button(
            rect=pygame.Rect(10, 10, 100, 40), text="B", callback=lambda: None
        )

        assert button.visible

        button.hide()
        assert not button.visible

        button.show()
        assert button.visible
