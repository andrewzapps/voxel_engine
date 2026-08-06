#one-off script, not run at game startup. regenerates atlas.png from scratch.
#run with: python assets/generate_textures.py
import random

from PIL import Image

TILE = 16
COLS = 4
ROWS = 4


def noisy_tile(base, variance, seed, alpha=255):
    rng = random.Random(seed)
    img = Image.new('RGBA', (TILE, TILE))
    px = img.load()
    for y in range(TILE):
        for x in range(TILE):
            jitter = rng.randint(-variance, variance)
            r = max(0, min(255, base[0] + jitter))
            g = max(0, min(255, base[1] + jitter))
            b = max(0, min(255, base[2] + jitter))
            px[x, y] = (r, g, b, alpha)
    return img


def speckled_tile(base, variance, seed, speck_color, speck_chance):
    img = noisy_tile(base, variance, seed)
    rng = random.Random(seed + 1)
    px = img.load()
    for y in range(TILE):
        for x in range(TILE):
            if rng.random() < speck_chance:
                px[x, y] = speck_color
    return img


def grass_top():
    return noisy_tile((79, 140, 54), 14, seed=1)


def grass_side():
    img = noisy_tile((134, 96, 57), 10, seed=2)
    px = img.load()
    rng = random.Random(3)
    #a few rows of grass on top with a ragged edge dipping into the dirt
    for x in range(TILE):
        dip = rng.randint(0, 2)
        for y in range(0, 4 + dip):
            g = 79 + rng.randint(-14, 14)
            px[x, y] = (g // 2, 140 + rng.randint(-14, 14), g // 2, 255)
    return img


def dirt():
    return speckled_tile((134, 96, 57), 10, seed=4, speck_color=(110, 78, 46, 255), speck_chance=0.06)


def stone():
    return speckled_tile((125, 125, 125), 8, seed=5, speck_color=(100, 100, 100, 255), speck_chance=0.08)


def sand():
    return noisy_tile((219, 205, 145), 8, seed=6)


def log_side():
    img = noisy_tile((103, 76, 46), 6, seed=7)
    px = img.load()
    #vertical bark lines
    for x in range(0, TILE, 3):
        for y in range(TILE):
            px[x, y] = (78, 56, 32, 255)
    return img


def log_top():
    img = noisy_tile((186, 152, 97), 8, seed=8)
    px = img.load()
    cx, cy = TILE / 2 - 0.5, TILE / 2 - 0.5
    for y in range(TILE):
        for x in range(TILE):
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if int(dist) % 2 == 0:
                r, g, b, a = px[x, y]
                px[x, y] = (max(0, r - 25), max(0, g - 25), max(0, b - 25), a)
    return img


def leaves():
    img = noisy_tile((52, 105, 39), 18, seed=9)
    px = img.load()
    rng = random.Random(10)
    for y in range(TILE):
        for x in range(TILE):
            if rng.random() < 0.12:
                px[x, y] = (30, 75, 24, 255)
    return img


def planks():
    img = noisy_tile((172, 134, 84), 8, seed=11)
    px = img.load()
    for y in range(0, TILE, 4):
        for x in range(TILE):
            px[x, y] = (140, 106, 64, 255)
    #stagger the plank seams
    for x in range(0, TILE, 7):
        for y in range(TILE):
            px[x, y] = (150, 114, 70, 255)
    return img


def cobblestone():
    img = noisy_tile((120, 120, 120), 10, seed=12)
    px = img.load()
    rng = random.Random(13)
    for _ in range(10):
        bx, by = rng.randint(0, TILE - 4), rng.randint(0, TILE - 4)
        for y in range(by, min(TILE, by + 3)):
            for x in range(bx, min(TILE, bx + 3)):
                px[x, y] = (85, 85, 85, 255)
    return img


def ore_tile(speck_color, seed):
    img = stone()
    px = img.load()
    rng = random.Random(seed)
    for _ in range(6):
        bx, by = rng.randint(0, TILE - 2), rng.randint(0, TILE - 2)
        for y in range(by, min(TILE, by + 2)):
            for x in range(bx, min(TILE, bx + 2)):
                px[x, y] = speck_color
    return img


def glass():
    img = noisy_tile((220, 235, 235), 4, seed=15, alpha=140)
    px = img.load()
    for i in range(TILE):
        px[i, 0] = (255, 255, 255, 200)
        px[0, i] = (255, 255, 255, 200)
        px[i, TILE - 1] = (150, 170, 170, 220)
        px[TILE - 1, i] = (150, 170, 170, 220)
    return img


def water():
    img = noisy_tile((44, 92, 191), 10, seed=16, alpha=170)
    px = img.load()
    for y in range(0, TILE, 4):
        for x in range(TILE):
            r, g, b, a = px[x, y]
            px[x, y] = (min(255, r + 25), min(255, g + 25), min(255, b + 25), a)
    return img


def torch():
    img = Image.new('RGBA', (TILE, TILE), (0, 0, 0, 0))
    px = img.load()
    for y in range(6, TILE):
        for x in range(7, 9):
            px[x, y] = (96, 68, 40, 255)
    for y in range(2, 7):
        for x in range(6, 10):
            px[x, y] = (255, 170, 40, 255)
    px[7, 3] = (255, 230, 120, 255)
    px[8, 3] = (255, 230, 120, 255)
    return img


def crafting_table():
    img = noisy_tile((155, 118, 72), 8, seed=17)
    px = img.load()
    for i in range(2, TILE - 2):
        px[i, 2] = (110, 82, 48, 255)
        px[i, TILE - 3] = (110, 82, 48, 255)
        px[2, i] = (110, 82, 48, 255)
        px[TILE - 3, i] = (110, 82, 48, 255)
    return img


def coal_ore():
    return ore_tile((40, 40, 40, 255), 18)


def iron_ore():
    return ore_tile((198, 146, 106, 255), 19)


#order matches blocks.py tile indices 0-15
TILES = [
    grass_top, grass_side, dirt, stone,
    sand, log_side, log_top, leaves,
    planks, cobblestone, coal_ore, iron_ore,
    glass, water, torch, crafting_table,
]


def build_atlas():
    atlas = Image.new('RGBA', (TILE * COLS, TILE * ROWS))
    for index, make_tile in enumerate(TILES):
        col, row = index % COLS, index // COLS
        atlas.paste(make_tile(), (col * TILE, row * TILE))
    return atlas


if __name__ == '__main__':
    build_atlas().save('assets/atlas.png')
    print('wrote assets/atlas.png')
