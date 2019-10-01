import math
import random
import matplotlib.pyplot as plt
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator

from rlutilities.linear_algebra import *
from rlutilities.mechanics import FollowPath, Dodge, AerialTurn, Drive
from rlutilities.simulation import Game, Navigator


class State:
    RESET = 0
    WAIT = 1
    INITIALIZE = 2
    DRIVING = 3
    DODGING = 4


class MyAgent(BaseAgent):

    def __init__(self, name, team, index):
        self.game = Game(index, team)
        self.name = name
        self.controls = SimpleControllerState()

        self.timer = 0.0

        self.drive = None
        self.navigator = None
        self.dodge = None
        self.turn = None
        self.state = State.RESET
        self.height = 0
        self.time = 0

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
                # location=Vector3(random.randint(-1000, 1000), random.randint(-2000, 500), 18),
                # location=Vector3(-2500, -2500, 18),
                location=Vector3(0, -2500, 18),
                velocity=Vector3(0, 0, 0),
                rotation=Rotator(0, math.pi / 2, 0),
                angular_velocity=Vector3(0, 0, 0)
            ))

            # put the ball in the middle of the field

            ball_state = BallState(physics=Physics(
                location=Vector3(0, 0, 234),
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
            # self.drive = FollowPath(self.game.my_car)
            #
            # self.navigator = Navigator(self.game.my_car)
            #
            # self.navigator.analyze_surroundings(3.0)
            # goal_to_ball = vec3(0, 5120, 0) - self.game.ball.location
            # self.drive.path = self.navigator.path_to(self.game.ball.location, goal_to_ball, self.drive.arrival_speed)
            self.drive = Drive(self.game.my_car)
            self.drive.target, self.drive.speed = self.game.ball.location, 1400
            next_state = State.DRIVING

        if self.state == State.DRIVING:
            # self.render()

            self.drive.step(self.game.time_delta)
            self.controls = self.drive.controls

            if norm((vec2(self.game.my_car.location - self.game.ball.location))) < 0.9*1400:
                self.dodge = Dodge(self.game.my_car)
                self.turn = AerialTurn(self.game.my_car)

                self.dodge.duration = 0.9
                self.dodge.target = self.game.ball.location
                # self.dodge.preorientation = look_at(-0.1 * f - u, -1.0 * u)
                self.timer = 0
                next_state = State.DODGING

        if self.state == State.DODGING:
            if self.game.my_car.location[2] > self.height:
                self.height = self.game.my_car.location[2]
                self.time = self.timer
            self.dodge.step(self.game.time_delta)
            self.controls = self.dodge.controls

            if self.dodge.finished and self.game.my_car.on_ground:
                print(self.time, self.height)
                next_state = State.RESET

        self.timer += self.game.time_delta
        self.state = next_state

        return self.controls

    def render(self):
        vertices = self.drive.path.points

        self.renderer.begin_rendering("path")
        red = self.renderer.create_color(255, 255, 255, 255)
        for i in range(0, len(vertices) - 1):
            self.renderer.draw_line_3d(vertices[i], vertices[i + 1], red)

        self.renderer.draw_string_2d(50, 50, 3, 3, str(self.drive.arrival_time - self.game.my_car.time), red)
        self.renderer.end_rendering()
