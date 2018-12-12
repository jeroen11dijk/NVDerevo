import math

from RLUtilities.LinearAlgebra import vec3, dot, norm, vec2
from RLUtilities.Maneuvers import Drive

from boost import boost_grabbing_speed
from catching import start_catching
from shooting import can_shoot, start_shooting
from util import get_closest_pad, cap, distance_2d, velocity_2d, remap_angle


def shadow(agent):
    agent.drive.step(1 / 60)
    agent.controls = agent.drive.controls
    target = shadow_target(agent)
    agent.drive.target_pos = target
    agent.drive.target_speed = shadow_speed(agent, target)
    if agent.conceding:
        agent.step = "Defending"
    elif in_shadow_position(agent) or can_challenge(agent):
        agent.step = "Ballchasing"
    elif agent.info.ball.pos[2] > 500:
        start_catching(agent)
    elif can_shoot(agent):
        start_shooting(agent)
    elif agent.boostGrabs:
        agent.step = "Grabbing Boost"
        target = get_closest_pad(agent).pos
        agent.drive = Drive(agent.info.my_car, target, boost_grabbing_speed(agent, target))


def in_shadow_position(agent):
    distance_car_to_goal = distance_2d(agent.info.my_car.pos, agent.info.my_goal.center)
    distance_ball_to_goal = distance_2d(agent.info.ball.pos, agent.info.my_goal.center)
    return 2 * distance_car_to_goal < distance_ball_to_goal


def can_challenge(agent):
    bot_to_ball = agent.info.ball.pos - agent.info.my_car.pos
    angle_between_bot_and_ball = math.atan2(bot_to_ball[1], bot_to_ball[0])
    angle_front_to_ball = remap_angle(math.fabs(angle_between_bot_and_ball - agent.yaw))
    distance_bot_to_ball = norm(vec2(bot_to_ball))
    could_challenge = math.radians(-45) < angle_front_to_ball < math.radians(45) and distance_bot_to_ball < 750
    return could_challenge and not agent.inFrontOfBall


def shadow_target(agent):
    center_goal = agent.info.my_goal.center
    ball = agent.info.ball
    goal_to_ball = ball.pos - center_goal
    target_vector = vec3(2 / 3 * goal_to_ball[0], 2 / 3 * goal_to_ball[1], 0)
    return center_goal + target_vector


def shadow_speed(agent, target_location):
    car = agent.info.my_car
    target_local = dot(target_location - car.pos, car.theta)
    angle_to_target = cap(math.atan2(target_local[1], target_local[0]), -3, 3)
    distance_to_target = distance_2d(agent.info.my_car.pos, target_location)
    if distance_to_target > 2.5 * velocity_2d(agent.info.my_car.vel):
        return 2300
    else:
        return 2300 - (340 * (angle_to_target ** 2))


def shadowSpeedOld(agent, targetLocation):
    car = agent.info.my_car
    targetLocal = dot(targetLocation - car.pos, car.theta)
    angleToTarget = cap(math.atan2(targetLocal[1], targetLocal[0]), -3, 3)
    distanceToTarget = distance_2d(car.pos, targetLocation)
    return 2300 - cap((900 * (angleToTarget ** 2)), 0, 2200) + cap((distanceToTarget - 1000) / 4, 0, 500)
