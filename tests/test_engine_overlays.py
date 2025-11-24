"""
Tests for pygame overlay integrations inside engine.py.
"""

from __future__ import annotations

from unittest import mock

from src.micropolis import engine
from micropolis.context import AppContext
from micropolis.app_config import AppConfig

# Create a test context
context = AppContext(config=AppConfig())


def _mock_surface(size: tuple[int, int]) -> mock.Mock:
    surface = mock.Mock()
    surface.get_size.return_value = size
    return surface


def test_blit_overlay_panels_draws_graph_and_evaluation(monkeypatch):
    """Graph/evaluation toggles should result in pygame blits."""
    screen = mock.Mock()
    screen.get_width.return_value = 800

    graph_surface = _mock_surface((200, 100))
    evaluation_surface = _mock_surface((150, 80))

    monkeypatch.setattr(engine.graphs, "render_graph_panel", lambda: graph_surface)
    monkeypatch.setattr(engine.evaluation_ui, "get_evaluation_surface", lambda: evaluation_surface)

    engine._blit_overlay_panels(context, screen)

    assert screen.blit.call_count == 2
    assert screen.blit.call_args_list[0] == mock.call(graph_surface, (800 - 16 - 200, 16))
    assert screen.blit.call_args_list[1] == mock.call(evaluation_surface, (800 - 16 - 150, 16 + 100 + 12))


def test_blit_overlay_panels_no_surfaces(monkeypatch):
    """No blits should occur when both overlays are hidden."""
    screen = mock.Mock()
    screen.get_width.return_value = 800

    monkeypatch.setattr(engine.graphs, "render_graph_panel", lambda: None)
    monkeypatch.setattr(engine.evaluation_ui, "get_evaluation_surface", lambda: None)

    engine._blit_overlay_panels(context, screen)

    screen.blit.assert_not_called()


def test_graphdoer_requests_redraw(monkeypatch):
    """graphDoer should update history buffers and request redraws."""
    calls = {"updated": False, "requested": False}

    def fake_update():
        calls["updated"] = True

    def fake_request():
        calls["requested"] = True

    monkeypatch.setattr(engine.graphs, "update_all_graphs", fake_update)
    monkeypatch.setattr(engine.graphs, "request_graph_panel_redraw", fake_request)

    engine.graphDoer()

    assert calls["updated"]
    assert calls["requested"]


def test_scoredoer_triggers_evaluation(monkeypatch):
    """scoreDoer should propagate to evaluation helpers."""
    calls = {"score": False, "update": False}

    def fake_score():
        calls["score"] = True

    def fake_update():
        calls["update"] = True

    monkeypatch.setattr(engine.evaluation_ui, "score_doer", fake_score)
    monkeypatch.setattr(engine.evaluation_ui, "update_evaluation", fake_update)

    engine.scoreDoer()

    assert calls["score"]
    assert calls["update"]
