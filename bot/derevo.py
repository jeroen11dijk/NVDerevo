"""Main module"""
import math
from queue import Empty

from rlbot.agents.base_agent import BaseAgent
from rlbot.agents.base_agent import SimpleControllerState
from rlbot.matchcomms.common_uses.reply import reply_to
from rlbot.matchcomms.common_uses.set_attributes_message import handle_set_attributes_message
from rlbot.utils.structures.game_data_struct import GameTickPacket

from boost import init_boostpads, update_boostpads
from custom_drive import CustomDrive as Drive
from defending import defending
from goal import Goal
from halfflip import HalfFlip
from kick_off import init_kickoff, kick_off
from rlutilities.linear_algebra import normalize, vec3
from rlutilities.mechanics import Dodge
from rlutilities.simulation import Game
from steps import Step
from util import distance_2d, sign, velocity_2d, get_closest_big_pad


class Hypebot(BaseAgent):
    """Main bot class"""

    def __init__(self, name, team, index):
        """Initializing all parameters of the bot"""
        super().__init__(name, team, index)
        Game.set_mode("soccar")
        self.info = Game(index, team)
        self.team = team
        self.index = index
        self.drive = None
        self.dodge = None
        self.halfflip = None
        self.controls = SimpleControllerState()
        self.kickoff = False
        self.prev_kickoff = False
        self.in_front_off_ball = False
        self.conceding = False
        self.kickoff_Start = None
        self.step = Step.Shooting
        self.time = 0
        self.my_goal = None
        self.their_goal = None
        self.teammates = []
        self.has_to_go = False
        self.closest_to_ball = False

    def initialize_agent(self):
        """Initializing all parameters which require the field info"""
        self.my_goal = Goal(self.team, self.get_field_info())
        self.their_goal = Goal(1 - self.team, self.get_field_info())
        init_boostpads(self)
        """Setting all the mechanics to not none"""
        self.drive = Drive(self.info.my_car)
        self.dodge = Dodge(self.info.my_car)
        self.halfflip = HalfFlip(self.info.my_car)

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        """The main method which receives the packets and outputs the controls"""
        self.info.read_game_information(packet, self.get_rigid_body_tick(), self.get_field_info())
        self.in_front_off_ball = distance_2d(self.info.ball.location, self.my_goal.center) < distance_2d(
            self.info.my_car.location, self.my_goal.center)
        update_boostpads(self, packet)
        self.closest_to_ball = self.closest_to_the_ball()
        self.predict()
        self.teammates = []
        for i in range(self.info.num_cars):
            if self.info.cars[i].team == self.team and i != self.index:
                self.teammates.append(i)
        self.time = packet.game_info.seconds_elapsed
        # self.handle_match_comms()
        self.prev_kickoff = self.kickoff
        self.kickoff = packet.game_info.is_kickoff_pause and distance_2d(self.info.ball.location, vec3(0, 0, 0)) < 100
        if self.kickoff and not self.prev_kickoff:
            # if not self.close_to_kickoff_spawn():
            #     return
            if len(self.teammates) > 0:
                if self.closest_to_ball:
                    init_kickoff(self)
                    self.has_to_go = True
                else:
                    self.drive.target = get_closest_big_pad(self).location
                    self.drive.speed = 1399
            else:
                init_kickoff(self)
                self.has_to_go = True
        if (self.kickoff or self.step == "Dodge2") and self.has_to_go:
            kick_off(self)
        elif self.kickoff and not self.has_to_go:
            self.drive.step(self.info.time_delta)
            self.controls = self.drive.controls
        else:
            if self.has_to_go:
                self.has_to_go = False
            self.get_controls()
        self.render_string(self.step.name)
        # Make sure there is no variance in kickoff setups
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
                if physics.location.y * sign(self.team) > 5120:
                    self.conceding = True
                if physics.location.z > 180:
                    self.ball_bouncing = True
                    continue
                current_ang_velocity = normalize(
                    vec3(physics.angular_velocity.x, physics.angular_velocity.y, physics.angular_velocity.z))
                if physics.location.z < 125 and prev_ang_velocity != current_ang_velocity:
                    self.bounces.append((vec3(physics.location.x, physics.location.y, physics.location.z),
                                         prediction_slice.game_seconds - self.time))
                    if len(self.bounces) > 15:
                        return
                prev_ang_velocity = current_ang_velocity

    def closest_to_the_ball(self):
        dist_to_ball = math.inf
        for i in range(len(self.teammates)):
            if distance_2d(self.info.cars[self.teammates[i]].location, self.info.ball.location) < dist_to_ball:
                dist_to_ball = distance_2d(self.info.cars[self.teammates[i]].location, self.info.ball.location)
        return distance_2d(self.info.my_car.location, self.info.ball.location) <= dist_to_ball

    def get_controls(self):
        """Decides what strategy to uses and gives corresponding output"""
        self.drive.power_turn = False
        if self.step == Step.Steer or self.step == Step.Dodge_2 or self.step == Step.Dodge_1 or self.step == Step.Drive:
            self.step = Step.Shooting
        if self.step == Step.Shooting:
            self.drive.target = self.info.ball.location
            self.drive.speed = 1410
            self.drive.step(self.info.time_delta)
            self.controls = self.drive.controls
            if not self.closest_to_ball or self.in_front_off_ball:
                self.step = Step.Rotating
        elif self.step == Step.Rotating:
            self.drive.target = 0.5 * (self.info.ball.location - self.my_goal.center) + self.my_goal.center
            self.drive.speed = 1410
            self.drive.step(self.info.time_delta)
            self.controls = self.drive.controls
            teammate = self.info.cars[self.teammates[0]].location
            teammate_out_location = distance_2d(self.info.ball.location, self.my_goal.center) < distance_2d(teammate,
                                                                                                            self.my_goal.center)
            in_position = 3 * distance_2d(self.info.ball.location, self.my_goal.center) > 4 * distance_2d(
                self.info.my_car.location, self.my_goal.center)
            print(self.index)
            print(3 * distance_2d(self.info.ball.location, self.my_goal.center),
                  4 * distance_2d(self.info.my_car.location, self.my_goal.center))
            faster = self.closest_to_ball and in_position
            if teammate_out_location or faster:
                self.step = Step.Shooting
        elif self.step == Step.Defending:
            defending(self)
        elif self.step == Step.Dodge or self.step == Step.HalfFlip:
            halfflipping = self.step == Step.HalfFlip
            if halfflipping:
                self.halfflip.step(self.info.time_delta)
            else:
                self.dodge.step(self.info.time_delta)
            if (self.halfflip.finished if halfflipping else self.dodge.finished) and self.info.my_car.on_ground:
                self.step = Step.Catching
            else:
                self.controls = (self.halfflip.controls if halfflipping else self.dodge.controls)
                if not halfflipping:
                    self.controls.boost = False
                self.controls.throttle = velocity_2d(self.info.my_car.velocity) < 500

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
        if self.step == Step.Dodge_1:
            self.renderer.draw_line_3d(self.info.my_car.location, self.dodge.target, self.renderer.black())
        self.renderer.draw_line_3d(self.info.my_car.location, self.drive.target, self.renderer.blue())
        if self.index == 0:
            self.renderer.draw_string_2d(20, 20, 3, 3, string, self.renderer.red())
        else:
            self.renderer.draw_string_2d(20, 520, 3, 3, string, self.renderer.red())
        self.renderer.end_rendering()

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
