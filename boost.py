from ab0t import BaseAgent
from util import getClosestPad, distance2D, cap
from RLUtilities.LinearAlgebra import dot
import math


def grabBoost(agent: BaseAgent):
    agent.drive.step(1 / 60)
    agent.controls = agent.drive.controls
    agent.drive.target_speed = boostGrabbingSpeed(agent, agent.drive.target_pos)
    if agent.info.my_car.boost > 90 or not getClosestPad(agent).is_active:
        agent.step = "Ballchasing"


def boostGrabbingAvaiable(agent: BaseAgent, ball):
    pad = getClosestPad(agent)
    distance = distance2D(agent.info.my_car.pos, pad.pos)
    futureInFrontOfBall = distance2D(ball.pos, agent.info.my_goal.center) < distance2D(agent.info.my_car.pos,
                                                                                       agent.info.my_goal.center)
    if distance < 1500 and agent.info.my_car.boost < 34 and pad.is_active and not agent.inFrontOfBall and not futureInFrontOfBall:
        return True
    return False


def boostGrabbingSpeed(agent, target_location):
    target_local = dot(target_location - agent.info.my_car.pos, agent.info.my_car.theta)
    angle_to_target = math.atan2(target_local[1], target_local[0])
    distance_to_target = distance2D(target_location, agent.info.my_car.pos)
    return 2300 - cap((900 * (angle_to_target ** 2)), 0, 2200) + cap((distance_to_target - 1000) / 4, 0, 500)
