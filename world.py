import math
import random

import moderngl as mgl

from settings import *
from blocks import BLOCK_TYPES, GRASS, WATER
from entities.mob import HOSTILE, MOB_STATS, Mob, PASSIVE
from lighting import MAX_LIGHT, day_factor, propagate_block_light
from meshes.cube_mesh import CubeMesh
from world_objects.chunk import Chunk

EMPTY_CHUNK_VOXELS = np.zeros(CHUNK_VOL, dtype='uint8')

MAX_MOBS = 15
SPAWN_CHECK_INTERVAL = 4.0
SPAWN_MIN_RADIUS = 10
SPAWN_MAX_RADIUS = 24
DESPAWN_RADIUS = 48


def _local_index(lx, ly, lz):
    return lx + CHUNK_SIZE * lz + CHUNK_AREA * ly


def _chunk_coord(wx, wy, wz):
    return wx // CHUNK_SIZE, wy // CHUNK_SIZE, wz // CHUNK_SIZE


def _face_neighbor_coords(coord):
    cx, cy, cz = coord
    return (
        (cx - 1, cy, cz), (cx + 1, cy, cz),
        (cx, cy - 1, cz), (cx, cy + 1, cz),
        (cx, cy, cz - 1), (cx, cy, cz + 1),
    )


class World():
    def __init__(self, app):
        self.app = app
        self.chunks = {}  # (cx, cy, cz) -> Chunk

        #(wx, wy, wz) -> voxel_id for every block the player has broken or
        #placed - terrain itself is regenerated from the seed, only edits
        #away from that generated shape need to be remembered
        save_data = getattr(app, 'save_data', None)
        self.edits = dict(save_data['edits']) if save_data else {}

        #(wx, wy, wz) -> light level, rebuilt from edits rather than saved
        #separately - any placed block that glows is already in self.edits
        self.light_sources = {
            pos: BLOCK_TYPES[voxel_id].light_level
            for pos, voxel_id in self.edits.items()
            if voxel_id in BLOCK_TYPES and BLOCK_TYPES[voxel_id].light_level > 0
        }

        #load a full radius around spawn up front so the player has ground to stand on
        spawn_cx, spawn_cz = int(SPAWN_POINT.x) // CHUNK_SIZE, int(SPAWN_POINT.z) // CHUNK_SIZE
        for coord in self._coords_in_range(spawn_cx, spawn_cz):
            self._load_chunk(coord)
        for chunk in self.chunks.values():
            chunk.rebuild_mesh()

        if self.light_sources:
            self.recompute_lighting()

        self.mobs = []
        self._spawn_timer = SPAWN_CHECK_INTERVAL
        self.mob_meshes = {
            PASSIVE: CubeMesh(app, MOB_STATS[PASSIVE]['color']),
            HOSTILE: CubeMesh(app, MOB_STATS[HOSTILE]['color']),
        }

    def _coords_in_range(self, center_cx, center_cz):
        coords = set()
        r2 = RENDER_DISTANCE * RENDER_DISTANCE
        for dx in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
            for dz in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
                if dx * dx + dz * dz > r2:
                    continue
                for cy in range(WORLD_H):
                    coords.add((center_cx + dx, cy, center_cz + dz))
        return coords

    def _load_chunk(self, coord):
        chunk = Chunk(self, position=coord)
        chunk.voxels = chunk.build_voxels()
        self._apply_edits(chunk, coord)
        self.chunks[coord] = chunk

        #a chunk streaming in next to an already-lit torch needs its block
        #light filled in too, not just newly-placed torches
        if self.light_sources and self._chunk_near_any_light_source(coord):
            self.recompute_lighting()

    def _apply_edits(self, chunk, coord):
        if not self.edits:
            return
        cx, cy, cz = coord
        base_x, base_y, base_z = cx * CHUNK_SIZE, cy * CHUNK_SIZE, cz * CHUNK_SIZE
        for (wx, wy, wz), voxel_id in self.edits.items():
            if (base_x <= wx < base_x + CHUNK_SIZE and
                    base_y <= wy < base_y + CHUNK_SIZE and
                    base_z <= wz < base_z + CHUNK_SIZE):
                lx, ly, lz = wx - base_x, wy - base_y, wz - base_z
                chunk.voxels[_local_index(lx, ly, lz)] = voxel_id

    def _unload_chunk(self, coord):
        chunk = self.chunks.pop(coord)
        chunk.release_mesh()

        #neighbours bordering the chunk that just disappeared need their
        #boundary faces rebuilt now that it's gone
        for neighbor_coord in _face_neighbor_coords(coord):
            neighbor = self.chunks.get(neighbor_coord)
            if neighbor is not None:
                neighbor.rebuild_mesh()

    def stream_chunks(self):
        player_pos = self.app.player.position
        center_cx = int(glm.floor(player_pos.x)) // CHUNK_SIZE
        center_cz = int(glm.floor(player_pos.z)) // CHUNK_SIZE

        wanted = self._coords_in_range(center_cx, center_cz)

        missing = [coord for coord in wanted if coord not in self.chunks]
        for coord in missing[:CHUNK_LOAD_BUDGET]:
            self._load_chunk(coord)
            self.chunks[coord].rebuild_mesh()
            for neighbor_coord in _face_neighbor_coords(coord):
                neighbor = self.chunks.get(neighbor_coord)
                if neighbor is not None:
                    neighbor.rebuild_mesh()

        for coord in [c for c in self.chunks if c not in wanted]:
            self._unload_chunk(coord)

    def gather_neighbor_voxels(self, coord):
        cx, cy, cz = coord
        neighbors = np.empty((27, CHUNK_VOL), dtype='uint8')
        for dz in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    slot = (dx + 1) + (dy + 1) * 3 + (dz + 1) * 9
                    neighbor = self.chunks.get((cx + dx, cy + dy, cz + dz))
                    neighbors[slot] = neighbor.voxels if neighbor is not None else EMPTY_CHUNK_VOXELS
        return neighbors

    def is_water(self, wx, wy, wz):
        return int(self.get_voxel(wx, wy, wz)) == WATER

    def aabb_overlaps_water(self, min_pos, max_pos):
        min_x, min_y, min_z = int(glm.floor(min_pos.x)), int(glm.floor(min_pos.y)), int(glm.floor(min_pos.z))
        max_x, max_y, max_z = int(glm.floor(max_pos.x)), int(glm.floor(max_pos.y)), int(glm.floor(max_pos.z))

        for wx in range(min_x, max_x + 1):
            for wy in range(min_y, max_y + 1):
                for wz in range(min_z, max_z + 1):
                    if self.is_water(wx, wy, wz):
                        if (min_pos.x < wx + 1 and max_pos.x > wx and
                                min_pos.y < wy + 1 and max_pos.y > wy and
                                min_pos.z < wz + 1 and max_pos.z > wz):
                            return True
        return False

    def is_solid(self, wx, wy, wz):
        voxel_id = int(self.get_voxel(wx, wy, wz))
        if voxel_id == 0:
            return False
        block = BLOCK_TYPES.get(voxel_id)
        return block.solid if block is not None else True

    def collides_aabb(self, min_pos, max_pos):
        min_x = int(glm.floor(min_pos.x))
        min_y = int(glm.floor(min_pos.y))
        min_z = int(glm.floor(min_pos.z))
        max_x = int(glm.floor(max_pos.x))
        max_y = int(glm.floor(max_pos.y))
        max_z = int(glm.floor(max_pos.z))

        for wx in range(min_x, max_x + 1):
            for wy in range(min_y, max_y + 1):
                for wz in range(min_z, max_z + 1):
                    if self.is_solid(wx, wy, wz):
                        if (min_pos.x < wx + 1 and max_pos.x > wx and
                                min_pos.y < wy + 1 and max_pos.y > wy and
                                min_pos.z < wz + 1 and max_pos.z > wz):
                            return True
        return False

    def get_ground_height(self, wx, wz):
        wx, wz = int(glm.floor(wx)), int(glm.floor(wz))
        for wy in range(WORLD_H * CHUNK_SIZE - 1, -1, -1):
            if self.is_solid(wx, wy, wz):
                return wy + 1
        return 0

    def get_footprint_ground(self, min_x, max_x, min_z, max_z):
        top = 0
        for wx in range(min_x, max_x + 1):
            for wz in range(min_z, max_z + 1):
                top = max(top, self.get_ground_height(wx, wz))
        return top

    def get_voxel(self, wx, wy, wz):
        chunk = self.chunks.get(_chunk_coord(wx, wy, wz))
        if chunk is None:
            return 0
        lx, ly, lz = wx % CHUNK_SIZE, wy % CHUNK_SIZE, wz % CHUNK_SIZE
        return chunk.voxels[_local_index(lx, ly, lz)]

    def set_voxel(self, wx, wy, wz, voxel_id):
        chunk = self.chunks.get(_chunk_coord(wx, wy, wz))
        if chunk is None:
            return False

        old_voxel_id = int(self.get_voxel(wx, wy, wz))
        lx, ly, lz = wx % CHUNK_SIZE, wy % CHUNK_SIZE, wz % CHUNK_SIZE
        chunk.voxels[_local_index(lx, ly, lz)] = voxel_id
        self.edits[(wx, wy, wz)] = int(voxel_id)

        self._update_light_sources(wx, wy, wz, old_voxel_id, int(voxel_id))
        self._update_sky_light_column(wx, wz)
        self.rebuild_chunks_around(wx, wy, wz)
        return True

    def _light_level_of(self, voxel_id):
        block = BLOCK_TYPES.get(voxel_id)
        return block.light_level if block is not None else 0

    def _update_light_sources(self, wx, wy, wz, old_voxel_id, new_voxel_id):
        new_level = self._light_level_of(new_voxel_id)
        pos = (wx, wy, wz)

        source_changed = False
        if new_level > 0:
            if self.light_sources.get(pos) != new_level:
                self.light_sources[pos] = new_level
                source_changed = True
        elif pos in self.light_sources:
            del self.light_sources[pos]
            source_changed = True

        #placing/removing a solid block near an existing light can also
        #open or close off where that light reaches, not just the source itself
        if source_changed or self._near_any_light_source(wx, wy, wz):
            self.recompute_lighting()

    def _near_any_light_source(self, wx, wy, wz):
        for (sx, sy, sz), level in self.light_sources.items():
            if abs(sx - wx) <= level and abs(sy - wy) <= level and abs(sz - wz) <= level:
                return True
        return False

    def _chunk_near_any_light_source(self, coord):
        cx, cy, cz = coord
        base_x, base_y, base_z = cx * CHUNK_SIZE, cy * CHUNK_SIZE, cz * CHUNK_SIZE
        for (sx, sy, sz), level in self.light_sources.items():
            if (base_x - level <= sx <= base_x + CHUNK_SIZE + level and
                    base_y - level <= sy <= base_y + CHUNK_SIZE + level and
                    base_z - level <= sz <= base_z + CHUNK_SIZE + level):
                return True
        return False

    def _update_sky_light_column(self, wx, wz):
        top_y = WORLD_H * CHUNK_SIZE - 1
        exposed = True
        changed_chunks = set()

        for wy in range(top_y, -1, -1):
            coord = _chunk_coord(wx, wy, wz)
            chunk = self.chunks.get(coord)
            if chunk is None:
                continue

            lx, ly, lz = wx % CHUNK_SIZE, wy % CHUNK_SIZE, wz % CHUNK_SIZE
            idx = _local_index(lx, ly, lz)
            is_solid_here = chunk.voxels[idx] != 0

            new_value = MAX_LIGHT if (exposed and not is_solid_here) else 0
            if is_solid_here:
                exposed = False

            if chunk.sky_light[idx] != new_value:
                chunk.sky_light[idx] = new_value
                changed_chunks.add(coord)

        for coord in changed_chunks:
            self.chunks[coord].rebuild_mesh()

    def get_block_light(self, wx, wy, wz):
        chunk = self.chunks.get(_chunk_coord(wx, wy, wz))
        if chunk is None:
            return 0
        lx, ly, lz = wx % CHUNK_SIZE, wy % CHUNK_SIZE, wz % CHUNK_SIZE
        return chunk.block_light[_local_index(lx, ly, lz)]

    def set_block_light(self, wx, wy, wz, level):
        chunk = self.chunks.get(_chunk_coord(wx, wy, wz))
        if chunk is None:
            return False
        lx, ly, lz = wx % CHUNK_SIZE, wy % CHUNK_SIZE, wz % CHUNK_SIZE
        idx = _local_index(lx, ly, lz)
        if chunk.block_light[idx] >= level:
            return False
        chunk.block_light[idx] = level
        return True

    def recompute_lighting(self):
        #simplest correct approach: clear every loaded chunk's block light
        #and re-run the flood fill from every known source, rather than
        #trying to incrementally "unlight" what a removed torch used to
        #reach. only runs on edits near a light, not every frame.
        old_light = {coord: chunk.block_light.copy() for coord, chunk in self.chunks.items()}

        for chunk in self.chunks.values():
            chunk.block_light.fill(0)

        sources = [(sx, sy, sz, level) for (sx, sy, sz), level in self.light_sources.items()]
        propagate_block_light(self, sources)

        for coord, chunk in self.chunks.items():
            if not np.array_equal(old_light[coord], chunk.block_light):
                chunk.rebuild_mesh()

    def gather_neighbor_light(self, coord):
        cx, cy, cz = coord
        sky = np.empty((27, CHUNK_VOL), dtype='uint8')
        block = np.empty((27, CHUNK_VOL), dtype='uint8')

        for dz in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    slot = (dx + 1) + (dy + 1) * 3 + (dz + 1) * 9
                    neighbor = self.chunks.get((cx + dx, cy + dy, cz + dz))
                    if neighbor is not None:
                        sky[slot] = neighbor.sky_light
                        block[slot] = neighbor.block_light
                    else:
                        #above the world's height cap is still open sky even
                        #though there's no chunk loaded up there
                        sky[slot] = MAX_LIGHT if (cy + dy) >= WORLD_H else 0
                        block[slot] = 0

        return sky, block

    def remove_voxel(self, wx, wy, wz):
        return self.set_voxel(wx, wy, wz, 0)

    def rebuild_chunks_around(self, wx, wy, wz):
        lx, ly, lz = wx % CHUNK_SIZE, wy % CHUNK_SIZE, wz % CHUNK_SIZE
        coords = {_chunk_coord(wx, wy, wz)}

        if lx == 0:
            coords.add(_chunk_coord(wx - 1, wy, wz))
        if lx == CHUNK_SIZE - 1:
            coords.add(_chunk_coord(wx + 1, wy, wz))
        if ly == 0:
            coords.add(_chunk_coord(wx, wy - 1, wz))
        if ly == CHUNK_SIZE - 1:
            coords.add(_chunk_coord(wx, wy + 1, wz))
        if lz == 0:
            coords.add(_chunk_coord(wx, wy, wz - 1))
        if lz == CHUNK_SIZE - 1:
            coords.add(_chunk_coord(wx, wy, wz + 1))

        for coord in coords:
            chunk = self.chunks.get(coord)
            if chunk is not None:
                chunk.rebuild_mesh()

    def update(self):
        self.stream_chunks()
        self._update_mobs()

    def _update_mobs(self):
        dt = min(self.app.delta_time, 50) * 0.001
        player = self.app.player

        self._spawn_timer -= dt
        if self._spawn_timer <= 0:
            self._spawn_timer = SPAWN_CHECK_INTERVAL
            self._try_spawn_mob()

        for mob in self.mobs:
            mob.update(player, dt)

        self.mobs = [
            mob for mob in self.mobs
            if mob.alive and glm.distance(mob.position, player.position) < DESPAWN_RADIUS
        ]

    def _try_spawn_mob(self):
        if len(self.mobs) >= MAX_MOBS:
            return

        player = self.app.player
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(SPAWN_MIN_RADIUS, SPAWN_MAX_RADIUS)
        sx = int(player.position.x + math.cos(angle) * dist)
        sz = int(player.position.z + math.sin(angle) * dist)

        ground = self.get_ground_height(sx, sz)
        if ground <= 0 or self.get_voxel(sx, ground - 1, sz) != GRASS:
            return  # only spawn on open grass, keep it simple

        #passive mobs come out in daylight, hostiles once it's dark - same
        #split real minecraft uses for spawning
        mob_type = PASSIVE if day_factor(self.app.time) > 0.5 else HOSTILE
        self.mobs.append(Mob(self.app, glm.vec3(sx + 0.5, ground, sz + 0.5), mob_type))

    def render(self):
        for chunk in self.chunks.values():
            chunk.render()

        self._render_mobs()

        #water goes in a second pass, after every opaque face is already in
        #the depth buffer, with depth writes off so it blends instead of
        #fighting with itself where multiple water faces overlap
        self.app.ctx.screen.depth_mask = False
        for chunk in self.chunks.values():
            chunk.render_water()
        self.app.ctx.screen.depth_mask = True

    def _render_mobs(self):
        if not self.mobs:
            return

        player = self.app.player
        self.app.ctx.disable(mgl.CULL_FACE)
        for mob in self.mobs:
            mesh = self.mob_meshes[mob.mob_type]
            mesh.program['m_proj'].write(player.m_proj)
            mesh.program['m_view'].write(player.m_view)
            mesh.program['m_model'].write(mob.get_model_matrix())
            mesh.vao.render()
        self.app.ctx.enable(mgl.CULL_FACE)
