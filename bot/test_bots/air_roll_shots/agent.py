import math
import random
import time
import sys
from pathlib import Path

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from rlbot.utils.structures.game_data_struct import GameTickPacket

sys.path.insert(1, str(Path(__file__).absolute().parent.parent.parent))
from rlutilities.linear_algebra import *
from rlutilities.mechanics import Dodge, AerialTurn, Drive
from rlutilities.simulation import Game, Car, obb, intersect, Ball, sphere


class State:
    RESET = 0
    WAIT = 1
    INITIALIZE = 2
    DRIVING = 3
    DODGING = 4


class MyAgent(BaseAgent):

    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.game = Game(index, team)
        self.name = name
        self.controls = SimpleControllerState()

        self.timer = 0.0

        self.drive = Drive(self.game.my_car)
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
                location=Vector3(0, -2500, 18),
                velocity=Vector3(0, 0, 0),
                rotation=Rotator(0, math.pi / 2, 0),
                angular_velocity=Vector3(0, 0, 0)
            ))

            # put the ball in the middle of the field

            ball_state = BallState(physics=Physics(
                location=Vector3(0, 0, 93),
                velocity=Vector3(0, random.randint(-250, 800), random.randint(700, 800)),
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
            self.drive.target = self.game.ball.location
            self.drive.step(self.game.time_delta)
            self.controls = self.drive.controls
            a = time.time()
            can_dodge, simulated_duration, simulated_target = self.simulate()
            print(time.time() - a)
            if can_dodge:
                self.dodge = Dodge(self.game.my_car)
                self.turn = AerialTurn(self.game.my_car)

                self.dodge.duration = simulated_duration
                self.dodge.target = simulated_target
                # self.dodge.preorientation = look_at(-0.1 * f - u, -1.0 * u)
                self.timer = 0
                next_state = State.DODGING

        if self.state == State.DODGING:
            self.dodge.step(self.game.time_delta)
            self.controls = self.dodge.controls
            if self.dodge.finished and self.game.my_car.on_ground:
                next_state = State.RESET

        self.timer += self.game.time_delta
        self.state = next_state

        return self.controls

    def simulate(self):
        for i in range(18):
            car = Car(self.game.my_car)
            ball = Ball(self.game.ball)
            batmobile = obb()
            batmobile.half_width = vec3(64.4098892211914, 42.335182189941406, 14.697200775146484)
            batmobile.center = car.location + dot(car.rotation, vec3(9.01, 0, 12.09))
            batmobile.orientation = car.rotation
            ball_prediction = self.get_ball_prediction_struct()
            dodge = Dodge(car)
            dodge.duration = i * 0.05
            dodge.target = ball.location
            for j in range(round(60 * i * 0.05)):
                dodge.target = ball.location
                dodge.step(1 / 60)
                car.step(dodge.controls, 1 / 60)
                prediction_slice = ball_prediction.slices[j]
                physics = prediction_slice.physics
                ball_location = vec3(physics.location.x, physics.location.y, physics.location.z)
                dodge.target = ball_location
                batmobile.center = car.location + dot(car.rotation, vec3(9.01, 0, 12.09))
                batmobile.orientation = car.rotation
                if intersect(sphere(ball_location, 93.15), batmobile) and abs(ball_location[2] - car.location[2]) < 25 and car.location[2] < ball_location[2]:
                    print(ball.location)
                    print(car.location)
                    print(j / 60)
                    print(i * 0.05)
                    return True, j / 60, ball_location
        return False, None, None
