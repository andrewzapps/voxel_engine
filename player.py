import pygame as pg
from camera import Camera
from settings import *

class Player(Camera):
    def __init__(self, app, position = PLAYER_POS, yaw = -90, pitch = 0):
        self.app = app
        super().__init__(position, yaw, pitch)

    def keyboard_control(self):
        key_state = pg.key.get_pressed()
        #speed * time is distance, delta time is time from last frame
        vel = PLAYER_SPEED * self.app.delta_time
        if key_state[pg.K_w]:
            self.move_forward(vel)
        if key_state[pg.K_s]:
            self.move_back(vel)
        if key_state[pg.K_d]:
            self.move_right(vel)
        if key_state[pg.K_a]:
            self.move_left(vel)
        if key_state[pg.K_q]:
            self.move_up(vel)
        if key_state[pg.K_e]:
            self.move_down(vel)
