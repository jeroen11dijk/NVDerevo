""""Module that handles the catching strategy"""
import math

from rlutilities.linear_algebra import *
from rlutilities.simulation import Input


class Catching:
    """"Class that handles the defending strategy"""
    __slots__ = ['car', 'target_location', 'target_speed', 'controls', 'finished']

    def __init__(self, car, target_location=vec3(0, 0, 0), target_speed=0):

        self.car = car
        self.target_location = target_location
        self.target_speed = target_speed
        self.controls = Input()

        self.finished = False

    def step(self):
        """"Gives output for the catching strategy"""
        max_throttle_speed = 1410
        # max_boost_speed = 2300

        # get the local coordinates of where the ball is, relative to the car
        # delta_local[0]: how far in front
        # delta_local[1]: how far to the left
        # delta_local[2]: how far above
        delta_local = dot(self.target_location - self.car.location, self.car.rotation)

        # angle between car's forward direction and target locationition
        phi = math.atan2(delta_local[1], delta_local[0])

        if phi < -math.radians(10):
            # If the target is more than 10 degrees right from the centre, steer left
            self.controls.steer = -1
        elif phi > math.radians(10):
            # If the target is more than 10 degrees left from the centre, steer right
            self.controls.steer = 1
        else:
            # If the target is less than 10 degrees from the centre, steer straight
            self.controls.steer = phi / math.radians(10)

        if abs(phi) < math.radians(3) and not self.car.supersonic:
            self.controls.boost = True
        else:
            self.controls.boost = False

        if abs(phi) > 1.75:
            self.controls.handbrake = 1
        else:
            self.controls.handbrake = 0

        # forward velocity
        vf = dot(self.car.velocity, self.car.forward())

        if vf < self.target_speed:
            self.controls.throttle = 1.0
            if self.target_speed > max_throttle_speed:
                self.controls.boost = 1
            else:
                self.controls.boost = 0
        else:
            self.controls.throttle = -1
            self.controls.boost = 0
            if norm(delta_local) < 20:
                self.controls.throttle = -norm(delta_local) / 20
            if norm(delta_local) < 10:
                self.controls.throttle = -norm(delta_local) / 10

        if self.car.supersonic:
            self.controls.boost = False

        if norm(self.car.location - self.target_location) < 100:
            self.finished = True
