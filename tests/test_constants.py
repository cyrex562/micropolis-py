"""
Unit tests for micropolis.constants ensuring the Macintosh resource
compatibility layer behaves as expected.
"""

from __future__ import annotations

from micropolis import constants


def test_quad_type_definition():
    """QUAD should be aliased to int for portability."""
    assert constants.QUAD is int


def test_basic_mac_types_exist():
    """The core Macintosh pointer/handle stand-ins should exist."""
    assert hasattr(constants, "Byte")
    assert hasattr(constants, "Ptr")
    assert hasattr(constants, "Handle")


def test_resource_dataclass_fields():
    """Resource dataclass should preserve initialization data."""
    resource = constants.Resource(buf=b"test", size=4, name="TEST", id=123)
    assert resource.buf == b"test"
    assert resource.size == 4
    assert resource.name == "TEST"
    assert resource.id == 123
    assert resource.next is None


def test_resource_management_stubs_return_safe_defaults():
    """Placeholder resource APIs must return harmless defaults."""
    assert constants.NewPtr(100) is None
    assert constants.GetResource("TILE", 1) is None
    assert constants.ResourceSize(None) == 0
    assert constants.ResourceName(None) == ""
    assert constants.ResourceID(None) == 0


def test_resource_type_catalog_contains_expected_entries():
    """Ensure key resource type identifiers are registered."""
    assert "TILE" in constants.RESOURCE_TYPES
    assert "SND " in constants.RESOURCE_TYPES
    assert constants.MAX_RESOURCE_SIZE == 65536
