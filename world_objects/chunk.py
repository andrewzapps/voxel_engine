from settings import *
from meshes.chunk_mesh import chunkMesh

class Chunk:
    def __init__(self, app):
        self.app = app
        self.voxels: np.array = self.build_voxels()
        self.mesh: chunkMesh = None
        self.build_mesh()

    def build_mesh(self):
        self.mesh = chunkMesh(self)

    def render(self):
        self.mesh.render()
    
    def build_voxels(self):
        #empty chunk
        voxels = np.zeros(CHUNK_VOL, dtype = 'uint8')

        #fill
        for x in range(CHUNK_SIZE):
            for z in range(CHUNK_SIZE):
                for y in range(CHUNK_SIZE):
                    #1d array instead of 3d, formula to convert 3d position into a single index
                    voxels[x + CHUNK_SIZE * z + CHUNK_AREA * y] = x + y + z
        return voxels
