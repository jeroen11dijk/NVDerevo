import math
import random
import time

from RLUtilities.GameInfo import Car
from RLUtilities.LinearAlgebra import vec3, vec2, dot, normalize
from rlbot.utils.game_state_util import Vector3, Rotator, CarState, GameState, BallState, Physics


def ETACalculator(car: Car, target: vec3):
    boost_time = car.boost / 33
    speed = cap(dot(vec2(car.vel), vec2(normalize((target - car.pos)))) + 500 * boost_time ** 2, 1, 2300)
    distance = distance2D(car.pos, target)
    if (distance / speed) < boost_time:
        speed = cap(dot(vec2(car.vel), vec2(normalize((target - car.pos)))) + 500 * (distance / speed) ** 2, 1, 2300)
        distance = distance2D(car.pos, target)
        return 60 * distance / speed
    return 60 * distance / speed


def distance2D(target_location: vec3, object_location: vec3):
    vector = target_location - object_location
    return math.sqrt(vector[0] ** 2 + vector[1] ** 2)


def angle2D(target_location: vec3, object_location: vec3):
    difference = target_location - object_location
    return math.atan2(difference[1], difference[0])


def velocity2D(targetObject):
    return math.sqrt(targetObject.vel[0] ** 2 + targetObject.vel[1] ** 2)


def getClosestPad(agent):
    pads = agent.info.boost_pads
    closestPad = None
    distToClosestPad = math.inf
    for i in range(len(pads)):
        if distance2D(agent.info.my_car.pos, pads[i].pos) < distToClosestPad:
            distToClosestPad = distance2D(agent.info.my_car.pos, pads[i].pos)
            closestPad = pads[i]
    return closestPad


def getClosestSmallPad(agent):
    closestPad = None
    distToClosestPad = math.inf
    for i in range(agent.get_field_info().num_boosts):
        current = agent.get_field_info().boost_pads[i]
        current_pos = vec3(current.location.x, current.location.y, current.location.z)
        if not (current.is_full_boost) and distance2D(agent.info.my_car.pos, current_pos) < distToClosestPad:
            distToClosestPad = distance2D(agent.info.my_car.pos, current_pos)
            closestPad = current
    return closestPad


def quad(a, b, c):
    inside = (b ** 2) - (4 * a * c)
    if inside < 0 or a == 0:
        return 0.1
    else:
        n = ((-b - math.sqrt(inside)) / (2 * a))
        p = ((-b + math.sqrt(inside)) / (2 * a))
        if p > n:
            return p
        return n


def sign(x):
    if x <= 0:
        return -1
    else:
        return 1


def cap(x, low, high):
    if x < low:
        return low
    elif x > high:
        return high
    else:
        return x


def timeZ(ball):
    rate = 0.97
    return quad(-325, ball.vel[2] * rate, ball.pos[2] - 92.75)


def kickOffStateSetting(agent, prevKickoff):
    if not agent.kickoff and prevKickoff:
        agent.timer = time.time()
    if agent.timer is not (None) and time.time() - agent.timer > 2.5:
        theirGoal = agent.info.their_goal.center - sign(agent.team) * vec3(0, 400, 0)
        ball_state = BallState(Physics(location=Vector3(theirGoal[0], theirGoal[1], theirGoal[2])))
        game_state = GameState(ball=ball_state)
        agent.timer = None
        agent.set_game_state(game_state)


def boostNeeded(initialSpeed, goalSpeed):
    p1 = 6.31e-06
    p2 = 0.010383
    p3 = 1.3183
    boost_initial = p1 * initialSpeed ** 2 + p2 * initialSpeed + p3
    boost_goal = p1 * goalSpeed ** 2 + p2 * goalSpeed + p3
    boost_needed = boost_goal - boost_initial
    return boost_needed


def isReachable(agent, location, eta):
    distance = distance2D(agent.info.my_car.pos, location)
    speed = distance / (eta - agent.time)
    if speed < 2300:
        if speed < 1399:
            return True
        return agent.info.my_car.boost > boostNeeded(velocity2D(agent.info.my_car), speed)


def speedController(agent, location):
    distance = distance2D(agent.info.my_car.pos, location)

    alpha = 1.3
    time_left = agent.eta - agent.time
    avg_vf = distance / time_left
    target_vf = (1.0 - alpha) * velocity2D(agent.info.my_car) + alpha * avg_vf

    if velocity2D(agent.info.my_car) < target_vf:
        agent.controls.throttle = 1.0
        if target_vf > 1399:
            agent.controls.boost = 1
        else:
            agent.controls.boost = 0
    else:
        if velocity2D(agent.info.my_car) - target_vf > 75:
            agent.controls.throttle = -1.0
        else:
            agent.controls.throttle = 0.0


def renderString(agent, string):
    agent.renderer.begin_rendering()
    agent.renderer.draw_line_3d(agent.info.my_car.pos, agent.drive.target_pos, agent.renderer.black())
    agent.renderer.draw_string_2d(20, 20, 3, 3, string, agent.renderer.red())
    agent.renderer.end_rendering()


def setState(agent):
    # this just initializes the car and ball
    # to different starting points each time
    c_position = Vector3(random.uniform(-1000, 1000),
                         random.uniform(-4500, -4000),
                         25)

    car_state = CarState(boost_amount=100, physics=Physics(
        location=c_position,
        velocity=Vector3(0, 1000, 0),
        rotation=Rotator(0, 1.5, 0),
        angular_velocity=Vector3(0, 0, 0)
    ))

    bsign = random.choice([-1, 1])

    b_position = Vector3(random.uniform(-3500, -3000) * bsign,
                         random.uniform(-1500, 1500),
                         random.uniform(150, 500))

    b_velocity = Vector3(random.uniform(1000, 1500) * bsign,
                         random.uniform(- 500, 500),
                         random.uniform(1000, 1500))

    ball_state = BallState(physics=Physics(
        location=b_position,
        velocity=b_velocity,
        rotation=Rotator(0, 0, 0),
        angular_velocity=Vector3(0, 0, 0)
    ))

    agent.set_game_state(GameState(
        ball=ball_state,
        cars={agent.index: car_state})
    )
