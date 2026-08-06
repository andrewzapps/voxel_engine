from settings import *
from blocks import COAL_ORE, IRON_ORE

#shifts every noise sample by a fixed offset so different saves get
#different worlds instead of the same terrain every time
_seed_offset = 0.0


def set_seed(seed):
    global _seed_offset
    _seed_offset = (seed % 100000) + 0.0

#terrain shape - a few octaves of simplex stacked together (fbm) so hills
#have both big rolling shape and smaller bumps, instead of one smooth wave
OCTAVES = 3
PERSISTENCE = 0.5
LACUNARITY = 2.0
BASE_FREQUENCY = 0.01
BASE_AMPLITUDE = 24
HEIGHT_OFFSET = 32

#beaches sit right at the waterline
SAND_LEVEL = 30
SEA_LEVEL = SAND_LEVEL

#caves are cheap winding tunnels carved per column rather than full 3d
#noise per voxel - a real 3d field was too slow to generate on the fly
#while chunks stream in around the player
CAVE_MIN_DEPTH = 6
CAVE_FREQUENCY = 0.04
CAVE_WIDTH_FREQUENCY = 0.08
CAVE_CHANCE_FREQUENCY = 0.03
CAVE_CHANCE_THRESHOLD = 0.25

#ore veins - noise is sampled on a coarse 3-voxel grid and cached per chunk
#so ore comes out as small clustered pockets instead of scattered single
#blocks, and so we're not calling simplex on every stone voxel
ORE_BLOCK_SIZE = 3

COAL_MIN_DEPTH = 5
COAL_FREQUENCY = 0.2
COAL_THRESHOLD = 0.86

IRON_MIN_DEPTH = 10
IRON_MAX_HEIGHT = 40
IRON_FREQUENCY = 0.22
IRON_THRESHOLD = 0.90


def terrain_height(wx, wz):
    sx, sz = wx + _seed_offset, wz + _seed_offset
    height = 0.0
    amplitude = BASE_AMPLITUDE
    frequency = BASE_FREQUENCY
    for _ in range(OCTAVES):
        height += glm.simplex(glm.vec2(sx, sz) * frequency) * amplitude
        amplitude *= PERSISTENCE
        frequency *= LACUNARITY
    return int(height + HEIGHT_OFFSET)


def cave_column(wx, wz, surface_height):
    #called once per (x, z) column - returns whether this column has a
    #tunnel running through it and where, so the y loop can do a cheap
    #range check instead of more noise calls
    sx, sz = wx + _seed_offset, wz + _seed_offset
    chance = glm.simplex(glm.vec2(sx, sz) * CAVE_CHANCE_FREQUENCY)
    if chance < CAVE_CHANCE_THRESHOLD:
        return False, 0, 0

    center = glm.simplex(glm.vec2(sx, sz) * CAVE_FREQUENCY) * 10 + surface_height * 0.4
    width = 2 + glm.simplex(glm.vec2(sx + 500, sz + 500) * CAVE_WIDTH_FREQUENCY) * 2
    return True, center, width


def is_cave_voxel(wy, surface_height, cave_active, cave_center, cave_width):
    if not cave_active or surface_height - wy < CAVE_MIN_DEPTH:
        return False
    return abs(wy - cave_center) < cave_width


def ore_id(wx, wy, wz, surface_height, cache):
    depth = surface_height - wy
    if depth < COAL_MIN_DEPTH:
        return None

    #snap to a coarse grid and memoize so a whole little block of stone
    #shares one noise sample instead of paying for one per voxel
    bx = int((wx + _seed_offset) // ORE_BLOCK_SIZE)
    by = wy // ORE_BLOCK_SIZE
    bz = int((wz + _seed_offset) // ORE_BLOCK_SIZE)

    if depth >= IRON_MIN_DEPTH and wy <= IRON_MAX_HEIGHT:
        key = ('iron', bx, by, bz)
        if key not in cache:
            cache[key] = glm.simplex(glm.vec3(bx, by, bz) * IRON_FREQUENCY) > IRON_THRESHOLD
        if cache[key]:
            return IRON_ORE

    key = ('coal', bx, by, bz)
    if key not in cache:
        cache[key] = glm.simplex(glm.vec3(bx + 1000, by, bz - 1000) * COAL_FREQUENCY) > COAL_THRESHOLD
    if cache[key]:
        return COAL_ORE

    return None
