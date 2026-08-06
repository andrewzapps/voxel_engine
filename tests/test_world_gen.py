from blocks import COAL_ORE, IRON_ORE
from world_gen import is_cave_voxel, ore_id, terrain_height


def test_terrain_height_is_deterministic_for_the_same_column():
    assert terrain_height(100, -50) == terrain_height(100, -50)


def test_terrain_height_varies_across_columns():
    heights = {terrain_height(x * 37, x * 19) for x in range(20)}
    assert len(heights) > 1


def test_cave_voxel_requires_minimum_depth_even_inside_a_tunnel():
    #right at the surface, even a wide-open tunnel shouldn't poke through
    assert is_cave_voxel(wy=99, surface_height=100, cave_active=True, cave_center=99, cave_width=5) is False


def test_cave_voxel_inactive_column_never_carves():
    assert is_cave_voxel(wy=10, surface_height=100, cave_active=False, cave_center=10, cave_width=5) is False


def test_ore_id_is_cached_per_block_not_recomputed_per_voxel():
    cache = {}
    #two voxels in the same coarse 3-voxel block should hit the cache and
    #agree, instead of independently rolling different results
    first = ore_id(30, 5, 30, surface_height=40, cache=cache)
    second = ore_id(31, 5, 31, surface_height=40, cache=cache)
    assert first == second


def test_ore_id_returns_none_close_to_the_surface():
    cache = {}
    assert ore_id(30, 39, 30, surface_height=40, cache={}) is None
