from numba import njit
import numpy as np
import glm
import math 

#resolutions - sized to fill most of a 1800x1169 screen with room for the
#title bar/dock, window gets centered on launch (see main.py)
WIN_RES = glm.vec2(1700, 1060)

#chunk
CHUNK_SIZE = 32
H_CHUNK_SIZE = CHUNK_SIZE // 2
CHUNK_AREA = CHUNK_SIZE * CHUNK_SIZE
CHUNK_VOL = CHUNK_AREA * CHUNK_SIZE

#world - height is capped like real minecraft, but x/z stream in around the player forever
WORLD_H = 3
RENDER_DISTANCE = 6  # chunks, horizontal
CHUNK_LOAD_BUDGET = 2  # new chunks generated per frame so movement doesn't stutter

#spawn near the middle of chunk (0, *, 0)
CENTER_XZ = H_CHUNK_SIZE

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

#swimming
WATER_GRAVITY = 6.0
WATER_SINK_SPEED = 1.5
WATER_SWIM_SPEED = 3.0
WATER_SPEED_MULTIPLIER = 0.5

#health
PLAYER_MAX_HEALTH = 20

SPAWN_POINT = glm.vec3(CENTER_XZ, 0, CENTER_XZ)
PLAYER_POS = SPAWN_POINT

