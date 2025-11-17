"""Tests for the Sugar protocol bridge."""

from __future__ import annotations

import io
import time

import pytest

from micropolis.ui.event_bus import EventBus
from micropolis.ui.sugar_bridge import SugarCommand, SugarProtocolBridge


class TestSugarCommand:
    """Test SugarCommand dataclass."""

    def test_creation(self):
        cmd = SugarCommand(command="Test", args=["arg1", "arg2"], raw="Test arg1 arg2")
        assert cmd.command == "Test"
        assert cmd.args == ["arg1", "arg2"]
        assert cmd.raw == "Test arg1 arg2"


class TestSugarProtocolBridge:
    """Test SugarProtocolBridge functionality."""

    @pytest.fixture
    def event_bus(self):
        """Create a fresh event bus for each test."""
        return EventBus()

    @pytest.fixture
    def stdin_stream(self):
        """Create a mock stdin stream."""
        return io.StringIO()

    @pytest.fixture
    def stdout_stream(self):
        """Create a mock stdout stream."""
        return io.StringIO()

    @pytest.fixture
    def bridge(self, event_bus, stdin_stream, stdout_stream):
        """Create a bridge with mock streams."""
        return SugarProtocolBridge(
            event_bus=event_bus,
            stdin=stdin_stream,
            stdout=stdout_stream,
            enable_pygame_messages=True,
        )

    # ------------------------------------------------------------------
    # Initialization tests
    # ------------------------------------------------------------------
    def test_initialization(self, bridge):
        """Test bridge initializes with correct defaults."""
        assert not bridge._running
        assert bridge._reader_thread is None
        assert bridge.uri == ""
        assert bridge.nickname == ""
        assert not bridge.activated
        assert not bridge.shared
        assert bridge.buddies == []
        assert not bridge.shutdown_requested

    # ------------------------------------------------------------------
    # Command parsing tests
    # ------------------------------------------------------------------
    def test_parse_simple_command(self, bridge):
        """Test parsing command without arguments."""
        cmd = bridge._parse_command("SugarQuit")
        assert cmd.command == "SugarQuit"
        assert cmd.args == []
        assert cmd.raw == "SugarQuit"

    def test_parse_command_with_args(self, bridge):
        """Test parsing command with multiple arguments."""
        cmd = bridge._parse_command("SugarStartUp file:///cities/test.cty")
        assert cmd.command == "SugarStartUp"
        assert cmd.args == ["file:///cities/test.cty"]

    def test_parse_command_with_quoted_args(self, bridge):
        """Test parsing command with quoted arguments."""
        cmd = bridge._parse_command('SugarNickName "Player One"')
        assert cmd.command == "SugarNickName"
        assert cmd.args == ["Player One"]

    def test_parse_command_with_multiple_quoted_args(self, bridge):
        """Test parsing command with multiple quoted arguments."""
        cmd = bridge._parse_command('SugarBuddyAdd "key123" "Bob" "red" "192.168.1.1"')
        assert cmd.command == "SugarBuddyAdd"
        assert len(cmd.args) == 4
        assert cmd.args == ["key123", "Bob", "red", "192.168.1.1"]

    # ------------------------------------------------------------------
    # Command handling tests
    # ------------------------------------------------------------------
    def test_handle_sugarstartup(self, bridge, event_bus):
        """Test SugarStartUp command handling."""
        events = []
        event_bus.subscribe("sugar.startup", lambda e: events.append(e))

        cmd = SugarCommand(
            "SugarStartUp", ["file:///test.cty"], "SugarStartUp file:///test.cty"
        )
        bridge._handle_sugarstartup(cmd)

        assert bridge.uri == "file:///test.cty"
        assert len(events) == 1
        assert events[0].payload["uri"] == "file:///test.cty"

    def test_handle_sugarnickname(self, bridge, event_bus):
        """Test SugarNickName command handling."""
        events = []
        event_bus.subscribe("sugar.nickname", lambda e: events.append(e))

        cmd = SugarCommand("SugarNickName", ["Alice"], "SugarNickName Alice")
        bridge._handle_sugarnickname(cmd)

        assert bridge.nickname == "Alice"
        assert len(events) == 1
        assert events[0].payload["nickname"] == "Alice"

    def test_handle_sugaractivate(self, bridge, event_bus):
        """Test SugarActivate command handling."""
        events = []
        event_bus.subscribe("sugar.activate", lambda e: events.append(e))

        cmd = SugarCommand("SugarActivate", [], "SugarActivate")
        bridge._handle_sugaractivate(cmd)

        assert bridge.activated
        assert len(events) == 1

    def test_handle_sugardeactivate(self, bridge, event_bus):
        """Test SugarDeactivate command handling."""
        bridge._state["activated"] = True
        events = []
        event_bus.subscribe("sugar.deactivate", lambda e: events.append(e))

        cmd = SugarCommand("SugarDeactivate", [], "SugarDeactivate")
        bridge._handle_sugardeactivate(cmd)

        assert not bridge.activated
        assert len(events) == 1

    def test_handle_sugarshare(self, bridge, event_bus):
        """Test SugarShare command handling."""
        events = []
        event_bus.subscribe("sugar.share", lambda e: events.append(e))

        cmd = SugarCommand("SugarShare", [], "SugarShare")
        bridge._handle_sugarshare(cmd)

        assert bridge.shared
        assert len(events) == 1

    def test_handle_sugarbuddyadd(self, bridge, event_bus):
        """Test SugarBuddyAdd command handling."""
        events = []
        event_bus.subscribe("sugar.buddy_add", lambda e: events.append(e))

        cmd = SugarCommand(
            "SugarBuddyAdd",
            ["key1", "Bob", "blue", "192.168.1.5"],
            "SugarBuddyAdd key1 Bob blue 192.168.1.5",
        )
        bridge._handle_sugarbuddyadd(cmd)

        assert len(bridge.buddies) == 1
        assert bridge.buddies[0] == ("key1", "Bob", "blue", "192.168.1.5")
        assert len(events) == 1
        assert events[0].payload["nick"] == "Bob"

    def test_handle_sugarbuddydel(self, bridge, event_bus):
        """Test SugarBuddyDel command handling."""
        # Add a buddy first
        bridge._state["buddies"].append(("key1", "Bob", "blue", "192.168.1.5"))

        events = []
        event_bus.subscribe("sugar.buddy_del", lambda e: events.append(e))

        cmd = SugarCommand(
            "SugarBuddyDel",
            ["key1", "Bob", "blue", "192.168.1.5"],
            "SugarBuddyDel key1 Bob blue 192.168.1.5",
        )
        bridge._handle_sugarbuddydel(cmd)

        assert len(bridge.buddies) == 0
        assert len(events) == 1

    def test_handle_sugarquit(self, bridge, event_bus):
        """Test SugarQuit command handling."""
        events = []
        event_bus.subscribe("sugar.quit", lambda e: events.append(e))

        cmd = SugarCommand("SugarQuit", [], "SugarQuit")
        bridge._handle_sugarquit(cmd)

        assert bridge.shutdown_requested
        assert len(events) == 1

    def test_handle_unknown_command(self, bridge, event_bus):
        """Test unknown command publishes generic event."""
        events = []
        event_bus.subscribe("sugar.*", lambda e: events.append(e))

        cmd = SugarCommand("UnknownCommand", ["arg"], "UnknownCommand arg")
        bridge._dispatch_command(cmd)

        # Should still publish to event bus for extensibility
        assert len(events) == 1
        assert "unknown" in events[0].topic

    # ------------------------------------------------------------------
    # Output tests
    # ------------------------------------------------------------------
    def test_send_ui_ready(self, bridge, stdout_stream):
        """Test sending UI ready notification."""
        bridge.send_ui_ready("TestPanel")
        output = stdout_stream.getvalue()
        assert "UITestPanelReady" in output

    def test_send_city_saved(self, bridge, stdout_stream):
        """Test sending city saved notification."""
        bridge.send_city_saved("test.cty")
        output = stdout_stream.getvalue()
        assert "UICitySaved test.cty" in output

    def test_send_sound_play(self, bridge, stdout_stream):
        """Test sending sound play notification."""
        bridge.send_sound_play("edit", "click")
        output = stdout_stream.getvalue()
        assert "UISoundPlay:edit:click" in output

    def test_send_custom_command(self, bridge, stdout_stream):
        """Test sending custom command."""
        bridge.send_custom_command("TestPayload")
        output = stdout_stream.getvalue()
        assert "UICmd:TestPayload" in output

    def test_send_quit_ack(self, bridge, stdout_stream):
        """Test sending quit acknowledgment."""
        bridge.send_quit_ack()
        output = stdout_stream.getvalue()
        assert "UIQuitAck" in output

    def test_send_pygame_message(self, bridge, stdout_stream):
        """Test sending pygame-specific message."""
        bridge.send_pygame_message("TestMessage")
        output = stdout_stream.getvalue()
        assert "PYGAME:TestMessage" in output

    def test_send_pygame_message_disabled(self, event_bus, stdin_stream, stdout_stream):
        """Test pygame messages can be disabled."""
        bridge = SugarProtocolBridge(
            event_bus=event_bus,
            stdin=stdin_stream,
            stdout=stdout_stream,
            enable_pygame_messages=False,
        )
        bridge.send_pygame_message("TestMessage")
        output = stdout_stream.getvalue()
        assert "PYGAME" not in output

    # ------------------------------------------------------------------
    # Threading tests
    # ------------------------------------------------------------------
    def test_start_and_stop(self, bridge):
        """Test starting and stopping the bridge."""
        assert not bridge._running

        bridge.start()
        assert bridge._running
        assert bridge._reader_thread is not None

        # Give thread time to start
        time.sleep(0.1)

        bridge.stop(timeout=1.0)
        assert not bridge._running

    def test_process_commands_from_queue(self, bridge, event_bus, stdin_stream):
        """Test processing queued commands."""
        events = []
        event_bus.subscribe("sugar.*", lambda e: events.append(e))

        # Manually queue commands (simulating what reader thread would do)
        cmd1 = SugarCommand("SugarActivate", [], "SugarActivate")
        cmd2 = SugarCommand("SugarShare", [], "SugarShare")

        with bridge._queue_lock:
            bridge._command_queue.append(cmd1)
            bridge._command_queue.append(cmd2)

        # Process commands
        count = bridge.process_commands()

        assert count == 2
        assert len(events) == 2
        assert bridge.activated
        assert bridge.shared

    def test_thread_reads_stdin(self, bridge, event_bus, stdin_stream):
        """Test reader thread processes stdin commands."""
        events = []
        event_bus.subscribe("sugar.activate", lambda e: events.append(e))

        # Write command to stdin
        stdin_stream.write("SugarActivate\n")
        stdin_stream.seek(0)

        # Start bridge
        bridge.start()
        time.sleep(0.2)  # Let thread read command

        # Process queued commands
        bridge.process_commands()

        # Stop bridge
        bridge.stop(timeout=1.0)

        assert len(events) == 1
        assert bridge.activated

    def test_reader_thread_handles_eof(self, event_bus, stdout_stream):
        """Test reader thread handles EOF gracefully."""
        # Create stdin that returns EOF immediately
        stdin_stream = io.StringIO("")
        stdin_stream.seek(0)

        bridge = SugarProtocolBridge(
            event_bus=event_bus,
            stdin=stdin_stream,
            stdout=stdout_stream,
        )

        bridge.start()
        time.sleep(0.2)  # Let thread detect EOF
        bridge.stop(timeout=1.0)

        # Thread should exit cleanly without errors

    # ------------------------------------------------------------------
    # Integration tests
    # ------------------------------------------------------------------
    def test_full_lifecycle(self, bridge, event_bus, stdin_stream, stdout_stream):
        """Test full Sugar activity lifecycle."""
        # Track all events
        all_events = []
        event_bus.subscribe("sugar.*", lambda e: all_events.append(e))

        # Write lifecycle commands to stdin
        commands = [
            'SugarStartUp "file:///test.cty"\n',
            'SugarNickName "TestPlayer"\n',
            "SugarActivate\n",
            "SugarShare\n",
            'SugarBuddyAdd "key1" "Friend1" "red" "10.0.0.1"\n',
            'SugarBuddyAdd "key2" "Friend2" "blue" "10.0.0.2"\n',
            "SugarDeactivate\n",
            'SugarBuddyDel "key1" "Friend1" "red" "10.0.0.1"\n',
            "SugarQuit\n",
        ]

        for cmd in commands:
            stdin_stream.write(cmd)
        stdin_stream.seek(0)

        # Start bridge and let it process
        bridge.start()
        time.sleep(0.3)
        bridge.process_commands()
        bridge.stop(timeout=1.0)

        # Verify state changes
        assert bridge.uri == "file:///test.cty"
        assert bridge.nickname == "TestPlayer"
        assert not bridge.activated  # Deactivated
        assert bridge.shared
        assert len(bridge.buddies) == 1  # One removed
        assert bridge.buddies[0][1] == "Friend2"
        assert bridge.shutdown_requested

        # Verify all events were published
        assert len(all_events) >= 8

        # Send quit acknowledgment
        bridge.send_quit_ack()
        output = stdout_stream.getvalue()
        assert "UIQuitAck" in output


class TestSugarBridgeSingleton:
    """Test module-level singleton functions."""

    def test_get_default_sugar_bridge(self):
        """Test getting default bridge instance."""
        from micropolis.ui.sugar_bridge import get_default_sugar_bridge

        bridge1 = get_default_sugar_bridge()
        bridge2 = get_default_sugar_bridge()

        assert bridge1 is bridge2
        assert isinstance(bridge1, SugarProtocolBridge)

    def test_set_default_sugar_bridge(self):
        """Test overriding default bridge instance."""
        from micropolis.ui.sugar_bridge import (
            get_default_sugar_bridge,
            set_default_sugar_bridge,
        )

        custom_bridge = SugarProtocolBridge()
        returned = set_default_sugar_bridge(custom_bridge)

        assert returned is custom_bridge
        assert get_default_sugar_bridge() is custom_bridge

        # Reset to default for other tests
        set_default_sugar_bridge(SugarProtocolBridge())
