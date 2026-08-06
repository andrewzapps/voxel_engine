import glm

from entities import ai
from entities.entity import Entity

PASSIVE = 'passive'
HOSTILE = 'hostile'

#kept to simple colored boxes rather than the multi-part textured/animated
#cuboid models real minecraft mobs use - that's a whole rigging system on
#top of everything else built so far, this gets something that wanders,
#chases, fights and dies without it
MOB_STATS = {
    PASSIVE: {'width': 0.9, 'height': 0.9, 'health': 10, 'color': (0.85, 0.62, 0.66)},
    HOSTILE: {'width': 0.6, 'height': 1.8, 'health': 20, 'color': (0.27, 0.45, 0.27)},
}


class Mob(Entity):
    def __init__(self, app, position, mob_type):
        stats = MOB_STATS[mob_type]
        super().__init__(app, position, stats['width'], stats['height'])
        self.mob_type = mob_type
        self.health = stats['health']
        self.wander_direction = None
        self.wander_timer = 0.0
        self.attack_cooldown = 0.0

    def update(self, player, dt):
        if self.mob_type == HOSTILE:
            ai.update_hostile(self, player, dt)
        else:
            ai.update_passive(self, player, dt)
        self.apply_gravity_and_move(dt)

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.alive = False

    def get_model_matrix(self):
        half = self.width * 0.5
        base = glm.vec3(self.position.x - half, self.position.y, self.position.z - half)
        m_model = glm.translate(glm.mat4(), base)
        m_model = glm.scale(m_model, glm.vec3(self.width, self.height, self.width))
        return m_model
