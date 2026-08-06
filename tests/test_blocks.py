from blocks import DIRT, GRASS, LOG, build_tile_table


def test_grass_uses_different_tiles_per_face():
    table = build_tile_table()
    top = table[GRASS * 6 + 0]
    bottom = table[GRASS * 6 + 1]
    side = table[GRASS * 6 + 2]

    assert top != side
    assert bottom != side
    assert bottom == table[DIRT * 6 + 0]  # grass bottom reuses the dirt tile


def test_uniform_block_same_tile_on_every_face():
    table = build_tile_table()
    tiles = {table[DIRT * 6 + face] for face in range(6)}
    assert len(tiles) == 1


def test_log_top_differs_from_log_side():
    table = build_tile_table()
    assert table[LOG * 6 + 0] != table[LOG * 6 + 2]
