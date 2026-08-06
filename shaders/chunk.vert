#version 330 core

layout (location = 0) in uint packed_data;
layout (location = 1) in uint light_data;

int x, y, z;
int voxel_id;
int face_id;
int ao_id;
int flip_id;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;

//texture atlas: voxel_id * 6 + face_id -> tile index in a u_atlas_cols wide grid
uniform int u_block_tiles[384];
uniform int u_atlas_cols;

//0..1, how much outdoor sky light actually counts right now - see lighting.py
uniform float u_day_factor;

out vec2 uv;
out float shading;

const float ao_values[4] = float[4](0.1, 0.25, 0.5, 1.0);

const float face_shading[6] = float[6](
    1.0, 0.5, //top bottom
    0.5, 0.8, //rl
    0.5, 0.6 //front back
);

const vec2 uv_coords[4] = vec2[4](
    vec2(0, 0), vec2(0, 1),
    vec2(1, 0), vec2(1, 1)
);

const int uv_indices[24] = int[24](
    1, 0, 2, 1, 2, 3,  //tex coords indices for verticies of an even face
    3, 0, 2, 3, 1, 0,   //odd face
    3, 1, 0, 3, 0, 2,   //even flipped face
    1, 2, 3, 1, 0, 2    // odd flipped face
);

void unpack(uint packed_data)
{
    //a, b, c, d, e, f, g = x, y, z, voxel_id, face_id, ao_id, flip_id
    uint b_bit = 6u, c_bit = 6u, d_bit = 8u, e_bit = 3u, f_bit = 2u, g_bit = 1u;
    uint b_mask = 63u, c_mask = 63u, d_mask = 255u, e_mask = 7u, f_mask = 3u, g_mask = 1u;

    uint fg_bit = f_bit + g_bit;
    uint efg_bit = e_bit + fg_bit;
    uint defg_bit = d_bit + efg_bit;
    uint cdefg_bit = c_bit + defg_bit;
    uint bcdefg_bit = b_bit + cdefg_bit;

    //unpacking data
    x = int(packed_data >> bcdefg_bit);
    y = int((packed_data >> cdefg_bit) & b_mask);
    z = int((packed_data >> defg_bit) & c_mask);

    voxel_id = int((packed_data >> efg_bit) & d_mask);
    face_id = int((packed_data >> fg_bit) & e_mask);
    ao_id = int((packed_data >> g_bit) & f_mask);
    flip_id = int(packed_data & g_mask);
}

void main()
{
    unpack(packed_data);

    vec3 in_position = vec3(x, y, z);
    int uv_index = gl_VertexID %  6 + ((face_id & 1) + flip_id * 2) * 6;

    vec2 corner_uv = uv_coords[uv_indices[uv_index]];
    int tile = u_block_tiles[voxel_id * 6 + face_id];
    vec2 tile_origin = vec2(tile % u_atlas_cols, tile / u_atlas_cols);
    uv = (tile_origin + corner_uv) / float(u_atlas_cols);

    uint sky_light = light_data & 0xFFu;
    uint block_light = (light_data >> 8) & 0xFFu;
    float light = max(float(block_light) / 15.0, (float(sky_light) / 15.0) * u_day_factor);

    shading = face_shading[face_id] * ao_values[ao_id] * light;
    gl_Position = m_proj * m_view * m_model * vec4(in_position, 1.0);
}
