#version 400 core

layout (location = 0) in vec3 in_pos;
layout (location = 1) in vec3 in_normal;
layout (location = 2) in vec2 in_uv;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_proj;
uniform mat3 u_normal_matrix;

out vec3 v_frag_pos;
out vec3 v_normal;
out vec2 v_uv;

void main() {
    vec4 world_pos = u_model * vec4(in_pos, 1.0);
    v_frag_pos = world_pos.xyz;
    v_normal = normalize(u_normal_matrix * in_normal);
    v_uv = in_uv;

    gl_Position = u_proj * u_view * world_pos;
}
