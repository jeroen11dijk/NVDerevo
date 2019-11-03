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
from rlutilities.mechanics import AerialTurn, Aerial, Drive
from rlutilities.simulation import Game, Ball

ball_z = 300


class State:
    RESET = 0
    WAIT = 1
    INITIALIZE = 2
    RUNNING = 3
    DRIVING = 4


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
        self.dodge = None
        self.state = State.RESET
        self.ball_predictions = None

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:

        # Update the game values and set the state
        self.game.read_game_information(packet,
                                        self.get_rigid_body_tick(),
                                        self.get_field_info())

        self.controls = SimpleControllerState()

        next_state = self.state

        # Reset everything
        if self.state == State.RESET:
            self.timer = 0.0
            self.set_state_stationary()
            next_state = State.WAIT

        # Wait so everything can settle in, mainly for ball prediction
        if self.state == State.WAIT:

            if self.timer > 0.2:
                next_state = State.INITIALIZE

        # Initialize the drive mechanic
        if self.state == State.INITIALIZE:
            self.drive = Drive(self.game.my_car)
            self.drive.target = self.game.ball.location + 200 * normalize(
                vec3(vec2(self.game.ball.location - vec3(0, 5120, 0))))
            self.drive.speed = 1400
            next_state = State.DRIVING

        # Start driving towards the target and check whether an aerial is possible, if so initialize the dodge
        if self.state == State.DRIVING:
            self.drive.target = self.game.ball.location + 200 * normalize(
                vec3(vec2(self.game.ball.location - vec3(0, 5120, 0))))
            self.drive.step(self.game.time_delta)
            self.controls = self.drive.controls

            # Initialize the aerial and aerial turn
            self.aerial = Aerial(self.game.my_car)
            self.turn = AerialTurn(self.game.my_car)

            # predict where the ball will be
            prediction = Ball(self.game.ball)
            self.ball_predictions = [vec3(prediction.location)]

            # Loop over 87 frames which results in a time limit of 1.45
            # Seeing we jump once and hold it for 0.2s we keep our second dodge until that moment
            a = time.time()
            for i in range(87):
                # Step the ball prediction and add it to the array for rendering
                prediction.step(0.016666)
                self.ball_predictions.append(vec3(prediction.location))
                # TODO dont hardcode the goal vector!
                # Set the target to a slight offset of the ball so we will hit it towards the target or goal
                # Set the arrival time to the time the ball will be in that location
                # Set the preorientation so we will look at the goal
                goal = vec3(0, 5120, 0)
                # self.aerial.target = prediction.location + 200 * normalize(prediction.location - goal)
                self.aerial.target = vec3(0, 0, ball_z) + 200 * normalize(prediction.location - goal)
                self.aerial.arrival_time = prediction.time
                print(prediction.time)
                # self.aerial.target_orientation = look_at(goal - self.aerial.target, vec3(0, 0, 1))
                self.aerial.target_orientation = look_at(goal - self.game.my_car.location, vec3(0, 0, 1))
                # Simulate the aerial and see whether its doable or not
                simulation = self.aerial.simulate()
                # # check if we can reach it by an aerial
                if norm(simulation.location - self.aerial.target) < 100 and angle_between(simulation.rotation,
                                                                                          self.aerial.target_orientation) < 0.01:
                    print(i)
                    print(prediction.location)
                    print(self.game.my_car.rotation)
                    print("predicted rotation")
                    print(simulation.rotation)
                    next_state = State.RUNNING
                    break
            print("time:")
            print(time.time() - a)

        # Perform the aerial mechanic
        if self.state == State.RUNNING:
            self.aerial.step(self.game.time_delta)
            self.controls = self.aerial.controls
            if self.game.time == packet.game_ball.latest_touch.time_seconds:
                print(self.game.my_car.double_jumped)
                self.controls.jump = True
                print("actual rotation")
                print(self.game.my_car.rotation)
            if self.timer > self.timeout:
                next_state = State.RESET

                self.aerial = None
                self.turn = None

        self.timer += self.game.time_delta
        self.state = next_state

        # Render the target for the aerial
        self.renderer.begin_rendering()
        purple = self.renderer.create_color(255, 230, 30, 230)

        if self.aerial:
            r = 200
            x = vec3(r, 0, 0)
            y = vec3(0, r, 0)
            z = vec3(0, 0, r)
            target = self.aerial.target

            self.renderer.draw_line_3d(target - x, target + x, purple)
            self.renderer.draw_line_3d(target - y, target + y, purple)
            self.renderer.draw_line_3d(target - z, target + z, purple)
            # self.renderer.draw_line_3d(self.game.my_car.location,
            #                            1000 * dot(self.aerial.target_orientation, self.game.my_car.forward()), purple)

        # Render ball prediction
        if self.ball_predictions:
            self.renderer.draw_polyline_3d(self.ball_predictions, purple)

        self.renderer.end_rendering()

        return self.controls

    def set_state_1(self):
        car_state = CarState(physics=Physics(
            location=Vector3(0, -2000, 18),
            velocity=Vector3(0, 500, 0),
            rotation=Rotator(0, math.pi / 2, 0),
            angular_velocity=Vector3(0, 0, 0),
        ), boost_amount=100)

        # put the ball in the middle of the field
        ball_state = BallState(physics=Physics(
            location=Vector3(0, 0, 400),
            velocity=Vector3(0, 0, 450),
            angular_velocity=Vector3(0, 0, 0),
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
            rotation=Rotator(0, math.pi / 2, 0),
            angular_velocity=Vector3(0, 0, 0),
        ), boost_amount=100)

        # put the ball in the middle of the field
        ball_state = BallState(physics=Physics(
            location=Vector3(0, 0, ball_z),
            velocity=Vector3(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0),
        ))

        self.set_game_state(GameState(
            ball=ball_state,
            cars={self.game.id: car_state})
        )
