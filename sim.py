import pygame
from pygame.locals import *
from pygame.color import *

import pymunk as pm
import math
import random
from time import time

class Sim(object):

    def __init__(self):
        self.screen_width = 600
        self.screen_height = 600
        self.running = True

        self.gravity = (0.0,-900)

        self.physics_dt = 1.0/60
        self.physics_update_counter = 0

        self.max_time = 100 * self.physics_dt # s

        self.screen_update_ratio = 1.0/90

    def flip_y(self,y):
        return -y + self.screen_height

    def init_pygame(self):
        """ setup our screen """
        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_width,
                                              self.screen_height))
        self.clock = pygame.time.Clock()

    def init_pymunk(self):
        """ setup our space """
        pm.init_pymunk()
        pm.reset_shapeid_counter()
        self.space = pm.Space()
        if self.gravity:
            self.space.gravity = pm.Vec2d(self.gravity)
        self.space.resize_static_hash(100,2000)
        self.space.resize_active_hash(100,2000)

    def is_running(self):
        """ checked to see if we should keep running """
        return self.running

    def handle_events(self):
        """ your chance to go through the events """
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                self.running = False

    def update_physics(self):
        self.physics_update_counter += 1
        for x in range(1): # wtf?
            self.space.step(self.physics_dt)

    def update_scene(self):
        """ update pygame elements """
        pass

    def setup_scene(self):
        """
        add to space the inital objects
        """
        pass

    def wrap_up(self):
        """ last call of run """

    def reset(self):
        """ restore our pristine condition """
        pass

    def run(self):
        start_time = time()
        self.init_pymunk()
        self.init_pygame()

        self.setup_scene()

        while self.is_running():
            if time() - start_time > self.max_time:
                self.running = False

            self.handle_events()

            if self.screen_update_ratio * 100 == self.physics_update_counter:
                self.update_scene()
                self.physics_update_counter = 0

            self.update_physics()

        self.wrap_up()


