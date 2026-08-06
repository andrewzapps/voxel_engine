from meshes.base_mesh import baseMesh
from meshes.chunk_mesh_builder import build_chunk_mesh

class chunkMesh(baseMesh):
    def __init__(self, chunk):
        super().__init__()
        self.app = chunk.app
        self.chunk = chunk
        self.ctx = self.app.ctx
        self.program = self.app.shader_program.chunk

        self.vbo_format = '1u4 1u4'
        self.format_size = sum(int(fmt[:1]) for fmt in self.vbo_format.split())
        self.attrs = ('packed_data', 'light_data')
        self.vao = self.get_vao()

    def get_vertex_data(self):
        neighbor_sky_light, neighbor_block_light = self.chunk.world.gather_neighbor_light(self.chunk.position)
        mesh = build_chunk_mesh(
            chunk_voxels = self.chunk.voxels,
            format_size = self.format_size,
            neighbor_voxels = self.chunk.world.gather_neighbor_voxels(self.chunk.position),
            neighbor_sky_light = neighbor_sky_light,
            neighbor_block_light = neighbor_block_light,
        )
        return mesh
