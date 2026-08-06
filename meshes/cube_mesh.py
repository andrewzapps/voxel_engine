import numpy as np

from meshes.base_mesh import baseMesh

#unit cube corners, 0..1 on every axis - mobs scale/translate this to their
#own size and position rather than each building their own geometry
_CORNERS = (
    (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
    (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1),
)
_FACES = (
    (0, 1, 2, 0, 2, 3),  # back   -z
    (5, 4, 7, 5, 7, 6),  # front  +z
    (4, 0, 3, 4, 3, 7),  # left   -x
    (1, 5, 6, 1, 6, 2),  # right  +x
    (3, 2, 6, 3, 6, 7),  # top    +y
    (4, 5, 1, 4, 1, 0),  # bottom -y
)


class CubeMesh(baseMesh):
    def __init__(self, app, color):
        super().__init__()
        self.app = app
        self.ctx = app.ctx
        self.program = app.shader_program.quad
        self.color = color

        self.vbo_format = '3f 3f'
        self.attrs = ('in_position', 'in_color')
        self.vao = self.get_vao()

    def get_vertex_data(self):
        positions = [_CORNERS[i] for face in _FACES for i in face]
        colors = [self.color] * len(positions)
        return np.hstack([positions, colors]).astype('float32')
