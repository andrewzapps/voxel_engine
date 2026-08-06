import pygame as pg 
import moderngl as gl

class Textures:
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx

        self.texture_0 = self.load('atlas.png')

        #assign texture unit
        self.texture_0.use(location = 0)

    def load(self, file_name):
        texture = pg.image.load(f'assets/{file_name}')
        texture = pg.transform.flip(texture, flip_x = True, flip_y = False)

        texture = self.ctx.texture(
                size = texture.get_size(),
                components = 4,
                data = pg.image.tostring(texture, 'RGBA', False)
                )

        #no mipmaps here - the atlas is tightly packed 16px tiles and mipmapping
        #bleeds neighbouring tiles into each other at a distance
        texture.filter = (gl.NEAREST, gl.NEAREST)
        return texture


