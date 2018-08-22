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
        self.kickoff = False
        self.kickOffHasDodged = False
        self.kickOffStart = time.time()
        self.nextDodgeTime = time.time()
        self.dodging = False
        self.onGround = True
        self.boosts = []

    def checkState(self):
        if self.kickoff:
            self.state = kickOff()
        if self.state.expired:
            if calcShot().available(self):
                self.state = calcShot()
            elif boostManager().available(self) == True:
                self.state = boostManager()
            else:
                self.state = defending()

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

        prevKickoff = self.kickoff
        self.kickoff = game.game_info.is_kickoff_pause
        if not prevKickoff and self.kickoff:
            self.kickOffStart = time.time()
            self.kickOffHasDodged = False
        self.boosts = game.game_boosts
        self.onGround = game.game_cars[self.index].has_wheel_contact
