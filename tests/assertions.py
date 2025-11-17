"""
Lightweight assertion mixin so pytest-based tests can keep the familiar
`self.assert*` helpers without depending on unittest.TestCase.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np
import pygame
import pytest
from PIL import Image


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

    def assertIn(
        self, member: Any, container: Iterable, msg: str | None = None
    ) -> None:
        assert member in container, msg or f"{member!r} not found in {container!r}"

    def assertNotIn(
        self, member: Any, container: Iterable, msg: str | None = None
    ) -> None:
        assert member not in container, (
            msg or f"{member!r} unexpectedly found in {container!r}"
        )

    def assertGreater(self, first: Any, second: Any, msg: str | None = None) -> None:
        assert first > second, msg or f"{first!r} is not > {second!r}"

    def assertGreaterEqual(
        self, first: Any, second: Any, msg: str | None = None
    ) -> None:
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


# Snapshot testing utilities -------------------------------------------------


def compute_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Compute Structural Similarity Index (SSIM) between two images.

    Args:
        img1: First image as numpy array (H, W, C)
        img2: Second image as numpy array (H, W, C)

    Returns:
        SSIM score between 0 and 1 (1 = identical)
    """
    # Convert to grayscale if needed
    if len(img1.shape) == 3:
        img1_gray = np.mean(img1, axis=2)
    else:
        img1_gray = img1

    if len(img2.shape) == 3:
        img2_gray = np.mean(img2, axis=2)
    else:
        img2_gray = img2

    # Constants for SSIM calculation
    k1, k2 = 0.01, 0.03
    l_value = 255  # Dynamic range
    c1 = (k1 * l_value) ** 2
    c2 = (k2 * l_value) ** 2

    # Compute means
    mu1 = np.mean(img1_gray)
    mu2 = np.mean(img2_gray)

    # Compute variances and covariance
    sigma1_sq = np.var(img1_gray)
    sigma2_sq = np.var(img2_gray)
    sigma12 = np.mean((img1_gray - mu1) * (img2_gray - mu2))

    # SSIM formula
    numerator = (2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)
    denominator = (mu1**2 + mu2**2 + c1) * (sigma1_sq + sigma2_sq + c2)

    if denominator == 0:
        return 1.0 if numerator == 0 else 0.0

    return numerator / denominator


def assert_surface_matches_golden(
    surface: pygame.Surface,
    name: str,
    tolerance: float = 0.95,
    golden_dir: str | None = None,
) -> None:
    """
    Assert that a pygame surface matches a golden reference image.

    If UPDATE_GOLDEN environment variable is set, updates the golden image.
    Otherwise, compares using SSIM with the specified tolerance.

    Args:
        surface: pygame Surface to test
        name: Name of the golden image (without .png extension)
        tolerance: SSIM threshold (0-1, default 0.95)
        golden_dir: Directory for golden images (default: tests/golden/)

    Raises:
        AssertionError: If SSIM score is below tolerance
        FileNotFoundError: If golden image doesn't exist and UPDATE_GOLDEN
            is not set
    """
    if golden_dir is None:
        # Default to tests/golden/ relative to this file
        test_root = Path(__file__).parent
        golden_dir = str(test_root / "golden")

    golden_path = Path(golden_dir) / f"{name}.png"
    golden_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert pygame surface to numpy array
    width, height = surface.get_size()
    pixels = pygame.surfarray.array3d(surface)
    # pygame uses (width, height, channels) - transpose to (height, width, ch)
    current_array = np.transpose(pixels, (1, 0, 2))

    # Check if we should update golden images
    update_mode = os.environ.get("UPDATE_GOLDEN", "").lower() in (
        "1",
        "true",
        "yes",
    )

    if update_mode:
        # Save current image as golden
        img = Image.fromarray(current_array.astype(np.uint8))
        img.save(golden_path)
        print(f"Updated golden image: {golden_path}")
        return

    # Load golden image for comparison
    if not golden_path.exists():
        msg = (
            f"Golden image not found: {golden_path}\n"
            f"Run with UPDATE_GOLDEN=1 to create it."
        )
        raise FileNotFoundError(msg)

    golden_img = Image.open(golden_path)
    golden_array = np.array(golden_img)

    # Ensure dimensions match
    if current_array.shape != golden_array.shape:
        msg = (
            f"Image dimensions mismatch for '{name}':\n"
            f"  Current: {current_array.shape}\n"
            f"  Golden:  {golden_array.shape}"
        )
        raise AssertionError(msg)

    # Compute SSIM
    ssim_score = compute_ssim(current_array, golden_array)

    if ssim_score < tolerance:
        # Save diff image for debugging
        diff_path = golden_path.parent / f"{name}_diff.png"
        diff_array = np.abs(current_array.astype(int) - golden_array.astype(int))
        diff_img = Image.fromarray(diff_array.astype(np.uint8))
        diff_img.save(diff_path)

        # Also save current for comparison
        current_path = golden_path.parent / f"{name}_current.png"
        current_img = Image.fromarray(current_array.astype(np.uint8))
        current_img.save(current_path)

        msg = (
            f"Image mismatch for '{name}':\n"
            f"  SSIM score: {ssim_score:.4f} (threshold: {tolerance:.4f})\n"
            f"  Diff saved to: {diff_path}\n"
            f"  Current saved to: {current_path}\n"
            f"Run with UPDATE_GOLDEN=1 to update golden images."
        )
        raise AssertionError(msg)
