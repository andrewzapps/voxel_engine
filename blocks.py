from dataclasses import dataclass

#block ids
AIR = 0
GRASS = 1
DIRT = 2
STONE = 3
SAND = 4
LOG = 5
LEAVES = 6
PLANKS = 7
COBBLESTONE = 8
COAL_ORE = 9
IRON_ORE = 10
GLASS = 11
WATER = 12
TORCH = 13
CRAFTING_TABLE = 14

#atlas is a 4x4 grid of 16px tiles, keep this in sync with generate_textures.py
ATLAS_COLS = 4

#room to grow past the block list below without touching the shader again
MAX_BLOCK_TILES = 64 * 6


@dataclass(frozen=True)
class BlockType:
    id: int
    name: str
    top: int
    side: int
    bottom: int
    solid: bool = True
    light_level: int = 0  # how brightly this block itself glows, 0-15


def _uniform(block_id, name, tile, solid=True, light_level=0):
    return BlockType(block_id, name, top=tile, side=tile, bottom=tile, solid=solid, light_level=light_level)


BLOCK_TYPES = {
    GRASS: BlockType(GRASS, 'grass', top=0, side=1, bottom=2),
    DIRT: _uniform(DIRT, 'dirt', 2),
    STONE: _uniform(STONE, 'stone', 3),
    SAND: _uniform(SAND, 'sand', 4),
    LOG: BlockType(LOG, 'log', top=6, side=5, bottom=6),
    LEAVES: _uniform(LEAVES, 'leaves', 7),
    PLANKS: _uniform(PLANKS, 'planks', 8),
    COBBLESTONE: _uniform(COBBLESTONE, 'cobblestone', 9),
    COAL_ORE: _uniform(COAL_ORE, 'coal ore', 10),
    IRON_ORE: _uniform(IRON_ORE, 'iron ore', 11),
    GLASS: _uniform(GLASS, 'glass', 12),
    WATER: _uniform(WATER, 'water', 13, solid=False),
    TORCH: _uniform(TORCH, 'torch', 14, solid=False, light_level=14),
    CRAFTING_TABLE: _uniform(CRAFTING_TABLE, 'crafting table', 15),
}

#faces in the order the mesh builder emits them: top, bottom, right, left, back, front
FACE_TILE_ATTRS = ('top', 'bottom', 'side', 'side', 'side', 'side')


def build_tile_table():
    #flat voxel_id * 6 + face_id -> atlas tile index, fed to the shader as a uniform
    table = [0] * MAX_BLOCK_TILES
    for block in BLOCK_TYPES.values():
        for face_id, attr in enumerate(FACE_TILE_ATTRS):
            table[block.id * 6 + face_id] = getattr(block, attr)
    return table
