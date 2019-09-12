"""Main module"""
import math

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

from boost import init_boostpads, update_boostpads
from goal import Goal
from catching import Catching
from defending import defending
from dribble import Dribbling
from kick_off import init_kickoff, kick_off
from rlutilities.linear_algebra import norm, normalize, vec2, vec3, dot
from rlutilities.mechanics import Drive, Dodge
from rlutilities.simulation import Game, Ball
from shooting import shooting
from util import distance_2d, get_bounce, line_backline_intersect, sign


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
        self.in_front_off_the_ball = False
        self.kickoff_Start = None
        self.step = "Catching"
        self.time = 0
        self.fps = 1 / 60
        self.my_goal = None
        self.their_goal = None

    def initialize_agent(self):
        """Initializing all parameters whch require the field info"""
        self.my_goal = Goal(self.team, self.get_field_info())
        self.their_goal = Goal(1 - self.team, self.get_field_info())
        init_boostpads(self)

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        """The main method which receives the packets and outputs the controls"""
        if packet.game_info.seconds_elapsed - self.time > 0:
            self.fps = packet.game_info.seconds_elapsed - self.time
        self.time = packet.game_info.seconds_elapsed
        self.info.read_game_information(packet, self.get_rigid_body_tick(), self.get_field_info())
        update_boostpads(self, packet)
        self.predict()
        self.set_mechanics()
        prev_kickoff = self.kickoff
        self.kickoff = packet.game_info.is_kickoff_pause
        self.defending = self.should_defending()
        if self.kickoff and not prev_kickoff:
            init_kickoff(self)
        if self.kickoff or self.step == "Dodge2":
            kick_off(self)
        else:
            self.get_controls()
        self.render_string(str(self.step))
        if not packet.game_info.is_round_active:
            self.controls.steer = 0
        return self.controls

    def predict(self):
        """Method which uses ball prediction to fill in future data"""
        self.bounces = []
        prediction = Ball(self.info.ball)
        for i in range(360):
            prev_ang_velocity = normalize(prediction.angular_velocity)
            prediction.step(0.016666)
            current_ang_velocity = normalize(prediction.angular_velocity)
            if prev_ang_velocity != current_ang_velocity and prediction.location[2] < 125:
                self.bounces.append((vec3(prediction.location), i * 1 / 60))

    def set_mechanics(self):
        """Setting all the mechanics to not none"""
        if self.drive is None:
            self.drive = Drive(self.info.my_car)
        if self.catching is None:
            self.catching = Catching(self.info.my_car, self.info.ball.location, 1399)
        if self.dodge is None:
            self.dodge = Dodge(self.info.my_car)
        if self.dribble is None:
            self.dribble = Dribbling(self.info.my_car, self.info.ball, self.their_goal)

    def get_controls(self):
        """Decides what strategy to uses and gives corresponding output"""
        if self.step == "Steer" or self.step == "Dodge2":
            self.step = "Catching"
        if self.step == "Catching":
            target = get_bounce(self)
            if target is None:
                self.step = "Defending"
            else:
                self.catching.target_location = target[0]
                self.catching.target_speed = (distance_2d(self.info.my_car.location, target[0]) + 50) / target[1]
                self.catching.step()
                self.controls = self.catching.controls
                ball = self.info.ball
                car = self.info.my_car
                if distance_2d(ball.location, car.location) < 150 and 65 < abs(
                        ball.location[2] - car.location[2]) < 127:
                    self.step = "Dribbling"
                    self.dribble = Dribbling(self.info.my_car, self.info.ball, self.their_goal)
                if self.defending:
                    self.step = "Defending"
                ball = self.info.ball
                if abs(ball.velocity[2]) < 100 and sign(self.team) * ball.velocity[1] < 0 and sign(self.team) * \
                        ball.location[1] < 0:
                    self.step = "Shooting"
        elif self.step == "Dribbling":
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
                self.step = "Catching"
            if self.defending:
                self.step = "Defending"
            if opponent_is_near and opponent_is_in_the_way:
                self.step = "Dodge"
                self.dodge = Dodge(self.info.my_car)
                self.dodge.duration = 0.25
                self.dodge.target = self.their_goal.center
        elif self.step == "Defending":
            defending(self)
        elif self.step == "Dodge":
            self.dodge.step(self.fps)
            self.controls = self.dodge.controls
            self.controls.boost = 0
            if self.dodge.finished and self.info.my_car.on_ground:
                self.step = "Catching"
        elif self.step == "Shooting":
            shooting(self)

    def render_string(self, string):
        """Rendering method mainly used to show the current state"""
        self.renderer.begin_rendering('The State')
        if self.step == "Dodge1":
            self.renderer.draw_line_3d(self.info.my_car.location, self.dodge.target, self.renderer.black())
        self.renderer.draw_line_3d(self.info.my_car.location, self.bounces[0][0], self.renderer.blue())
        self.renderer.draw_string_2d(20, 20, 3, 3, string + " " + str(abs(self.info.ball.velocity[2])) + " " + str(
            sign(self.team) * self.info.ball.velocity[1]), self.renderer.red())
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
