#version 330 core

layout (location = 0) out vec4 fragColor;

const vec3 gamma = vec3(2.2);
const vec3 inv_gamma = 1 / gamma;

uniform sampler2D u_texture_0;

in vec2 uv;
in float shading;

void main()
{
    vec4 tex = texture(u_texture_0, uv);
    vec3 tex_col = pow(tex.rgb, gamma);

    tex_col *= shading;

    tex_col = pow(tex_col, inv_gamma);
    //water/glass tiles carry real alpha in the atlas, opaque tiles are
    //always 1.0 - same shader draws both passes, this just lets it through
    fragColor = vec4(tex_col, tex.a);
}
