import pygame
from pygame.locals import *
from pygame.color import THECOLORS as COLORS
import pymunk as pm
import math
import random
from time import sleep,time
from sim import Sim
from helpers import get_board_data
from headless import HeadlessSim

COLLTYPE_DEFAULT = 0
COLLTYPE_PAD = 1
COLLTYPE_BALL = 2

class SlantSim(Sim):
    def __init__(self):
        super(SlantSim,self).__init__()

        self.balls = []
        self.lines = []
        self.pads = []

        self.ball_count = 10
        self.ball_radius = 10
        self.ball_mass = 10
        self.ball_moment = 100
        self.ball_friction = 0.5

        self.platform_width = 5

        self.pad_width = 5
        self.pad_count = 5
        self.pad_length = 12
        self.pad_max_value = 100
        self.pad_min_value = 10

        self.gravity = pm.Vec2d(0.0,-900)

        self.physics_dt = 1.0/60
        self.screen_update_ratio = .5

        self.score = 0

        self.platform_data = [ ]

        self.board_name = ''

        # variables for handling movement detection
        self.last_collision = None
        self.ball_min_movement = self.physics_dt / 2
        self.previous_position_diff = 1000
        self.previous_position_diff_diff = 1000
        self.ball_position_lookup = {}
        self.diff_check_frequency = .1
        self.diff_check_counter = 0
        self.moving = False
        self.no_movement_count = 0
        self.max_no_movement = 5

        self.to_remove_from_space = []

        if self.board_name:
           self.populate_from_board()

    def populate_from_board(self):
        board_data = get_board_data(self.board_name)

        # the sizes are in % to width

        # sim settings, window dims etc
        for k,v in board_data.get('sim').iteritems():
            setattr(self,k,v)

        # now we map it all to our self
        for k,v in board_data.get('balls').iteritems():
            setattr(self,'ball_%s'%k,v)

        for k,v in board_data.get('pads').iteritems():
            setattr(self,'pad_%s'%k,v)
            if k == 'length':
                self.pad_length = (self.screen_width/100) * self.pad_length

        self.platform_data = board_data.get('platforms')
        for data in self.platform_data:
            data['length'] = (self.screen_width / 100)\
                             * data.get('length')
            data['position'][0] = (self.screen_width / 100)\
                                  * data['position'][0]
            data['position'][1] = (self.screen_height / 100)\
                                  * data['position'][1]

    def setup_scene(self):
        super(SlantSim,self).setup_scene()

        # we want to setup the balls and the platforms
        # first the balls
        self.add_balls()

        # now that we've added the balls, add platforms
        self.add_platforms()

        # add our score pads
        self.add_pads()

    def add_balls(self):
        for i in range(self.ball_count):
            # choose a random x position
            x = random.randint(0,self.screen_width)
            y = 0

            # they are going to be simple
            body = pm.Body(self.ball_mass,self.ball_moment)
            body.position = ( x, self.flip_y(y) )
            shape = pm.Circle(body, self.ball_radius, (0,0))
            shape.friction = self.ball_friction
            shape.collision_type = COLLTYPE_BALL
            shape.ball_id = i
            self.space.add(body,shape)
            self.balls.append(shape)

        return True

    def add_platforms(self):
        # the platforms are going to have set center points
        # the variation comes in the angle that they are placed
        for data in self.platform_data:

            end1 = self.find_endpoint(data.get('position'),
                                      data.get('angle'),
                                      data.get('length')/2)
            end2 = self.find_endpoint(data.get('position'),
                                      data.get('angle')+180,
                                      data.get('length')/2)

            body = pm.Body(pm.inf, pm.inf)
            shape = pm.Segment(body,end1,end2,self.platform_width)
            shape.friction = 0.99
            self.space.add_static(shape)
            self.lines.append(shape)

    def find_endpoint(self,position,angle,length):
        position = list(position) # in case it's a tuple

        # just in case they give me some bullshit
        angle = angle % 360

        # we need to derive the end points of the segment from our data
        c = length * math.sin(math.radians(angle))
        b = length * math.cos(math.radians(angle))


        # better method ?
        end = []

        end = position[0]+b, self.flip_y(position[1])+c
        return end


    def add_pads(self):
        # we want to add lines @ The bottom of the screen which
        # the balls try + hit. we need to be able to keep a score
        # counter / ball value tally on colisions. after collision
        # we should remove the ball

        # we are going to add a platform under the point ones
        # to kill off the balls that miss
        body = pm.Body(pm.inf, pm.inf)
        shape = pm.Segment(body,
                           (0,0),(self.screen_width,0),
                           self.pad_width)
        shape.collision_type = COLLTYPE_PAD
        shape.collision_value = -1
        self.space.add_static(shape)
        self.pads.append(shape)

        # and on the walls
        points = (((0,0),
                   (0,self.screen_height)),
                  ((self.screen_width,0),
                   (self.screen_width,self.screen_height)))
        for p1,p2 in points:
            body = pm.Body(pm.inf, pm.inf)
            shape = pm.Segment(body,p1,p2,self.pad_width)
            shape.collision_type = COLLTYPE_PAD
            shape.collision_value = 0
            self.space.add_static(shape)
            self.pads.append(shape)

        # we want the pad values to be highest in the middlea
        score_range = self.pad_max_value - self.pad_min_value
        step = int(score_range / (self.pad_count / 2))
        pad_values = []
        for i in range(self.pad_min_value,self.pad_max_value,step):
            pad_values.append(i)
        pad_values += [self.pad_max_value]
        other_side = pad_values[:]
        other_side.reverse()
        pad_values += other_side

        # we are going to space them out evently across the bottom
        space = self.screen_width - self.pad_length * self.pad_count
        padding = space / (self.pad_count + 1)
        step = self.pad_length + padding
        y = self.flip_y(self.screen_height - self.pad_width)

        for x1, x2, value in zip(range(padding,self.screen_width,step),
                                 range(step,self.screen_width,step),
                                 pad_values):


            body = pm.Body(pm.inf, pm.inf)
            shape = pm.Segment(body,(x1,y),(x2,y),self.pad_width)
            shape.collision_type = COLLTYPE_PAD
            shape.collision_value = value
            self.space.add_static(shape)
            self.pads.append(shape)
            self.space.add_collision_handler(COLLTYPE_PAD,
                                             COLLTYPE_BALL,
                                             None,
                                             self.handle_pad_collision,
                                             None, None)

    def handle_pad_collision(self, space, arbiter):
        # we need to add the pads value to our score and remove
        # the ball that hit it

        s1,s2 = arbiter.shapes

        if s1 is None:
            return True

        # if we hit the bottom bar, remove the ball, no points
        if s1.collision_value == -1 and s2 in self.balls:
            self.balls.remove(s2)
            self.to_remove_from_space.append(s2)
            return False

        # side walls get no points
        elif s1.collision_value == 0:
            return True

        elif s1.collision_value > 0:
            self.score += s1.collision_value
            if s2 in self.balls:
                self.balls.remove(s2)
                self.to_remove_from_space.append(s2)

        return True


    def update_scene(self):
        super(SlantSim,self).update_scene()

        self.screen.fill(COLORS['white'])

        for line in self.lines:
            body = line.body

            # not quite sure what this is doing
            pv1 = body.position + line.a.rotated(body.angle)
            pv2 = body.position + line.b.rotated(body.angle)
            p1 = pv1.x, self.flip_y(pv1.y)
            p2 = pv2.x, self.flip_y(pv2.y)

            # draw our platform
            pygame.draw.lines(self.screen,
                              COLORS['lightgray'],
                              False,
                              (p1, p2),
                              self.platform_width)

        for pad in self.pads:
            body = pad.body

            # not quite sure what this is doing
            pv1 = body.position + pad.a.rotated(body.angle)
            pv2 = body.position + pad.b.rotated(body.angle)
            p1 = pv1.x, self.flip_y(pv1.y)
            p2 = pv2.x, self.flip_y(pv2.y)

            # draw our platform
            pygame.draw.lines(self.screen,
                              COLORS['brown'],
                              False,
                              (p1, p2),
                              self.pad_width)

        for ball in self.balls:
            r = ball.radius
            v = ball.body.position
            rot = ball.body.rotation_vector
            p = int(v.x), int(self.flip_y(v.y))
            p2 = pm.Vec2d(rot.x, -rot.y) * r * 0.9
            pygame.draw.circle(self.screen, COLORS['blue'], p, int(r), 2)
            pygame.draw.line(self.screen, COLORS['red'], p, p + p2)

        if len(self.balls) == 0:
            self.running = False

        pygame.display.flip()
        self.clock.tick(1000)
        pygame.display.set_caption("fps: %s" % str(self.clock.get_fps()))

    def update_physics(self):
        for obj in self.to_remove_from_space:
            self.space.remove(obj)
        self.to_remove_from_space = []

        super(SlantSim,self).update_physics()

        # trying to figure out if more than the min amount of
        # movement has occured
        self.diff_check_counter += 1
        if self.diff_check_frequency * 100 == self.diff_check_counter:
            self.diff_check_counter = 0

            position_diff = 0
            for ball in self.balls:
                prev_pos = self.ball_position_lookup.get(ball)
                if prev_pos:
                    position_diff += abs(prev_pos[0]-ball.body.position[0])
                    position_diff += abs(prev_pos[1]-ball.body.position[1])
                self.ball_position_lookup[ball] = list(ball.body.position)

            # the difference in movement from the last check
            diff = abs(position_diff - self.previous_position_diff)

            # update our previous diff to current
            self.previous_position_diff = position_diff

            # change in change
            position_diff_diff = abs(diff-self.previous_position_diff_diff)
            self.previous_position_diff_diff = diff

            # are we moving ? are we moving enough?
            min_movement = self.ball_min_movement * len(self.balls)
            if self.moving and position_diff_diff < self.ball_min_movement:
                self.no_movement_count += 1
            else:
                self.no_movement_count = 0

            if self.no_movement_count > self.max_no_movement:
                print 'STOPPING'
                self.running = False

            self.moving = True

    def wrap_up(self):
        print 'score:',self.score
        print

    def reset(self):
        # we need to reset the lists and flags
        self.balls = []
        self.pads = []
        self.lines = []
        self.ball_position_lookup = {}
        pm.init_pymunk()
        pm.reset_shapeid_counter()

        self.__init__()

class HeadlessSlantSim(HeadlessSim,SlantSim):
    pass

if __name__ == "__main__":
    sim = SlantSim()
    sim.run()
