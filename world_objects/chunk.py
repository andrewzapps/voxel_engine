from settings import *

class Chunk:
    def __init__(self, app):
        self.app = app
        self.voxels: np.array = self.build_voxels
    
    def build_voxels(self):
        #empty chunk
        voxels = np.zeros(CHUNK_VOL, dtype = 'uint8')

        #fill
        for x in range(CHUNK_SIZE):
            for z in range(CHUNK_SIZE):
                for y in range(CHUNK_SIZE):
                    #1d array instead of 3d, formula to convert 3d position into a single index
                    voxels[x + CHUNK_SIZE * z + CHUNK_AREA * y] = 1
        return voxels