"""Main module"""
import math
from queue import Empty
from rlbot.agents.base_agent import BaseAgent
from rlbot.agents.base_agent import SimpleControllerState
from rlbot.matchcomms.common_uses.reply import reply_to
from rlbot.matchcomms.common_uses.set_attributes_message import handle_set_attributes_message
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlutilities.linear_algebra import norm, normalize, vec2, vec3, dot
from rlutilities.mechanics import Drive, Dodge
from rlutilities.simulation import Game

from boost import init_boostpads, update_boostpads
from defending import defending
from dribble import Dribbling
from goal import Goal
from kick_off import init_kickoff, kick_off
from shooting import shooting
from util import distance_2d, get_bounce, line_backline_intersect, sign
from steps import Step


class Hypebot(BaseAgent):
    """Main bot class"""

    def __init__(self, name, team, index):
        """Initializing all parameters of the bot"""
        super().__init__(name, team, index)
        Game.set_mode("soccar")
        self.info = Game(index, team)
        self.name = name
        self.team = team
        self.index = index
        self.defending = False
        self.bounces = []
        self.drive = None
        self.catching = None
        self.dodge = None
        self.dribble = None
        self.controls = SimpleControllerState()
        self.kickoff = False
        self.prev_kickoff = False
        self.in_front_off_the_ball = False
        self.kickoff_Start = None
        self.step = Step.Catching
        self.time = 0
        self.fps = 1 / 60
        self.my_goal = None
        self.their_goal = None
        self.ball_bouncing = False

    def initialize_agent(self):
        """Initializing all parameters whch require the field info"""
        self.my_goal = Goal(self.team, self.get_field_info())
        self.their_goal = Goal(1 - self.team, self.get_field_info())
        init_boostpads(self)

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        """The main method which receives the packets and outputs the controls"""
        if packet.game_info.seconds_elapsed - self.time > 0:
            self.fps = packet.game_info.seconds_elapsed - self.time
        print(self.info.time_delta)
        self.time = packet.game_info.seconds_elapsed
        self.info.read_game_information(packet, self.get_rigid_body_tick(), self.get_field_info())
        update_boostpads(self, packet)
        self.predict()
        self.set_mechanics()
        # self.handle_match_comms()
        self.prev_kickoff = self.kickoff
        self.kickoff = packet.game_info.is_kickoff_pause
        self.defending = self.should_defending()
        if self.kickoff and not self.prev_kickoff:
            # if not self.close_to_kickoff_spawn():
            #     return
            init_kickoff(self)
            self.prev_kickoff = True
        elif self.kickoff or self.step is Step.Dodge_2:
            kick_off(self)
        else:
            self.get_controls()
        self.render_string(self.step.name)
        if not packet.game_info.is_round_active:
            self.controls.steer = 0
        return self.controls

    def predict(self):
        """Method which uses ball prediction to fill in future data"""
        self.bounces = []
        self.ball_bouncing = False
        ball_prediction = self.get_ball_prediction_struct()
        if ball_prediction is not None:
            prev_ang_velocity = normalize(self.info.ball.angular_velocity)
            for i in range(ball_prediction.num_slices):
                prediction_slice = ball_prediction.slices[i]
                physics = prediction_slice.physics
                if physics.location.z > 150:
                    self.ball_bouncing = True
                    continue
                current_ang_velocity = normalize(vec3(physics.angular_velocity.x, physics.angular_velocity.y, physics.angular_velocity.z))
                if physics.location.z < 125 and prev_ang_velocity != current_ang_velocity:
                    self.bounces.append((vec3(physics.location.x, physics.location.y, physics.location.z), prediction_slice.game_seconds - self.time))
                    if len(self.bounces) > 15: return
                prev_ang_velocity = current_ang_velocity

    def set_mechanics(self):
        """Setting all the mechanics to not none"""
        if self.drive is None:
            self.drive = Drive(self.info.my_car)
        if self.catching is None:
            self.catching = Drive(self.info.my_car)
        if self.dodge is None:
            self.dodge = Dodge(self.info.my_car)
        if self.dribble is None:
            self.dribble = Dribbling(self.info.my_car, self.info.ball, self.their_goal)

    def get_controls(self):
        """Decides what strategy to uses and gives corresponding output"""
        if self.step is Step.Steer or self.step is Step.Dodge_2 or self.step is Step.Dodge_1:
            self.step = Step.Catching
        if self.step is Step.Catching and not self.ball_bouncing:
            self.step = Step.Shooting if (self.info.ball.location[1] - self.info.my_car.location[1]) * sign(self.info.my_car.team) < 0 else Step.Defending
        if self.step is Step.Catching:
            target = get_bounce(self)
            if target is None:
                self.step = Step.Defending
            else:
                self.catching.target = target[0]
                self.catching.speed = (distance_2d(self.info.my_car.location, target[0]) + 50) / target[1]
                self.catching.step(self.info.time_delta)
                self.controls = self.catching.controls
                ball = self.info.ball
                car = self.info.my_car
                if distance_2d(ball.location, car.location) < 150 and 65 < abs(
                        ball.location[2] - car.location[2]) < 127:
                    self.step = Step.Dribbling
                    self.dribble = Dribbling(self.info.my_car, self.info.ball, self.their_goal)
                if self.defending:
                    self.step = Step.Defending
                ball = self.info.ball
                if abs(ball.velocity[2]) < 100 and sign(self.team) * ball.velocity[1] < 0 and sign(self.team) * \
                        ball.location[1] < 0:
                    self.step = Step.Shooting
        elif self.step is Step.Dribbling:
            self.dribble.step()
            self.controls = self.dribble.controls
            ball = self.info.ball
            car = self.info.my_car
            bot_to_opponent = self.info.cars[1 - self.index].location - self.info.my_car.location
            local_bot_to_target = dot(bot_to_opponent, self.info.my_car.rotation)
            angle_front_to_target = math.atan2(local_bot_to_target[1], local_bot_to_target[0])
            opponent_is_near = norm(vec2(bot_to_opponent)) < 2000
            opponent_is_in_the_way = math.radians(-10) < angle_front_to_target < math.radians(10)
            if not (distance_2d(ball.location, car.location) < 150 and 65 < abs(
                    ball.location[2] - car.location[2]) < 127):
                self.step = Step.Catching
            if self.defending:
                self.step = Step.Defending
            if opponent_is_near and opponent_is_in_the_way:
                self.step = Step.Dodge
                self.dodge = Dodge(self.info.my_car)
                self.dodge.duration = 0.25
                self.dodge.target = self.their_goal.center
        elif self.step is Step.Defending:
            defending(self)
        elif self.step is Step.Dodge:
            self.dodge.step(self.fps)
            self.controls = self.dodge.controls
            self.controls.boost = 0
            if self.dodge.finished and self.info.my_car.on_ground:
                self.step = Step.Catching
        elif self.step is Step.Shooting:
            shooting(self)

    def handle_match_comms(self):
        try:
            msg = self.matchcomms.incoming_broadcast.get_nowait()
        except Empty:
            return
        if handle_set_attributes_message(msg, self, allowed_keys=['kickoff', 'prev_kickoff']):
            reply_to(self.matchcomms, msg)
        else:
            self.logger.debug('Unhandled message: {msg}')

    def render_string(self, string):
        """Rendering method mainly used to show the current state"""
        self.renderer.begin_rendering('The State')
        if self.step is Step.Dodge_1:
            self.renderer.draw_line_3d(self.info.my_car.location, self.dodge.target, self.renderer.black())
        self.renderer.draw_line_3d(self.info.my_car.location, self.drive.target, self.renderer.blue())
        if self.kickoff_Start is None:
            self.renderer.draw_string_2d(20, 20, 3, 3, string, self.renderer.red())
        else:
            self.renderer.draw_string_2d(20, 20, 3, 3, string + " " + self.kickoff_Start, self.renderer.red())
        self.renderer.end_rendering()

    def should_defending(self):
        """Method which returns a boolean regarding whether we should defend or not"""
        ball = self.info.ball
        car = self.info.my_car
        our_goal = self.my_goal.center
        car_to_ball = ball.location - car.location
        in_front_of_ball = distance_2d(ball.location, our_goal) < distance_2d(car.location, our_goal)
        backline_intersect = line_backline_intersect(self.my_goal.center[1], vec2(car.location), vec2(car_to_ball))
        return in_front_of_ball and abs(backline_intersect) < 2000

    def close_to_kickoff_spawn(self):
        blue_one = distance_2d(self.info.my_car.location, vec3(-2048, -2560, 18)) < 10
        blue_two = distance_2d(self.info.my_car.location, vec3(2048, -2560, 18)) < 10
        blue_three = distance_2d(self.info.my_car.location, vec3(-256, -3840, 18)) < 10
        blue_four = distance_2d(self.info.my_car.location, vec3(256, -3840, 18)) < 10
        blue_five = distance_2d(self.info.my_car.location, vec3(0, -4608, 18)) < 10
        blue = blue_one or blue_two or blue_three or blue_four or blue_five
        orange_one = distance_2d(self.info.my_car.location, vec3(-2048, 2560, 18)) < 10
        orange_two = distance_2d(self.info.my_car.location, vec3(2048, 2560, 18)) < 10
        orange_three = distance_2d(self.info.my_car.location, vec3(-256, 3840, 18)) < 10
        orange_four = distance_2d(self.info.my_car.location, vec3(256, 3840, 18)) < 10
        orange_five = distance_2d(self.info.my_car.location, vec3(0, 4608, 18)) < 10
        orange = orange_one or orange_two or orange_three or orange_four or orange_five
        return orange or blue
