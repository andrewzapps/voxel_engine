from types import SimpleNamespace

import glm

from voxel_handler import VoxelHandler


def make_handler(voxels, origin, forward):
    #bypass __init__ so we don't need a real gl context just to test the DDA math
    handler = VoxelHandler.__new__(VoxelHandler)
    handler.max_distance = 8.0
    world = SimpleNamespace(get_voxel=lambda x, y, z: voxels.get((x, y, z), 0))
    handler.app = SimpleNamespace(
        player=SimpleNamespace(position=glm.vec3(*origin), forward=glm.vec3(*forward)),
        scene=SimpleNamespace(world=world),
    )
    return handler


def test_raycast_hits_face_normal_pointing_back_at_the_player():
    voxels = {(5, 0, 0): 1}
    handler = make_handler(voxels, origin=(0.5, 0.5, 0.5), forward=(1, 0, 0))

    hit = handler.raycast()

    assert hit is not None
    block, normal = hit
    assert block == (5, 0, 0)
    assert normal == (-1, 0, 0)


def test_raycast_from_above_hits_top_face():
    voxels = {(0, 3, 0): 1}
    handler = make_handler(voxels, origin=(0.5, 10.5, 0.5), forward=(0, -1, 0))

    block, normal = handler.raycast()

    assert block == (0, 3, 0)
    assert normal == (0, 1, 0)


def test_raycast_misses_when_nothing_in_range():
    handler = make_handler({}, origin=(0.5, 0.5, 0.5), forward=(1, 0, 0))

    assert handler.raycast() is None
