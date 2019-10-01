import sys

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from rlbot.utils.structures.game_data_struct import GameTickPacket

sys.path.insert(1, 'C:/Users/Jeroen van Dijk/Documents/RLBotPythonExample-master/NV Derevo/bot')
from rlutilities.linear_algebra import *
from rlutilities.mechanics import Dodge, AerialTurn, Drive
from rlutilities.simulation import Game

import math


class State:
    RESET = 0
    WAIT = 1
    INITIALIZE = 2
    RUNNING = 3


class self(BaseAgent):

    def __init__(self, name, team, index):
        self.game = Game(index, team)
        self.controls = SimpleControllerState()
        self.team = team
        self.timer = 0.0
        self.timeout = 3.0
        self.renderPoint = vec3(0, 0, 0)
        self.turn = None
        self.dodge = None
        self.drive = None
        self.step = None
        self.name = "NotNone"
        self.state = State.RESET

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.game.read_game_information(packet,
                                        self.get_rigid_body_tick(),
                                        self.get_field_info())
        self.controls = SimpleControllerState()
        next_state = self.state
        if self.state == State.RESET:
            self.timer = 0.0

            # put the car in the middle of the field
            car_state = CarState(physics=Physics(
                location=Vector3(0, -4608, 18),
                velocity=Vector3(0, 0, 0),
                rotation=Rotator(0, math.pi / 2, 0),
                angular_velocity=Vector3(0, 0, 0)
            ), boost_amount=33)

            # put the ball somewhere out of the way
            ball_state = BallState(physics=Physics(
                location=Vector3(0, 0, 93),
                velocity=Vector3(0, 0, 0),
                rotation=Rotator(0, 0, 0),
                angular_velocity=Vector3(0, 0, 0)
            ))

            self.set_game_state(GameState(
                ball=ball_state,
                cars={self.game.id: car_state})
            )

            next_state = State.WAIT

        if self.state == State.WAIT:

            if self.timer > 0.2:
                next_state = State.INITIALIZE

        if self.state == State.INITIALIZE:
            pad = self.get_closest_small_pad()
            # target = vec3(pad[0], pad[1], pad[2]) - sign(self.team) * vec3(0, 500, 0)
            target = vec3(pad[0], pad[1], pad[2])
            self.drive = Drive(self.game.my_car)
            self.dodge = Dodge(self.game.my_car)
            self.turn = AerialTurn(self.game.my_car)
            self.drive.target = target
            self.drive.speed = 2400
            self.step = "Drive"
            self.drive.step(self.game.time_delta)
            self.controls = self.drive.controls
            next_state = State.RUNNING

        if self.state == State.RUNNING:

            if self.step == "Drive":
                self.drive.step(self.game.time_delta)
                self.controls = self.drive.controls
                if self.drive.finished:
                    self.dodge.duration = 0.15
                    self.dodge.delay = 0.4
                    self.dodge.target = vec3(dot(rotation(math.radians(-60)), vec2(self.game.my_car.forward())) * 10000)
                    self.dodge.preorientation = dot(axis_to_rotation(vec3(0, 0, math.radians(40))),
                                                    self.game.my_car.rotation)
                    self.timer = 0.0
                    self.step = "Dodge1"
            elif self.step == "Dodge1":
                if self.timer > 1.2:
                    self.turn.target = look_at(xy(self.game.my_car.velocity), vec3(0, 0, 1))
                    self.turn.step(self.game.time_delta)
                    self.controls = self.turn.controls
                    self.controls.boost = 0

                else:
                    self.dodge.step(self.game.time_delta)
                    self.controls = self.dodge.controls
                    self.controls.boost = 1

                if self.timer > self.timeout:
                    self.step = "Steer"
                    target = self.game.ball.location + sign(self.team) * vec3(0, 850, 0)
                    self.drive = Drive(self.game.my_car)
                    self.drive.target = target
                    self.drive.speed = 2400
                    next_state = State.RESET
            elif self.step == "Steer":
                self.drive.step(self.game.time_delta)
                self.controls = self.drive.controls
                if self.drive.finished:
                    self.step = "Dodge2"
                    self.dodge = Dodge(self.game.my_car)
                    self.dodge.duration = 0.075
                    self.dodge.target = self.game.ball.location
            elif self.step == "Dodge2":
                self.dodge.step(self.game.time_delta)
                self.controls = self.dodge.controls
                if self.dodge.finished and self.game.my_car.on_ground:
                    next_state = State.RESET

        self.timer += self.game.time_delta
        self.state = next_state

        if self.step:
            self.renderer.begin_rendering()
            self.renderer.draw_string_2d(50, 50, 6, 6, self.step, self.renderer.red())
            # self.renderer.draw_line_3d(self.game.my_car.location, self.renderPoint, self.renderer.red())
            self.renderer.end_rendering()

        return self.controls

    def get_closest_small_pad(self):
        """Gets the small boostpad closest to the bot"""
        small_boost_pads = []
        field_info = self.get_field_info()
        for i in range(field_info.num_boosts):
            current = field_info.boost_pads[i]
            if not field_info.boost_pads[i].is_full_boost:
                small_boost_pads.append(vec3(current.location.x, current.location.y, current.location.z))
        closest_pad = None
        distance = math.inf
        for pad in small_boost_pads:
            if distance_2d(self.game.my_car.location, pad) < distance:
                distance = distance_2d(self.game.my_car.location, pad)
                closest_pad = pad
        return closest_pad


def distance_2d(vec_a, vec_b):
    """returns 2d distance between two vectors"""
    return norm(vec2(vec_a - vec_b))


def sign(num):
    """Returns 1 if the number is bigger then 0 otherwise it returns -1"""
    if num <= 0:
        return -1
    return 1
