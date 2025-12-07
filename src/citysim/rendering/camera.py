import math
import numpy as np
from typing import Tuple


class Camera:
    """
    Sim City style 3D camera.
    Uses an orbit style control or free movement on a plane.
    """

    def __init__(self, position=(0.0, 10.0, 10.0), yaw=-90.0, pitch=-45.0, fov=45.0):
        self.position = np.array(position, dtype=np.float32)
        self.yaw = yaw
        self.pitch = pitch
        self.fov = fov
        self.aspect_ratio = 16 / 9

        self.front = np.array([0.0, 0.0, -1.0], dtype=np.float32)
        self.up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        self.right = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        self.world_up = np.array([0.0, 1.0, 0.0], dtype=np.float32)

        self.speed = 10.0
        self.sensitivity = 0.1
        self.zoom_speed = 2.0

        self.update_vectors()

    def update_vectors(self):
        """Recalculate front/right/up vectors from euler angles."""
        rad_yaw = math.radians(self.yaw)
        rad_pitch = math.radians(self.pitch)

        front = np.array(
            [
                math.cos(rad_yaw) * math.cos(rad_pitch),
                math.sin(rad_pitch),
                math.sin(rad_yaw) * math.cos(rad_pitch),
            ],
            dtype=np.float32,
        )

        self.front = front / np.linalg.norm(front)
        self.right = np.cross(self.front, self.world_up)
        self.right = self.right / np.linalg.norm(self.right)
        self.up = np.cross(self.right, self.front)
        self.up = self.up / np.linalg.norm(self.up)

    def get_view_matrix(self) -> np.ndarray:
        """Returns the 4x4 view matrix."""
        # LookAt matrix construction
        target = self.position + self.front

        z_axis = self.position - target
        z_axis = z_axis / np.linalg.norm(z_axis)

        x_axis = np.cross(
            self.up, z_axis
        )  # Note: Using self.up instead of world_up to respect roll if added
        # Actually standard LookAt uses world up usually, but here our updated 'up' is orthogonal
        x_axis = np.cross(np.array([0, 1, 0]), z_axis)
        x_axis = x_axis / np.linalg.norm(x_axis)

        y_axis = np.cross(z_axis, x_axis)

        # Translation
        translation = np.identity(4)
        translation[0][3] = -self.position[0]
        translation[1][3] = -self.position[1]
        translation[2][3] = -self.position[2]

        rotation = np.identity(4)
        rotation[0][0] = x_axis[0]
        rotation[0][1] = x_axis[1]
        rotation[0][2] = x_axis[2]
        rotation[1][0] = y_axis[0]
        rotation[1][1] = y_axis[1]
        rotation[1][2] = y_axis[2]
        rotation[2][0] = z_axis[0]
        rotation[2][1] = z_axis[1]
        rotation[2][2] = z_axis[2]

        return np.dot(rotation, translation)

    def get_projection_matrix(self, width, height) -> np.ndarray:
        """Returns the 4x4 perspective projection matrix."""
        aspect = width / height if height > 0 else 1.0
        self.aspect_ratio = aspect
        return self.perspective(self.fov, aspect, 0.1, 1000.0)

    def perspective(self, fov_deg, aspect, near, far) -> np.ndarray:
        """Create perspective matrix."""
        fov_rad = math.radians(fov_deg)
        f = 1.0 / math.tan(fov_rad / 2.0)

        mat = np.zeros((4, 4), dtype=np.float32)
        mat[0][0] = f / aspect
        mat[1][1] = f
        mat[2][2] = (far + near) / (near - far)
        mat[2][3] = (2 * far * near) / (near - far)
        mat[3][2] = -1.0

        return mat

    def process_keyboard(self, direction: str, dt: float):
        """Move camera based on direction string."""
        velocity = self.speed * dt
        if direction == "FORWARD":
            # Move on XZ plane only for RTS style
            move_dir = np.array([self.front[0], 0, self.front[2]])
            move_dir = move_dir / np.linalg.norm(move_dir)
            self.position += move_dir * velocity
        elif direction == "BACKWARD":
            move_dir = np.array([self.front[0], 0, self.front[2]])
            move_dir = move_dir / np.linalg.norm(move_dir)
            self.position -= move_dir * velocity
        elif direction == "LEFT":
            self.position -= self.right * velocity
        elif direction == "RIGHT":
            self.position += self.right * velocity

    def process_zoom(self, offset: float):
        """
        Zoom in/out by moving camera along front vector.
        offset > 0: Zoom In
        offset < 0: Zoom Out
        """
        zoom_sensitivity = 2.0

        # Move along front vector
        # We want to zoom towards what we are looking at
        move = self.front * offset * zoom_sensitivity
        new_pos = self.position + move

        # Constraint: logic to prevent going under ground or too high
        if new_pos[1] < 2.0 and offset > 0:
            return  # Too close to ground
        if new_pos[1] > 100.0 and offset < 0:
            return  # Too high

        self.position = new_pos

    def get_mouse_ray(
        self, mouse_x, mouse_y, screen_width, screen_height
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns (origin, direction) of ray from camera through mouse position.
        """
        # NDC
        x = (2.0 * mouse_x) / screen_width - 1.0
        y = 1.0 - (2.0 * mouse_y) / screen_height  # Flip Y
        z = 1.0

        # Clip Space
        ray_nds = np.array(
            [x, y, -1.0, 1.0], dtype=np.float32
        )  # using -1 for forward? usually we want direction

        # To View Space
        proj = self.get_projection_matrix(screen_width, screen_height)
        inv_proj = np.linalg.inv(proj)

        ray_eye = np.dot(inv_proj, np.array([x, y, -1.0, 1.0]))
        ray_eye = np.array(
            [ray_eye[0], ray_eye[1], -1.0, 0.0]
        )  # Z=-1 forward, W=0 for vector

        # To World Space
        view = self.get_view_matrix()
        inv_view = np.linalg.inv(view)

        ray_world = np.dot(inv_view, ray_eye)
        ray_world = ray_world[:3]  # vec3
        ray_world = ray_world / np.linalg.norm(ray_world)

        return self.position, ray_world
