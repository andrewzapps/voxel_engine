from lighting import MAX_LIGHT, NIGHT_FLOOR, day_factor, propagate_block_light, sky_color, sky_light_column


def test_day_factor_is_full_at_noon():
    assert day_factor(1200.0 * 0.5) == 1.0


def test_day_factor_is_at_its_floor_at_midnight():
    assert abs(day_factor(0.0) - NIGHT_FLOOR) < 1e-6


def test_day_factor_wraps_around_multiple_days():
    #a day and a half in should look the same as half a day in
    assert abs(day_factor(1200.0 * 1.5) - day_factor(1200.0 * 0.5)) < 1e-6


def test_sky_color_is_darkest_around_midnight():
    midnight = sky_color(0.0)
    noon = sky_color(1200.0 * 0.5)
    assert midnight.x < noon.x
    assert midnight.y < noon.y


def test_sky_light_column_lit_above_surface_dark_below():
    column = sky_light_column(surface_height=40, chunk_base_y=32)
    #local y=8 -> world y=40 (the surface itself, open to sky)
    assert column[8] == MAX_LIGHT
    #local y=0 -> world y=32, well below the surface
    assert column[0] == 0


class FakeWorld:
    def __init__(self, solids=()):
        self.solids = set(solids)
        self.light = {}

    def get_voxel(self, wx, wy, wz):
        return 1 if (wx, wy, wz) in self.solids else 0

    def set_block_light(self, wx, wy, wz, level):
        if self.light.get((wx, wy, wz), 0) >= level:
            return False
        self.light[(wx, wy, wz)] = level
        return True


def test_block_light_decays_by_one_per_step_in_open_air():
    world = FakeWorld()
    propagate_block_light(world, [(0, 0, 0, 15)])

    assert world.light[(0, 0, 0)] == 15
    assert world.light[(1, 0, 0)] == 14
    assert world.light[(2, 0, 0)] == 13


def test_block_light_does_not_pass_through_solid_blocks():
    world = FakeWorld(solids=[(1, 0, 0)])
    propagate_block_light(world, [(0, 0, 0, 15)])

    assert (1, 0, 0) not in world.light
    #other directions are unaffected by the wall to the east
    assert world.light[(-1, 0, 0)] == 14
    assert world.light[(0, 1, 0)] == 14


def test_two_sources_take_the_brighter_value_where_they_overlap():
    world = FakeWorld()
    propagate_block_light(world, [(0, 0, 0, 15), (2, 0, 0, 5)])

    #(1,0,0) is one step from the strong source (->14) and one step from
    #the weak one (->4) - the stronger contribution should win
    assert world.light[(1, 0, 0)] == 14
