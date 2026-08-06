import moderngl as mgl
import pygame as pg

from blocks import ATLAS_COLS, BLOCK_TYPES, COBBLESTONE, DIRT, GLASS, GRASS, LEAVES, LOG, PLANKS, SAND, STONE
from meshes.hud_mesh import HudMesh
from settings import WIN_RES

SLOT_SIZE = 56
SLOT_MARGIN = 6
SLOT_PADDING = 6
HOTBAR_BOTTOM_MARGIN = 20
CROSSHAIR_SIZE = 10

HOTBAR_BLOCKS = [GRASS, DIRT, STONE, SAND, LOG, PLANKS, LEAVES, COBBLESTONE, GLASS]


class HUD:
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        self.program = app.shader_program.hud

        self.slots = HOTBAR_BLOCKS
        self.selected_slot = 0

        self.width, self.height = int(WIN_RES.x), int(WIN_RES.y)
        self.surface = pg.Surface((self.width, self.height), pg.SRCALPHA)
        self.icons = self._load_icons()

        self.texture = self.ctx.texture((self.width, self.height), 4)
        self.texture.filter = (mgl.NEAREST, mgl.NEAREST)

        #make sure alpha actually blends the hud over the 3d scene behind it
        self.ctx.blend_func = (mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA)

        self.mesh = HudMesh(app)

    def _load_icons(self):
        atlas = pg.image.load('assets/atlas.png').convert_alpha()
        tile_px = atlas.get_width() // ATLAS_COLS

        icons = {}
        icon_size = SLOT_SIZE - SLOT_PADDING * 2
        for block_id in self.slots:
            tile = BLOCK_TYPES[block_id].side
            tile_x, tile_y = tile % ATLAS_COLS, tile // ATLAS_COLS
            rect = pg.Rect(tile_x * tile_px, tile_y * tile_px, tile_px, tile_px)
            icons[block_id] = pg.transform.scale(atlas.subsurface(rect), (icon_size, icon_size))
        return icons

    @property
    def selected_block_id(self):
        return self.slots[self.selected_slot]

    def handle_event(self, event):
        if event.type == pg.KEYDOWN and pg.K_1 <= event.key <= pg.K_9:
            slot = event.key - pg.K_1
            if slot < len(self.slots):
                self.selected_slot = slot
        elif event.type == pg.MOUSEWHEEL:
            self.selected_slot = (self.selected_slot - event.y) % len(self.slots)

    def update(self):
        self.surface.fill((0, 0, 0, 0))
        self._draw_crosshair()
        self._draw_hotbar()
        self.texture.write(pg.image.tostring(self.surface, 'RGBA', True))

    def _draw_crosshair(self):
        cx, cy = self.width // 2, self.height // 2
        color = (255, 255, 255, 220)
        pg.draw.line(self.surface, color, (cx - CROSSHAIR_SIZE, cy), (cx + CROSSHAIR_SIZE, cy), 2)
        pg.draw.line(self.surface, color, (cx, cy - CROSSHAIR_SIZE), (cx, cy + CROSSHAIR_SIZE), 2)

    def _draw_hotbar(self):
        total_width = len(self.slots) * SLOT_SIZE + (len(self.slots) - 1) * SLOT_MARGIN
        start_x = self.width // 2 - total_width // 2
        y = self.height - SLOT_SIZE - HOTBAR_BOTTOM_MARGIN

        for i, block_id in enumerate(self.slots):
            x = start_x + i * (SLOT_SIZE + SLOT_MARGIN)
            rect = pg.Rect(x, y, SLOT_SIZE, SLOT_SIZE)
            selected = i == self.selected_slot

            pg.draw.rect(self.surface, (255, 255, 255, 90) if selected else (0, 0, 0, 90), rect)
            pg.draw.rect(self.surface, (255, 255, 255, 255) if selected else (255, 255, 255, 120), rect, width=2)

            icon = self.icons[block_id]
            self.surface.blit(icon, icon.get_rect(center=rect.center))

    def render(self):
        self.texture.use(location=1)
        self.program['u_hud_texture'] = 1

        self.ctx.disable(mgl.DEPTH_TEST)
        self.mesh.render()
        self.ctx.enable(mgl.DEPTH_TEST)
