import json
import os

import glm

SAVE_DIR = 'saves'
SAVE_PATH = os.path.join(SAVE_DIR, 'world.json')


def save_world(world, player, hud, seed):
    os.makedirs(SAVE_DIR, exist_ok=True)

    data = {
        'seed': seed,
        'edits': {f'{wx},{wy},{wz}': int(voxel_id) for (wx, wy, wz), voxel_id in world.edits.items()},
        'player': {
            'position': [player.position.x, player.position.y, player.position.z],
            'yaw': glm.degrees(player.yaw),
            'pitch': glm.degrees(player.pitch),
        },
        'hotbar_slot': hud.selected_slot,
        'inventory': hud.inventory.to_serializable(),
    }

    with open(SAVE_PATH, 'w') as save_file:
        json.dump(data, save_file)


def load_world():
    if not os.path.exists(SAVE_PATH):
        return None

    with open(SAVE_PATH) as save_file:
        data = json.load(save_file)

    edits = {}
    for key, voxel_id in data.get('edits', {}).items():
        wx, wy, wz = (int(part) for part in key.split(','))
        edits[(wx, wy, wz)] = voxel_id

    return {
        'seed': data.get('seed', 0),
        'edits': edits,
        'player': data.get('player'),
        'hotbar_slot': data.get('hotbar_slot', 0),
        'inventory': data.get('inventory'),
    }
