from settings import *
from blocks import GRASS, DIRT, STONE
from meshes.chunk_mesh import chunkMesh

class Chunk:
    def __init__(self, world, position):
        self.app = world.app
        self.world = world 
        self.position = position
        self.m_model = self.get_model_matrix()
        self.voxels: np.array = None
        self.mesh: chunkMesh = None
        self.is_empty = True

    def get_model_matrix(self):
        m_model = glm.translate(glm.mat4(), glm.vec3(self.position) * CHUNK_SIZE)
        return m_model

    def set_uniform(self):
        self.mesh.program['m_model'].write(self.m_model)

    def build_mesh(self):
        if not self.is_empty:
            self.mesh = chunkMesh(self)

    def rebuild_mesh(self):
        if self.mesh is not None and self.mesh.vao is not None:
            self.mesh.vao.release()
            self.mesh = None

        self.is_empty = not np.any(self.voxels)
        if not self.is_empty:
            self.mesh = chunkMesh(self)

    def render(self):
        if self.mesh is not None:
            self.set_uniform()
            self.mesh.render()
    
    def build_voxels(self):
        #empty chunk
        voxels = np.zeros(CHUNK_VOL, dtype = 'uint8')

        #fill chunk 

        cx, cy, cz = glm.ivec3(self.position) * CHUNK_SIZE

        for x in range(CHUNK_SIZE):
            for z in range(CHUNK_SIZE):
                wx = x + cx
                wz = z + cz 
                world_height = int(glm.simplex(glm.vec2(wx, wz) * 0.01) * 32 + 32)
                local_height = min(world_height - cy, CHUNK_SIZE)

                for y in range(local_height):
                    wy = y + cy
                    depth = world_height - 1 - wy
                    if depth == 0:
                        block_id = GRASS
                    elif depth < 4:
                        block_id = DIRT
                    else:
                        block_id = STONE
                    voxels[x + CHUNK_SIZE * z + CHUNK_AREA * y] = block_id

        if np.any(voxels):
            self.is_empty = False

        
        return voxels
