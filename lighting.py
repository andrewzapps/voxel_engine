import math
from collections import deque

import glm

from settings import CHUNK_SIZE

MAX_LIGHT = 15

#matches vanilla's 20 real-minute day
DAY_LENGTH_SECONDS = 1200.0

#outdoor light never drops all the way to zero at night - there's still
#moonlight, same as real minecraft
NIGHT_FLOOR = 0.2

#sky color keyframes through the day, (time_of_day, color) - wraps around
_SKY_KEYFRAMES = (
    (0.00, glm.vec3(0.02, 0.02, 0.05)),   # midnight
    (0.23, glm.vec3(0.05, 0.05, 0.12)),   # just before dawn
    (0.27, glm.vec3(0.9, 0.55, 0.35)),    # sunrise
    (0.35, glm.vec3(0.45, 0.65, 0.9)),    # morning
    (0.50, glm.vec3(0.45, 0.65, 0.9)),    # noon
    (0.65, glm.vec3(0.45, 0.65, 0.9)),    # afternoon
    (0.73, glm.vec3(0.9, 0.45, 0.3)),     # sunset
    (0.77, glm.vec3(0.05, 0.05, 0.12)),   # dusk
    (1.00, glm.vec3(0.02, 0.02, 0.05)),   # midnight again
)


def time_of_day(elapsed_seconds):
    #0..1 fraction through the current day
    return (elapsed_seconds % DAY_LENGTH_SECONDS) / DAY_LENGTH_SECONDS


def sky_color(elapsed_seconds):
    t = time_of_day(elapsed_seconds)
    for (t0, c0), (t1, c1) in zip(_SKY_KEYFRAMES, _SKY_KEYFRAMES[1:]):
        if t0 <= t <= t1:
            blend = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            return glm.mix(c0, c1, blend)
    return _SKY_KEYFRAMES[-1][1]


def day_factor(elapsed_seconds):
    #how much outdoor sky light actually counts right now - 1.0 at noon,
    #NIGHT_FLOOR at midnight, smooth in between
    t = time_of_day(elapsed_seconds)
    #cosine wave peaking at t=0.5 (noon), troughing at t=0.0/1.0 (midnight)
    swing = (math.cos((t - 0.5) * 2 * math.pi) + 1) * 0.5
    return NIGHT_FLOOR + (1.0 - NIGHT_FLOOR) * swing


_NEIGHBOR_OFFSETS = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


def propagate_block_light(world, sources):
    """BFS flood fill outward from (wx, wy, wz, level) sources, writing into
    each chunk's block_light array. Only called on edits near a light source,
    not every frame - a real per-voxel 3d BFS is too slow to run continuously."""
    queue = deque()
    visited = set()

    for wx, wy, wz, level in sources:
        if world.set_block_light(wx, wy, wz, level):
            queue.append((wx, wy, wz, level))
        visited.add((wx, wy, wz))

    while queue:
        wx, wy, wz, level = queue.popleft()
        if level <= 1:
            continue

        next_level = level - 1
        for dx, dy, dz in _NEIGHBOR_OFFSETS:
            nx, ny, nz = wx + dx, wy + dy, wz + dz
            pos = (nx, ny, nz)
            if pos in visited:
                continue
            visited.add(pos)

            if world.get_voxel(nx, ny, nz) != 0:
                continue  # solid blocks stop light

            if world.set_block_light(nx, ny, nz, next_level):
                queue.append((nx, ny, nz, next_level))


def sky_light_column(surface_height, chunk_base_y):
    #everything at/above the generated surface is open to the sky - caves
    #and overhangs below it start dark until a torch reaches them
    sky_light = [0] * CHUNK_SIZE
    for y in range(CHUNK_SIZE):
        if y + chunk_base_y >= surface_height:
            sky_light[y] = MAX_LIGHT
    return sky_light
