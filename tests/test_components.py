import pytest
from citysim.simulation.components import Cost, Growth, RenderInfo, Description
from citysim.simulation.tile import TileDef


def test_component_retrieval():
    # Create a definition with specific components
    cost = Cost(500)
    desc = Description("Test Tile")

    td = TileDef(cost, desc)

    # Verify retrieval
    assert td.get_component(Cost) == cost
    assert td.get_component(Description) == desc
    assert td.get_component(RenderInfo) is None  # Missing component should be None


def test_component_properties_backward_compat():
    # Verify the properties still map to components
    td = TileDef(
        Cost(100), RenderInfo((1.0, 0.0, 0.0), 0.5), Description("Property Test")
    )

    assert td.cost == 100
    assert td.color == (1.0, 0.0, 0.0)
    assert td.height == 0.5
    assert td.name == "Property Test"


def test_missing_component_defaults():
    # Verify defaults when components are missing
    td = TileDef()

    assert td.cost == 0
    assert td.height == 0.1  # Default height
    assert td.name == "Unknown"
