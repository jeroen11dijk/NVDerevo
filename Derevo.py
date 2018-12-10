from RLUtilities.GameInfo import GameInfo, Ball
from RLUtilities.LinearAlgebra import vec3
from RLUtilities.Maneuvers import Drive
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

from boost import boostGrabbingAvaiable
from controls import controls
from kickOff import initKickOff, kickOff
from shooting import shootingAvailable
from util import distance2D, renderString, ETACalculator, getClosestPad


class Derevo(BaseAgent):

    def __init__(self, name, team, index):
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
        self.target = vec3(0, 0, 0)
        self.bounces = []
        self.shots = []
        self.boostGrabs = False
        self.step = 0
        self.time = 0
        self.eta = None
        self.inFrontOfBall = False

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.info.read_packet(packet)
        prevKickoff = self.kickoff
        predict(self)
        self.kickoff = packet.game_info.is_kickoff_pause
        self.time = packet.game_info.seconds_elapsed
        self.inFrontOfBall = distance2D(self.info.ball.pos, self.info.my_goal.center) < distance2D(self.info.my_car.pos,
                                                                                                   self.info.my_goal.center)
        if self.firstKickOff:
            if self.drive is None:
                self.drive = Drive(self.info.my_car, self.info.ball.pos, 1399)
            self.drive.step(1 / 60)
            self.controls = self.drive.controls
        if self.kickoff and not prevKickoff and not self.firstKickOff:
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
        renderString(self, str(self.step))
        return self.controls


def predict(agent):
    agent.bounces = []
    agent.shots = []
    agent.boostGrabs = False
    eta_to_boostpad = round(ETACalculator(agent.info.my_car, getClosestPad(agent).pos))
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
        if shootingAvailable(ball, agent.info.my_car, agent.info.their_goal):
            agent.shots.append((location, i))
        if location[2] < 100:
            agent.bounces.append((location, i))
        if i == eta_to_boostpad:
            agent.boostGrabs = boostGrabbingAvaiable(agent, ball)