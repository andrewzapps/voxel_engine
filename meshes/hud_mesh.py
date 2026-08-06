import numpy as np

from meshes.base_mesh import baseMesh


class HudMesh(baseMesh):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.ctx = app.ctx
        self.program = app.shader_program.hud

        self.vbo_format = '2f 2f'
        self.attrs = ('in_position', 'in_uv')
        self.vao = self.get_vao()

    def get_vertex_data(self):
        #a single quad covering the whole screen, straight in clip space
        positions = [
            (-1, -1), (1, -1), (1, 1),
            (-1, -1), (1, 1), (-1, 1),
        ]
        uvs = [
            (0, 0), (1, 0), (1, 1),
            (0, 0), (1, 1), (0, 1),
        ]
        return np.hstack([positions, uvs]).astype('float32')
