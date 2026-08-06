import pygame as pg

from hud import HUD
from inventory import HOTBAR_SIZE, Inventory, ItemStack


def make_hud():
    #bypass __init__ so we don't need a real gl context/window just for slot logic
    hud = HUD.__new__(HUD)
    hud.inventory = Inventory()
    hud.selected_slot = 0
    hud.inventory_open = False
    hud.cursor_stack = None
    hud.width, hud.height = 1920, 1080
    return hud


def test_number_key_selects_matching_slot():
    hud = make_hud()
    hud.inventory.slots[1] = ItemStack(2, 5)

    hud.handle_event(pg.event.Event(pg.KEYDOWN, key=pg.K_2))

    assert hud.selected_slot == 1
    assert hud.selected_block_id == 2


def test_scroll_wheel_wraps_around():
    hud = make_hud()
    hud.selected_slot = HOTBAR_SIZE - 1

    hud.handle_event(pg.event.Event(pg.MOUSEWHEEL, y=-1))

    assert hud.selected_slot == 0


def test_empty_selected_slot_has_no_block_id():
    hud = make_hud()
    assert hud.selected_block_id is None


def test_hotbar_keys_do_nothing_while_inventory_is_open():
    hud = make_hud()
    hud.inventory_open = True

    hud.handle_event(pg.event.Event(pg.KEYDOWN, key=pg.K_2))

    assert hud.selected_slot == 0


def test_clicking_an_empty_cursor_onto_a_slot_picks_it_up(monkeypatch):
    hud = make_hud()
    hud.inventory_open = True
    hud.inventory.slots[0] = ItemStack(3, 4)

    rect = hud._slot_rects()[0]
    monkeypatch.setattr(pg.mouse, 'get_pos', lambda: rect.center)
    hud._handle_inventory_click(pg.event.Event(pg.MOUSEBUTTONDOWN, button=1))

    assert hud.cursor_stack == ItemStack(3, 4)
    assert hud.inventory.slots[0] is None


def test_closing_inventory_returns_held_cursor_stack(monkeypatch):
    hud = make_hud()
    hud.cursor_stack = ItemStack(3, 4)
    monkeypatch.setattr(pg.mouse, 'set_visible', lambda *_: None)
    monkeypatch.setattr(pg.event, 'set_grab', lambda *_: None)

    hud.set_inventory_open(False)

    assert hud.cursor_stack is None
    assert hud.inventory.slots[0] == ItemStack(3, 4)
