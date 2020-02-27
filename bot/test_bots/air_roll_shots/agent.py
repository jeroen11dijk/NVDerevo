import math
import sys
import time
from pathlib import Path

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from rlbot.utils.structures.game_data_struct import GameTickPacket

from jump_sim import get_time_at_height, get_time_at_height_boost

sys.path.insert(1, str(Path(__file__).absolute().parent.parent.parent))
from rlutilities.linear_algebra import Dodge, AerialTurn, Drive
from rlutilities.simulation import Game, Car, obb, sphere

ball_z = 275
ball_y = 1000
jeroens_magic_number = 5


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
            # self.set_gamestate_straight_moving()
            # self.set_gamestate_straight_moving_towards()
            self.set_state_stationary_angled()
            # self.set_gamestate_angled_stationary()
            # self.set_state_stationary()
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

                target = vec3(0, 5120, jeroens_magic_number * simulated_target[2])
                self.dodge.preorientation = look_at(target - simulated_target, vec3(0, 0, 1))
                self.timer = 0
                next_state = State.DODGING

        # Perform the dodge
        if self.state == State.DODGING:
            self.dodge.step(self.game.time_delta)
            self.controls = self.dodge.controls

            T = self.dodge.duration - self.dodge.timer
            if T > 0:
                if self.dodge.timer < 0.2:
                    self.controls.boost = 1
                    # self.controls.pitch = 1
                else:
                    xf = self.game.my_car.location + 0.5 * T * T * vec3(0, 0, -650) + T * self.game.my_car.velocity

                    delta_x = self.game.ball.location - xf
                    if angle_between(vec2(self.game.my_car.forward()), self.dodge.direction) < 0.3:
                        if norm(delta_x) > 50:
                            self.controls.boost = 1
                            self.controls.throttle = 0.0
                        else:
                            self.controls.boost = 0
                            self.controls.throttle = clip(0.5 * (200 / 3) * T * T, 0.0, 1.0)
                    else:
                        self.controls.boost = 0
                        self.controls.throttle = 0.0
            else:
                self.controls.boost = 0

            # Great line
            # if self.game.time == packet.game_ball.latest_touch.time_seconds:
            #     print(self.game.my_car.location)
            if self.dodge.finished and self.game.my_car.on_ground:
                next_state = State.RESET

        self.timer += self.game.time_delta
        self.state = next_state

        return self.controls

    # The miraculous simulate function
    # TODO optimize heavily in case I actually need it
    # Option one: estimate the time for the current height and look at that ball prediction.
    # If its heigher use that unless it gets unreachable and else compare with the lower one.
    # If duration_estimate = 0.8 and the ball is moving up there is not sense in even simulating it.
    # Might even lower it since the higher the duration estimate the longer the simulation takes.
    def simulate(self):
        lol = 0
        # Initialize the ball prediction
        # Estimate the probable duration of the jump and round it down to the floor decimal
        ball_prediction = self.get_ball_prediction_struct()
        if self.game.my_car.boost < 6:
            duration_estimate = math.floor(get_time_at_height(self.game.ball.location[2]) * 10) / 10
        else:
            adjacent = norm(vec2(self.game.my_car.location - self.game.ball.location))
            opposite = (self.game.ball.location[2] - self.game.my_car.location[2])
            theta = math.atan(opposite / adjacent)
            t = get_time_at_height_boost(self.game.ball.location[2], theta, self.game.my_car.boost)
            duration_estimate = (math.ceil(t * 10) / 10)
        # Loop for 6 frames meaning adding 0.1 to the estimated duration. Keeps the time constraint under 0.3s
        for i in range(6):
            # Copy the car object and reset the values for the hitbox
            car = Car(self.game.my_car)
            # Create a dodge object on the copied car object
            # Direction is from the ball to the enemy goal
            # Duration is estimated duration plus the time added by the for loop
            # preorientation is the rotation matrix from the ball to the goal
            # TODO make it work on both sides
            #  Test with preorientation. Currently it still picks a low duration at a later time meaning it
            #  wont do any of the preorientation.
            dodge = Dodge(car)
            prediction_slice = ball_prediction.slices[round(60 * (duration_estimate + i / 60))]
            physics = prediction_slice.physics
            ball_location = vec3(physics.location.x, physics.location.y, physics.location.z)
            # ball_location = vec3(0, ball_y, ball_z)
            dodge.direction = vec2(vec3(0, 5120, 321) - ball_location)
            dodge.duration = duration_estimate + i / 60
            if dodge.duration > 1.4:
                break

            target = vec3(0, 5120, jeroens_magic_number * ball_location[2])
            dodge.preorientation = look_at(target - ball_location, vec3(0, 0, 1))
            # Loop from now till the end of the duration
            fps = 30
            for j in range(round(fps * dodge.duration)):
                lol = lol + 1
                # Get the ball prediction slice at this time and convert the location to RLU vec3
                prediction_slice = ball_prediction.slices[round(60 * j / fps)]
                physics = prediction_slice.physics
                ball_location = vec3(physics.location.x, physics.location.y, physics.location.z)
                dodge.step(1 / fps)

                T = dodge.duration - dodge.timer
                if T > 0:
                    if dodge.timer < 0.2:
                        dodge.controls.boost = 1
                        dodge.controls.pitch = 1
                    else:
                        xf = car.location + 0.5 * T * T * vec3(0, 0, -650) + T * car.velocity

                        delta_x = ball_location - xf
                        if angle_between(vec2(car.forward()), dodge.direction) < 0.3:
                            if norm(delta_x) > 50:
                                dodge.controls.boost = 1
                                dodge.controls.throttle = 0.0
                            else:
                                dodge.controls.boost = 0
                                dodge.controls.throttle = clip(0.5 * (200 / 3) * T * T, 0.0, 1.0)
                        else:
                            dodge.controls.boost = 0
                            dodge.controls.throttle = 0.0
                else:
                    dodge.controls.boost = 0

                car.step(dodge.controls, 1 / fps)
                succesfull = self.dodge_succesfull(car, ball_location, dodge)
                if succesfull is not None:
                    if succesfull:
                        return True, j / fps, ball_location
                    else:
                        break
        return False, None, None

    def dodge_succesfull(self, car, ball_location, dodge):
        batmobile = obb()
        batmobile.half_width = vec3(64.4098892211914, 42.335182189941406, 14.697200775146484)
        batmobile.center = car.location + dot(car.rotation, vec3(9.01, 0, 12.09))
        batmobile.rotation = car.rotation
        ball = sphere(ball_location, 93.15)
        b_local = dot(ball.center - batmobile.center, batmobile.rotation)

        closest_local = vec3(
            min(max(b_local[0], -batmobile.half_width[0]), batmobile.half_width[0]),
            min(max(b_local[1], -batmobile.half_width[1]), batmobile.half_width[1]),
            min(max(b_local[2], -batmobile.half_width[2]), batmobile.half_width[2])
        )

        hit_location = dot(batmobile.rotation, closest_local) + batmobile.center
        if norm(hit_location - ball.center) > ball.radius:
            return None
        # if abs(ball_location[2] - hit_location[2]) < 25 and hit_location[2] < ball_location[2]:
        if abs(ball_location[2] - hit_location[2]) < 25:
            if closest_local[0] > 35 and -12 < closest_local[2] < 12:
                hit_check = True
            else:
                print("local: ", closest_local)
                hit_check = True
        else:
            hit_check = False
        # Seems to work without angle_check. No clue why though
        angle_car_simulation = angle_between(car.rotation, self.game.my_car.rotation)
        angle_simulation_target = angle_between(car.rotation, dodge.preorientation)
        angle_check = angle_simulation_target < angle_car_simulation or angle_simulation_target < 0.1
        return hit_check

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
            rotation=Rotator(0, math.pi / 2, 0),
            angular_velocity=Vector3(0, 0, 0),
        ), boost_amount=50)

        # put the ball in the middle of the field

        ball_state = BallState(physics=Physics(
            location=Vector3(0, 2500, 93),
            velocity=Vector3(0, -250, 500),
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
            location=Vector3(0, ball_y, ball_z),
            velocity=Vector3(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0),
        ))

        self.set_game_state(GameState(
            ball=ball_state,
            cars={self.game.id: car_state})
        )

    def set_state_stationary_angled(self):
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
