"""
Test module for dialog panels.

This verifies that the notice, help, player, and file dialogs can be
imported and instantiated correctly.
"""

import pytest

from micropolis.context import AppContext


def test_notice_dialog_import():
    """Test that NoticeDialog can be imported."""
    from micropolis.ui.panels.notice_dialog import NoticeDialog

    assert NoticeDialog is not None


def test_help_dialog_import():
    """Test that HelpDialog can be imported."""
    from micropolis.ui.panels.help_dialog import HelpDialog

    assert HelpDialog is not None


def test_player_dialog_import():
    """Test that PlayerDialog can be imported."""
    from micropolis.ui.panels.player_dialog import PlayerDialog

    assert PlayerDialog is not None


def test_file_dialog_import():
    """Test that FileDialog can be imported."""
    from micropolis.ui.panels.file_dialog import FileDialog

    assert FileDialog is not None


def test_dialogs_in_panel_init():
    """Test that dialogs are exported from panels __init__."""
    from micropolis.ui.panels import (
        FileDialog,
        HelpDialog,
        NoticeDialog,
        PlayerDialog,
    )

    assert FileDialog is not None
    assert HelpDialog is not None
    assert NoticeDialog is not None
    assert PlayerDialog is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
