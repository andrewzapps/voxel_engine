import glm

from settings import GRAVITY


class Entity:
    #a stripped-down version of the player's own physics - falls, gets
    #stopped by solid blocks, doesn't need stairs/ground-snap smoothing
    #since mobs aren't jumping around
    def __init__(self, app, position, width, height):
        self.app = app
        self.world = app.scene.world
        self.position = glm.vec3(position)
        self.velocity = glm.vec3(0)
        self.width = width
        self.height = height
        self.on_ground = False
        self.alive = True

    def get_aabb(self, position=None):
        pos = position if position is not None else self.position
        half = self.width * 0.5
        return (
            glm.vec3(pos.x - half, pos.y, pos.z - half),
            glm.vec3(pos.x + half, pos.y + self.height, pos.z + half),
        )

    def collides_at(self, position):
        return self.world.collides_aabb(*self.get_aabb(position))

    def apply_gravity_and_move(self, dt):
        if self.on_ground:
            self.velocity.y = 0
        else:
            self.velocity.y -= GRAVITY * dt

        pos = glm.vec3(self.position)

        for i in (0, 2):
            old = pos[i]
            pos[i] += self.velocity[i] * dt
            if self.collides_at(pos):
                pos[i] = old

        old_y = pos.y
        pos.y += self.velocity.y * dt
        if self.collides_at(pos):
            pos.y = old_y
            self.on_ground = self.velocity.y <= 0
            self.velocity.y = 0
        else:
            self.on_ground = False

        self.position = pos
