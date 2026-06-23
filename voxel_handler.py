from settings import *
import pygame as pg
from meshes.selection_outline import SelectionOutline


class VoxelHandler:
    def __init__(self, app):
        self.app = app
        self.max_distance = 8.0
        self.selected_block = None
        self.outline = SelectionOutline(app)

    def update(self):
        self.selected_block = self.raycast()

    def render(self):
        if self.selected_block is not None:
            self.outline.render(*self.selected_block)

    def handle_event(self, event):
        if event.type != pg.MOUSEBUTTONDOWN or event.button != 1:
            return

        if self.selected_block is None:
            return

        wx, wy, wz = self.selected_block
        self.app.scene.world.remove_voxel(wx, wy, wz)

    def raycast(self):
        origin = self.app.player.position
        direction = self.app.player.forward
        world = self.app.scene.world

        o = glm.vec3(origin)
        d = glm.normalize(glm.vec3(direction))

        map_x = int(glm.floor(o.x))
        map_y = int(glm.floor(o.y))
        map_z = int(glm.floor(o.z))

        delta_dist_x = abs(1.0 / d.x) if d.x != 0 else float('inf')
        delta_dist_y = abs(1.0 / d.y) if d.y != 0 else float('inf')
        delta_dist_z = abs(1.0 / d.z) if d.z != 0 else float('inf')

        if d.x < 0:
            step_x = -1
            side_dist_x = (o.x - map_x) * delta_dist_x
        elif d.x > 0:
            step_x = 1
            side_dist_x = (map_x + 1.0 - o.x) * delta_dist_x
        else:
            step_x = 0
            side_dist_x = float('inf')

        if d.y < 0:
            step_y = -1
            side_dist_y = (o.y - map_y) * delta_dist_y
        elif d.y > 0:
            step_y = 1
            side_dist_y = (map_y + 1.0 - o.y) * delta_dist_y
        else:
            step_y = 0
            side_dist_y = float('inf')

        if d.z < 0:
            step_z = -1
            side_dist_z = (o.z - map_z) * delta_dist_z
        elif d.z > 0:
            step_z = 1
            side_dist_z = (map_z + 1.0 - o.z) * delta_dist_z
        else:
            step_z = 0
            side_dist_z = float('inf')

        dist = 0.0
        while dist <= self.max_distance:
            if world.get_voxel(map_x, map_y, map_z):
                return map_x, map_y, map_z

            if side_dist_x < side_dist_y:
                if side_dist_x < side_dist_z:
                    dist = side_dist_x
                    side_dist_x += delta_dist_x
                    map_x += step_x
                else:
                    dist = side_dist_z
                    side_dist_z += delta_dist_z
                    map_z += step_z
            else:
                if side_dist_y < side_dist_z:
                    dist = side_dist_y
                    side_dist_y += delta_dist_y
                    map_y += step_y
                else:
                    dist = side_dist_z
                    side_dist_z += delta_dist_z
                    map_z += step_z

        return None
