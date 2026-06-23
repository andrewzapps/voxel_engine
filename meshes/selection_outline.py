import moderngl as mgl
import glm
import numpy as np

# Minecraft expands the selection box by 0.002 to avoid z-fighting
_EXPAND = 0.002
_EDGES = (
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 6), (6, 7), (7, 4),
    (0, 4), (1, 5), (2, 6), (3, 7),
)
_CORNERS = (
    (-_EXPAND, -_EXPAND, -_EXPAND),
    (1 + _EXPAND, -_EXPAND, -_EXPAND),
    (1 + _EXPAND, -_EXPAND, 1 + _EXPAND),
    (-_EXPAND, -_EXPAND, 1 + _EXPAND),
    (-_EXPAND, 1 + _EXPAND, -_EXPAND),
    (1 + _EXPAND, 1 + _EXPAND, -_EXPAND),
    (1 + _EXPAND, 1 + _EXPAND, 1 + _EXPAND),
    (-_EXPAND, 1 + _EXPAND, 1 + _EXPAND),
)
_OUTLINE_COLOR = (0.0, 0.0, 0.0)


class SelectionOutline:
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        self.program = app.shader_program.quad
        self.vao = self._build_vao()

    def _build_vao(self):
        vertices = []
        for i, j in _EDGES:
            for corner in (_CORNERS[i], _CORNERS[j]):
                vertices.extend(corner)
                vertices.extend(_OUTLINE_COLOR)

        vbo = self.ctx.buffer(np.array(vertices, dtype='f4'))
        return self.ctx.vertex_array(
            self.program,
            [(vbo, '3f 3f', 'in_position', 'in_color')],
        )

    def render(self, wx, wy, wz):
        player = self.app.player
        m_model = glm.translate(glm.mat4(), glm.vec3(wx, wy, wz))

        self.program['m_proj'].write(player.m_proj)
        self.program['m_view'].write(player.m_view)
        self.program['m_model'].write(m_model)

        self.ctx.disable(mgl.CULL_FACE)
        self.ctx.enable(mgl.DEPTH_TEST)
        self.vao.render(mode=mgl.LINES)
        self.ctx.enable(mgl.CULL_FACE)
