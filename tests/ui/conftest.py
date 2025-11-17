"""
UI test fixtures and helpers for pygame-based UI components.

Provides fixtures for:
- SDL dummy driver setup (headless testing)
- Mock contexts and dependency injection
- Event synthesis helpers
- Panel testing utilities
"""

import os
from typing import Any
from unittest.mock import Mock

import pygame
import pytest

from micropolis.app_config import AppConfig
from micropolis.context import AppContext
from micropolis.ui.asset_service import AssetService
from micropolis.ui.event_bus import EventBus
from micropolis.ui.timer_service import TimerService


@pytest.fixture(scope="session", autouse=True)
def setup_sdl_dummy_driver():
    """
    Configure pygame to use SDL dummy video driver for headless testing.

    This allows tests to run without a display, which is essential for:
    - CI/CD pipelines
    - Automated testing
    - Headless server environments
    """
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"

    # Initialize pygame with dummy drivers
    pygame.init()

    yield

    # Cleanup
    pygame.quit()


@pytest.fixture
def mock_display():
    """Create a mock pygame display surface for testing."""
    return pygame.Surface((800, 600))


@pytest.fixture
def mock_app_context():
    """
    Create a mock AppContext with common defaults for testing.

    Returns a fully configured AppContext suitable for UI tests
    without requiring full game state.
    """
    config = AppConfig()
    context = AppContext(config=config)

    # Set common test defaults
    context.user_sound_on = False  # Disable sound in tests
    context.city_name = "Test City"
    context.total_funds = 20000
    context.city_pop = 10000
    context.city_time = 100
    # Ensure auto_budget default for tests is False to match legacy expectations
    context.auto_budget = False

    return context


@pytest.fixture
def mock_event_bus():
    """
    Create a mock Event Bus for dependency injection in panel tests.

    Allows tests to:
    - Subscribe to events
    - Emit test events
    - Verify event handling
    """
    event_bus = EventBus()
    return event_bus


@pytest.fixture
def mock_timer_service():
    """
    Create a mock Timer Service for testing time-dependent UI behavior.

    Provides control over:
    - Timer scheduling
    - Time advancement
    - Timer cancellation
    """
    timer_service = TimerService()
    return timer_service


@pytest.fixture
def mock_asset_service():
    """
    Create a mock Asset Service that returns test assets.

    Returns mock surfaces/fonts/sounds without loading actual files.
    """
    service = Mock(spec=AssetService)

    # Create a dummy surface for any image request
    def get_image(name: str, **kwargs) -> pygame.Surface:
        return pygame.Surface((32, 32))

    # Create a dummy font for any font request
    def get_font(name: str, size: int) -> pygame.font.Font:
        return pygame.font.Font(None, size)

    service.get_image = Mock(side_effect=get_image)
    service.get_font = Mock(side_effect=get_font)
    service.get_sound = Mock(return_value=None)

    return service


def synthesize_mouse_event(
    event_type: str, pos: tuple[int, int], button: int = 1, **kwargs
) -> pygame.event.Event:
    """
    Create a synthetic pygame mouse event for testing.

    Args:
        event_type: "MOUSEBUTTONDOWN", "MOUSEBUTTONUP", "MOUSEMOTION"
        pos: (x, y) position
        button: Mouse button number (1=left, 2=middle, 3=right)
        **kwargs: Additional event attributes

    Returns:
        pygame.event.Event suitable for testing
    """
    event_types = {
        "MOUSEBUTTONDOWN": pygame.MOUSEBUTTONDOWN,
        "MOUSEBUTTONUP": pygame.MOUSEBUTTONUP,
        "MOUSEMOTION": pygame.MOUSEMOTION,
    }

    event_dict = {"pos": pos, "button": button, **kwargs}

    return pygame.event.Event(event_types.get(event_type, pygame.USEREVENT), event_dict)


def synthesize_key_event(
    event_type: str, key: int, mod: int = 0, unicode: str = "", **kwargs
) -> pygame.event.Event:
    """
    Create a synthetic pygame keyboard event for testing.

    Args:
        event_type: "KEYDOWN" or "KEYUP"
        key: pygame key constant (e.g., pygame.K_SPACE)
        mod: Key modifiers (e.g., pygame.KMOD_CTRL)
        unicode: Unicode character representation
        **kwargs: Additional event attributes

    Returns:
        pygame.event.Event suitable for testing
    """
    event_types = {
        "KEYDOWN": pygame.KEYDOWN,
        "KEYUP": pygame.KEYUP,
    }

    event_dict = {"key": key, "mod": mod, "unicode": unicode, **kwargs}

    return pygame.event.Event(event_types.get(event_type, pygame.USEREVENT), event_dict)


@pytest.fixture
def event_synthesizer():
    """
    Fixture providing event synthesis helpers.

    Returns:
        Dictionary of helper functions for creating test events
    """
    return {
        "mouse": synthesize_mouse_event,
        "key": synthesize_key_event,
    }


class MockPanel:
    """
    Mock panel for testing panel manager and event routing.

    Tracks lifecycle calls and events received for assertions.
    """

    def __init__(self, name: str = "test_panel"):
        self.name = name
        self.mounted = False
        self.unmounted = False
        self.update_calls = []
        self.render_calls = []
        self.events_received = []
        self.rect = pygame.Rect(0, 0, 800, 600)

    def on_mount(self, context: Any) -> None:
        self.mounted = True

    def on_unmount(self) -> None:
        self.unmounted = True

    def on_update(self, dt_ms: float) -> None:
        self.update_calls.append(dt_ms)

    def on_event(self, event: pygame.event.Event) -> bool:
        self.events_received.append(event)
        return False

    def render(self, surface: pygame.Surface) -> None:
        self.render_calls.append(surface)


@pytest.fixture
def mock_panel():
    """Create a mock panel for testing."""
    return MockPanel()


class EventCapture:
    """
    Helper class for capturing and asserting on Event Bus events.

    Usage:
        capture = EventCapture(event_bus)
        capture.subscribe("funds.updated")

        # Trigger some action
        event_bus.emit("funds.updated", {"amount": 1000})

        # Assert
        assert capture.received("funds.updated")
        assert capture.count("funds.updated") == 1
        assert capture.last_payload("funds.updated")["amount"] == 1000
    """

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.events: dict[str, list[Any]] = {}

    def subscribe(self, topic: str) -> None:
        """Subscribe to an event topic and capture payloads."""
        if topic not in self.events:
            self.events[topic] = []

        def capture_callback(payload: Any) -> None:
            self.events[topic].append(payload)

        self.event_bus.subscribe(topic, capture_callback)

    def received(self, topic: str) -> bool:
        """Check if any events were received for topic."""
        return topic in self.events and len(self.events[topic]) > 0

    def count(self, topic: str) -> int:
        """Get count of events received for topic."""
        return len(self.events.get(topic, []))

    def last_payload(self, topic: str) -> Any:
        """Get the payload of the last event for topic."""
        if not self.received(topic):
            return None
        return self.events[topic][-1]

    def all_payloads(self, topic: str) -> list[Any]:
        """Get all payloads for topic."""
        return self.events.get(topic, [])

    def clear(self, topic: str | None = None) -> None:
        """Clear captured events for topic (or all if None)."""
        if topic:
            self.events[topic] = []
        else:
            self.events.clear()


@pytest.fixture
def event_capture(mock_event_bus):
    """Create an EventCapture helper for the mock event bus."""
    return EventCapture(mock_event_bus)


def assert_rect_contains(rect: pygame.Rect, point: tuple[int, int]) -> None:
    """Assert that a rectangle contains a point."""
    assert rect.collidepoint(point), f"Point {point} not in rect {rect}"


def assert_rect_equal(actual: pygame.Rect, expected: pygame.Rect) -> None:
    """Assert two rectangles are equal."""
    assert actual == expected, f"Expected rect {expected}, got {actual}"


def assert_color_equal(
    actual: pygame.Color | tuple, expected: pygame.Color | tuple, tolerance: int = 0
) -> None:
    """
    Assert two colors are equal within tolerance.

    Args:
        actual: Actual color
        expected: Expected color
        tolerance: Maximum difference per channel
    """
    actual_c = pygame.Color(*actual) if isinstance(actual, tuple) else actual
    expected_c = pygame.Color(*expected) if isinstance(expected, tuple) else expected

    for i, (a, e) in enumerate(zip(actual_c, expected_c)):
        assert abs(a - e) <= tolerance, (
            f"Color channel {i} differs: expected {e}, got {a} (tolerance {tolerance})"
        )
