import math
import time
from RLUtilities.Maneuvers import *
from RLUtilities.Simulation import Car
from Util import *
from States import *
from RLUtilities.GameInfo import GameInfo
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

class NVDeevo(BaseAgent):
    def initialize_agent(self):
        #self.info = GameInfo(self.index, self.team, self.get_field_info())
        self.info = GameInfo(self.index, self.team)
        self.action = None
        self.state = calcShot()
        self.controller = None
        self.kickoff = False
        self.startGrabbingBoost = time.time()
        self.time = time.time()

    def checkState(self):
        if self.kickoff:
            self.state = kickOff(self)
        if self.state.expired:
            if calcShot().available(self):
                self.state = calcShot()
            elif boostManager().available(self):
                self.startGrabbingBoost = time.time()
                self.state = boostManager()
            else:
                self.state = defending()

    def get_output(self, game: GameTickPacket) -> SimpleControllerState:
        self.preprocess(game)
        self.checkState()
        if self.action == None:
            print("MAAIEN")
        renderString(self, str(self.state))
        return self.state.execute(self)

    def preprocess(self, game):
        self.info.read_packet(game)
        self.boosts = game.game_boosts
        self.kickoff = game.game_info.is_kickoff_pause
        # if time.time() - self.time > 3:
        #     self.time = time.time()
        #     setState(self)
