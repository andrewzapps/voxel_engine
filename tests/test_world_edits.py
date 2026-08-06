import numpy as np

from settings import CHUNK_SIZE, CHUNK_VOL
from world import World


class StubApp:
    save_data = None


def make_world_with_edits(edits):
    world = World.__new__(World)
    world.app = StubApp()
    world.chunks = {}
    world.edits = edits
    world.light_sources = {}
    return world


def test_set_voxel_records_an_edit(monkeypatch):
    world = make_world_with_edits({})

    class StubChunk:
        def __init__(self):
            self.voxels = np.zeros(CHUNK_VOL, dtype='uint8')
            self.sky_light = np.zeros(CHUNK_VOL, dtype='uint8')
            self.block_light = np.zeros(CHUNK_VOL, dtype='uint8')

        def rebuild_mesh(self):
            pass

    chunk = StubChunk()
    world.chunks[(0, 0, 0)] = chunk
    monkeypatch.setattr(world, 'rebuild_chunks_around', lambda *a: None)

    world.set_voxel(1, 1, 1, 5)

    assert world.edits[(1, 1, 1)] == 5


def test_loaded_chunk_gets_edits_applied_on_top_of_generated_terrain():
    from world_objects.chunk import Chunk

    #a fake generated chunk that's solid everywhere so we can prove the
    #edit (an air pocket) actually overwrote the generated block
    world = make_world_with_edits({(5, 5, 5): 0})

    class StubGeneratedChunk(Chunk):
        def build_voxels(self):
            import numpy as np
            from settings import CHUNK_VOL
            return np.full(CHUNK_VOL, 3, dtype='uint8')

    chunk = StubGeneratedChunk(world, position=(0, 0, 0))
    chunk.voxels = chunk.build_voxels()
    world._apply_edits(chunk, (0, 0, 0))

    from world import _local_index
    assert chunk.voxels[_local_index(5, 5, 5)] == 0
    assert chunk.voxels[_local_index(6, 6, 6)] == 3  # untouched terrain stays as generated
