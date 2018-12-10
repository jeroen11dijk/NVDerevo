import math

from RLUtilities.LinearAlgebra import dot

from util import getClosestPad, cap, distance2D, velocity2D


def grabBoost(agent):
    agent.drive.step(1 / 60)
    agent.controls = agent.drive.controls
    agent.drive.target_speed = boostGrabbingSpeed(agent, agent.drive.target_pos)
    if agent.info.my_car.boost > 90 or not getClosestPad(agent).is_active:
        agent.step = "Ballchasing"


def boostGrabbingAvaiable(agent, ball):
    pad = getClosestPad(agent)
    distance = distance2D(agent.info.my_car.pos, pad.pos)
    futureInFrontOfBall = distance2D(ball.pos, agent.info.my_goal.center) < distance2D(agent.info.my_car.pos,
                                                                                       agent.info.my_goal.center)
    if distance < 1500 and agent.info.my_car.boost < 34 and pad.is_active and not agent.inFrontOfBall and not futureInFrontOfBall:
        return True
    return False


def boostGrabbingSpeed(agent, target_location):
    car = agent.info.my_car
    targetLocal = dot(target_location - car.pos, car.theta)
    angle_to_target = cap(math.atan2(targetLocal[1], targetLocal[0]), -3, 3)
    distance_to_target = distance2D(agent.info.my_car.pos, target_location)
    if distance_to_target > 2.5 * velocity2D(agent.info.my_car):
        return 2300
    else:
        return 2300 - (340 * (angle_to_target ** 2))
