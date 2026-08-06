import random

import glm

WANDER_INTERVAL = 3.0
WANDER_SPEED = 1.5
CHASE_SPEED = 2.6
DETECT_RADIUS = 10.0
ATTACK_RANGE = 1.3
ATTACK_COOLDOWN = 1.0
ATTACK_DAMAGE = 2


def update_passive(mob, player, dt):
    _wander(mob, dt)


def update_hostile(mob, player, dt):
    to_player = glm.vec2(player.position.x - mob.position.x, player.position.z - mob.position.z)
    dist = glm.length(to_player)

    if dist > DETECT_RADIUS:
        _wander(mob, dt)
        return

    if dist > 0.01:
        direction = glm.normalize(to_player)
        mob.velocity.x = direction.x * CHASE_SPEED
        mob.velocity.z = direction.y * CHASE_SPEED

    mob.attack_cooldown = max(0.0, mob.attack_cooldown - dt)
    if dist <= ATTACK_RANGE and mob.attack_cooldown <= 0:
        player.take_damage(ATTACK_DAMAGE)
        mob.attack_cooldown = ATTACK_COOLDOWN


def _wander(mob, dt):
    mob.wander_timer -= dt
    if mob.wander_timer <= 0 or mob.wander_direction is None:
        angle = random.uniform(0, 2 * 3.14159265)
        mob.wander_direction = glm.vec2(glm.cos(angle), glm.sin(angle))
        mob.wander_timer = WANDER_INTERVAL

    mob.velocity.x = mob.wander_direction.x * WANDER_SPEED
    mob.velocity.z = mob.wander_direction.y * WANDER_SPEED
