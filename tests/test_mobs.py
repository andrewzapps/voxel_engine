import glm

from entities import ai
from entities.mob import HOSTILE, PASSIVE, Mob


class FakeWorld:
    def collides_aabb(self, min_pos, max_pos):
        return False  # open air everywhere, mobs just fall/wander freely


class FakeApp:
    def __init__(self):
        self.scene = type('Scene', (), {'world': FakeWorld()})()


class FakePlayer:
    def __init__(self, position):
        self.position = glm.vec3(position)
        self.damage_taken = 0

    def take_damage(self, amount):
        self.damage_taken += amount


def make_mob(mob_type, position=(0, 10, 0)):
    return Mob(FakeApp(), glm.vec3(*position), mob_type)


def test_passive_mob_never_damages_the_player():
    mob = make_mob(PASSIVE)
    player = FakePlayer((0.5, 10, 0.5))  # right on top of it

    for _ in range(20):
        mob.update(player, dt=0.5)

    assert player.damage_taken == 0


def test_hostile_mob_attacks_when_close_enough():
    mob = make_mob(HOSTILE, position=(0, 10, 0))
    player = FakePlayer((0.5, 10, 0.5))

    mob.update(player, dt=0.5)

    assert player.damage_taken > 0


def test_hostile_mob_ignores_a_far_away_player_and_just_wanders():
    mob = make_mob(HOSTILE, position=(0, 10, 0))
    player = FakePlayer((500, 10, 500))

    mob.update(player, dt=0.5)

    assert player.damage_taken == 0
    assert mob.wander_direction is not None


def test_attack_cooldown_prevents_hitting_every_single_frame():
    mob = make_mob(HOSTILE, position=(0, 10, 0))
    player = FakePlayer((0.5, 10, 0.5))

    mob.update(player, dt=0.1)
    hits_after_first = player.damage_taken
    mob.update(player, dt=0.1)

    assert player.damage_taken == hits_after_first  # still on cooldown


def test_take_damage_kills_mob_at_zero_health():
    mob = make_mob(PASSIVE)
    mob.take_damage(mob.health)

    assert mob.alive is False


def test_take_damage_does_not_go_below_dead():
    mob = make_mob(PASSIVE)
    mob.take_damage(mob.health * 5)

    assert mob.alive is False
