from math import sin, cos
import random
import sys
import time
from pathlib import Path

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from rlbot.utils.structures.game_data_struct import GameTickPacket

sys.path.insert(1, str(Path(__file__).absolute().parent.parent.parent))
from rlutilities.linear_algebra import *
from rlutilities.mechanics import Jump
from rlutilities.simulation import Game, Ball


class State:
    RESET = 0
    WAIT = 1
    INITIALIZE = 2
    RUNNING = 3


class MyAgent(BaseAgent):

    def __init__(self, name, team, index):
        self.name = name
        self.game = Game(index, team)
        self.controls = SimpleControllerState()

        self.timer = 0.0

        self.action = None
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
                location=Vector3(0, 0, 18),
                velocity=Vector3(0, 0, 0),
                rotation=Rotator(0, 0, 0),
                angular_velocity=Vector3(0, 0, 0)
            ), boost_amount=100)

            theta = random.uniform(0, 6.28)
            pos = Vector3(sin(theta) * 1000.0, cos(theta) * 1000.0, 100.0)

            # put the ball somewhere out of the way
            ball_state = BallState(physics=Physics(
                location=pos,
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

            self.action = Jump(self.game.my_car)
            self.action.duration = 0.2

            next_state = State.RUNNING
            self.timer = 0.0

        if self.state == State.RUNNING:

            self.action.step(self.game.time_delta)
            self.controls = self.action.controls
            if self.controls.jump:
                self.controls.boost = 1
                self.controls.pitch = 1
            else:
                self.controls.boost = 1
                self.controls.pitch = 0.2
            print(self.timer, self.game.my_car.location[2], self.controls.jump)

            if self.timer > 2:
                next_state = State.RESET

        self.timer += self.game.time_delta
        self.state = next_state

        return self.controls