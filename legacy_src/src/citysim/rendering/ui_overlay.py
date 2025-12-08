from OpenGL.GL import *
import pygame
import numpy as np
from .shader import create_shader_program

# Simple pass-through vertex shader for full screen quad
VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec2 aPos;
layout (location = 1) in vec2 aTexCoords;

out vec2 TexCoords;

void main()
{
    gl_Position = vec4(aPos.x, aPos.y, 0.0, 1.0);
    TexCoords = aTexCoords;
}
"""

FRAGMENT_SHADER = """
#version 330 core
out vec4 FragColor;

in vec2 TexCoords;

uniform sampler2D screenTexture;

void main()
{
    vec4 col = texture(screenTexture, TexCoords);
    // Discard transparent pixels to allow seeing 3D scene behind
    if(col.a < 0.1)
        discard;
    FragColor = col;
}
"""


class UIOverlay:
    """
    Renders a Pygame Surface as a full-screen overlay using OpenGL.
    """

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.shader = create_shader_program(VERTEX_SHADER, FRAGMENT_SHADER)

        # Quad vertices (NDC coordinates)
        # x, y, u, v
        vertices = np.array(
            [
                # positions   # texCoords
                -1.0,
                1.0,
                0.0,
                0.0,
                -1.0,
                -1.0,
                0.0,
                1.0,
                1.0,
                -1.0,
                1.0,
                1.0,
                -1.0,
                1.0,
                0.0,
                0.0,
                1.0,
                -1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.0,
            ],
            dtype=np.float32,
        )

        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))

        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(2 * 4))

        # Texture
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        # Initialize empty texture
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
        )

        self.tex_loc = glGetUniformLocation(self.shader, "screenTexture")

    def resize(self, width, height):
        self.width = width
        self.height = height
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
        )

    def render(self, surface: pygame.Surface):
        # Update texture from surface
        data = pygame.image.tobytes(surface, "RGBA", False)

        # Check if surface changed size
        if surface.get_width() != self.width or surface.get_height() != self.height:
            self.resize(surface.get_width(), surface.get_height())

        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexSubImage2D(
            GL_TEXTURE_2D,
            0,
            0,
            0,
            self.width,
            self.height,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            data,
        )

        # Render Quad
        glUseProgram(self.shader)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glUniform1i(self.tex_loc, 0)

        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)

        glDisable(GL_BLEND)
