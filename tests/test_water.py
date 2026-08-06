import glm

from settings import CHUNK_VOL
from world import World


class StubApp:
    save_data = None


class StubChunk:
    def __init__(self, voxels):
        self.voxels = voxels


def make_world_with_voxel_at_origin(voxel_id):
    import numpy as np

    world = World.__new__(World)
    world.app = StubApp()
    voxels = np.zeros(CHUNK_VOL, dtype='uint8')
    voxels[0] = voxel_id  # local (0,0,0)
    world.chunks = {(0, 0, 0): StubChunk(voxels)}
    return world


def test_aabb_overlaps_water_when_standing_in_it():
    from blocks import WATER

    world = make_world_with_voxel_at_origin(WATER)

    overlaps = world.aabb_overlaps_water(glm.vec3(0.2, 0.2, 0.2), glm.vec3(0.8, 0.8, 0.8))

    assert overlaps is True


def test_aabb_does_not_overlap_water_when_nowhere_near_it():
    from blocks import WATER

    world = make_world_with_voxel_at_origin(WATER)

    overlaps = world.aabb_overlaps_water(glm.vec3(50, 50, 50), glm.vec3(51, 51, 51))

    assert overlaps is False


def test_stone_does_not_count_as_water():
    from blocks import STONE

    world = make_world_with_voxel_at_origin(STONE)

    overlaps = world.aabb_overlaps_water(glm.vec3(0.2, 0.2, 0.2), glm.vec3(0.8, 0.8, 0.8))

    assert overlaps is False
