

from RLUtilities.GameInfo import GameInfo, Ball
from RLUtilities.LinearAlgebra import vec3
from RLUtilities.Maneuvers import Drive
from keyboardInput import keyboard
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

from boost import boost_grabbing_available
from controls import controls
from kickOff import initKickOff, kickOff
from util import in_front_of_ball, render_string, eta_calculator, get_closest_pad, distance_2d
from stateSetting import defending

class Derevo(BaseAgent):

    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.name = name
        self.team = team
        self.index = index
        self.info = GameInfo(self.index, self.team)
        self.controls = None
        self.kickoff = False
        self.firstKickOff = True
        self.kickoffStart = None
        self.drive = None
        self.dodge = None
        self.dribble = None
        self.bounces = []
        self.boostGrabs = False
        self.step = 0
        self.time = 0
        self.eta = None
        self.inFrontOfBall = False
        self.defending = False
        self.p_s = 0.
        self.yaw = 0

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.yaw = packet.game_cars[self.index].physics.rotation.yaw
        self.info.read_packet(packet)
        prev_kickoff = self.kickoff
        predict(self)
        self.kickoff = packet.game_info.is_kickoff_pause
        self.time = packet.game_info.seconds_elapsed
        self.inFrontOfBall = in_front_of_ball(self)
        if self.firstKickOff:
            if self.drive is None:
                self.drive = Drive(self.info.my_car, self.info.ball.pos, 1399)
            self.drive.step(1 / 60)
            self.controls = self.drive.controls
        if self.kickoff and not prev_kickoff and not self.firstKickOff:
            initKickOff(self)
        if self.firstKickOff and self.get_field_info() is not None:
            initKickOff(self)
            self.firstKickOff = False
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
        # if keyboard.get_output():
        #     defending(self)
        return self.controls


def predict(agent):
    agent.bounces = []
    agent.boostGrabs = False
    agent.defending = False
    eta_to_boostpad = round(eta_calculator(agent.info.my_car, get_closest_pad(agent).pos))
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
        if location[2] < 100:
            agent.bounces.append((location, i))
        if i == eta_to_boostpad:
            agent.boostGrabs = boost_grabbing_available(agent, ball)
        if agent.info.my_goal.inside(location) or distance_2d(location, agent.info.my_goal.center) < 3000:
            agent.defending = True
