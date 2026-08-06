import numpy as np

from meshes.chunk_mesh_builder import build_chunk_mesh, get_neighbor_slot
from settings import CHUNK_SIZE, CHUNK_VOL
from world import EMPTY_CHUNK_VOXELS, World


class StubChunk:
    def __init__(self, voxels):
        self.voxels = voxels


def test_get_neighbor_slot_center_is_13():
    assert get_neighbor_slot(0, 0, 0) == 13


def test_gather_neighbor_voxels_puts_the_right_chunk_in_the_right_slot():
    world = World.__new__(World)
    world.chunks = {
        (0, 0, 0): StubChunk(np.full(CHUNK_VOL, 1, dtype='uint8')),
        (1, 0, 0): StubChunk(np.full(CHUNK_VOL, 2, dtype='uint8')),
    }
    neighbors = world.gather_neighbor_voxels((0, 0, 0))

    #stepping past CHUNK_SIZE on x should land in whatever slot the +x
    #neighbor chunk occupies
    slot = get_neighbor_slot(CHUNK_SIZE, 0, 0)
    assert neighbors[slot][0] == 2


def test_missing_neighbor_chunk_is_treated_as_air():
    world = World.__new__(World)
    world.chunks = {(0, 0, 0): StubChunk(np.full(CHUNK_VOL, 1, dtype='uint8'))}
    neighbors = world.gather_neighbor_voxels((0, 0, 0))

    slot = get_neighbor_slot(-1, 0, 0)
    assert np.array_equal(neighbors[slot], EMPTY_CHUNK_VOXELS)


def test_solid_chunk_surrounded_by_solid_neighbors_has_no_visible_faces():
    chunk_voxels = np.full(CHUNK_VOL, 1, dtype='uint8')
    neighbor_voxels = np.full((27, CHUNK_VOL), 1, dtype='uint8')
    neighbor_light = np.zeros((27, CHUNK_VOL), dtype='uint8')

    vertex_data = build_chunk_mesh(
        chunk_voxels, format_size=2, neighbor_voxels=neighbor_voxels,
        neighbor_sky_light=neighbor_light, neighbor_block_light=neighbor_light,
    )

    assert len(vertex_data) == 0


def test_single_voxel_surrounded_by_air_gets_all_six_faces():
    chunk_voxels = np.zeros(CHUNK_VOL, dtype='uint8')
    chunk_voxels[0] = 1  # x=0, y=0, z=0
    neighbor_voxels = np.zeros((27, CHUNK_VOL), dtype='uint8')
    neighbor_light = np.zeros((27, CHUNK_VOL), dtype='uint8')

    vertex_data = build_chunk_mesh(
        chunk_voxels, format_size=2, neighbor_voxels=neighbor_voxels,
        neighbor_sky_light=neighbor_light, neighbor_block_light=neighbor_light,
    )

    #6 faces * 2 triangles * 3 vertices, 2 words (packed_data + light) each
    assert len(vertex_data) == 72
