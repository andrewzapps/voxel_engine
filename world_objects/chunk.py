from settings import *
from blocks import GRASS, DIRT, SAND, STONE, WATER
from lighting import sky_light_column
from meshes.chunk_mesh import chunkMesh
from world_gen import cave_column, is_cave_voxel, ore_id, terrain_height, SAND_LEVEL, SEA_LEVEL

class Chunk:
    def __init__(self, world, position):
        self.app = world.app
        self.world = world 
        self.position = position
        self.m_model = self.get_model_matrix()
        self.voxels: np.array = None
        self.sky_light: np.array = None
        self.block_light: np.array = None
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

    def release_mesh(self):
        if self.mesh is None:
            return
        if self.mesh.vao is not None:
            self.mesh.vao.release()
        if self.mesh.water_vao is not None:
            self.mesh.water_vao.release()
        self.mesh = None

    def rebuild_mesh(self):
        self.release_mesh()

        self.is_empty = not np.any(self.voxels)
        if not self.is_empty:
            self.mesh = chunkMesh(self)

    def render(self):
        if self.mesh is not None:
            self.set_uniform()
            self.mesh.render()

    def render_water(self):
        if self.mesh is not None:
            self.set_uniform()
            self.mesh.render_water()
    
    def build_voxels(self):
        #empty chunk
        voxels = np.zeros(CHUNK_VOL, dtype = 'uint8')
        sky_light = np.zeros(CHUNK_VOL, dtype = 'uint8')

        #fill chunk

        cx, cy, cz = glm.ivec3(self.position) * CHUNK_SIZE
        ore_cache = {}

        for x in range(CHUNK_SIZE):
            for z in range(CHUNK_SIZE):
                wx = x + cx
                wz = z + cz
                world_height = terrain_height(wx, wz)
                local_height = min(world_height - cy, CHUNK_SIZE)
                cave_active, cave_center, cave_width = cave_column(wx, wz, world_height)
                beach = world_height - 1 <= SAND_LEVEL

                column_sky_light = sky_light_column(world_height, cy)
                for y in range(CHUNK_SIZE):
                    sky_light[x + CHUNK_SIZE * z + CHUNK_AREA * y] = column_sky_light[y]

                for y in range(max(0, local_height)):
                    wy = y + cy

                    if is_cave_voxel(wy, world_height, cave_active, cave_center, cave_width):
                        continue

                    depth = world_height - 1 - wy
                    if depth == 0:
                        block_id = SAND if beach else GRASS
                    elif depth < 4:
                        block_id = SAND if beach else DIRT
                    else:
                        block_id = ore_id(wx, wy, wz, world_height, ore_cache) or STONE
                    voxels[x + CHUNK_SIZE * z + CHUNK_AREA * y] = block_id

                #anything still open between the terrain and sea level fills
                #in with water - lakes/oceans wherever the ground dips low
                if world_height <= SEA_LEVEL:
                    water_start = max(0, local_height)
                    water_end = min(SEA_LEVEL - cy, CHUNK_SIZE - 1)
                    for y in range(water_start, water_end + 1):
                        voxels[x + CHUNK_SIZE * z + CHUNK_AREA * y] = WATER

        if np.any(voxels):
            self.is_empty = False

        self.sky_light = sky_light
        self.block_light = np.zeros(CHUNK_VOL, dtype = 'uint8')

        return voxels
