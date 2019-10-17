import math
import random
import sys
import time
from pathlib import Path

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from rlbot.utils.structures.game_data_struct import GameTickPacket

sys.path.insert(1, str(Path(__file__).absolute().parent.parent.parent))
from rlutilities.linear_algebra import *
from rlutilities.mechanics import Aerial, Drive
from rlutilities.simulation import Game, Ball


class State:
    RESET = 0
    WAIT = 1
    INITIALIZE = 2
    RUNNING = 3
    AERIAL = 4


class Agent(BaseAgent):

    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        Game.set_mode("soccar")
        self.game = Game(index, team)
        self.name = name
        self.controls = SimpleControllerState()

        self.timer = 0.0
        self.timeout = 5.0

        self.aerial = None
        self.state = State.RESET
        self.ball_predictions = None
        self.drive = None
        self.target_ball = None

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.game.read_game_information(packet,
                                        self.get_rigid_body_tick(),
                                        self.get_field_info())

        self.controls = SimpleControllerState()

        next_state = self.state

        if self.state == State.RESET:
            self.timer = 0.0

            # self.set_state_overhead()
            # self.set_state_towards()
            self.set_state_stationary()
            next_state = State.WAIT

        if self.state == State.WAIT:

            if self.timer > 0.2:
                next_state = State.INITIALIZE

        if self.state == State.INITIALIZE:
            self.aerial = Aerial(self.game.my_car)
            self.drive = Drive(self.game.my_car)
            self.drive.target = self.game.ball.location
            self.drive.speed = 1400
            next_state = State.RUNNING

        if self.state == State.RUNNING:
            self.aerial = Aerial(self.game.my_car)

            # predict where the ball will be
            prediction = Ball(self.game.ball)
            self.ball_predictions = [vec3(prediction.location)]
            for i in range(87):

                prediction.step(0.016666)
                self.ball_predictions.append(vec3(prediction.location))
                goal = vec3(0, 5120, 0)
                self.aerial.target = prediction.location + 200 * normalize(prediction.location - goal)
                self.aerial.arrival_time = prediction.time
                self.aerial.target_orientation = look_at(goal - self.aerial.target, vec3(0, 0, 1))
                self.aerial.reorient_distance = 250
                simulation = self.aerial.simulate()
                # # check if we can reach it by an aerial
                if norm(simulation.location - self.aerial.target) < 75 and simulation.location[2] > self.aerial.target[
                    2]:
                    next_state = State.AERIAL
                    break
                # We cant make it
                if i == 86:
                    self.drive.step(self.game.time_delta)
                    self.controls = self.drive.controls
        if self.state == State.AERIAL:
            self.aerial.step(self.game.time_delta)
            self.controls = self.aerial.controls
            if self.timer > self.timeout:
                next_state = State.RESET

                self.aerial = None

        self.timer += self.game.time_delta
        self.state = next_state

        self.renderer.begin_rendering()
        red = self.renderer.create_color(255, 230, 30, 30)
        purple = self.renderer.create_color(255, 230, 30, 230)
        white = self.renderer.create_color(255, 230, 230, 230)

        if self.aerial:
            r = 200
            x = vec3(r, 0, 0)
            y = vec3(0, r, 0)
            z = vec3(0, 0, r)
            target = self.aerial.target

            self.renderer.draw_line_3d(target - x, target + x, purple)
            self.renderer.draw_line_3d(target - y, target + y, purple)
            self.renderer.draw_line_3d(target - z, target + z, purple)

        if self.ball_predictions:
            self.renderer.draw_polyline_3d(self.ball_predictions, purple)

        self.renderer.end_rendering()

        return self.controls

    def set_state_towards(self):
        ball_state = BallState(physics=Physics(
            location=Vector3(0, 4000, 500),
            velocity=Vector3(250, -500, 1000),
            rotation=Rotator(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0)
        ))
        car_state = CarState(physics=Physics(
            location=Vector3(0, 0, 18),
            velocity=Vector3(0, 800, 0),
            rotation=Rotator(0, 1.6, 0),
            angular_velocity=Vector3(0, 0, 0)
        ), boost_amount=100)

        self.set_game_state(GameState(
            ball=ball_state,
            cars={self.game.id: car_state})
        )

    def set_state_overhead(self):
        ball_state = BallState(physics=Physics(
            location=Vector3(0, 0, 500),
            velocity=Vector3(0, 2000, 1500),
            rotation=Rotator(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0)
        ))
        car_state = CarState(physics=Physics(
            location=Vector3(0, 0, 18),
            velocity=Vector3(0, 800, 0),
            rotation=Rotator(0, 1.6, 0),
            angular_velocity=Vector3(0, 0, 0)
        ), boost_amount=100)

        self.set_game_state(GameState(
            ball=ball_state,
            cars={self.game.id: car_state})
        )

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
            velocity=Vector3(0, 650, 750),
            rotation=Rotator(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0)
        ))

        self.set_game_state(GameState(
            ball=ball_state,
            cars={self.game.id: car_state})
        )

    def set_state_stationary(self):
        # put the car in the middle of the field
        car_state = CarState(physics=Physics(
            location=Vector3(0, -2500, 18),
            velocity=Vector3(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0),
        ), boost_amount=100)

        # put the ball in the middle of the field
        ball_state = BallState(physics=Physics(
            location=Vector3(0, 0, 200),
            velocity=Vector3(0, 0, 750),
            angular_velocity=Vector3(0, 0, 0),
        ))

        self.set_game_state(GameState(
            ball=ball_state,
            cars={self.game.id: car_state})
        )
