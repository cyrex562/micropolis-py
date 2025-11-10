"""
test_camera.py - Tests for camera system

Tests the cellular automata camera system stub implementations.
These tests ensure that the camera classes and functions work correctly
and maintain API compatibility with the original C code.
"""

import pytest

from src.micropolis import camera


class TestCan:
    """Test Can (canvas) class."""

    def test_can_creation(self):
        """Test creating a Can instance."""
        can = camera.Can(10, 20)
        assert can.width == 10
        assert can.height == 20
        assert can.line_bytes == 10
        assert len(can.mem) == 200  # 10 * 20

    def test_can_with_custom_mem(self):
        """Test creating a Can with custom memory."""
        mem = bytearray([1, 2, 3, 4])
        can = camera.Can(2, 2, mem, 2)
        assert can.mem is mem
        assert can.line_bytes == 2

    def test_get_pixel(self):
        """Test getting pixel values."""
        can = camera.Can(2, 2)
        can.mem[0] = 42
        can.mem[3] = 99

        assert can.get_pixel(0, 0) == 42
        assert can.get_pixel(1, 1) == 99
        assert can.get_pixel(2, 0) == 0  # Out of bounds
        assert can.get_pixel(0, 2) == 0  # Out of bounds

    def test_set_pixel(self):
        """Test setting pixel values."""
        can = camera.Can(2, 2)

        can.set_pixel(0, 0, 42)
        can.set_pixel(1, 1, 99)
        can.set_pixel(2, 0, 255)  # Out of bounds - should not crash

        assert can.mem[0] == 42
        assert can.mem[3] == 99


class TestCam:
    """Test Cam (cellular automaton) class."""

    def test_cam_creation(self):
        """Test creating a Cam instance."""
        cam = camera.Cam()
        assert cam.width == 0
        assert cam.height == 0
        assert cam.x == 0
        assert cam.y == 0
        assert cam.rule_size == 256
        assert len(cam.rule) == 256


class TestSimCam:
    """Test SimCam (simulation camera) class."""

    def test_simcam_creation(self):
        """Test creating a SimCam instance."""
        scam = camera.SimCam()
        assert scam.w_width == 512
        assert scam.w_height == 512
        assert scam.visible is False
        assert scam.cam_count == 0
        assert scam.cam_list is None


class TestUtilityFunctions:
    """Test utility functions."""

    def test_new_can(self):
        """Test new_can function."""
        can = camera.new_can(5, 10)
        assert can.width == 5
        assert can.height == 10
        assert can.line_bytes == 5
        assert len(can.mem) == 50

    def test_new_can_with_mem(self):
        """Test new_can with custom memory."""
        mem = bytearray(20)
        can = camera.new_can(4, 5, mem, 4)
        assert can.mem is mem
        assert can.line_bytes == 4

    def test_new_cam(self):
        """Test new_cam function."""
        scam = camera.SimCam()
        scam.data = bytearray(1000)
        scam.line_bytes = 20

        cam = camera.new_cam(scam, 5, 10, 8, 12)

        assert cam.x == 5
        assert cam.y == 10
        assert cam.width == 8  # Rounded up to even
        assert cam.height == 12  # Rounded up to even
        assert cam.back is not None
        assert cam.front is not None

    def test_find_cam_by_name(self):
        """Test finding camera by name."""
        scam = camera.SimCam()

        # Create test cameras
        cam1 = camera.Cam()
        cam1.name = "test1"
        scam.cam_list = cam1

        cam2 = camera.Cam()
        cam2.name = "test2"
        cam1.next = cam2

        assert camera.find_cam_by_name(scam, "test1") is cam1
        assert camera.find_cam_by_name(scam, "test2") is cam2
        assert camera.find_cam_by_name(scam, "nonexistent") is None

    def test_find_cam(self):
        """Test finding camera at coordinates."""
        scam = camera.SimCam()

        # Create test camera
        cam = camera.Cam()
        cam.x, cam.y = 10, 20
        cam.width, cam.height = 30, 40
        scam.cam_list = cam

        assert camera.find_cam(scam, 15, 25) is cam  # Inside
        assert camera.find_cam(scam, 5, 5) is None   # Outside
        assert camera.find_cam(scam, 45, 65) is None  # Outside


class TestCameraManagement:
    """Test camera management functions."""

    def test_create_simcam(self):
        """Test creating simulation camera."""
        scam = camera.create_simcam(100, 200)
        assert scam.w_width == 100
        assert scam.w_height == 200
        assert scam.line_bytes == 100
        assert scam.data is not None
        assert len(scam.data) == 20000  # 100 * 200
        assert scam.surface is not None
        assert scam in camera._simcam_list

    def test_destroy_simcam(self):
        """Test destroying simulation camera."""
        scam = camera.create_simcam()
        assert scam in camera._simcam_list

        camera.destroy_simcam(scam)
        assert scam not in camera._simcam_list

    def test_add_cam_to_simcam(self):
        """Test adding camera to simulation camera."""
        scam = camera.SimCam()
        cam = camera.Cam()

        camera.add_cam_to_simcam(scam, cam)
        assert scam.cam_list is cam
        assert scam.cam_count == 1

        # Add another
        cam2 = camera.Cam()
        camera.add_cam_to_simcam(scam, cam2)
        assert scam.cam_list is cam2
        assert cam2.next is cam
        assert scam.cam_count == 2

    def test_destroy_cam(self):
        """Test destroying camera."""
        scam = camera.SimCam()
        cam1 = camera.Cam()
        cam2 = camera.Cam()

        camera.add_cam_to_simcam(scam, cam1)
        camera.add_cam_to_simcam(scam, cam2)

        camera.destroy_cam(scam, cam1)
        assert scam.cam_list is cam2
        assert scam.cam_count == 1

        camera.destroy_cam(scam, cam2)
        assert scam.cam_list is None
        assert scam.cam_count == 0


class TestCellularAutomata:
    """Test cellular automata functions."""

    def test_cam_set_neighborhood(self):
        """Test setting neighborhood rule."""
        cam = camera.Cam()
        camera.cam_set_neighborhood(cam, 0)

        # Check that rule table was set
        assert len(cam.rule) == 256
        # Basic sanity check - some rules should be set
        assert sum(cam.rule) > 0

    def test_cam_load_rule(self):
        """Test loading named rule."""
        cam = camera.Cam()
        camera.cam_load_rule(cam, "life")

        # Should set some rule
        assert len(cam.rule) == 256

    def test_cam_randomize(self):
        """Test randomizing camera state."""
        cam = camera.Cam()
        cam.back = camera.Can(10, 10)

        camera.cam_randomize(cam)

        # Check that some pixels were set
        assert sum(cam.back.mem) > 0

    def test_cam_step(self):
        """Test stepping cellular automaton."""
        scam = camera.SimCam()
        scam.data = bytearray(100)
        scam.line_bytes = 10

        cam = camera.new_cam(scam, 0, 0, 8, 8)
        camera.cam_set_neighborhood(cam, 0)

        # Set up a simple pattern
        assert cam.front is not None
        cam.front.set_pixel(4, 4, 1)
        cam.front.set_pixel(4, 5, 1)
        cam.front.set_pixel(4, 6, 1)

        camera.cam_step(cam)

        # Should have evolved (exact result depends on rule)
        # Just check that it didn't crash and produced some output
        assert cam.front is not None


class TestRendering:
    """Test rendering functions."""

    def test_render_simcam(self):
        """Test rendering simulation camera."""
        scam = camera.create_simcam(10, 10)

        # Add a camera with some live cells
        cam = camera.new_cam(scam, 0, 0, 8, 8)
        assert cam.front is not None
        cam.front.set_pixel(0, 0, 1)
        cam.front.set_pixel(7, 7, 1)
        camera.add_cam_to_simcam(scam, cam)

        surface = camera.render_simcam(scam)
        assert surface is not None
        assert surface.get_size() == (10, 10)

    def test_update_simcam(self):
        """Test updating simulation camera."""
        scam = camera.create_simcam(10, 10)

        # Add a camera that should step
        cam = camera.new_cam(scam, 0, 0, 8, 8)
        cam.steps = 1
        camera.add_cam_to_simcam(scam, cam)

        # Should not crash
        camera.update_simcam(scam)
        assert cam.steps == 0


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_create_life_camera(self):
        """Test creating Conway's Game of Life camera."""
        scam = camera.create_simcam(20, 20)
        cam = camera.create_life_camera(scam, "life", 0, 0, 10, 10)

        assert cam.name == "life"
        assert cam.width == 10
        assert cam.height == 10
        assert scam.cam_list is cam

    def test_create_random_camera(self):
        """Test creating random camera."""
        scam = camera.create_simcam(20, 20)
        cam = camera.create_random_camera(scam, "random", 0, 0, 10, 10)

        assert cam.name == "random"
        # Should have some random pixels set
        if cam.back:
            assert sum(cam.back.mem) > 0


class TestSystemLifecycle:
    """Test system initialization and cleanup."""

    def test_initialize_camera_system(self):
        """Test initializing camera system."""
        camera.initialize_camera_system()
        assert camera._simcam_list == []
        assert camera._next_cam_id == 1

    def test_cleanup_camera_system(self):
        """Test cleaning up camera system."""
        # Create some cameras
        camera.create_simcam(10, 10)
        camera.create_simcam(10, 10)

        assert len(camera._simcam_list) == 2

        camera.cleanup_camera_system()
        assert len(camera._simcam_list) == 0


class TestCommandInterface:
    """Test command interface."""

    def test_cam_command(self):
        """Test camera command processing."""
        result = camera.cam_command("test", "arg1", "arg2")
        # Stub implementation returns empty string
        assert result == ""


if __name__ == "__main__":
    pytest.main([__file__])