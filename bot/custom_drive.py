from math import cos, atan2, pi, radians

from rlbot.agents.base_agent import SimpleControllerState
from rlutilities.linear_algebra import vec3, dot
from rlutilities.mechanics import Drive as RLUDrive

from util import sign, cap


class CustomDrive:

    def __init__(self, car):
        self.car = car
        self.target = vec3(0, 0, 0)
        self.speed = 2300
        self.controls = SimpleControllerState()
        self.finished = False
        self.rlu_drive = RLUDrive(self.car)
        self.update_rlu_drive()
        self.power_turn = True  # Handbrake while reversing to turn around quickly

    def step(self, dt: float):
        self.update_rlu_drive()
        self.rlu_drive.step(dt)
        self.finished = self.rlu_drive.finished

        car_to_target = (self.target - self.car.location)
        local_target = dot(car_to_target, self.car.rotation)
        angle = atan2(local_target[1], local_target[0])

        self.controls = self.rlu_drive.controls
        reverse = (cos(angle) < 0)
        if reverse:
            angle = -invert_angle(angle)
            if self.power_turn:
                self.controls.throttle = (-self.controls.throttle - 1) / 2
                angle *= -1
            else:
                self.controls.throttle = -1
            self.controls.steer = cap(angle * 3, -1, 1)
            self.controls.boost = False
        self.controls.handbrake = (abs(angle) > radians(70))

    def update_rlu_drive(self):
        self.target = self.target
        self.rlu_drive.target = self.target
        self.rlu_drive.speed = self.speed


def invert_angle(angle: float):
    return angle - sign(angle) * pi
