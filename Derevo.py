import math
import random

from RLUtilities.GameInfo import Ball
from RLUtilities.GameInfo import GameInfo
from RLUtilities.LinearAlgebra import dot, vec3, vec2
from RLUtilities.Maneuvers import Drive, AerialTurn, AirDodge
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.game_state_util import Vector3, GameState, BallState, Physics, CarState, Rotator
from rlbot.utils.structures.game_data_struct import GameTickPacket

from area import Area, AreaName
from boost import boost_grabbing_available
from controls import controls
from kickOff import initKickOff, kickOff
from util import in_front_of_ball, render_string, get_closest_pad, distance_2d, sign


class Derevo(BaseAgent):

    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.name = name
        self.team = team
        self.index = index
        self.info = None
        a = sign(team)
        self.my_box = Area(AreaName.BOX, vec2(-1788.0, a * 2300.0), vec2(1788.0, a * 5120.0))
        self.their_box = Area(AreaName.BOX, vec2(-1788.0, sign(team) * 2300.0), vec2(1788.0, a * 5120.0))
        self.back_left = Area(AreaName.CORNER, vec2(-a * 1788.0, a * 2300.0), vec2(-a * 4096.0, a * 5120.0))
        self.back_right = Area(AreaName.CORNER, vec2(a * 1788.0, a * 2300.0), vec2(a * 4096.0, a * 5120.0))
        self.their_left = Area(AreaName.CORNER, vec2(-a * 1788.0, -a * 2300.0), vec2(-a * 4096.0, -a * 5120.0))
        self.their_right = Area(AreaName.CORNER, vec2(a * 1788.0, a * 2300.0), vec2(a * 4096.0, a * 5120.0))
        self.right_wall = Area(AreaName.WALL, vec2(-a * 3072.0, -2300.0), vec2(-a * 4096.0, 2300.0))
        self.left_wall = Area(AreaName.WALL, vec2(a * 3072.0, -2300.0), vec2(a * 4096.0, 2300.0))
        self.our_half = Area(AreaName.HALF, vec2(3072.0, a * 2300.0), vec2(-3072.0, 0.0))
        self.controls = SimpleControllerState()
        self.kickoff = False
        self.kickoffStart = None
        self.drive = None
        self.dodge = None
        self.recovery = None
        self.bounces = []
        self.boostGrabs = False
        self.step = 0
        self.time = 0
        self.FPS = 1 / 60
        self.eta = None
        self.inFrontOfBall = False
        self.defending = False
        self.back_corners = False
        self.p_s = 0.

    def initialize_agent(self):
        while self.get_field_info().num_boosts == 0:
            continue
        self.info = GameInfo(self.index, self.team, self.get_field_info())

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.info.read_packet(packet)
        prev_kickoff = self.kickoff
        predict(self)
        self.kickoff = packet.game_info.is_kickoff_pause
        self.FPS = packet.game_info.seconds_elapsed - self.time
        if self.FPS == 0:
            self.FPS = 1 / 60
        self.time = packet.game_info.seconds_elapsed
        self.inFrontOfBall = in_front_of_ball(self)
        if self.drive is None:
            self.drive = Drive(self.info.my_car, self.info.ball.pos, 1399)
        if self.recovery is None:
            self.recovery = AerialTurn(self.info.my_car)
        if self.dodge is None:
            self.dodge = AirDodge(self.info.my_car, 0.25, self.info.ball.pos)
        if self.kickoff and not prev_kickoff:
            initKickOff(self)
        if self.kickoff or self.step == "Dodge2":
            kickOff(self)
        else:
            if self.drive is None or self.drive.finished:
                self.step = "Ballchasing"
                self.drive = Drive(self.info.my_car, self.info.ball.pos, 1399)
            controls(self)
        if not packet.game_info.is_round_active:
            self.controls.steer = 0
        render_string(self, str(self.step))
        if self.drive.target_speed - dot(self.info.my_car.vel, self.info.my_car.forward()) < 10:
            self.controls.boost = 0
            self.controls.throttle = 1
        # if self.kickoff and not prev_kickoff or self.info.ball.pos[2] < 100:
        #     set_state(self)
        return self.controls


def predict(agent):
    agent.bounces = []
    agent.boostGrabs = False
    agent.defending = False
    agent.back_corners = False
    eta_to_boostpad = round(distance_2d(agent.info.my_car.pos, get_closest_pad(agent).pos) * 60 / 1399)
    ball_prediction = agent.get_ball_prediction_struct()
    for i in range(ball_prediction.num_slices):
        location = vec3(ball_prediction.slices[i].physics.location.x,
                        ball_prediction.slices[i].physics.location.y,
                        ball_prediction.slices[i].physics.location.z)
        velocity = vec3(ball_prediction.slices[i].physics.velocity.x,
                        ball_prediction.slices[i].physics.velocity.y,
                        ball_prediction.slices[i].physics.velocity.z)
        ball = Ball()
        ball.pos = location
        ball.vel = velocity
        if abs(location[0]) < 3840 and abs(location[1]) < 4940 and location[2] < 95:
            agent.bounces.append((location, i))
        if i == eta_to_boostpad:
            agent.boostGrabs = boost_grabbing_available(agent, ball)
        if agent.my_box.is_inside(location):
            agent.defending = True
        if agent.back_left.is_inside(location) and agent.back_right.is_inside(location):
            agent.back_corners = True


def set_state(agent):
    agent.step = "Ballchasing"
    car_pos = Vector3(random.uniform(-3500, 3500), random.uniform(0, -4000), 25)
    enemy_car = CarState(physics=Physics(location=Vector3(0, 5120, 25), velocity=Vector3(0, 0, 0)))
    # enemy_car = CarState(physics=Physics(location=Vector3(10000, 5120, 25), velocity=Vector3(0, 0, 0)))
    ball_pos = Vector3(car_pos.x, car_pos.y + 500, 500)
    ball_state = BallState(Physics(location=ball_pos, velocity=Vector3(0, 100, 500)))
    car_state = CarState(boost_amount=87, physics=Physics(location=car_pos, velocity=Vector3(0, 0, 0),
                                                          rotation=Rotator(0, math.pi / 2, 0)))
    game_state = GameState(ball=ball_state, cars={0: car_state, 1: enemy_car})
    agent.set_game_state(game_state)
