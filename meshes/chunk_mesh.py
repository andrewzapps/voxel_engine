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

        #one pass over the voxels builds both buffers - water/glass faces
        #split off into their own vao so they can be drawn in a separate
        #pass without writing depth
        opaque_data, water_data = self._build_mesh_data()
        self.vao = self._build_vao(opaque_data)
        self.water_vao = self._build_vao(water_data)

    def _build_mesh_data(self):
        neighbor_sky_light, neighbor_block_light = self.chunk.world.gather_neighbor_light(self.chunk.position)
        return build_chunk_mesh(
            chunk_voxels = self.chunk.voxels,
            format_size = self.format_size,
            neighbor_voxels = self.chunk.world.gather_neighbor_voxels(self.chunk.position),
            neighbor_sky_light = neighbor_sky_light,
            neighbor_block_light = neighbor_block_light,
        )

    def _build_vao(self, vertex_data):
        if len(vertex_data) == 0:
            return None
        vbo = self.ctx.buffer(vertex_data)
        return self.ctx.vertex_array(
            self.program, [(vbo, self.vbo_format, *self.attrs)], skip_errors=True
        )

    def render_water(self):
        if self.water_vao is not None:
            self.water_vao.render()
