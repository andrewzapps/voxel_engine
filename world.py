from settings import *
from world_objects.chunk import Chunk
from meshes.chunk_mesh_builder import get_chunk_index


def _local_index(lx, ly, lz):
    return lx + CHUNK_SIZE * lz + CHUNK_AREA * ly


class World():
    def __init__(self, app):
        self.app = app
        self.chunks = [None for _ in range(WORLD_VOL)]
        self.voxels = np.empty([WORLD_VOL, CHUNK_VOL], dtype = 'uint8')
        self.build_chunks()
        self.build_chunk_mesh()

    def build_chunks(self):
        for x in range(WORLD_W):
            for y in range(WORLD_H):
                for z in range(WORLD_D):
                    chunk = Chunk(self, position = (x, y, z))

                    chunk_index = x + WORLD_W * z + WORLD_AREA * y
                    self.chunks[chunk_index] = chunk 

                    #put the chunk voxels in a seperate array
                    self.voxels[chunk_index] = chunk.build_voxels()

                    #get pointer to voxels
                    chunk.voxels = self.voxels[chunk_index]

    def build_chunk_mesh(self):
        for chunk in self.chunks:
            chunk.build_mesh()

    def is_solid(self, wx, wy, wz):
        return self.get_voxel(wx, wy, wz) != 0

    def collides_aabb(self, min_pos, max_pos):
        min_x = int(glm.floor(min_pos.x))
        min_y = int(glm.floor(min_pos.y))
        min_z = int(glm.floor(min_pos.z))
        max_x = int(glm.floor(max_pos.x))
        max_y = int(glm.floor(max_pos.y))
        max_z = int(glm.floor(max_pos.z))

        for wx in range(min_x, max_x + 1):
            for wy in range(min_y, max_y + 1):
                for wz in range(min_z, max_z + 1):
                    if self.is_solid(wx, wy, wz):
                        if (min_pos.x < wx + 1 and max_pos.x > wx and
                                min_pos.y < wy + 1 and max_pos.y > wy and
                                min_pos.z < wz + 1 and max_pos.z > wz):
                            return True
        return False

    def get_ground_height(self, wx, wz):
        wx, wz = int(glm.floor(wx)), int(glm.floor(wz))
        for wy in range(WORLD_H * CHUNK_SIZE - 1, -1, -1):
            if self.is_solid(wx, wy, wz):
                return wy + 1
        return 0

    def get_footprint_ground(self, min_x, max_x, min_z, max_z):
        top = 0
        for wx in range(min_x, max_x + 1):
            for wz in range(min_z, max_z + 1):
                top = max(top, self.get_ground_height(wx, wz))
        return top

    def get_voxel(self, wx, wy, wz):
        chunk_index = get_chunk_index((wx, wy, wz))
        if chunk_index == -1:
            return 0
        lx, ly, lz = wx % CHUNK_SIZE, wy % CHUNK_SIZE, wz % CHUNK_SIZE
        return self.voxels[chunk_index][_local_index(lx, ly, lz)]

    def set_voxel(self, wx, wy, wz, voxel_id):
        chunk_index = get_chunk_index((wx, wy, wz))
        if chunk_index == -1:
            return False

        lx, ly, lz = wx % CHUNK_SIZE, wy % CHUNK_SIZE, wz % CHUNK_SIZE
        self.voxels[chunk_index][_local_index(lx, ly, lz)] = voxel_id
        self.rebuild_chunks_around(wx, wy, wz)
        return True

    def remove_voxel(self, wx, wy, wz):
        return self.set_voxel(wx, wy, wz, 0)

    def rebuild_chunks_around(self, wx, wy, wz):
        lx, ly, lz = wx % CHUNK_SIZE, wy % CHUNK_SIZE, wz % CHUNK_SIZE
        indices = {get_chunk_index((wx, wy, wz))}

        if lx == 0:
            indices.add(get_chunk_index((wx - 1, wy, wz)))
        if lx == CHUNK_SIZE - 1:
            indices.add(get_chunk_index((wx + 1, wy, wz)))
        if ly == 0:
            indices.add(get_chunk_index((wx, wy - 1, wz)))
        if ly == CHUNK_SIZE - 1:
            indices.add(get_chunk_index((wx, wy + 1, wz)))
        if lz == 0:
            indices.add(get_chunk_index((wx, wy, wz - 1)))
        if lz == CHUNK_SIZE - 1:
            indices.add(get_chunk_index((wx, wy, wz + 1)))

        for chunk_index in indices:
            if chunk_index >= 0:
                self.chunks[chunk_index].rebuild_mesh()

    def update(self):
        pass

    def render(self):
        for chunk in self.chunks:
            chunk.render()
