import pygame as pg
from camera import Camera
from settings import *

MAX_DELTA_MS = 50
GROUND_EPSILON = 0.05


class Player(Camera):
    def __init__(self, app, position=None, yaw=-90, pitch=0):
        self.app = app
        self.velocity = glm.vec3(0)
        self.on_ground = False
        if position is None:
            super().__init__(glm.vec3(CENTER_XZ, 0, CENTER_XZ), yaw, pitch)
            self.snap_to_ground()
        else:
            super().__init__(position, yaw, pitch)

    def snap_to_ground(self):
        world = self.app.scene.world
        ground = world.get_footprint_ground(*self._footprint_xz(self.position))
        self.position.y = ground + PLAYER_EYE_HEIGHT
        self.velocity = glm.vec3(0)
        self.on_ground = True

    def update(self):
        self.keyboard_control()
        self.mouse_control()
        self.apply_physics()
        super().update()

    def _footprint_xz(self, position):
        half = PLAYER_WIDTH * 0.5
        min_x = int(glm.floor(position.x - half))
        max_x = int(glm.floor(position.x + half))
        min_z = int(glm.floor(position.z - half))
        max_z = int(glm.floor(position.z + half))
        return min_x, max_x, min_z, max_z

    def get_aabb(self, position=None):
        pos = position if position is not None else self.position
        half = PLAYER_WIDTH * 0.5
        feet_y = pos.y - PLAYER_EYE_HEIGHT
        return (
            glm.vec3(pos.x - half, feet_y, pos.z - half),
            glm.vec3(pos.x + half, feet_y + PLAYER_HEIGHT, pos.z + half),
        )

    def collides_at(self, position):
        return self.app.scene.world.collides_aabb(*self.get_aabb(position))

    def _distance_above_ground(self, pos):
        feet_y = pos.y - PLAYER_EYE_HEIGHT
        ground = self.app.scene.world.get_footprint_ground(*self._footprint_xz(pos))
        return feet_y - ground

    def _push_out_y(self, pos, moving_down):
        step = 0.02
        limit = 200
        for _ in range(limit):
            if not self.collides_at(pos):
                return pos
            pos.y += step if moving_down else -step
        return pos

    def apply_physics(self):
        dt = min(self.app.delta_time, MAX_DELTA_MS) * 0.001

        if not self.on_ground:
            self.velocity.y -= GRAVITY * dt
        elif self.velocity.y < 0:
            self.velocity.y = 0

        pos = glm.vec3(self.position)

        for i in (0, 2):
            old = pos[i]
            pos[i] += self.velocity[i] * dt
            if self.collides_at(pos):
                pos[i] = old
                self.velocity[i] = 0

        # vertical movement with collision
        old_y = pos.y
        pos.y += self.velocity.y * dt

        if self.collides_at(pos):
            moving_down = self.velocity.y <= 0
            pos.y = old_y
            pos = self._push_out_y(pos, moving_down)
            self.velocity.y = 0
            self.on_ground = moving_down
        else:
            gap = self._distance_above_ground(pos)
            if gap >= 0 and gap <= GROUND_EPSILON and self.velocity.y <= 0:
                pos.y -= gap
                self.velocity.y = 0
                self.on_ground = True
            else:
                self.on_ground = False

        self.position = pos

    def mouse_control(self):
        mouse_dx, mouse_dy = pg.mouse.get_rel()
        if mouse_dx:
            self.rotate_yaw(delta_x=mouse_dx * MOUSE_SENSITIVITY)
        if mouse_dy:
            self.rotate_pitch(delta_y=mouse_dy * MOUSE_SENSITIVITY)

    def keyboard_control(self):
        key_state = pg.key.get_pressed()
        dt = min(self.app.delta_time, MAX_DELTA_MS) * 0.001

        speed = PLAYER_RUN_SPEED if key_state[pg.K_LSHIFT] or key_state[pg.K_RSHIFT] else PLAYER_WALK_SPEED

        forward = glm.vec3(self.forward.x, 0, self.forward.z)
        if glm.length(forward) > 0:
            forward = glm.normalize(forward)
        right = glm.normalize(glm.cross(forward, glm.vec3(0, 1, 0)))

        target = glm.vec3(0)
        if key_state[pg.K_w]:
            target += forward
        if key_state[pg.K_s]:
            target -= forward
        if key_state[pg.K_d]:
            target += right
        if key_state[pg.K_a]:
            target -= right

        if glm.length(target) > 0:
            target = glm.normalize(target) * speed
            blend = min(1.0, PLAYER_ACCEL * dt)
            self.velocity.x += (target.x - self.velocity.x) * blend
            self.velocity.z += (target.z - self.velocity.z) * blend
        else:
            friction = max(0.0, 1.0 - PLAYER_FRICTION * dt)
            self.velocity.x *= friction
            self.velocity.z *= friction
            if abs(self.velocity.x) < 0.01:
                self.velocity.x = 0
            if abs(self.velocity.z) < 0.01:
                self.velocity.z = 0

        if key_state[pg.K_SPACE] and self.on_ground:
            self.velocity.y = JUMP_SPEED
            self.on_ground = False
