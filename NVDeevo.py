import math
import time
from Util import *
from States import *

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

class NVDeevo(BaseAgent):

    def initialize_agent(self):
        self.deevo = obj()
        self.ball = obj()
        self.start = time.time()
        self.state = calcShot()
        self.fieldInfo = self.get_field_info()
        self.bigBoostPads = getBigBoostPads(self)
        self.attackingGoal = getAttackingGoal(self)
        self.ourGoal = getOurGoal(self)
        self.theirGoal = getTheirGoal(self)
        self.controller = calcController
        self.kickoff = True
        self.boosts = []

    def checkState(self):
        if self.state.expired:
            if calcShot().available(self) == True or self.kickoff:
                self.state = calcShot()
            elif boostManager().available(self) == True:
                self.state = boostManager()
            else:
                self.state = defending()
        self.renderer.begin_rendering()
        self.renderer.draw_string_2d(20, 20, 3, 3, str(self.state), self.renderer.black())
        self.renderer.end_rendering()


    def get_output(self, game: GameTickPacket) -> SimpleControllerState:
        self.preprocess(game)
        self.checkState()
        return self.state.execute(self)

    def preprocess(self, game):
        self.deevo.location.data = [game.game_cars[self.index].physics.location.x,game.game_cars[self.index].physics.location.y,game.game_cars[self.index].physics.location.z]
        self.deevo.velocity.data = [game.game_cars[self.index].physics.velocity.x,game.game_cars[self.index].physics.velocity.y,game.game_cars[self.index].physics.velocity.z]
        self.deevo.rotation.data = [game.game_cars[self.index].physics.rotation.pitch,game.game_cars[self.index].physics.rotation.yaw,game.game_cars[self.index].physics.rotation.roll]
        self.deevo.rotationVelocity.data = [game.game_cars[self.index].physics.angular_velocity.x,game.game_cars[self.index].physics.angular_velocity.y,game.game_cars[self.index].physics.angular_velocity.z]
        self.deevo.matrix = rotator_to_matrix(self.deevo)
        self.deevo.boost = game.game_cars[self.index].boost

        self.ball.location.data = [game.game_ball.physics.location.x,game.game_ball.physics.location.y,game.game_ball.physics.location.z]
        self.ball.velocity.data = [game.game_ball.physics.velocity.x,game.game_ball.physics.velocity.y,game.game_ball.physics.velocity.z]
        self.ball.rotation.data = [game.game_ball.physics.rotation.pitch,game.game_ball.physics.rotation.yaw,game.game_ball.physics.rotation.roll]
        self.ball.rotationVelocity.data = [game.game_ball.physics.angular_velocity.x,game.game_ball.physics.angular_velocity.y,game.game_ball.physics.angular_velocity.z]
        self.ball.localLocation = to_local(self.ball,self.deevo)

        self.kickoff = game.game_info.is_kickoff_pause
        self.boosts = game.game_boosts
