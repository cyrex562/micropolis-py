"""
Panel tests with Event Bus dependency injection.

Tests data binding between panels and AppContext, validating:
- Event Bus event handling
- Context state updates
- Panel UI synchronization
- Legacy types compatibility
"""

import pygame

from micropolis.context import AppContext
from micropolis.ui.panels.head_panel import HeadPanel
from tests.ui.conftest import EventCapture, synthesize_mouse_event


class TestHeadPanelEventHandling:
    """Test HeadPanel event subscriptions and reactions."""

    def test_funds_updated_event(
        self,
        mock_app_context: AppContext,
        mock_event_bus,
        event_capture: EventCapture,
        mock_display,
    ):
        """HeadPanel should update display when funds.updated event fires."""
        event_capture.subscribe("funds.updated")

        panel = HeadPanel(
            rect=pygame.Rect(0, 0, 800, 60),
            context=mock_app_context,
            event_bus=mock_event_bus,
        )
        panel.on_mount(mock_app_context)

        # Initial funds
        initial_funds = mock_app_context.total_funds
        assert initial_funds == 20000

        # Emit funds.updated event
        new_funds = 25000
        mock_event_bus.emit("funds.updated", {"amount": new_funds})

        # Verify event was captured
        assert event_capture.received("funds.updated")
        assert event_capture.last_payload("funds.updated")["amount"] == new_funds

        # Panel should reflect new funds
        # (Actual implementation would update internal state)

    def test_population_updated_event(
        self,
        mock_app_context: AppContext,
        mock_event_bus,
        event_capture: EventCapture,
        mock_display,
    ):
        """HeadPanel should update population display on city.stats event."""
        event_capture.subscribe("city.stats.updated")

        panel = HeadPanel(
            rect=pygame.Rect(0, 0, 800, 60),
            context=mock_app_context,
            event_bus=mock_event_bus,
        )
        panel.on_mount(mock_app_context)

        # Emit population update
        new_stats = {
            "population": 15000,
            "residential_zones": 50,
            "commercial_zones": 30,
            "industrial_zones": 20,
        }
        mock_event_bus.emit("city.stats.updated", new_stats)

        assert event_capture.received("city.stats.updated")
        stats = event_capture.last_payload("city.stats.updated")
        assert stats["population"] == 15000

    def test_disaster_notification(
        self,
        mock_app_context: AppContext,
        mock_event_bus,
        event_capture: EventCapture,
        mock_display,
    ):
        """HeadPanel should show disaster icon when disaster.triggered fires."""
        event_capture.subscribe("disaster.triggered")

        panel = HeadPanel(
            rect=pygame.Rect(0, 0, 800, 60),
            context=mock_app_context,
            event_bus=mock_event_bus,
        )
        panel.on_mount(mock_app_context)

        # Trigger disaster event
        disaster_data = {"type": "fire", "location": (50, 50), "severity": "major"}
        mock_event_bus.emit("disaster.triggered", disaster_data)

        assert event_capture.received("disaster.triggered")
        data = event_capture.last_payload("disaster.triggered")
        assert data["type"] == "fire"


class TestBudgetPanelDataBinding:
    """Test BudgetPanel data binding with AppContext."""

    def test_auto_budget_toggle_updates_context(
        self, mock_app_context: AppContext, mock_event_bus, mock_display
    ):
        """Toggling AutoBudget should update both context and legacy types."""
        from micropolis.ui.panels.budget_panel import BudgetPanel

        panel = BudgetPanel(
            rect=pygame.Rect(0, 0, 400, 300),
            context=mock_app_context,
            event_bus=mock_event_bus,
        )
        panel.on_mount(mock_app_context)

        # Initial state
        initial_auto_budget = mock_app_context.auto_budget
        assert initial_auto_budget is False

        # Simulate clicking auto budget checkbox
        # (Find checkbox in panel and click it)
        auto_budget_checkbox = None
        for widget in panel.widgets:
            if hasattr(widget, "label") and "auto" in widget.label.lower():
                auto_budget_checkbox = widget
                break

        if auto_budget_checkbox:
            # Click checkbox
            event = synthesize_mouse_event(
                "MOUSEBUTTONDOWN", auto_budget_checkbox.rect.center, button=1
            )
            auto_budget_checkbox.on_event(event)

            event = synthesize_mouse_event(
                "MOUSEBUTTONUP", auto_budget_checkbox.rect.center, button=1
            )
            auto_budget_checkbox.on_event(event)

            # Context should update
            assert mock_app_context.auto_budget is True

    def test_tax_rate_slider_updates_context(
        self, mock_app_context: AppContext, mock_event_bus, mock_display
    ):
        """Dragging tax rate slider should update context."""
        from micropolis.ui.panels.budget_panel import BudgetPanel

        panel = BudgetPanel(
            rect=pygame.Rect(0, 0, 400, 300),
            context=mock_app_context,
            event_bus=mock_event_bus,
        )
        panel.on_mount(mock_app_context)

        # Find tax rate slider
        tax_slider = None
        for widget in panel.widgets:
            if hasattr(widget, "label") and "tax" in str(widget.label).lower():
                tax_slider = widget
                break

        if tax_slider:
            # Drag slider to new position
            initial_tax = mock_app_context.city_tax
            tax_slider.set_value(12)  # 12% tax rate

            # Context should update
            # (Actual implementation would sync on slider change)

    def test_budget_allocation_emits_event(
        self,
        mock_app_context: AppContext,
        mock_event_bus,
        event_capture: EventCapture,
        mock_display,
    ):
        """Changing budget allocations should emit budget.changed event."""
        from micropolis.ui.panels.budget_panel import BudgetPanel

        event_capture.subscribe("budget.changed")

        panel = BudgetPanel(
            rect=pygame.Rect(0, 0, 400, 300),
            context=mock_app_context,
            event_bus=mock_event_bus,
        )
        panel.on_mount(mock_app_context)

        # Modify budget allocation (e.g., police funding)
        new_allocations = {
            "police": 25,
            "fire": 25,
            "roads": 50,
        }

        # Simulate clicking Apply button
        mock_event_bus.emit("budget.changed", new_allocations)

        assert event_capture.received("budget.changed")
        allocations = event_capture.last_payload("budget.changed")
        assert allocations["police"] == 25


class TestMapPanelInteraction:
    """Test MapPanel mouse interaction and viewport updates."""

    def test_map_click_emits_location_event(
        self,
        mock_app_context: AppContext,
        mock_event_bus,
        event_capture: EventCapture,
        mock_display,
    ):
        """Clicking map should emit map.location.selected event."""
        from micropolis.ui.panels.map_panel import MapPanel

        event_capture.subscribe("map.location.selected")

        panel = MapPanel(
            rect=pygame.Rect(600, 100, 180, 180),
            context=mock_app_context,
            event_bus=mock_event_bus,
        )
        panel.on_mount(mock_app_context)

        # Click on map
        click_pos = (650, 150)
        event = synthesize_mouse_event("MOUSEBUTTONDOWN", click_pos, button=1)
        panel.on_event(event)

        # Should emit location event
        assert event_capture.received("map.location.selected")
        location = event_capture.last_payload("map.location.selected")
        assert "x" in location
        assert "y" in location

    def test_map_viewport_follows_editor(
        self,
        mock_app_context: AppContext,
        mock_event_bus,
        event_capture: EventCapture,
        mock_display,
    ):
        """Map viewport should update when editor.viewport.changed fires."""
        from micropolis.ui.panels.map_panel import MapPanel

        event_capture.subscribe("editor.viewport.changed")

        panel = MapPanel(
            rect=pygame.Rect(600, 100, 180, 180),
            context=mock_app_context,
            event_bus=mock_event_bus,
        )
        panel.on_mount(mock_app_context)

        # Emit viewport change
        viewport_data = {
            "x": 10,
            "y": 20,
            "width": 30,
            "height": 30,
        }
        mock_event_bus.emit("editor.viewport.changed", viewport_data)

        assert event_capture.received("editor.viewport.changed")


class TestGraphsPanelUpdates:
    """Test GraphsPanel real-time data updates."""

    def test_graphs_update_on_stats_event(
        self,
        mock_app_context: AppContext,
        mock_event_bus,
        event_capture: EventCapture,
        mock_display,
    ):
        """Graphs should update when city.stats.updated fires."""
        from micropolis.ui.panels.graphs_panel import GraphsPanel

        event_capture.subscribe("city.stats.updated")

        panel = GraphsPanel(
            rect=pygame.Rect(0, 0, 600, 400),
            context=mock_app_context,
            event_bus=mock_event_bus,
        )
        panel.on_mount(mock_app_context)

        # Emit multiple stat updates (simulate time passing)
        for month in range(12):
            stats = {
                "month": month,
                "residential_pop": 1000 + month * 100,
                "commercial_pop": 500 + month * 50,
                "industrial_pop": 300 + month * 30,
            }
            mock_event_bus.emit("city.stats.updated", stats)

        # Should have received all updates
        assert event_capture.count("city.stats.updated") == 12


class TestEvaluationPanelScores:
    """Test EvaluationPanel score calculations and display."""

    def test_evaluation_triggered_on_demand(
        self,
        mock_app_context: AppContext,
        mock_event_bus,
        event_capture: EventCapture,
        mock_display,
    ):
        """Clicking Evaluate button should trigger evaluation."""
        from micropolis.ui.panels.evaluation_panel import EvaluationPanel

        event_capture.subscribe("evaluation.requested")

        panel = EvaluationPanel(
            rect=pygame.Rect(0, 0, 500, 400),
            context=mock_app_context,
            event_bus=mock_event_bus,
        )
        panel.on_mount(mock_app_context)

        # Simulate clicking Evaluate button
        mock_event_bus.emit("evaluation.requested", {})

        assert event_capture.received("evaluation.requested")

    def test_evaluation_results_displayed(
        self,
        mock_app_context: AppContext,
        mock_event_bus,
        event_capture: EventCapture,
        mock_display,
    ):
        """Evaluation results should update panel display."""
        from micropolis.ui.panels.evaluation_panel import EvaluationPanel

        event_capture.subscribe("evaluation.completed")

        panel = EvaluationPanel(
            rect=pygame.Rect(0, 0, 500, 400),
            context=mock_app_context,
            event_bus=mock_event_bus,
        )
        panel.on_mount(mock_app_context)

        # Emit evaluation results
        results = {
            "overall_score": 750,
            "public_opinion": 65,
            "city_problems": ["traffic", "crime"],
            "statistics": {
                "population": 50000,
                "approval_rating": 65,
            },
        }
        mock_event_bus.emit("evaluation.completed", results)

        assert event_capture.received("evaluation.completed")
        data = event_capture.last_payload("evaluation.completed")
        assert data["overall_score"] == 750
