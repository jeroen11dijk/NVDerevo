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
        self.info = GameInfo(self.index, self.team, self.get_field_info())
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
        if self.action != None:
            self.renderer.begin_rendering()
            self.renderer.draw_line_3d(self.info.my_car.pos, self.action.target, self.renderer.red())
            self.renderer.end_rendering()
        # if time.time() - self.time > 3:
        #     self.time = time.time()
        #     setState(self)
