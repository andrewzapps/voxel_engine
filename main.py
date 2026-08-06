from settings import *
import moderngl as mgl
import pygame as pg
import random
import sys
from shader_program import shaderProgram
from scene import Scene
from player import Player
from textures import Textures
from voxel_handler import VoxelHandler
from hud import HUD
import world_gen
from save import load_world, save_world

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

        pg.event.set_grab(True)
        pg.mouse.set_visible(False)

        self.is_running = True
        self.on_init()

    def on_init(self):
        self.textures = Textures(self)
        self.shader_program = shaderProgram(self)

        self.save_data = load_world()
        self.seed = self.save_data['seed'] if self.save_data else random.randint(0, 1_000_000)
        world_gen.set_seed(self.seed)

        self.scene = Scene(self)

        if self.save_data and self.save_data.get('player'):
            saved_player = self.save_data['player']
            self.player = Player(
                self,
                position=glm.vec3(*saved_player['position']),
                yaw=saved_player['yaw'],
                pitch=saved_player['pitch'],
            )
        else:
            self.player = Player(self)

        self.voxel_handler = VoxelHandler(self)
        self.hud = HUD(self)
        if self.save_data:
            self.hud.selected_slot = self.save_data.get('hotbar_slot', 0)
            if self.save_data.get('inventory') is not None:
                self.hud.inventory.load_serializable(self.save_data['inventory'])

    def update(self):
        self.delta_time = min(self.clock.tick(), 50)
        self.player.update()
        self.shader_program.update()
        self.scene.update()
        self.voxel_handler.update()
        self.hud.update()

        self.time = pg.time.get_ticks() * 0.001
        pg.display.set_caption(f'{self.clock.get_fps() :.0f}')

    def render(self):
        self.ctx.clear(color = BG_COLOR)
        self.scene.render()
        self.voxel_handler.render()
        self.hud.render()
        pg.display.flip()

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                self.is_running = False
                continue
            self.voxel_handler.handle_event(event)
            self.hud.handle_event(event)

    def run(self):
        while(self.is_running):
            self.handle_events()
            self.update()
            self.render()
        save_world(self.scene.world, self.player, self.hud, self.seed)
        pg.quit()
        sys.exit()

if __name__ == '__main__':
    app = voxelEngine();
    app.run()
