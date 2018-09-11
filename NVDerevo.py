import math
import time
from Util import *
from States import *

from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

class NVDeevo(BaseAgent):
    def initialize_agent(self):
        self.deevo = obj()
        self.ball = obj()
        self.state = calcShot()
        self.fieldInfo = self.get_field_info()
        self.bigBoostPads = getBigBoostPads(self)
        self.theirGoalPosts = getTheirGoalPosts(self)
        self.ourGoal = getOurGoal(self)
        self.theirGoal = getTheirGoal(self)
        self.controller = calcController
        self.closestEnemyDistance = math.inf
        self.kickoff = False
        self.time = time.time()
        self.startDodgeTime = time.time()
        self.startHalfFlipTime = time.time()
        self.startGrabbingBoost = time.time()
        self.dodging = False
        self.halfFlipping = False
        self.onGround = True
        self.boosts = []
        self.time = time.time()

    def checkState(self):
        if self.kickoff:
            self.state = kickOff()
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
        # ball_prediction = self.get_ball_prediction()
        # if ball_prediction is not None:
        #     for i in range(0, ball_prediction.SlicesLength()):
        #         prediction_slice = ball_prediction.Slices(i)
        #         location = prediction_slice.Physics().Location()
        #         if(location.Z() < 100):
        #             self.logger.info("At time {}, the ball will be at ({}, {}, {})".format(prediction_slice.GameSeconds(), location.X(), location.Y(), location.Z()))
        return self.state.execute(self)

    def preprocess(self, game):
        deevo = game.game_cars[self.index].physics
        self.deevo.location.data = [deevo.location.x, deevo.location.y, deevo.location.z]
        self.deevo.velocity.data = [deevo.velocity.x, deevo.velocity.y, deevo.velocity.z]
        self.deevo.rotation.data = [deevo.rotation.pitch, deevo.rotation.yaw, deevo.rotation.roll]
        self.deevo.rotationVelocity.data = [deevo.angular_velocity.x, deevo.angular_velocity.y, deevo.angular_velocity.z]
        self.deevo.matrix = rotator_to_matrix(self.deevo)
        self.deevo.boost = game.game_cars[self.index].boost
        ball = game.game_ball.physics
        self.ball.location.data = [ball.location.x, ball.location.y, ball.location.z]
        self.ball.velocity.data = [ball.velocity.x, ball.velocity.y, ball.velocity.z]
        self.ball.rotation.data = [ball.rotation.pitch, ball.rotation.yaw, ball.rotation.roll]
        self.ball.rotationVelocity.data = [ball.angular_velocity.x, ball.angular_velocity.y, ball.angular_velocity.z]
        self.ball.localLocation = to_local(self.ball,self.deevo)
        if time.time() - self.time > 3:
            self.time = time.time()
            setState(self)
        self.kickoff = game.game_info.is_kickoff_pause
        self.boosts = game.game_boosts
        self.onGround = game.game_cars[self.index].has_wheel_contact and self.deevo.location.data[2] < 18
        distance = math.inf
        for i in range(len(game.game_cars)):
            enemy = game.game_cars[i]
            if enemy.team == self.team:
                enemyLocation = [enemy.physics.location.x,enemy.physics.location.y,enemy.physics.location.z]
                if distance2D(enemyLocation, self.ball) < distance:
                    self.closestEnemyDistance = distance
