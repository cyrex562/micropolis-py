"""
Lightweight assertion mixin so pytest-based tests can keep the familiar
`self.assert*` helpers without depending on unittest.TestCase.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterable, Iterator

import pytest


class Assertions:
    """Helper mixin providing common assertion helpers for pytest classes."""

    # pytest hooks ---------------------------------------------------------
    def setup_method(self) -> None:  # pragma: no cover - glue code
        hook = getattr(self, "setUp", None)
        if callable(hook):
            hook()

    def teardown_method(self) -> None:  # pragma: no cover - glue code
        hook = getattr(self, "tearDown", None)
        if callable(hook):
            hook()

    # Assertion helpers ----------------------------------------------------
    def assertEqual(self, first: Any, second: Any, msg: str | None = None) -> None:
        assert first == second, msg or f"{first!r} != {second!r}"

    def assertNotEqual(self, first: Any, second: Any, msg: str | None = None) -> None:
        assert first != second, msg or f"{first!r} == {second!r}"

    def assertTrue(self, expr: Any, msg: str | None = None) -> None:
        assert bool(expr), msg or "Expected truthy value"

    def assertFalse(self, expr: Any, msg: str | None = None) -> None:
        assert not bool(expr), msg or "Expected falsy value"

    def assertIsNone(self, value: Any, msg: str | None = None) -> None:
        assert value is None, msg or f"Expected None, got {value!r}"

    def assertIsNotNone(self, value: Any, msg: str | None = None) -> None:
        assert value is not None, msg or "Unexpected None"

    def assertIs(self, first: Any, second: Any, msg: str | None = None) -> None:
        assert first is second, msg or f"{first!r} is not {second!r}"

    def assertIsNot(self, first: Any, second: Any, msg: str | None = None) -> None:
        assert first is not second, msg or f"{first!r} is {second!r}"

    def assertIsInstance(self, value: Any, cls: type, msg: str | None = None) -> None:
        assert isinstance(value, cls), msg or f"{value!r} is not instance of {cls!r}"

    def assertIn(self, member: Any, container: Iterable, msg: str | None = None) -> None:
        assert member in container, msg or f"{member!r} not found in {container!r}"

    def assertNotIn(self, member: Any, container: Iterable, msg: str | None = None) -> None:
        assert member not in container, msg or f"{member!r} unexpectedly found in {container!r}"

    def assertGreater(self, first: Any, second: Any, msg: str | None = None) -> None:
        assert first > second, msg or f"{first!r} is not > {second!r}"

    def assertGreaterEqual(self, first: Any, second: Any, msg: str | None = None) -> None:
        assert first >= second, msg or f"{first!r} is not >= {second!r}"

    def assertLess(self, first: Any, second: Any, msg: str | None = None) -> None:
        assert first < second, msg or f"{first!r} is not < {second!r}"

    def assertLessEqual(self, first: Any, second: Any, msg: str | None = None) -> None:
        assert first <= second, msg or f"{first!r} is not <= {second!r}"

    def assertRaises(self, exc_type):  # pragma: no cover - simple proxy
        return pytest.raises(exc_type)

    @contextmanager
    def subTest(self, **params) -> Iterator[None]:  # pragma: no cover - helper
        yield
