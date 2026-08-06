import moderngl as mgl
import pygame as pg

from blocks import ATLAS_COLS, BLOCK_TYPES
from inventory import HOTBAR_SIZE, Inventory
from meshes.hud_mesh import HudMesh
from settings import WIN_RES

SLOT_SIZE = 56
SLOT_MARGIN = 6
SLOT_PADDING = 6
HOTBAR_BOTTOM_MARGIN = 20
CROSSHAIR_SIZE = 10

INV_COLS = 9
INV_ROWS = 3
INV_TOP_MARGIN = 90


class HUD:
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        self.program = app.shader_program.hud

        self.inventory = Inventory()
        self.selected_slot = 0
        self.inventory_open = False
        self.cursor_stack = None  # item the mouse is currently dragging around

        self.width, self.height = int(WIN_RES.x), int(WIN_RES.y)
        self.surface = pg.Surface((self.width, self.height), pg.SRCALPHA)
        self.font = pg.font.SysFont(None, 20)
        self.icons = self._load_icons()

        self.texture = self.ctx.texture((self.width, self.height), 4)
        self.texture.filter = (mgl.NEAREST, mgl.NEAREST)

        #make sure alpha actually blends the hud over the 3d scene behind it
        self.ctx.blend_func = (mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA)

        self.mesh = HudMesh(app)

    def _load_icons(self):
        atlas = pg.image.load('assets/atlas.png').convert_alpha()
        tile_px = atlas.get_width() // ATLAS_COLS
        icon_size = SLOT_SIZE - SLOT_PADDING * 2

        icons = {}
        for block_id, block in BLOCK_TYPES.items():
            tile_x, tile_y = block.side % ATLAS_COLS, block.side // ATLAS_COLS
            rect = pg.Rect(tile_x * tile_px, tile_y * tile_px, tile_px, tile_px)
            icons[block_id] = pg.transform.scale(atlas.subsurface(rect), (icon_size, icon_size))
        return icons

    @property
    def selected_block_id(self):
        stack = self.inventory.slots[self.selected_slot]
        return stack.block_id if stack is not None else None

    def set_inventory_open(self, is_open):
        self.inventory_open = is_open
        pg.mouse.set_visible(is_open)
        pg.event.set_grab(not is_open)

        if not is_open and self.cursor_stack is not None:
            #don't let items vanish if the player closes mid-drag
            self.inventory.add_item(self.cursor_stack.block_id, self.cursor_stack.count)
            self.cursor_stack = None

    def handle_event(self, event):
        if event.type == pg.KEYDOWN and event.key == pg.K_e:
            self.set_inventory_open(not self.inventory_open)
            return

        if self.inventory_open:
            self._handle_inventory_click(event)
            return

        if event.type == pg.KEYDOWN and pg.K_1 <= event.key <= pg.K_9:
            self.selected_slot = event.key - pg.K_1
        elif event.type == pg.MOUSEWHEEL:
            self.selected_slot = (self.selected_slot - event.y) % HOTBAR_SIZE

    def _handle_inventory_click(self, event):
        if event.type != pg.MOUSEBUTTONDOWN or event.button != 1:
            return

        mouse_pos = pg.mouse.get_pos()
        for index, rect in enumerate(self._slot_rects()):
            if rect.collidepoint(mouse_pos):
                self.inventory.slots[index], self.cursor_stack = self.cursor_stack, self.inventory.slots[index]
                return

    def _hotbar_rects(self):
        total_width = HOTBAR_SIZE * SLOT_SIZE + (HOTBAR_SIZE - 1) * SLOT_MARGIN
        start_x = self.width // 2 - total_width // 2
        y = self.height - SLOT_SIZE - HOTBAR_BOTTOM_MARGIN
        return [pg.Rect(start_x + i * (SLOT_SIZE + SLOT_MARGIN), y, SLOT_SIZE, SLOT_SIZE) for i in range(HOTBAR_SIZE)]

    def _main_inventory_rects(self):
        total_width = INV_COLS * SLOT_SIZE + (INV_COLS - 1) * SLOT_MARGIN
        total_height = INV_ROWS * SLOT_SIZE + (INV_ROWS - 1) * SLOT_MARGIN
        start_x = self.width // 2 - total_width // 2
        start_y = self.height // 2 - total_height // 2 - INV_TOP_MARGIN

        rects = []
        for row in range(INV_ROWS):
            for col in range(INV_COLS):
                x = start_x + col * (SLOT_SIZE + SLOT_MARGIN)
                y = start_y + row * (SLOT_SIZE + SLOT_MARGIN)
                rects.append(pg.Rect(x, y, SLOT_SIZE, SLOT_SIZE))
        return rects

    def _slot_rects(self):
        #index order matches Inventory.slots: hotbar first, then the main grid
        return self._hotbar_rects() + self._main_inventory_rects()

    def update(self):
        self.surface.fill((0, 0, 0, 0))
        self._draw_crosshair()
        self._draw_slots(self._hotbar_rects(), range(0, HOTBAR_SIZE), highlight_selected=True)
        if self.inventory_open:
            self._draw_slots(self._main_inventory_rects(), range(HOTBAR_SIZE, len(self.inventory.slots)))
            self._draw_cursor_stack()
        self.texture.write(pg.image.tostring(self.surface, 'RGBA', True))

    def _draw_crosshair(self):
        if self.inventory_open:
            return
        cx, cy = self.width // 2, self.height // 2
        color = (255, 255, 255, 220)
        pg.draw.line(self.surface, color, (cx - CROSSHAIR_SIZE, cy), (cx + CROSSHAIR_SIZE, cy), 2)
        pg.draw.line(self.surface, color, (cx, cy - CROSSHAIR_SIZE), (cx, cy + CROSSHAIR_SIZE), 2)

    def _draw_slots(self, rects, slot_indices, highlight_selected=False):
        for rect, index in zip(rects, slot_indices):
            selected = highlight_selected and index == self.selected_slot
            pg.draw.rect(self.surface, (255, 255, 255, 90) if selected else (0, 0, 0, 90), rect)
            pg.draw.rect(self.surface, (255, 255, 255, 255) if selected else (255, 255, 255, 120), rect, width=2)
            self._draw_stack(self.inventory.slots[index], rect)

    def _draw_stack(self, stack, rect):
        if stack is None:
            return
        icon = self.icons[stack.block_id]
        self.surface.blit(icon, icon.get_rect(center=rect.center))
        if stack.count > 1:
            label = self.font.render(str(stack.count), True, (255, 255, 255))
            label_rect = label.get_rect(bottomright=(rect.right - 4, rect.bottom - 2))
            self.surface.blit(label, label_rect)

    def _draw_cursor_stack(self):
        if self.cursor_stack is None:
            return
        icon = self.icons[self.cursor_stack.block_id]
        self.surface.blit(icon, icon.get_rect(center=pg.mouse.get_pos()))

    def render(self):
        self.texture.use(location=1)
        self.program['u_hud_texture'] = 1

        self.ctx.disable(mgl.DEPTH_TEST)
        self.mesh.render()
        self.ctx.enable(mgl.DEPTH_TEST)
