from settings import *
from blocks import ATLAS_COLS, build_tile_table

class shaderProgram:
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        #------shader------
        self.chunk = self.get_program(shader_name = 'chunk')
        self.quad = self.get_program(shader_name = 'quad')
        #------------------
        self.set_uniforms_on_init()

    def set_uniforms_on_init(self):
        m_proj = glm.perspective(V_FOV, ASPECT_RATIO, NEAR, FAR)
        self.chunk['m_proj'].write(m_proj)
        self.chunk['m_model'].write(glm.mat4())
        self.chunk['u_texture_0'] = 0
        self.chunk['u_atlas_cols'] = ATLAS_COLS
        self.chunk['u_block_tiles'].value = build_tile_table()

    def update(self):
        self.chunk['m_view'].write(self.app.player.m_view)

    def get_program(self, shader_name):
        with open(f'shaders/{shader_name}.vert') as file:
            vertex_shader = file.read()

        with open(f'shaders/{shader_name}.frag') as file:
            fragment_shader = file.read()

        program = self.ctx.program(vertex_shader = vertex_shader, fragment_shader = fragment_shader)
        return program 
