from OpenGL.GL import *
from typing import Optional


def create_shader_program(vertex_source: str, fragment_source: str) -> Optional[int]:
    """Compiles and links a shader program."""

    # Compile Vertex Shader
    vertex_shader = glCreateShader(GL_VERTEX_SHADER)
    glShaderSource(vertex_shader, vertex_source)
    glCompileShader(vertex_shader)

    if not glGetShaderiv(vertex_shader, GL_COMPILE_STATUS):
        print(
            f"Vertex Shader Compilation Error: {glGetShaderInfoLog(vertex_shader).decode()}"
        )
        return None

    # Compile Fragment Shader
    fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
    glShaderSource(fragment_shader, fragment_source)
    glCompileShader(fragment_shader)

    if not glGetShaderiv(fragment_shader, GL_COMPILE_STATUS):
        print(
            f"Fragment Shader Compilation Error: {glGetShaderInfoLog(fragment_shader).decode()}"
        )
        return None

    # Link Program
    shader_program = glCreateProgram()
    glAttachShader(shader_program, vertex_shader)
    glAttachShader(shader_program, fragment_shader)
    glLinkProgram(shader_program)

    if not glGetProgramiv(shader_program, GL_LINK_STATUS):
        print(f"Shader Linking Error: {glGetProgramInfoLog(shader_program).decode()}")
        return None

    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)

    return shader_program
