from settings import *
from numba import uint8

#neighbor_voxels is always the 27 chunks in a 3x3x3 block centered on the chunk
#being meshed (index 13), gathered by World.gather_neighbor_voxels each rebuild.
#this is what lets face culling see across chunk borders without needing one
#giant array sized for the whole world.
@njit
def get_neighbor_slot(x, y, z):
    dx = -1 if x < 0 else (1 if x >= CHUNK_SIZE else 0)
    dy = -1 if y < 0 else (1 if y >= CHUNK_SIZE else 0)
    dz = -1 if z < 0 else (1 if z >= CHUNK_SIZE else 0)
    return (dx + 1) + (dy + 1) * 3 + (dz + 1) * 9


@njit
def is_void(local_pos, neighbor_voxels):
    x, y, z = local_pos
    chunk_voxels = neighbor_voxels[get_neighbor_slot(x, y, z)]

    lx, ly, lz = x % CHUNK_SIZE, y % CHUNK_SIZE, z % CHUNK_SIZE
    voxel_index = lx + CHUNK_SIZE * lz + CHUNK_AREA * ly

    if chunk_voxels[voxel_index]:
        return False
    return True


@njit
def get_ao(local_pos, neighbor_voxels, plane):
    x, y, z = local_pos

    if plane == 'Y': #yplane
        a = is_void((x    , y, z - 1), neighbor_voxels)
        b = is_void((x - 1, y, z - 1), neighbor_voxels)
        c = is_void((x - 1, y, z    ), neighbor_voxels)
        d = is_void((x - 1, y, z + 1), neighbor_voxels)
        e = is_void((x    , y, z + 1), neighbor_voxels)
        f = is_void((x + 1, y, z + 1), neighbor_voxels)
        g = is_void((x + 1, y, z    ), neighbor_voxels)
        h = is_void((x + 1, y, z - 1), neighbor_voxels)

    elif plane == 'X': #xplane
        a = is_void((x, y    , z - 1), neighbor_voxels)
        b = is_void((x, y - 1, z - 1), neighbor_voxels)
        c = is_void((x, y - 1, z    ), neighbor_voxels)
        d = is_void((x, y - 1, z + 1), neighbor_voxels)
        e = is_void((x, y    , z + 1), neighbor_voxels)
        f = is_void((x, y + 1, z + 1), neighbor_voxels)
        g = is_void((x, y + 1, z    ), neighbor_voxels)
        h = is_void((x, y + 1, z - 1), neighbor_voxels)

    else: #z plane
        a = is_void((x - 1, y    , z), neighbor_voxels)
        b = is_void((x - 1, y - 1, z), neighbor_voxels)
        c = is_void((x    , y - 1, z), neighbor_voxels)
        d = is_void((x + 1, y - 1, z), neighbor_voxels)
        e = is_void((x + 1, y    , z), neighbor_voxels)
        f = is_void((x + 1, y + 1, z), neighbor_voxels)
        g = is_void((x    , y + 1, z), neighbor_voxels)
        h = is_void((x - 1, y + 1, z), neighbor_voxels)

    #ambient occlusion
    ao = (a + b + c), (g + h + a), (e + f + g), (c + d + e)
    return ao

@njit
def pack_data(x, y, z, voxel_id, face_id, ao_id, flip_id):
    # x: 6b y: 6b z: 6b voxel_id: 8b face_id: 3b ao_id: 2b flip_id: 1b
    a, b, c, d, e, f, g = x, y, z, voxel_id, face_id, ao_id, flip_id

    b_bit, c_bit, d_bit, e_bit, f_bit, g_bit = 6, 6, 8, 3, 2, 1
    fg_bit = f_bit + g_bit
    efg_bit = e_bit + fg_bit
    defg_bit = d_bit + efg_bit
    cdefg_bit = c_bit + defg_bit
    bcdefg_bit = b_bit + cdefg_bit

    packed_data = (
        a << bcdefg_bit |
        b << cdefg_bit |
        c << defg_bit |
        d << efg_bit |
        e << fg_bit |
        f << g_bit | g
    )
    return packed_data


@njit
def add_data(vertex_data, index, *vertices):
    for vertex in vertices:
        vertex_data[index] = vertex
        index += 1
    return index

@njit
def build_chunk_mesh(chunk_voxels, format_size, neighbor_voxels):
    vertex_data = np.empty(CHUNK_VOL * 18 * format_size, dtype = 'uint32')
    index = 0

    for x in range(CHUNK_SIZE):
        for y in range(CHUNK_SIZE):
            for z in range(CHUNK_SIZE):
                voxel_id = chunk_voxels[x + CHUNK_SIZE * z + CHUNK_AREA * y]
                if not voxel_id:
                    continue

                #top face
                if is_void((x, y + 1, z), neighbor_voxels):
                    #get ao values
                    ao = get_ao((x, y + 1, z), neighbor_voxels, plane = 'Y')
                    flip_id = ao[1] + ao[3] > ao[0] + ao[2]

                    #format: x, y, z, voxel_id, face_id, ao_id
                    v0 = pack_data(x    , y + 1, z    , voxel_id, 0, ao[0], flip_id)
                    v1 = pack_data(x + 1, y + 1, z    , voxel_id, 0, ao[1], flip_id)
                    v2 = pack_data(x + 1, y + 1, z + 1, voxel_id, 0, ao[2], flip_id)
                    v3 = pack_data(x    , y + 1, z + 1, voxel_id, 0, ao[3], flip_id)

                    #flip triangle vertices for each face
                    if flip_id:
                        index = add_data(vertex_data, index, v1, v0, v3, v1, v3, v2)
                    else:
                        index = add_data(vertex_data, index, v0, v3, v2, v0, v2, v1)

                #bottom face
                if is_void((x, y - 1, z), neighbor_voxels):
                    ao = get_ao((x, y - 1, z), neighbor_voxels, plane = 'Y')
                    flip_id = ao[1] + ao[3] > ao[0] + ao[2]

                    v0 = pack_data(x    , y, z    , voxel_id, 1, ao[0], flip_id)
                    v1 = pack_data(x + 1, y, z    , voxel_id, 1, ao[1], flip_id)
                    v2 = pack_data(x + 1, y, z + 1, voxel_id, 1, ao[2], flip_id)
                    v3 = pack_data(x    , y, z + 1, voxel_id, 1, ao[3], flip_id)

                    if flip_id:
                        index = add_data(vertex_data, index, v1, v3, v0, v1, v2, v3)
                    else:
                        index = add_data(vertex_data, index, v0, v2, v3, v0, v1, v2)

                #right face
                if is_void((x + 1, y, z), neighbor_voxels):
                    ao = get_ao((x + 1, y, z), neighbor_voxels, plane = 'X')
                    flip_id = ao[1] + ao[3] > ao[0] + ao[2]

                    v0 = pack_data(x + 1, y    , z    , voxel_id, 2, ao[0], flip_id)
                    v1 = pack_data(x + 1, y + 1, z    , voxel_id, 2, ao[1], flip_id)
                    v2 = pack_data(x + 1, y + 1, z + 1, voxel_id, 2, ao[2], flip_id)
                    v3 = pack_data(x + 1, y    , z + 1, voxel_id, 2, ao[3], flip_id)

                    if flip_id:
                        index = add_data(vertex_data, index, v3, v0, v1, v3, v1, v2)
                    else:
                        index = add_data(vertex_data, index, v0, v1, v2, v0, v2, v3)

                #left face
                if is_void((x - 1, y, z), neighbor_voxels):
                    ao = get_ao((x - 1, y, z), neighbor_voxels, plane = 'X')
                    flip_id = ao[1] + ao[3] > ao[0] + ao[2]

                    v0 = pack_data(x, y    , z    , voxel_id, 3, ao[0], flip_id)
                    v1 = pack_data(x, y + 1, z    , voxel_id, 3, ao[1], flip_id)
                    v2 = pack_data(x, y + 1, z + 1, voxel_id, 3, ao[2], flip_id)
                    v3 = pack_data(x, y    , z + 1, voxel_id, 3, ao[3], flip_id)

                    if flip_id:
                        index = add_data(vertex_data, index, v3, v1, v0, v3, v2, v1)
                    else:
                        index = add_data(vertex_data, index, v0, v2, v1, v0, v3, v2)

                #back face
                if is_void((x, y, z - 1), neighbor_voxels):
                    ao = get_ao((x, y, z - 1), neighbor_voxels, plane = 'Z')
                    flip_id = ao[1] + ao[3] > ao[0] + ao[2]

                    v0 = pack_data(x    , y    , z, voxel_id, 4, ao[0], flip_id)
                    v1 = pack_data(x    , y + 1, z, voxel_id, 4, ao[1], flip_id)
                    v2 = pack_data(x + 1, y + 1, z, voxel_id, 4, ao[2], flip_id)
                    v3 = pack_data(x + 1, y    , z, voxel_id, 4, ao[3], flip_id)

                    if flip_id:
                        index = add_data(vertex_data, index, v3, v0, v1, v3, v1, v2)
                    else:
                        index = add_data(vertex_data, index, v0, v1, v2, v0, v2, v3)

                #front face
                if is_void((x, y, z + 1), neighbor_voxels):
                    ao = get_ao((x, y, z + 1), neighbor_voxels, plane = 'Z')
                    flip_id = ao[1] + ao[3] > ao[0] + ao[2]

                    v0 = pack_data(x    , y    , z + 1, voxel_id, 5, ao[0], flip_id)
                    v1 = pack_data(x    , y + 1, z + 1, voxel_id, 5, ao[1], flip_id)
                    v2 = pack_data(x + 1, y + 1, z + 1, voxel_id, 5, ao[2], flip_id)
                    v3 = pack_data(x + 1, y    , z + 1, voxel_id, 5, ao[3], flip_id)

                    if flip_id:
                        index = add_data(vertex_data, index, v3, v1, v0, v3, v2, v1)
                    else:
                        index = add_data(vertex_data, index, v0, v2, v1, v0, v3, v2)

    return vertex_data[:index]
