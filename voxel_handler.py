from settings import *
import pygame as pg
from meshes.selection_outline import SelectionOutline

ATTACK_RANGE = 4.0
ATTACK_DAMAGE = 4
#how narrow the "in front of you" cone is - 1.0 is dead center, 0.0 is 90 degrees off
ATTACK_DOT_THRESHOLD = 0.6


class VoxelHandler:
    def __init__(self, app):
        self.app = app
        self.max_distance = 8.0
        self.selected_block = None
        self.selected_normal = None
        self.outline = SelectionOutline(app)

    def update(self):
        hit = self.raycast()
        if hit is None:
            self.selected_block = None
            self.selected_normal = None
        else:
            self.selected_block, self.selected_normal = hit

    def render(self):
        if self.selected_block is not None:
            self.outline.render(*self.selected_block)

    def handle_event(self, event):
        if self.app.hud.inventory_open:
            return
        if event.type != pg.MOUSEBUTTONDOWN:
            return

        if event.button == 1:
            self.break_block()
        elif event.button == 3:
            self.place_block()

    def break_block(self):
        #a mob standing where you're aiming takes priority over the block behind it
        target = self._find_attack_target()
        if target is not None:
            target.take_damage(ATTACK_DAMAGE)
            return

        if self.selected_block is None:
            return

        wx, wy, wz = self.selected_block
        broken_id = self.app.scene.world.get_voxel(wx, wy, wz)
        self.app.scene.world.remove_voxel(wx, wy, wz)
        self.app.hud.inventory.add_item(broken_id)

    def _find_attack_target(self):
        player = self.app.player
        closest, closest_dist = None, ATTACK_RANGE

        for mob in self.app.scene.world.mobs:
            to_mob = mob.position - player.position
            dist = glm.length(to_mob)
            if dist < 0.01 or dist > closest_dist:
                continue
            if glm.dot(glm.normalize(to_mob), player.forward) < ATTACK_DOT_THRESHOLD:
                continue
            closest, closest_dist = mob, dist

        return closest

    def place_block(self):
        if self.selected_block is None or self.selected_normal is None:
            return
        if self.selected_normal == (0, 0, 0):
            return

        held_block_id = self.app.hud.selected_block_id
        if held_block_id is None:
            return

        bx, by, bz = self.selected_block
        nx, ny, nz = self.selected_normal
        px, py, pz = bx + nx, by + ny, bz + nz

        if self.app.scene.world.get_voxel(px, py, pz) != 0:
            return

        if self._overlaps_player(px, py, pz):
            return

        self.app.scene.world.set_voxel(px, py, pz, held_block_id)
        self.app.hud.inventory.take_one(self.app.hud.selected_slot)

    def _overlaps_player(self, px, py, pz):
        player_min, player_max = self.app.player.get_aabb()
        return (player_min.x < px + 1 and player_max.x > px and
                player_min.y < py + 1 and player_max.y > py and
                player_min.z < pz + 1 and player_max.z > pz)

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
        #which axis we last stepped along, so we know which face of the hit
        #block the ray actually came in through
        step_axis = None
        while dist <= self.max_distance:
            if world.get_voxel(map_x, map_y, map_z):
                normal = (0, 0, 0)
                if step_axis == 'x':
                    normal = (-step_x, 0, 0)
                elif step_axis == 'y':
                    normal = (0, -step_y, 0)
                elif step_axis == 'z':
                    normal = (0, 0, -step_z)
                return (map_x, map_y, map_z), normal

            if side_dist_x < side_dist_y:
                if side_dist_x < side_dist_z:
                    dist = side_dist_x
                    side_dist_x += delta_dist_x
                    map_x += step_x
                    step_axis = 'x'
                else:
                    dist = side_dist_z
                    side_dist_z += delta_dist_z
                    map_z += step_z
                    step_axis = 'z'
            else:
                if side_dist_y < side_dist_z:
                    dist = side_dist_y
                    side_dist_y += delta_dist_y
                    map_y += step_y
                    step_axis = 'y'
                else:
                    dist = side_dist_z
                    side_dist_z += delta_dist_z
                    map_z += step_z
                    step_axis = 'z'

        return None
