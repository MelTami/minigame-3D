#version 400 core

layout (location = 0) in vec2 in_pos;

uniform mat4 u_ortho;
uniform mat4 u_model;

void main() {
    gl_Position = u_ortho * u_model * vec4(in_pos, 0.0, 1.0);
}
