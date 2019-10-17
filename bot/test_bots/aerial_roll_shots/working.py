import math
from math import sin, cos
import random

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator

from rlutilities.linear_algebra import *
from rlutilities.mechanics import Aerial, AerialTurn
from rlutilities.simulation import Game, Ball, Car


class State:
    RESET = 0
    WAIT = 1
    INITIALIZE = 2
    RUNNING = 3


class Agent(BaseAgent):

    def __init__(self, name, team, index):
        self.name = name
        Game.set_mode("soccar")
        self.game = Game(index, team)
        self.controls = SimpleControllerState()

        self.timer = 0.0
        self.timeout = 5.0

        self.aerial = None
        self.turn = None
        self.state = State.RESET
        self.ball_predictions = None

        self.target_ball = None

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.game.read_game_information(packet,
                                        self.get_rigid_body_tick(),
                                        self.get_field_info())

        self.controls = SimpleControllerState()

        next_state = self.state

        if self.state == State.RESET:
            self.timer = 0.0

            car_state = CarState(physics=Physics(
                location=Vector3(0, -1500, 18),
                velocity=Vector3(0, 500, 0),
                rotation=Rotator(0, math.pi / 2, 0),
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

            next_state = State.WAIT

        if self.state == State.WAIT:

            if self.timer > 0.2:
                next_state = State.INITIALIZE

        if self.state == State.INITIALIZE:

            self.aerial = Aerial(self.game.my_car)
            # self.aerial.up = normalize(vec3(
            #     random.uniform(-1, 1),
            #     random.uniform(-1, 1),
            #     random.uniform(-1, 1)))
            self.turn = AerialTurn(self.game.my_car)

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
                self.aerial.reorient_distance = 200
                simulation = self.aerial.simulate()

                # # check if we can reach it by an aerial
                if norm(simulation.location - self.aerial.target) < 100:
                    print(i)
                    print(prediction.location)
                    break
                if i == 86:
                    print("FUCKED")

            next_state = State.RUNNING

        if self.state == State.RUNNING:
            self.aerial.step(self.game.time_delta)
            self.controls = self.aerial.controls
            if self.game.time == packet.game_ball.latest_touch.time_seconds:
                print(self.game.my_car.double_jumped)
                self.controls.jump = True
            if self.timer > self.timeout:
                next_state = State.RESET

                self.aerial = None
                self.turn = None

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
