import numpy as np
from OpenGL.GL import *
import ctypes


class Mesh:
    """
    Represents a 3D mesh with VBO, VAO, and EBO.
    """

    def __init__(self, vertices: np.ndarray, indices: np.ndarray = None):
        self.vertices = vertices
        self.indices = indices
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.ebo = glGenBuffers(1) if indices is not None else None

        self.setup_mesh()

    def setup_mesh(self):
        glBindVertexArray(self.vao)

        # VBO
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(
            GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW
        )

        # EBO
        if self.indices is not None:
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
            glBufferData(
                GL_ELEMENT_ARRAY_BUFFER,
                self.indices.nbytes,
                self.indices,
                GL_STATIC_DRAW,
            )

        # Attribute pointers
        # Assumes format: [x, y, z, nx, ny, nz, r, g, b] (Position, Normal, Color)
        # Stride = 9 * 4 bytes
        stride = 9 * 4

        # Position (loc 0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))

        # Normal (loc 1)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * 4))

        # Color (loc 2)
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(6 * 4))

        glBindVertexArray(0)

    def draw(self):
        glBindVertexArray(self.vao)
        if self.indices is not None:
            glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        else:
            glDrawArrays(GL_TRIANGLES, 0, len(self.vertices) // 9)
        glBindVertexArray(0)

    def delete(self):
        glDeleteVertexArrays(1, [self.vao])
        glDeleteBuffers(1, [self.vbo])
        if self.ebo:
            glDeleteBuffers(1, [self.ebo])


class MeshBuilder:
    @staticmethod
    def create_cube() -> Mesh:
        """Creates a unit cube mesh centered at origin."""
        # vertices: pos(3), normal(3), color(3)
        # Simple cube
        vertices = np.array(
            [
                # Front face
                -0.5,
                -0.5,
                0.5,
                0.0,
                0.0,
                1.0,
                1.0,
                0.0,
                0.0,  # Bottom Left
                0.5,
                -0.5,
                0.5,
                0.0,
                0.0,
                1.0,
                1.0,
                0.0,
                0.0,  # Bottom Right
                0.5,
                0.5,
                0.5,
                0.0,
                0.0,
                1.0,
                1.0,
                0.0,
                0.0,  # Top Right
                -0.5,
                0.5,
                0.5,
                0.0,
                0.0,
                1.0,
                1.0,
                0.0,
                0.0,  # Top Left
                # Back face
                -0.5,
                -0.5,
                -0.5,
                0.0,
                0.0,
                -1.0,
                0.0,
                1.0,
                0.0,
                0.5,
                -0.5,
                -0.5,
                0.0,
                0.0,
                -1.0,
                0.0,
                1.0,
                0.0,
                0.5,
                0.5,
                -0.5,
                0.0,
                0.0,
                -1.0,
                0.0,
                1.0,
                0.0,
                -0.5,
                0.5,
                -0.5,
                0.0,
                0.0,
                -1.0,
                0.0,
                1.0,
                0.0,
                # ... (Should define all 6 faces for proper normals)
                # keeping simple for now with indices
            ],
            dtype=np.float32,
        )

        # But for distinct normals we usually duplicate vertices.
        # Let's verify if we need full 24 vertices.
        # For flat shading or simple block style, we want sharp edges.

        # PROPER CUBE DEFINITION (24 vertices)
        # Format: x, y, z, nx, ny, nz, r, g, b
        def face(n, c, v0, v1, v2, v3):
            # n: normal, c: color
            return [
                *v0,
                *n,
                *c,
                *v1,
                *n,
                *c,
                *v2,
                *n,
                *c,
                *v0,
                *n,
                *c,
                *v2,
                *n,
                *c,
                *v3,
                *n,
                *c,
            ]

        # Corners
        p0 = [-0.5, -0.5, 0.5]
        p1 = [0.5, -0.5, 0.5]
        p2 = [0.5, 0.5, 0.5]
        p3 = [-0.5, 0.5, 0.5]
        p4 = [-0.5, -0.5, -0.5]
        p5 = [0.5, -0.5, -0.5]
        p6 = [0.5, 0.5, -0.5]
        p7 = [-0.5, 0.5, -0.5]

        data = []
        # Front (0,1,2,3) Z+
        data.extend(face([0, 0, 1], [0.8, 0.2, 0.2], p0, p1, p2, p3))
        # Back (5,4,7,6) Z-
        data.extend(face([0, 0, -1], [0.2, 0.8, 0.2], p5, p4, p7, p6))
        # Top (3,2,6,7) Y+
        data.extend(face([0, 1, 0], [0.2, 0.2, 0.8], p3, p2, p6, p7))
        # Bottom (4,5,1,0) Y-
        data.extend(face([0, -1, 0], [0.8, 0.8, 0.2], p4, p5, p1, p0))
        # Right (1,5,6,2) X+
        data.extend(face([1, 0, 0], [0.2, 0.8, 0.8], p1, p5, p6, p2))
        # Left (4,0,3,7) X-
        data.extend(face([-1, 0, 0], [0.8, 0.2, 0.8], p4, p0, p3, p7))

        vertices = np.array(data, dtype=np.float32)
        return Mesh(vertices)

    @staticmethod
    def create_plane() -> Mesh:
        """Creates a unit plane on XZ centered at origin."""
        # vertices: pos(3), normal(3), color(3)
        # Normal is +Y (0, 1, 0)
        # Two triangles
        # p0 -- p1
        # |      |
        # p3 -- p2
        w = 1.0  # size
        h = 1.0

        x0, z0 = -w / 2, -h / 2
        x1, z1 = w / 2, h / 2

        # Positions
        p0 = [x0, 0, z0]
        p1 = [x1, 0, z0]
        p2 = [x1, 0, z1]
        p3 = [x0, 0, z1]

        n = [0, 1, 0]
        c = [1, 1, 1]  # White base

        vertices = np.array(
            [
                *p0,
                *n,
                *c,
                *p2,
                *n,
                *c,
                *p1,
                *n,
                *c,
                *p0,
                *n,
                *c,
                *p3,
                *n,
                *c,
                *p2,
                *n,
                *c,
            ],
            dtype=np.float32,
        )

        return Mesh(vertices)


class InstancedMesh(Mesh):
    def __init__(
        self,
        vertices: np.ndarray,
        indices: np.ndarray = None,
        max_instances: int = 4096,
    ):
        # Call parent to setup geometry (VAO, VBO, EBO)
        super().__init__(vertices, indices)
        self.max_instances = max_instances
        self.instance_vbo = glGenBuffers(1)
        self.setup_instance_buffer()

    def setup_instance_buffer(self):
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.instance_vbo)

        # Stride = sizeof(mat4) + sizeof(vec3) = 16 floats + 3 floats = 19 floats
        # 19 * 4 bytes = 76 bytes
        stride = 19 * 4

        # Initialize buffer with null data
        glBufferData(
            GL_ARRAY_BUFFER, self.max_instances * stride, None, GL_DYNAMIC_DRAW
        )

        # Instance Attributes (Locations 3, 4, 5, 6 for Mat4, 7 for Color)
        # Mat4 is 4 vec4s
        for i in range(4):
            loc = 3 + i
            glEnableVertexAttribArray(loc)
            glVertexAttribPointer(
                loc, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(i * 16)
            )
            glVertexAttribDivisor(loc, 1)  # Tell OpenGL this is per-instance

        # Color (Location 7)
        glEnableVertexAttribArray(7)
        glVertexAttribPointer(
            7, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(64)
        )  # 16*4 = 64
        glVertexAttribDivisor(7, 1)

        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def update_instances(self, data: np.ndarray):
        """
        Update instance data.
        Data format: Flat array of [Mat4(16), Color(3)] per instance.
        """
        glBindBuffer(GL_ARRAY_BUFFER, self.instance_vbo)
        # Orphan buffer?
        glBufferData(
            GL_ARRAY_BUFFER, self.max_instances * 19 * 4, None, GL_DYNAMIC_DRAW
        )
        # Subdata
        glBufferSubData(GL_ARRAY_BUFFER, 0, data.nbytes, data)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def draw(self, instance_count: int):
        glBindVertexArray(self.vao)
        if self.indices is not None:
            glDrawElementsInstanced(
                GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None, instance_count
            )
        else:
            glDrawArraysInstanced(
                GL_TRIANGLES, 0, len(self.vertices) // 9, instance_count
            )
        glBindVertexArray(0)
