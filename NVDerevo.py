import math
import time
from Chip import *
from Simulation import Car
from Util import *
from States import *
from GameInfo import GameInfo
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

class NVDeevo(BaseAgent):
    def initialize_agent(self):
        self.action = None
        self.controls = Input()
        self.info = GameInfo(self.index, self.team)
        self.state = calcShot()
        self.controller = None
        self.kickoff = False
        self.startGrabbingBoost = time.time()
        self.time = time.time()

    def checkState(self):
        if self.kickoff:
            self.state = kickOff()
        if self.state.expired:
            if recovery().available(self):
                self.state = recovery()
            elif calcShot().available(self):
                self.state = calcShot()
            elif boostManager().available(self):
                self.startGrabbingBoost = time.time()
                self.state = boostManager()
            else:
                self.state = defending()

    def get_output(self, game: GameTickPacket) -> SimpleControllerState:
        self.preprocess(game)
        #self.checkState()
        return self.controls

    def preprocess(self, game):
        self.info.read_packet(game)
        self.boosts = game.game_boosts
        self.kickoff = game.game_info.is_kickoff_pause
        if self.action is None:
            self.action = AirDodge(self.info.my_car, target=self.info.ball.pos)
        if self.action.finished:
            self.action = None
        self.action.step(0.016666)
        # if time.time() - self.time > 3:
        #     self.time = time.time()
        #     setState(self)
