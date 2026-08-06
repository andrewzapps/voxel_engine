import pygame as pg

from blocks import DIRT, GRASS, STONE
from hud import HUD


def make_hud():
    #bypass __init__ so we don't need a real gl context/window just for slot logic
    hud = HUD.__new__(HUD)
    hud.slots = [GRASS, DIRT, STONE]
    hud.selected_slot = 0
    return hud


def test_number_key_selects_matching_slot():
    hud = make_hud()

    hud.handle_event(pg.event.Event(pg.KEYDOWN, key=pg.K_2))

    assert hud.selected_slot == 1
    assert hud.selected_block_id == DIRT


def test_number_key_beyond_slot_count_is_ignored():
    hud = make_hud()

    hud.handle_event(pg.event.Event(pg.KEYDOWN, key=pg.K_9))

    assert hud.selected_slot == 0


def test_scroll_wheel_wraps_around():
    hud = make_hud()
    hud.selected_slot = 2

    hud.handle_event(pg.event.Event(pg.MOUSEWHEEL, y=-1))

    assert hud.selected_slot == 0
