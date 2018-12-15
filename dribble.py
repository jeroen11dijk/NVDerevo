import math

import numpy as np
from RLUtilities.Simulation import Input
from RLUtilities.LinearAlgebra import dot
from util import distance_2d, velocity_2d, remap_angle


def aim(agent):
    controls = Input()
    car = agent.info.my_car
    ball = agent.info.ball
    target = agent.info.their_goal.center
    # direction of target relative to yaw of car (where should we aim verse where we are aiming)
    local_bot_to_target = dot(target - car.pos, car.theta)
    angle_front_to_target = math.atan2(local_bot_to_target[1], local_bot_to_target[0])
    # direction of ball relative to center of car (where should we aim)
    # direction of ball relative to yaw of car (where should we aim verse where we are aiming)
    local_ball_to_target = dot(ball.pos - car.pos, car.theta)
    angle_front_to_ball = math.atan2(local_ball_to_target[1], local_ball_to_target[0])
    # distance between bot and ball
    distance = distance_2d(car.pos, ball.pos)
    # direction of ball velocity relative to yaw of car (which way the ball is moving verse which way we are moving)
    velocity_direction = dot(ball.vel, car.theta)
    ball_angle_to_car = math.atan2(velocity_direction[1], velocity_direction[0])
    # magnitude of ball_bot_angle (squared)
    ball_bot_diff = (ball.vel[0] ** 2 + ball.vel[1] ** 2) - (car.vel[0] ** 2 + car.vel[1] ** 2)
    # p is the distance between ball and car
    # i is the magnitude of the ball's velocity (squared) the i term would normally
    # be the integral of p over time, but the ball's velocity is essentially that number
    # d is the relative speed between ball and car
    # note that bouncing a ball is distinctly different than balancing something that doesnt bounce
    # p_s is the x component of the distance to the ball
    # d_s is the one frame change of p_s, that's why p_s has to be global

    # speed of car to be used when deciding how much to accelerate when approaching the ball
    car_speed = velocity_2d(car.vel)
    # we modify distance and ball_bot_diff so that only the component along the car's path is counted
    # if the ball is too far to the left, we don't want the bot to think it has to drive forward
    # to catch it
    distance_y = math.fabs(distance * math.cos(angle_front_to_ball))
    distance_x = math.fabs(distance * math.sin(angle_front_to_ball))
    # ball moving forward WRT car yaw?
    forward = False
    if math.fabs(ball_angle_to_car) < math.radians(90):
        forward = True
    # this section is the standard approach to a dribble
    # the car quickly gets to the general area of the ball, then drives slow until it is very close
    # then begins balancing
    if (distance > 90000):  # 900
        controls.throttle = 1.
        controls.boost = False
    # we limit the speed to 300 to ensure a slow approach
    elif distance > 40000 and car_speed > 300:
        controls.throttle = 0
    elif (distance > 40000):  # 400
        controls.throttle = .1
        controls.boost = False
    # this is the balancing PID section
    # it always starts with full boost/throttle because the bot thinks the ball is too far in front
    # opposite is true for behind
    else:
        # first we give the distance values signs
        if forward:
            d = ball_bot_diff
            i = (ball.vel[0] ** 2 + ball.vel[1] ** 2)
        else:
            d = -ball_bot_diff
            i = -(ball.vel[0] ** 2 + ball.vel[1] ** 2)

        if math.fabs(math.degrees(angle_front_to_ball)) < 90:
            p = distance_y

        else:
            p = -1 * distance_y
        # this is the PID correction.  all of the callibration goes on right here
        # there is literature about how to set the variables but it doesn't work quite the same
        # because the car is only touching the ball (and interacting with the system) on bounces
        # we run the PID formula through tanh to give a value between -1 and 1 for steering input
        # if the ball is lower we have no velocity bias
        bias_v = 600000  # 600000

        # just the basic PID if the ball is too low
        if ball.pos[2] < 120:
            correction = np.tanh((20 * p + .0015 * i + .006 * d) / 500)
        # if the ball is on top of the car we use our bias (the bias is in velocity units squared)
        else:
            correction = np.tanh((20 * p + .0015 * (i - bias_v) + .006 * d) / 500)
        # makes sure we don't get value over .99 so we dont exceed maximum thrust
        controls.throttle = correction * .99
        # anything over .9 is boost
        if correction > .99:
            controls.boost = True
        else:
            controls.boost = False

    # this is the PID steering section
    # p_s is the x component of the distance to the ball (relative to the cars direction)
    # d_s is the on frame change in p_s

    # we use absolute value and then set the sign later
    d_s = math.fabs(agent.p_s) - math.fabs(distance_x)
    agent.p_s = math.fabs(distance_x)
    # give the values the correct sign
    if angle_front_to_ball < 0:
        agent.p_s = -agent.p_s
        d_s = -d_s
    # d_s is actually -d_s ...whoops
    d_s = -d_s
    min_angle = 10
    max_bias = 45
    if angle_front_to_target < math.radians(-min_angle):
        # If the target is more than 10 degrees right from the centre, steer left
        bias = max_bias
    elif angle_front_to_target > math.radians(min_angle):
        # If the target is more than 10 degrees left from the centre, steer right
        bias = -max_bias
    else:
        # If the target is less than 10 degrees from the centre, steer straight
        bias = max_bias * (math.degrees(angle_front_to_target) / min_angle)
    # the correction settings can be altered to change performance
    correction = np.tanh((100 * (agent.p_s + bias) + 1500 * d_s) / 8000)
    # apply the correction
    controls.steer = correction
    return controls
