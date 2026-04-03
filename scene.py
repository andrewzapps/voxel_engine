from settings import *
from meshes.quad_mesh import quadMesh

class Scene:
    def __init__(self, app):
        self.app = app
        self.quad = quadMesh(self.app)

    
    def update(self):
        pass

    def render(self):
        self.quad.render()