"""
Test suite for network.py

Tests for UDP networking functionality ported from w_net.c
"""

import pytest
import threading
import time
from unittest.mock import patch, MagicMock
import micropolis.network as network


@pytest.fixture
def network_manager():
    """Create a fresh NetworkManager for testing."""
    manager = network.NetworkManager()
    yield manager
    manager.stop_listening()


class TestNetworkManager:
    """Test NetworkManager basic functionality."""

    def test_init(self, network_manager):
        """Test NetworkManager initialization."""
        assert network_manager.listen_port is None
        assert network_manager.listen_socket is None
        assert not network_manager.is_listening
        assert network_manager.receive_thread is None
        assert network_manager.packet_callback is None
        assert not network_manager.running

    def test_start_listening_success(self, network_manager):
        """Test successful start of UDP listening."""
        # Use a high port number to avoid conflicts
        port = 54321
        success = network_manager.start_listening(port)

        assert success
        assert network_manager.is_listening
        assert network_manager.running
        assert network_manager.listen_port == port
        assert network_manager.listen_socket is not None
        assert network_manager.receive_thread is not None
        assert network_manager.receive_thread.is_alive()

        # Clean up
        network_manager.stop_listening()

    def test_start_listening_invalid_port(self, network_manager):
        """Test starting listening on invalid port."""
        # Try to bind to a privileged port (should fail)
        network_manager.start_listening(80)  # HTTP port, requires admin

        # This might succeed or fail depending on permissions
        # Just check that the manager handles it gracefully
        network_manager.stop_listening()

    def test_stop_listening(self, network_manager):
        """Test stopping UDP listening."""
        port = 54322
        network_manager.start_listening(port)
        assert network_manager.is_listening

        network_manager.stop_listening()
        assert not network_manager.is_listening
        assert not network_manager.running
        assert network_manager.listen_port is None
        assert network_manager.listen_socket is None

    def test_send_packet_without_socket(self, network_manager):
        """Test sending packet when not listening."""
        success = network_manager.send_packet("127.0.0.1", 54323, b"test")
        assert not success

    @patch('socket.socket')
    def test_send_packet_with_mock_socket(self, mock_socket_class, network_manager):
        """Test sending packet with mocked socket."""
        # Setup mock socket
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket

        # Start listening to create socket
        network_manager.start_listening(54324)

        # Send packet
        success = network_manager.send_packet("127.0.0.1", 54325, b"test data")

        assert success
        mock_socket.sendto.assert_called_once_with(b"test data", ("127.0.0.1", 54325))

        network_manager.stop_listening()

    @patch('socket.socket')
    def test_send_packet_failure(self, mock_socket_class, network_manager):
        """Test sending packet that fails."""
        mock_socket = MagicMock()
        mock_socket.sendto.side_effect = OSError("Network error")
        mock_socket_class.return_value = mock_socket

        network_manager.start_listening(54326)
        success = network_manager.send_packet("127.0.0.1", 54327, b"test")

        assert not success
        network_manager.stop_listening()

    def test_set_packet_callback(self, network_manager):
        """Test setting packet callback."""
        def dummy_callback(sock_id, addr, data):
            pass

        network_manager.set_packet_callback(dummy_callback)
        assert network_manager.packet_callback == dummy_callback

    def test_get_listen_port(self, network_manager):
        """Test getting listen port."""
        assert network_manager.get_listen_port() is None

        network_manager.start_listening(54328)
        assert network_manager.get_listen_port() == 54328

        network_manager.stop_listening()
        assert network_manager.get_listen_port() is None

    def test_is_active(self, network_manager):
        """Test checking if networking is active."""
        assert not network_manager.is_active()

        network_manager.start_listening(54329)
        assert network_manager.is_active()

        network_manager.running = False  # Simulate stopping
        assert not network_manager.is_active()

        network_manager.stop_listening()


class TestGlobalFunctions:
    """Test global network functions."""

    def test_start_network_listening(self):
        """Test global start listening function."""
        # Stop any existing listening first
        network.stop_network_listening()

        success = network.start_network_listening(54330)
        assert isinstance(success, bool)

        network.stop_network_listening()

    def test_stop_network_listening(self):
        """Test global stop listening function."""
        network.start_network_listening(54331)
        network.stop_network_listening()

        status = network.get_network_status()
        assert not status['active']

    def test_send_network_packet(self):
        """Test global send packet function."""
        # Should fail when not listening
        success = network.send_network_packet("127.0.0.1", 54332, b"test")
        assert not success

    def test_set_network_callback(self):
        """Test setting global network callback."""
        def callback(sock_id, addr, data):
            pass

        network.set_network_callback(callback)
        # Should not raise exception

    def test_get_network_status(self):
        """Test getting network status."""
        status = network.get_network_status()
        assert isinstance(status, dict)
        assert 'active' in status
        assert 'port' in status
        assert 'listening' in status


class TestNetworkCommand:
    """Test TCL command interface."""

    def test_command_init(self):
        """Test NetworkCommand initialization."""
        cmd = network.NetworkCommand()
        assert cmd.manager is network._network_manager

    def test_listen_command(self):
        """Test listen TCL command."""
        cmd = network.NetworkCommand()

        result = cmd.handle_command("listen", "54333")
        assert result in ["0", "1"]

        network.stop_network_listening()

    def test_stop_command(self):
        """Test stop TCL command."""
        cmd = network.NetworkCommand()

        result = cmd.handle_command("stop")
        assert result == ""

    def test_send_command(self):
        """Test send TCL command."""
        cmd = network.NetworkCommand()

        # Should work even without listening socket
        result = cmd.handle_command("send", "127.0.0.1", "54334", "1", "2", "3")
        assert result in ["0", "1"]

    def test_send_command_invalid_data(self):
        """Test send command with invalid data."""
        cmd = network.NetworkCommand()

        with pytest.raises(ValueError, match="Data must be space-separated integers"):
            cmd.handle_command("send", "127.0.0.1", "54335", "not", "numbers")

    def test_status_command(self):
        """Test status TCL command."""
        cmd = network.NetworkCommand()

        result = cmd.handle_command("status")
        assert "active=" in result
        assert "port=" in result

    def test_invalid_command(self):
        """Test invalid TCL command."""
        cmd = network.NetworkCommand()

        with pytest.raises(ValueError, match="Unknown network command"):
            cmd.handle_command("invalid")


class TestDefaultPacketHandler:
    """Test default packet handler."""

    def test_default_handler(self, capsys):
        """Test default packet handler output."""
        network.default_packet_handler(123, "192.168.1.1", b"abc")

        captured = capsys.readouterr()
        assert "HandlePacket 123 {192.168.1.1}" in captured.out
        assert "97  98  99" in captured.out  # ASCII values of 'a', 'b', 'c'


class TestIntegration:
    """Integration tests for network functionality."""

    def test_full_network_cycle(self):
        """Test complete network start/stop cycle."""
        # Start listening
        success = network.start_network_listening(54336)
        assert isinstance(success, bool)

        # Check status
        status = network.get_network_status()
        if success:
            assert status['active']
            assert status['port'] == 54336

        # Set callback
        callback_called = []

        def test_callback(sock_id, addr, data):
            callback_called.append((sock_id, addr, data))

        network.set_network_callback(test_callback)

        # Stop listening
        network.stop_network_listening()

        status = network.get_network_status()
        assert not status['active']

    @patch('socket.socket')
    def test_receive_loop_error_handling(self, mock_socket_class):
        """Test error handling in receive loop."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket

        # Make recvfrom raise an exception
        mock_socket.recvfrom.side_effect = OSError("Test error")

        manager = network.NetworkManager()
        manager.start_listening(54337)

        # Give the thread a moment to run and encounter the error
        time.sleep(0.2)

        # Should still be running (error handling should continue)
        assert manager.running

        manager.stop_listening()


class TestThreadSafety:
    """Test thread safety aspects."""

    def test_concurrent_start_stop(self):
        """Test starting and stopping concurrently."""
        results = []

        def start_stop_cycle():
            for i in range(3):
                success = network.start_network_listening(54338 + i)
                results.append(success)
                time.sleep(0.01)
                network.stop_network_listening()
                time.sleep(0.01)

        threads = []
        for _ in range(3):
            t = threading.Thread(target=start_stop_cycle)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Should have completed without exceptions
        assert len(results) == 9  # 3 threads * 3 cycles each


if __name__ == "__main__":
    pytest.main([__file__])