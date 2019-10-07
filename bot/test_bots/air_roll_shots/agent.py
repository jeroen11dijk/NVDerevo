import math
import random
import time
import sys
from pathlib import Path

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from rlbot.utils.structures.game_data_struct import GameTickPacket

from jump_sim import get_time_at_height

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

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:

        self.game.read_game_information(packet,
                                        self.get_rigid_body_tick(),
                                        self.get_field_info())
        self.controls = SimpleControllerState()

        next_state = self.state

        if self.state == State.RESET:
            self.timer = 0.0
            self.set_gamestate_straight_moving()
            # self.set_gamestate_angled_stationary()
            # self.set_gamestate_straight_moving_towards()
            next_state = State.WAIT

        if self.state == State.WAIT:

            if self.timer > 0.2:
                next_state = State.INITIALIZE

        if self.state == State.INITIALIZE:
            self.drive = Drive(self.game.my_car)
            self.drive.target, self.drive.speed = self.game.ball.location, 2300
            next_state = State.DRIVING

        if self.state == State.DRIVING:
            self.drive.target = self.game.ball.location
            self.drive.step(self.game.time_delta)
            self.controls = self.drive.controls
            can_dodge, simulated_duration, simulated_target = self.simulate()
            if can_dodge:
                self.dodge = Dodge(self.game.my_car)
                self.turn = AerialTurn(self.game.my_car)
                print("============")
                print(simulated_duration)
                self.dodge.duration = simulated_duration - 0.1
                self.dodge.target = simulated_target
                self.timer = 0
                next_state = State.DODGING

        if self.state == State.DODGING:
            self.dodge.step(self.game.time_delta)
            self.controls = self.dodge.controls
            if self.game.time == packet.game_ball.latest_touch.time_seconds:
                print(self.timer)
            if self.dodge.finished and self.game.my_car.on_ground:
                next_state = State.RESET

        self.timer += self.game.time_delta
        self.state = next_state

        return self.controls

    def simulate(self):
        ball_prediction = self.get_ball_prediction_struct()
        duration_estimate = math.floor(get_time_at_height(self.game.ball.location[2], 0.2) * 10) / 10
        for i in range(6):
            car = Car(self.game.my_car)
            ball = Ball(self.game.ball)
            batmobile = obb()
            batmobile.half_width = vec3(64.4098892211914, 42.335182189941406, 14.697200775146484)
            batmobile.center = car.location + dot(car.rotation, vec3(9.01, 0, 12.09))
            batmobile.orientation = car.rotation
            dodge = Dodge(car)
            dodge.duration = duration_estimate + i / 60
            dodge.target = ball.location
            for j in range(round(60 * dodge.duration)):
                dodge.target = ball.location
                dodge.step(1 / 60)
                car.step(dodge.controls, 1 / 60)
                prediction_slice = ball_prediction.slices[j]
                physics = prediction_slice.physics
                ball_location = vec3(physics.location.x, physics.location.y, physics.location.z)
                dodge.target = ball_location
                batmobile.center = car.location + dot(car.rotation, vec3(9.01, 0, 12.09))
                batmobile.orientation = car.rotation
                if intersect(sphere(ball_location, 93.15), batmobile) and abs(
                        ball_location[2] - car.location[2]) < 25 and car.location[2] < ball_location[2]:
                    return True, j / 60, ball_location
        return False, None, None

    def set_gamestate_straight_moving(self):
        # put the car in the middle of the field
        car_state = CarState(physics=Physics(
            location=Vector3(0, -1000, 18),
            velocity=Vector3(0, 0, 0),
            rotation=Rotator(0, math.pi / 2, 0),
            angular_velocity=Vector3(0, 0, 0)
        ))

        # put the ball in the middle of the field

        ball_state = BallState(physics=Physics(
            location=Vector3(0, 1500, 93),
            velocity=Vector3(0, random.randint(-250, 800), random.randint(700, 800)),
            rotation=Rotator(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0)
        ))

        self.set_game_state(GameState(
            ball=ball_state,
            cars={self.game.id: car_state})
        )

    def set_gamestate_straight_moving_towards(self):
        # put the car in the middle of the field
        car_state = CarState(physics=Physics(
            location=Vector3(0, 0, 18),
            velocity=Vector3(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0),
        ))

        # put the ball in the middle of the field

        ball_state = BallState(physics=Physics(
            location=Vector3(0, 2500, 93),
            velocity=Vector3(0, -250, 700),
            rotation=Rotator(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0),
        ))

        self.set_game_state(GameState(
            ball=ball_state,
            cars={self.game.id: car_state})
        )

    def set_gamestate_angled_stationary(self):
        # put the car in the middle of the field
        car_state = CarState(physics=Physics(
            location=Vector3(-1000, -1500, 18),
            velocity=Vector3(0, 0, 0),
            rotation=Rotator(0, math.pi / 8, 0),
            angular_velocity=Vector3(0, 0, 0)
        ))

        # put the ball in the middle of the field

        ball_state = BallState(physics=Physics(
            location=Vector3(0, 0, 750),
            velocity=Vector3(0, 0, 1),
            rotation=Rotator(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0)
        ))

        self.set_game_state(GameState(
            ball=ball_state,
            cars={self.game.id: car_state})
        )
