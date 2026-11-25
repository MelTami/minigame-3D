#version 400 core

in vec3 v_frag_pos;
in vec3 v_normal;
in vec2 v_uv;

out vec4 frag_color;

struct Light {
    int type;          // 0 = pontual, 1 = conica (spotlight)
    vec3 position;
    vec3 direction;
    vec3 color;
    float constant;
    float linear;
    float quadratic;
    float cutOff;
    float outerCutOff;
    bool enabled;
};

struct Material {
    vec3 ka;
    vec3 kd;
    vec3 ks;
    float shininess;
};

uniform sampler2D u_texture;
uniform vec3 u_view_pos;
uniform Light u_lights[3];
uniform Material u_material;

vec3 calc_light(Light light, vec3 normal, vec3 frag_pos, vec3 view_dir, vec3 tex_color) {
    if (!light.enabled) {
        return vec3(0.0);
    }

    vec3 light_dir = normalize(light.position - frag_pos);
    float distance = length(light.position - frag_pos);
    float attenuation = 1.0 / (light.constant + light.linear * distance + light.quadratic * (distance * distance));

    float intensity = 1.0;
    if (light.type == 1) {
        float theta = dot(light_dir, normalize(-light.direction));
        float epsilon = light.cutOff - light.outerCutOff;
        intensity = clamp((theta - light.outerCutOff) / epsilon, 0.0, 1.0);
    }

    vec3 ambient = u_material.ka * light.color * tex_color;
    float diff = max(dot(normal, light_dir), 0.0);
    vec3 diffuse = u_material.kd * diff * light.color * tex_color;

    vec3 halfway_dir = normalize(light_dir + view_dir);
    float spec = pow(max(dot(normal, halfway_dir), 0.0), u_material.shininess);
    vec3 specular = u_material.ks * spec * light.color;

    return (ambient + (diffuse + specular) * intensity) * attenuation;
}

void main() {
    vec3 norm = normalize(v_normal);
    vec3 view_dir = normalize(u_view_pos - v_frag_pos);
    vec3 tex_color = texture(u_texture, v_uv).rgb;

    vec3 result = vec3(0.0);
    for (int i = 0; i < 3; i++) {
        result += calc_light(u_lights[i], norm, v_frag_pos, view_dir, tex_color);
    }

    vec3 srgb = pow(clamp(result, 0.0, 1.0), vec3(1.0 / 2.2));
    frag_color = vec4(srgb, 1.0);
}
