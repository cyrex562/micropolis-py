"""Sugar stdin/stdout protocol bridge for pygame UI.

This module provides a non-blocking bridge between the Sugar GTK activity wrapper
and the pygame UI, translating stdin commands into Event Bus messages and emitting
stdout notifications for compatibility with the legacy Tcl/Tk interface.
"""

from __future__ import annotations

import logging
import sys
import threading
from collections import deque
from dataclasses import dataclass
from typing import TextIO

from .event_bus import EventBus, get_default_event_bus

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SugarCommand:
    """Parsed Sugar protocol command."""

    command: str
    args: list[str]
    raw: str


class SugarProtocolBridge:
    """Non-blocking bridge for Sugar activity stdin/stdout communication.

    This bridge:
    - Reads newline-delimited commands from stdin in a background thread
    - Parses Sugar lifecycle commands (SugarStartUp, SugarActivate, etc.)
    - Publishes events to the Event Bus under the 'sugar.*' namespace
    - Sends UI action notifications to stdout for GTK shell compatibility
    - Handles graceful shutdown with UIQuitAck acknowledgment

    Supported incoming commands:
    - SugarStartUp <uri>: Initialize with activity URI
    - SugarNickName <nickname>: Set player nickname
    - SugarActivate: Activity gained focus
    - SugarDeactivate: Activity lost focus
    - SugarShare: Activity was shared
    - SugarBuddyAdd <key> <nick> <color> <address>: Buddy joined
    - SugarBuddyDel <key> <nick> <color> <address>: Buddy left
    - SugarQuit: Graceful shutdown request

    Supported outgoing notifications (stdout):
    - UIHeadPanelReady: Head panel initialized
    - UICitySaved <filename>: City saved successfully
    - UISoundPlay:<channel>:<sound>: Play sound effect
    - UICmd:<payload>: Custom command for GTK shell
    - UIQuitAck: Acknowledge shutdown request
    - PYGAME:<message>: pygame-specific message (ignored by older shells)
    """

    def __init__(
        self,
        *,
        event_bus: EventBus | None = None,
        stdin: TextIO | None = None,
        stdout: TextIO | None = None,
        enable_pygame_messages: bool = True,
    ) -> None:
        """Initialize the Sugar protocol bridge.

        Args:
            event_bus: Event bus for publishing Sugar events (defaults to global)
            stdin: Input stream for commands (defaults to sys.stdin)
            stdout: Output stream for notifications (defaults to sys.stdout)
            enable_pygame_messages: Whether to emit PYGAME: prefixed messages
        """
        self._event_bus = event_bus or get_default_event_bus()
        self._stdin = stdin or sys.stdin
        self._stdout = stdout or sys.stdout
        self._enable_pygame_messages = enable_pygame_messages

        self._running = False
        self._reader_thread: threading.Thread | None = None
        self._command_queue: deque[SugarCommand] = deque()
        self._queue_lock = threading.Lock()
        self._shutdown_requested = False

        # Sugar state synchronized from incoming commands
        self._state = {
            "uri": "",
            "nickname": "",
            "activated": False,
            "shared": False,
            "buddies": [],  # list of (key, nick, color, address) tuples
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start the bridge reader thread."""
        if self._running:
            logger.warning("Sugar bridge already running")
            return

        self._running = True
        self._shutdown_requested = False
        self._reader_thread = threading.Thread(
            target=self._reader_loop,
            name="SugarBridgeReader",
            daemon=True,
        )
        self._reader_thread.start()
        logger.info("Sugar bridge started")

    def stop(self, *, timeout: float = 2.0) -> None:
        """Stop the bridge and wait for reader thread to finish."""
        if not self._running:
            return

        self._running = False
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=timeout)
        logger.info("Sugar bridge stopped")

    def process_commands(self) -> int:
        """Process queued commands and publish events (call from main thread)."""
        commands_processed = 0
        while True:
            with self._queue_lock:
                if not self._command_queue:
                    break
                command = self._command_queue.popleft()

            self._dispatch_command(command)
            commands_processed += 1

        return commands_processed

    # ------------------------------------------------------------------
    # Outgoing notifications (pygame → Sugar GTK shell)
    # ------------------------------------------------------------------
    def send_ui_ready(self, panel_name: str = "HeadPanel") -> None:
        """Notify Sugar shell that a UI panel is ready."""
        self._write_stdout(f"UI{panel_name}Ready")

    def send_city_saved(self, filename: str) -> None:
        """Notify Sugar shell that city was saved."""
        self._write_stdout(f"UICitySaved {filename}")

    def send_sound_play(self, channel: str, sound: str) -> None:
        """Notify Sugar shell to play sound (for hybrid audio setups)."""
        self._write_stdout(f"UISoundPlay:{channel}:{sound}")

    def send_custom_command(self, payload: str) -> None:
        """Send custom command to GTK shell."""
        self._write_stdout(f"UICmd:{payload}")

    def send_quit_ack(self) -> None:
        """Acknowledge quit request to Sugar shell."""
        self._write_stdout("UIQuitAck")

    def send_pygame_message(self, message: str) -> None:
        """Send pygame-specific message (prefixed, ignored by old shells)."""
        if self._enable_pygame_messages:
            self._write_stdout(f"PYGAME:{message}")

    # ------------------------------------------------------------------
    # State accessors
    # ------------------------------------------------------------------
    @property
    def uri(self) -> str:
        """Get current Sugar activity URI."""
        return self._state["uri"]

    @property
    def nickname(self) -> str:
        """Get current player nickname."""
        return self._state["nickname"]

    @property
    def activated(self) -> bool:
        """Check if activity is currently active (has focus)."""
        return self._state["activated"]

    @property
    def shared(self) -> bool:
        """Check if activity is shared."""
        return self._state["shared"]

    @property
    def buddies(self) -> list[tuple[str, str, str, str]]:
        """Get list of connected buddies (key, nick, color, address)."""
        return list(self._state["buddies"])

    @property
    def shutdown_requested(self) -> bool:
        """Check if graceful shutdown was requested."""
        return self._shutdown_requested

    # ------------------------------------------------------------------
    # Internal implementation
    # ------------------------------------------------------------------
    def _reader_loop(self) -> None:
        """Background thread loop reading stdin commands."""
        logger.debug("Sugar bridge reader thread started")
        try:
            while self._running:
                try:
                    line = self._stdin.readline()
                    if not line:
                        # EOF reached
                        logger.info("Sugar bridge stdin closed")
                        break

                    line = line.strip()
                    if not line:
                        continue

                    command = self._parse_command(line)
                    with self._queue_lock:
                        self._command_queue.append(command)

                except Exception as exc:  # pragma: no cover
                    logger.exception("Error reading Sugar command", exc_info=exc)
                    break
        finally:
            logger.debug("Sugar bridge reader thread exiting")

    def _parse_command(self, line: str) -> SugarCommand:
        """Parse a Sugar protocol command line."""
        parts = line.split(None, 1)  # Split on first whitespace
        command = parts[0] if parts else ""
        args_str = parts[1] if len(parts) > 1 else ""

        # Simple argument parsing (handles quoted strings)
        args = []
        if args_str:
            # Basic quote-aware split
            current = []
            in_quote = False
            for char in args_str:
                if char == '"':
                    in_quote = not in_quote
                elif char.isspace() and not in_quote:
                    if current:
                        args.append("".join(current))
                        current = []
                else:
                    current.append(char)
            if current:
                args.append("".join(current))

        return SugarCommand(command=command, args=args, raw=line)

    def _dispatch_command(self, cmd: SugarCommand) -> None:
        """Dispatch a parsed command to appropriate handler."""
        handler_name = f"_handle_{cmd.command.lower()}"
        handler = getattr(self, handler_name, None)

        if handler and callable(handler):
            try:
                handler(cmd)
            except Exception as exc:  # pragma: no cover
                logger.exception(
                    "Error handling Sugar command %s", cmd.command, exc_info=exc
                )
        else:
            logger.debug("Unknown Sugar command: %s", cmd.command)
            # Still publish to event bus for extensibility
            self._event_bus.publish_sugar_message(
                f"unknown_{cmd.command.lower()}",
                {"command": cmd.command, "args": cmd.args, "raw": cmd.raw},
            )

    # ------------------------------------------------------------------
    # Command handlers
    # ------------------------------------------------------------------
    def _handle_sugarstartup(self, cmd: SugarCommand) -> None:
        """Handle SugarStartUp <uri> command."""
        uri = cmd.args[0] if cmd.args else ""
        self._state["uri"] = uri
        logger.info("Sugar startup with URI: %s", uri)
        self._event_bus.publish_sugar_message("startup", uri=uri)

    def _handle_sugarnickname(self, cmd: SugarCommand) -> None:
        """Handle SugarNickName <nickname> command."""
        nickname = cmd.args[0] if cmd.args else ""
        self._state["nickname"] = nickname
        logger.info("Sugar nickname set: %s", nickname)
        self._event_bus.publish_sugar_message("nickname", nickname=nickname)

    def _handle_sugaractivate(self, cmd: SugarCommand) -> None:
        """Handle SugarActivate command."""
        self._state["activated"] = True
        logger.debug("Sugar activity activated")
        self._event_bus.publish_sugar_message("activate", activated=True)

    def _handle_sugardeactivate(self, cmd: SugarCommand) -> None:
        """Handle SugarDeactivate command."""
        self._state["activated"] = False
        logger.debug("Sugar activity deactivated")
        self._event_bus.publish_sugar_message("deactivate", activated=False)

    def _handle_sugarshare(self, cmd: SugarCommand) -> None:
        """Handle SugarShare command."""
        self._state["shared"] = True
        logger.info("Sugar activity shared")
        self._event_bus.publish_sugar_message("share", shared=True)

    def _handle_sugarbuddyadd(self, cmd: SugarCommand) -> None:
        """Handle SugarBuddyAdd <key> <nick> <color> <address> command."""
        if len(cmd.args) < 4:
            logger.warning("Invalid SugarBuddyAdd command: %s", cmd.raw)
            return

        buddy = tuple(cmd.args[:4])  # (key, nick, color, address)
        self._state["buddies"].append(buddy)
        logger.info("Sugar buddy added: %s", buddy[1])
        self._event_bus.publish_sugar_message(
            "buddy_add",
            key=buddy[0],
            nick=buddy[1],
            color=buddy[2],
            address=buddy[3],
        )

    def _handle_sugarbuddydel(self, cmd: SugarCommand) -> None:
        """Handle SugarBuddyDel <key> <nick> <color> <address> command."""
        if len(cmd.args) < 4:
            logger.warning("Invalid SugarBuddyDel command: %s", cmd.raw)
            return

        buddy = tuple(cmd.args[:4])
        try:
            self._state["buddies"].remove(buddy)
        except ValueError:
            logger.warning("Buddy not found for removal: %s", buddy[1])

        logger.info("Sugar buddy removed: %s", buddy[1])
        self._event_bus.publish_sugar_message(
            "buddy_del",
            key=buddy[0],
            nick=buddy[1],
            color=buddy[2],
            address=buddy[3],
        )

    def _handle_sugarquit(self, cmd: SugarCommand) -> None:
        """Handle SugarQuit command."""
        self._shutdown_requested = True
        logger.info("Sugar quit requested")
        self._event_bus.publish_sugar_message("quit")
        # Note: Main application loop should subscribe to sugar.quit and call
        # send_quit_ack() before exiting

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------
    def _write_stdout(self, message: str) -> None:
        """Write a message to stdout with error handling."""
        try:
            self._stdout.write(message + "\n")
            self._stdout.flush()
            logger.debug("Sugar bridge stdout: %s", message)
        except Exception as exc:  # pragma: no cover
            logger.exception("Error writing to stdout", exc_info=exc)


# ------------------------------------------------------------------
# Module-level singleton
# ------------------------------------------------------------------
_DEFAULT_SUGAR_BRIDGE: SugarProtocolBridge | None = None


def get_default_sugar_bridge() -> SugarProtocolBridge:
    """Get or create the default Sugar bridge instance."""
    global _DEFAULT_SUGAR_BRIDGE
    if _DEFAULT_SUGAR_BRIDGE is None:
        _DEFAULT_SUGAR_BRIDGE = SugarProtocolBridge()
    return _DEFAULT_SUGAR_BRIDGE


def set_default_sugar_bridge(bridge: SugarProtocolBridge) -> SugarProtocolBridge:
    """Override the default Sugar bridge (primarily for testing)."""
    global _DEFAULT_SUGAR_BRIDGE
    _DEFAULT_SUGAR_BRIDGE = bridge
    return _DEFAULT_SUGAR_BRIDGE


__all__ = [
    "SugarCommand",
    "SugarProtocolBridge",
    "get_default_sugar_bridge",
    "set_default_sugar_bridge",
]
