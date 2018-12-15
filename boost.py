import math

from RLUtilities.LinearAlgebra import dot

from util import get_closest_pad, cap, distance_2d, velocity_2d
from shooting import start_shooting, can_shoot
from catching import start_catching


def grabBoost(agent):
    agent.drive.step(1 / 60)
    agent.controls = agent.drive.controls
    agent.drive.target_speed = boost_grabbing_speed(agent, agent.drive.target_pos)
    if agent.info.my_car.boost > 90 or not get_closest_pad(agent).is_active:
        agent.step = "Ballchasing"
    if agent.conceding or distance_2d(agent.info.ball.pos, agent.info.my_goal.center) < 2000:
        agent.step = "Defending"
    elif agent.inFrontOfBall:
        agent.step = "Shadowing"
    elif agent.info.ball.pos[2] > 500:
        start_catching(agent)
    elif can_shoot(agent):
        start_shooting(agent)


def boost_grabbing_available(agent, ball):
    pad = get_closest_pad(agent)
    distance = distance_2d(agent.info.my_car.pos, pad.pos)
    futureInFrontOfBall = distance_2d(ball.pos, agent.info.my_goal.center) < distance_2d(agent.info.my_car.pos,
                                                                                         agent.info.my_goal.center)
    if distance < 1500 and agent.info.my_car.boost < 34 and pad.is_active and not agent.inFrontOfBall and not futureInFrontOfBall:
        return True
    return False


def boost_grabbing_speed(agent, target_location):
    car = agent.info.my_car
    target_local = dot(target_location - car.pos, car.theta)
    angle_to_target = cap(math.atan2(target_local[1], target_local[0]), -3, 3)
    distance_to_target = distance_2d(agent.info.my_car.pos, target_location)
    if distance_to_target > 2.5 * velocity_2d(agent.info.my_car.vel):
        return 2300
    else:
        return 2300 - (340 * (angle_to_target ** 2))
