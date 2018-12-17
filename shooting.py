import math

from RLUtilities.LinearAlgebra import normalize, rotation, vec3, vec2, dot
from RLUtilities.Maneuvers import Drive

from catching import start_catching
from util import angle_2d, cap, distance_2d, sign, velocity_2d, time_z, eta_calculator


def start_shooting(agent):
    agent.step = "Shooting"
    target = shooting_target(agent)
    speed = shooting_speed(agent, target)
    agent.drive = Drive(agent.info.my_car, target, speed)


def in_the_offensive_cone(agent):
    ball = agent.info.ball
    car = agent.info.my_car
    left_post = agent.info.their_goal.corners[3]
    right_post = agent.info.their_goal.corners[2]
    ball_left = angle_2d(ball.pos, left_post)
    ball_right = angle_2d(ball.pos, right_post)
    agent_left = angle_2d(car.pos, left_post)
    agent_right = angle_2d(car.pos, right_post)

    # determining if we are left/right/inside of cone
    if agent_left > ball_left and agent_right > ball_right:
        return right_post
    elif agent_left > ball_left and agent_right < ball_right:
        return None
    elif agent_left < ball_left and agent_right < ball_right:
        return left_post
    else:
        return None


def shooting(agent):
    agent.drive.step(1 / 60)
    agent.controls = agent.drive.controls
    target = shooting_target(agent)
    agent.drive.target_pos = target
    agent.drive.target_speed = shooting_speed(agent, target)
    if agent.conceding or distance_2d(agent.info.ball.pos, agent.info.my_goal.center) < 2000:
        agent.step = "Defending"
    # elif agent.inFrontOfBall or not can_shoot(agent):
    #     agent.step = "Shadowing"
    elif not can_shoot(agent):
        agent.step = "Ballchasing"
    elif agent.info.ball.pos[2] > 500:
        start_catching(agent)


def shooting_target(agent):
    ball = agent.info.ball
    car = agent.info.my_car
    target = in_the_offensive_cone(agent)

    if target is not None:
        goal_to_ball = normalize(ball.pos - target)
        goal_to_car = normalize(car.pos - target)
        difference = goal_to_ball - goal_to_car
        error = cap(abs(difference[0]) + abs(difference[1]), 1, 10)
    else:
        goal_to_ball = normalize(car.pos - ball.pos)
        error = cap(distance_2d(ball.pos, car.pos) / 1000, 0, 1)

    goal_to_ball_2d = vec2(goal_to_ball[0], goal_to_ball[1])
    test_vector_2d = dot(rotation(0.5 * math.pi), goal_to_ball_2d)
    test_vector = vec3(test_vector_2d[0], test_vector_2d[1], 0)

    distance = cap((40 + distance_2d(ball.pos, car.pos) * (error ** 2)) / 1.8, 0, 4000)
    location = ball.pos + vec3((goal_to_ball[0] * distance), goal_to_ball[1] * distance, 0)

    # this adjusts the target based on the ball velocity perpendicular to the direction we're trying to hit it
    multiplier = cap(distance_2d(car.pos, location) / 1500, 0, 2)
    distance_modifier = cap(dot(test_vector, ball.vel) * multiplier, -1000, 1000)
    modified_vector = vec3(test_vector[0] * distance_modifier, test_vector[1] * distance_modifier, 0)
    location += modified_vector

    # another target adjustment that applies if the ball is close to the wall
    extra = 3850 - abs(location[0])
    if extra < 0:
        location[0] = cap(location[0], -3850, 3850)
        location[1] = location[1] + (-sign(agent.team) * cap(extra, -800, 800))
    return location


def shooting_speed(agent, location):
    car = agent.info.my_car
    local = dot(location - car.pos, car.theta)
    angle = cap(math.atan2(local[1], local[0]), -3, 3)
    distance = distance_2d(car.pos, location)
    if distance > 2.5 * velocity_2d(car.vel):
        return 2300
    else:
        return 2300 - (340 * (angle ** 2))


def can_shoot(agent):
    ball = agent.info.ball
    closer = eta_calculator(agent.info.my_car, ball.pos) < eta_calculator(agent.info.opponents[0], ball.pos)
    on_the_ground = abs(ball.vel[2]) < 150 and time_z(ball) < 1
    if on_the_ground and closer and not agent.inFrontOfBall:
        return True
    return False


