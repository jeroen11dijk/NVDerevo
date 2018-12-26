import math

from RLUtilities.LinearAlgebra import normalize, rotation, vec3, vec2, dot

from util import line_backline_intersect, cap, distance_2d, sign, velocity_2d, render_string


def defending(agent):
    agent.drive.step(1 / 60)
    agent.controls = agent.drive.controls
    target = defending_target(agent)
    agent.drive.target_pos = target
    agent.drive.target_speed = defending_speed(agent, target)
    if not agent.defending:
        agent.step = "Ballchasing"


def defending_target(agent):
    ball = agent.info.ball
    car = agent.info.my_car
    car_to_ball = ball.pos - car.pos
    backline_intersect = sign(agent.team) * line_backline_intersect(agent, vec2(car.pos), vec2(car_to_ball))
    print(backline_intersect)
    if -1250 < backline_intersect < 1250:
        if backline_intersect < 0:
            target = agent.info.their_goal.corners[3] - vec3(10000, 0, 0) + sign(agent.team)*vec3(0, 10000, 0)
            goal_to_ball = normalize(ball.pos - target)
            goal_to_car = normalize(car.pos - target)
            difference = goal_to_ball - goal_to_car
            error = cap(abs(difference[0]) + abs(difference[1]), 1, 10)
        else:
            target = agent.info.their_goal.corners[2] + vec3(10000, 0, 0) + sign(agent.team)*vec3(0, 10000, 0)
            goal_to_ball = normalize(ball.pos - target)
            goal_to_car = normalize(car.pos - target)
            difference = goal_to_ball - goal_to_car
            error = cap(abs(difference[0]) + abs(difference[1]), 1, 10)
    # Right of the ball
    elif -900 > backline_intersect:
        goal_to_ball = normalize(car.pos - ball.pos)
        error = cap(distance_2d(ball.pos, car.pos) / 1000, 0, 1)
    # Left of the ball
    elif 900 < backline_intersect:
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


def defending_speed(agent, location):
    car = agent.info.my_car
    local = dot(location - car.pos, car.theta)
    angle = cap(math.atan2(local[1], local[0]), -3, 3)
    distance = distance_2d(car.pos, location)
    if distance > 2.5 * velocity_2d(car.vel):
        return 2300
    else:
        return 2300 - (340 * (angle ** 2))
