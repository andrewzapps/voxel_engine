from numba import njit
import numpy as np
import glm
import math 

#resolutions
WIN_RES = glm.vec2(1920, 1080)

#chunk
CHUNK_SIZE = 32
H_CHUNK_SIZE = CHUNK_SIZE // 2
CHUNK_AREA = CHUNK_SIZE * CHUNK_SIZE
CHUNK_VOL = CHUNK_AREA * CHUNK_SIZE

#world
WORLD_W, WORLD_H = 10, 3
WORLD_D = WORLD_W 
WORLD_AREA = WORLD_W * WORLD_D 
WORLD_VOL = WORLD_AREA * WORLD_H

#world center
CENTER_XZ = WORLD_W * H_CHUNK_SIZE 
CENTER_Y = WORLD_H * H_CHUNK_SIZE

#camera
ASPECT_RATIO = WIN_RES.x / WIN_RES.y
FOV_DEG = 50

#VERTICAL FOV
V_FOV = glm.radians(FOV_DEG)

#HORIZONTAL FOV
H_FOV = 2 * math.atan(math.tan(V_FOV * 0.5) * ASPECT_RATIO) 
NEAR = 0.1
FAR = 2000.0
PITCH_MAX = glm.radians(89)

#player
PLAYER_WALK_SPEED = 4.3
PLAYER_RUN_SPEED = 5.6
PLAYER_ACCEL = 50.0
PLAYER_FRICTION = 12.0
PLAYER_EYE_HEIGHT = 1.6
PLAYER_HEIGHT = 1.8
PLAYER_WIDTH = 0.6
GRAVITY = 28.0
JUMP_SPEED = 8.5
MOUSE_SENSITIVITY = 0.004

def terrain_height(wx, wz):
    return int(glm.simplex(glm.vec2(wx, wz) * 0.01) * 32 + 32)

SPAWN_POINT = glm.vec3(CENTER_XZ, 0, CENTER_XZ)
PLAYER_POS = SPAWN_POINT

#colors
BG_COLOR = glm.vec3(0.1, 0.16, 0.25)
