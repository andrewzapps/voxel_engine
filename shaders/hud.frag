#version 330 core

layout (location = 0) out vec4 fragColor;

uniform sampler2D u_hud_texture;

in vec2 uv;

void main()
{
    fragColor = texture(u_hud_texture, uv);
}
