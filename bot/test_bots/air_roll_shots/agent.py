import math
import sys
import time
from pathlib import Path

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from rlbot.utils.structures.game_data_struct import GameTickPacket

from jump_sim import get_time_at_height

sys.path.insert(1, str(Path(__file__).absolute().parent.parent.parent))
from rlutilities.linear_algebra import *
from rlutilities.mechanics import Dodge, AerialTurn, Drive
from rlutilities.simulation import Game, Car, obb, intersect, sphere


class State:
    RESET = 0
    WAIT = 1
    INITIALIZE = 2
    DRIVING = 3
    DODGING = 4


class MyAgent(BaseAgent):

    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        Game.set_mode("soccar")
        self.game = Game(index, team)
        self.name = name
        self.controls = SimpleControllerState()
        self.timer = 0.0

        self.drive = Drive(self.game.my_car)
        self.dodge = None
        self.turn = None
        self.state = State.RESET

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

        # Start driving towards the target and check whether a dodge is possible, if so initialize the dodge
        if self.state == State.DRIVING:
            self.drive.target = self.game.ball.location + 200 * normalize(
                vec3(vec2(self.game.ball.location - vec3(0, 5120, 0))))
            self.drive.step(self.game.time_delta)
            self.controls = self.drive.controls
            a = time.time()
            can_dodge, simulated_duration, simulated_target = self.simulate()
            print(time.time() - a)
            if can_dodge:
                self.dodge = Dodge(self.game.my_car)
                self.turn = AerialTurn(self.game.my_car)
                self.dodge.duration = simulated_duration - 0.1
                self.dodge.direction = vec2(vec3(0, 5120, 321) - simulated_target)
                self.dodge.preorientation = look_at(xy(vec3(0, 5120, 321) - simulated_target), vec3(0, 0, 1))
                self.timer = 0
                next_state = State.DODGING

        # Perform the dodge
        if self.state == State.DODGING:
            self.dodge.step(self.game.time_delta)
            self.controls = self.dodge.controls
            # Great line
            # if self.game.time == packet.game_ball.latest_touch.time_seconds:
            #     print(self.timer)
            if self.dodge.finished and self.game.my_car.on_ground:
                next_state = State.RESET

        self.timer += self.game.time_delta
        self.state = next_state

        return self.controls

    # The miraculous simulate function
    #TODO optimize heavily in case I actually need it
    # If duration_estimate = 0.8 and the ball is moving up there is not sense in even simulating it.
    # Might even lower it since the higher the duration estimate the longer the simulation takes.
    def simulate(self):
        lol = 0
        # Initialize the ball prediction and batmobile hitbox
        # Estimate the probable duration of the jump and round it down to the floor decimal
        ball_prediction = self.get_ball_prediction_struct()
        duration_estimate = math.floor(get_time_at_height(self.game.ball.location[2], 0.2) * 10) / 10
        batmobile = obb()
        batmobile.half_width = vec3(64.4098892211914, 42.335182189941406, 14.697200775146484)
        # Loop for 6 frames meaning adding 0.1 to the estimated duration. Keeps the time constraint under 0.3s
        for i in range(6):
            # Copy the car object and reset the values for the hitbox
            car = Car(self.game.my_car)
            batmobile.center = car.location + dot(car.rotation, vec3(9.01, 0, 12.09))
            batmobile.orientation = car.rotation
            # Create a dodge object on the copied car object
            # Direction is from the ball to the enemy goal
            # Duration is estimated duration plus the time added by the for loop
            # Preorientation is the rotation matrix from the ball to the goal
            # TODO make it work on both sides
            #  Test with preorientation. Currently it still picks a low duration at a later time meaning it
            #  wont do any of the preorientation.
            dodge = Dodge(car)
            prediction_slice = ball_prediction.slices[round(60 * (duration_estimate + i / 60))]
            physics = prediction_slice.physics
            ball_location = vec3(physics.location.x, physics.location.y, physics.location.z)
            dodge.direction = vec2(vec3(0, 5120, 321) - ball_location)
            dodge.duration = duration_estimate + i / 60
            dodge.preorientation = look_at(xy(vec3(0, 5120, 321) - car.location), vec3(0, 0, 1))
            # Loop from now till the end of the duration
            fps = 60
            for j in range(round(fps * dodge.duration)):
                lol = lol + 1
                # Get the dodge inputs and perform that to the copied car object
                dodge.preorientation = look_at(xy(vec3(0, 5120, 321) - car.location), vec3(0, 0, 1))
                dodge.step(1 / fps)
                car.step(dodge.controls, 1 / fps)
                # Get the ball prediction slice at this time and convert the location to RLU vec3
                prediction_slice = ball_prediction.slices[round(60 * j / fps)]
                physics = prediction_slice.physics
                ball_location = vec3(physics.location.x, physics.location.y, physics.location.z)
                # Update the hitbox information
                batmobile.center = car.location + dot(car.rotation, vec3(9.01, 0, 12.09))
                batmobile.orientation = car.rotation
                # Check if we hit the ball, and if the point of contact is just below the middle
                # TODO check for the actual point of contact instead of the car position
                hit_check = intersect(sphere(ball_location, 93.15), batmobile)
                hit_location_check = abs(ball_location[2] - car.location[2]) < 25 and car.location[2] < ball_location[2]
                angle_car_simulation = angle_between(car.rotation, self.game.my_car.rotation)
                angle_simulation_target = angle_between(car.rotation, dodge.preorientation)
                angle_check = angle_simulation_target < angle_car_simulation or angle_simulation_target < 0.1
                if hit_check and hit_location_check and angle_check:
                    print("------------------------------------------------------")
                    print(angle_simulation_target, angle_car_simulation)
                    return True, j / fps, ball_location
        return False, None, None

    """" State setting methods for various situations"""

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
            velocity=Vector3(200, 650, 750),
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
            location=Vector3(-1000, -2000, 18),
            velocity=Vector3(0, 0, 0),
            rotation=Rotator(0, math.pi / 8, 0),
            angular_velocity=Vector3(0, 0, 0)
        ))

        # put the ball in the middle of the field

        ball_state = BallState(physics=Physics(
            location=Vector3(0, 0, 600),
            velocity=Vector3(0, 0, 1),
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
            rotation=Rotator(0, math.pi / 2, 0),
            angular_velocity=Vector3(0, 0, 0),
        ), boost_amount=100)

        # put the ball in the middle of the field
        ball_state = BallState(physics=Physics(
            location=Vector3(1500, 0, 93),
            velocity=Vector3(0, 0, 750),
            angular_velocity=Vector3(0, 0, 0),
        ))

        self.set_game_state(GameState(
            ball=ball_state,
            cars={self.game.id: car_state})
        )
