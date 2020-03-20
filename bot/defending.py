""""Module that handles the defending strategy"""
import math
import time

from halfflip import HalfFlip
from rlutilities.linear_algebra import normalize, rotation, vec3, vec2, dot, look_at
from rlutilities.mechanics import Dodge, AerialTurn
from steps import Step
from util import line_backline_intersect, cap, distance_2d, sign, get_speed, velocity_forward


def defending(agent):
    """"Method that gives output for the defending strategy"""
    target = defending_target(agent)
    agent.drive.target = target
    distance = distance_2d(agent.info.my_car.position, target)
    vf = velocity_forward(agent.info.my_car)
    dodge_overshoot = distance < (abs(vf) + 500) * 1.5
    agent.drive.speed = get_speed(agent, target)
    agent.drive.step(agent.info.time_delta)
    agent.controls = agent.drive.controls
    t = time.time()
    can_dodge, simulated_duration, simulated_target = agent.simulate()
    # print(time.time() - t)
    if can_dodge:
        agent.dodge = Dodge(agent.info.my_car)
        agent.turn = AerialTurn(agent.info.my_car)
        agent.dodge.duration = simulated_duration - 0.1
        agent.dodge.target = simulated_target

        agent.dodge.preorientation = look_at(simulated_target, vec3(0, 0, 1))
        agent.timer = 0
        agent.step = Step.Dodge
    if not agent.should_defend():
        agent.step = Step.Shooting
    elif vf < -900 and (not dodge_overshoot or distance < 600):
        agent.step = Step.HalfFlip
        agent.halfflip = HalfFlip(agent.info.my_car)
    elif not dodge_overshoot and agent.info.my_car.position[2] < 80 and \
            (agent.drive.speed > abs(vf) + 300 and 1200 < abs(vf) < 2000 and agent.info.my_car.boost <= 25):
        # Dodge towards the target for speed
        agent.step = Step.Dodge
        agent.dodge = Dodge(agent.info.my_car)
        agent.dodge.duration = 0.1
        agent.dodge.target = target
            

def defending_target(agent):
    """"Method that gives the target for the shooting strategy"""
    ball = agent.info.ball
    car = agent.info.my_car
    car_to_ball = ball.position - car.position
    backline_intersect = line_backline_intersect(agent.my_goal.center[1], vec2(car.position), vec2(car_to_ball))
    target = agent.my_goal.center + vec3(sign(backline_intersect) * max(abs(ball.position[0]), 1500), 0, 0)
    target_to_ball = normalize(ball.position - target)
    # Subtract target to car vector
    difference = target_to_ball - normalize(car.position - target)
    error = cap(abs(difference[0]) + abs(difference[1]), 1, 10)

    goal_to_ball_2d = vec2(target_to_ball[0], target_to_ball[1])
    test_vector_2d = dot(rotation(0.5 * math.pi), goal_to_ball_2d)
    test_vector = vec3(test_vector_2d[0], test_vector_2d[1], 0)

    distance = cap((40 + distance_2d(ball.position, car.position) * (error ** 2)) / 1.8, 0, 4000)
    location = ball.position + vec3((target_to_ball[0] * distance), target_to_ball[1] * distance, 0)

    # this adjusts the target based on the ball velocity perpendicular to the direction we're trying to hit it
    multiplier = cap(distance_2d(car.position, location) / 1500, 0, 2)
    distance_modifier = cap(dot(test_vector, ball.velocity) * multiplier, -1000, 1000)
    location += vec3(test_vector[0] * distance_modifier, test_vector[1] * distance_modifier, 0)

    # another target adjustment that applies if the ball is close to the wall
    extra = 3850 - abs(location[0])
    if extra < 0:
        location[0] = cap(location[0], -3850, 3850)
        location[1] = location[1] + (-sign(agent.team) * cap(extra, -800, 800))
    return location
