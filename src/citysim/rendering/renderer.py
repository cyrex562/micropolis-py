from OpenGL.GL import *
import numpy as np
from typing import List
from .camera import Camera
from .mesh import Mesh
from .shader import create_shader_program

# Basic Shader Source
VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in vec3 aColor;

out vec3 FragPos;
out vec3 Normal;
out vec3 Color;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform vec3 colorMod; // Add color modifier

void main()
{
    FragPos = vec3(model * vec4(aPos, 1.0));
    Normal = mat3(transpose(inverse(model))) * aNormal;
    Color = colorMod; 
    gl_Position = projection * view * vec4(FragPos, 1.0);
}
"""

# Instanced Shader
INSTANCED_VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in vec3 aColor;

// Instance Attributes
layout (location = 3) in mat4 aInstanceModel;
layout (location = 7) in vec3 aInstanceColor;

out vec3 FragPos;
out vec3 Normal;
out vec3 Color;

uniform mat4 view;
uniform mat4 projection;

void main()
{
    FragPos = vec3(aInstanceModel * vec4(aPos, 1.0));
    Normal = mat3(transpose(inverse(aInstanceModel))) * aNormal;
    Color = aInstanceColor;
    gl_Position = projection * view * vec4(FragPos, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330 core
out vec4 FragColor;

in vec3 FragPos;
in vec3 Normal;
in vec3 Color;

uniform vec3 lightPos;
uniform vec3 viewPos;
uniform vec3 lightColor;

void main()
{
    // Ambient
    float ambientStrength = 0.3;
    vec3 ambient = ambientStrength * lightColor;
    
    // Diffuse
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(lightPos - FragPos);
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = diff * lightColor;
    
    vec3 result = (ambient + diffuse) * Color;
    FragColor = vec4(result, 1.0);
}
"""


class Renderer:
    def __init__(self):
        # Compile Basic Shader
        self.shader = create_shader_program(VERTEX_SHADER, FRAGMENT_SHADER)
        if not self.shader:
            raise RuntimeError("Failed to compile basic shader")

        # Compile Instanced Shader
        self.instanced_shader = create_shader_program(
            INSTANCED_VERTEX_SHADER, FRAGMENT_SHADER
        )
        if not self.instanced_shader:
            raise RuntimeError("Failed to compile instanced shader")

        # Basic Uniforms
        self.model_loc = glGetUniformLocation(self.shader, "model")
        self.view_loc = glGetUniformLocation(self.shader, "view")
        self.proj_loc = glGetUniformLocation(self.shader, "projection")
        self.light_pos_loc = glGetUniformLocation(self.shader, "lightPos")
        self.view_pos_loc = glGetUniformLocation(self.shader, "viewPos")
        self.light_color_loc = glGetUniformLocation(self.shader, "lightColor")
        self.color_mod_loc = glGetUniformLocation(self.shader, "colorMod")

        # Instanced Uniforms
        self.inst_view_loc = glGetUniformLocation(self.instanced_shader, "view")
        self.inst_proj_loc = glGetUniformLocation(self.instanced_shader, "projection")
        self.inst_light_pos_loc = glGetUniformLocation(
            self.instanced_shader, "lightPos"
        )
        self.inst_view_pos_loc = glGetUniformLocation(self.instanced_shader, "viewPos")
        self.inst_light_color_loc = glGetUniformLocation(
            self.instanced_shader, "lightColor"
        )

    def use(self):
        glUseProgram(self.shader)
        # Default Lighting
        glUniform3f(self.light_pos_loc, 10.0, 50.0, 10.0)
        glUniform3f(self.light_color_loc, 1.0, 1.0, 0.9)

    def use_instanced(self):
        glUseProgram(self.instanced_shader)
        # Default Lighting
        glUniform3f(self.inst_light_pos_loc, 10.0, 50.0, 10.0)
        glUniform3f(self.inst_light_color_loc, 1.0, 1.0, 0.9)

    def set_camera(self, view, proj, pos):
        # Set for basic
        glUseProgram(self.shader)
        glUniformMatrix4fv(self.view_loc, 1, GL_TRUE, view)
        glUniformMatrix4fv(self.proj_loc, 1, GL_TRUE, proj)
        glUniform3f(self.view_pos_loc, *pos)

        # Set for instanced
        glUseProgram(self.instanced_shader)
        glUniformMatrix4fv(self.inst_view_loc, 1, GL_TRUE, view)
        glUniformMatrix4fv(self.inst_proj_loc, 1, GL_TRUE, proj)
        glUniform3f(self.inst_view_pos_loc, *pos)

        # Revert to valid state (caller will likely call use() or use_instanced() before draw)
        glUseProgram(0)

    def set_model_matrix(self, model):
        glUniformMatrix4fv(self.model_loc, 1, GL_TRUE, model)

    def update_viewport(self, width, height):
        glViewport(0, 0, width, height)
