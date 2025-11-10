"""
network.py: UDP networking support for Micropolis Python port

This module provides basic UDP networking functionality ported from w_net.c.
It enables multiplayer features by allowing cities to exchange data via UDP packets.

Original C file: w_net.c
Ported to maintain compatibility with potential multiplayer features.
"""

import socket
import select
import threading
from typing import Optional, Callable


class NetworkManager:
    """
    UDP networking manager for Micropolis multiplayer features.

    Provides basic UDP socket functionality for sending and receiving
    network packets between Micropolis instances.
    """

    def __init__(self):
        self.listen_port: Optional[int] = None
        self.listen_socket: Optional[socket.socket] = None
        self.is_listening = False
        self.receive_thread: Optional[threading.Thread] = None
        self.packet_callback: Optional[Callable[[int, str, bytes], None]] = None
        self.running = False

    def start_listening(self, port: int) -> bool:
        """
        Start listening for UDP packets on the specified port.

        Args:
            port: Port number to listen on

        Returns:
            True if listening started successfully, False otherwise
        """
        if self.is_listening:
            self.stop_listening()

        try:
            self.listen_port = port
            self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Set socket options for reuse and non-blocking
            self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind to the port
            self.listen_socket.bind(('', port))

            # Set non-blocking mode
            self.listen_socket.setblocking(False)

            self.is_listening = True
            self.running = True

            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()

            return True

        except OSError as e:
            print(f"Failed to start UDP listening on port {port}: {e}")
            self.listen_socket = None
            return False

    def stop_listening(self):
        """Stop listening for UDP packets."""
        self.running = False

        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)

        if self.listen_socket:
            try:
                self.listen_socket.close()
            except OSError:
                pass
            self.listen_socket = None

        self.is_listening = False
        self.listen_port = None

    def send_packet(self, host: str, port: int, data: bytes) -> bool:
        """
        Send a UDP packet to the specified host and port.

        Args:
            host: Destination hostname or IP address
            port: Destination port
            data: Packet data to send

        Returns:
            True if packet sent successfully, False otherwise
        """
        if not self.listen_socket:
            return False

        try:
            self.listen_socket.sendto(data, (host, port))
            return True
        except OSError as e:
            print(f"Failed to send UDP packet to {host}:{port}: {e}")
            return False

    def set_packet_callback(self, callback: Callable[[int, str, bytes], None]):
        """
        Set the callback function to handle received packets.

        Args:
            callback: Function that takes (socket_id, sender_address, packet_data)
        """
        self.packet_callback = callback

    def _receive_loop(self):
        """Main receive loop running in background thread."""
        while self.running and self.listen_socket:
            try:
                # Use select to wait for data with timeout
                ready, _, _ = select.select([self.listen_socket], [], [], 0.1)

                if ready and self.running:
                    try:
                        data, addr = self.listen_socket.recvfrom(1024)
                        if data and self.packet_callback:
                            # Call callback with socket fileno, address, and data
                            self.packet_callback(
                                self.listen_socket.fileno(),
                                addr[0],  # IP address
                                data
                            )
                    except OSError:
                        # Socket might be closed
                        break

            except OSError:
                # Select failed, likely due to socket closure
                break

    def get_listen_port(self) -> Optional[int]:
        """Get the current listening port."""
        return self.listen_port

    def is_active(self) -> bool:
        """Check if networking is active."""
        return self.is_listening and self.running


# Global network manager instance
_network_manager = NetworkManager()


def start_network_listening(port: int) -> bool:
    """
    Start UDP network listening on the specified port.

    Args:
        port: Port number to listen on

    Returns:
        True if listening started successfully
    """
    return _network_manager.start_listening(port)


def stop_network_listening():
    """Stop UDP network listening."""
    _network_manager.stop_listening()


def send_network_packet(host: str, port: int, data: bytes) -> bool:
    """
    Send a UDP packet to another Micropolis instance.

    Args:
        host: Destination hostname or IP address
        port: Destination port
        data: Packet data

    Returns:
        True if sent successfully
    """
    return _network_manager.send_packet(host, port, data)


def set_network_callback(callback: Callable[[int, str, bytes], None]):
    """
    Set callback for handling received network packets.

    Args:
        callback: Function to call when packets are received
    """
    _network_manager.set_packet_callback(callback)


def get_network_status() -> dict:
    """
    Get current network status.

    Returns:
        Dictionary with network status information
    """
    return {
        'active': _network_manager.is_active(),
        'port': _network_manager.get_listen_port(),
        'listening': _network_manager.is_listening
    }


# TCL Command Interface (for compatibility)
class NetworkCommand:
    """TCL command interface for network operations."""

    def __init__(self):
        self.manager = _network_manager

    def handle_command(self, command: str, *args) -> str:
        """Handle TCL network commands."""
        if command == "listen":
            if len(args) != 1:
                raise ValueError("Usage: listen <port>")
            port = int(args[0])
            success = self.manager.start_listening(port)
            return "1" if success else "0"

        elif command == "stop":
            self.manager.stop_listening()
            return ""

        elif command == "send":
            if len(args) < 3:
                raise ValueError("Usage: send <host> <port> <data...>")
            host = args[0]
            port = int(args[1])
            # Convert remaining args to bytes (assuming space-separated integers)
            try:
                data = bytes(int(x) for x in args[2:])
                success = self.manager.send_packet(host, port, data)
                return "1" if success else "0"
            except ValueError:
                raise ValueError("Data must be space-separated integers")

        elif command == "status":
            status = get_network_status()
            return f"active={1 if status['active'] else 0} port={status['port'] or 0}"

        else:
            raise ValueError(f"Unknown network command: {command}")


# Default packet handler (for compatibility with original TCL interface)
def default_packet_handler(socket_id: int, address: str, data: bytes):
    """
    Default packet handler that formats packets similar to original TCL code.

    This creates a command string that could be evaluated, similar to the
    original "HandlePacket" TCL command.
    """
    # Format data as space-separated integers (matching original C code)
    data_str = " ".join(f"{b:3d}" for b in data)

    # Create command string (could be integrated with TCL interpreter if needed)
    command = f"HandlePacket {socket_id} {{{address}}} {{{data_str}}}"
    print(f"Received network packet: {command}")

    # In a full implementation, this would integrate with the TCL interpreter
    # For now, just log the packet


# Initialize default callback
_network_manager.set_packet_callback(default_packet_handler)