import glm

from inventory import Inventory
from save import SAVE_PATH, load_world, save_world


class FakePlayer:
    def __init__(self):
        self.position = glm.vec3(12.5, 40.0, -3.5)
        self.yaw = glm.radians(-70)
        self.pitch = glm.radians(15)


class FakeHud:
    def __init__(self):
        self.selected_slot = 4
        self.inventory = Inventory()


class FakeWorld:
    def __init__(self):
        self.edits = {(1, 2, 3): 0, (4, 5, 6): 7}


def test_save_and_load_round_trips_edits_and_player_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    save_world(FakeWorld(), FakePlayer(), FakeHud(), seed=42)
    loaded = load_world()

    assert loaded['seed'] == 42
    assert loaded['edits'] == {(1, 2, 3): 0, (4, 5, 6): 7}
    assert loaded['hotbar_slot'] == 4
    assert loaded['player']['position'] == [12.5, 40.0, -3.5]


def test_load_world_returns_none_when_no_save_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert load_world() is None
