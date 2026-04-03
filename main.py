from settings import * 
import moderngl as mgl
import pygame as pg
import sys
from shader_program import shaderProgram
from scene import Scene

class voxelEngine:
    def __init__(self):
        pg.init()
        #create opengl 3.3 context
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)

        #requests for opengl core profile
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)

        #24 bit depth buffer
        pg.display.gl_set_attribute(pg.GL_DEPTH_SIZE, 24)

        #creates window using gl and double buffering
        pg.display.set_mode(WIN_RES, flags=pg.OPENGL | pg.DOUBLEBUF)

        #opengl context object for gpu
        self.ctx = mgl.create_context()

        self.ctx.enable(flags=mgl.DEPTH_TEST | mgl.CULL_FACE | mgl.BLEND)
        
        #auto clean memory
        self.ctx.gc_mode = 'auto'

        self.clock = pg.time.Clock()
        self.delta_time = 0
        self.time = 0

        self.is_running = True
        self.on_init()

    def on_init(self):
        self.shader_program = shaderProgram(self)
        self.scene = Scene(self)

    def update(self):
        self.shader_program.update()
        self.scene.update()

        self.delta_time = self.clock.tick()
        self.time = pg.time.get_ticks() * 0.001
        pg.display.set_caption(f'{self.clock.get_fps() :.0f}')

    def render(self):
        self.ctx.clear(color = BG_COLOR)
        self.scene.render()
        pg.display.flip()

    def handle_events(self):
        #check for escpae key to stop
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                self.is_running = False

    def run(self):
        while(self.is_running):
            self.handle_events()
            self.update()
            self.render()
        pg.quit()
        sys.exit()

if __name__ == '__main__':
    app = voxelEngine();
    app.run()