from settings import *
from world_objects.chunk import Chunk

EMPTY_CHUNK_VOXELS = np.zeros(CHUNK_VOL, dtype='uint8')


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

        #load a full radius around spawn up front so the player has ground to stand on
        spawn_cx, spawn_cz = int(SPAWN_POINT.x) // CHUNK_SIZE, int(SPAWN_POINT.z) // CHUNK_SIZE
        for coord in self._coords_in_range(spawn_cx, spawn_cz):
            self._load_chunk(coord)
        for chunk in self.chunks.values():
            chunk.rebuild_mesh()

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
        if chunk.mesh is not None and chunk.mesh.vao is not None:
            chunk.mesh.vao.release()

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

    def is_solid(self, wx, wy, wz):
        return self.get_voxel(wx, wy, wz) != 0

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

        lx, ly, lz = wx % CHUNK_SIZE, wy % CHUNK_SIZE, wz % CHUNK_SIZE
        chunk.voxels[_local_index(lx, ly, lz)] = voxel_id
        self.edits[(wx, wy, wz)] = int(voxel_id)
        self.rebuild_chunks_around(wx, wy, wz)
        return True

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

    def render(self):
        for chunk in self.chunks.values():
            chunk.render()
