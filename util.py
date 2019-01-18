import math

from RLUtilities.LinearAlgebra import vec3, vec2, dot, norm


def get_speed(agent, location):
    car = agent.info.my_car
    local = dot(location - car.pos, car.theta)
    angle = cap(math.atan2(local[1], local[0]), -3, 3)
    distance = distance_2d(car.pos, location)
    if distance > 2.5 * velocity_2d(car.vel):
        return 2250
    else:
        return 2250 - (400 * (angle ** 2))


def powerslide(agent):
    target_local = dot(agent.drive.target_pos - agent.info.my_car.pos, agent.info.my_car.theta)
    phi = math.atan2(target_local[1], target_local[0])
    if abs(phi) > 1.7:
        agent.controls.handbrake = 1
        agent.controls.boost = 0


def get_ballchase_speed(agent, location):
    car = agent.info.my_car
    local = dot(location - car.pos, car.theta)
    angle = cap(math.atan2(local[1], local[0]), -3, 3)
    distance = distance_2d(car.pos, location)
    if distance > 2.5 * velocity_2d(car.vel):
        return 1500
    else:
        return 1500 - (375 * (angle ** 2))


def distance_2d(a, b):
    return norm(vec2(a - b))


def angle_2d(target_location, object_location):
    difference = target_location - object_location
    return math.atan2(difference[1], difference[0])


def velocity_2d(vel):
    return norm(vec2(vel))


def line_backline_intersect(y, origin, direction):
    if abs(direction[1]) < 1e-10:
        direction[1] = 1e-10
    mult = (y - origin[1]) / direction[1]
    return (origin + mult * direction)[0]


def get_closest_pad(agent):
    pads = agent.info.boost_pads
    pad = None
    distance = math.inf
    for i in range(len(pads)):
        if distance_2d(agent.info.my_car.pos, pads[i].pos) < distance:
            distance = distance_2d(agent.info.my_car.pos, pads[i].pos)
            pad = pads[i]
    return pad


def get_closest_small_pad(agent):
    pads = agent.info.small_boost_pads
    pad = None
    distance = math.inf
    for i in range(len(pads)):
        if distance_2d(agent.info.my_car.pos, pads[i].pos) < distance:
            distance = distance_2d(agent.info.my_car.pos, pads[i].pos)
            pad = pads[i]
    return pad


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


def remap_angle(angle):
    if angle < -math.pi:
        angle += 2 * math.pi
    if angle > math.pi:
        angle -= 2 * math.pi
    return angle


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


def z0(vector):
    return vec3(vector[0], vector[1], 0)


def time_z(ball):
    rate = 0.97
    return quad(-325, ball.vel[2] * rate, ball.pos[2] - 92.75)


def can_dodge(agent, target):
    bot_to_target = target - agent.info.my_car.pos
    local_bot_to_target = dot(bot_to_target, agent.info.my_car.theta)
    angle_front_to_target = math.atan2(local_bot_to_target[1], local_bot_to_target[0])
    distance_bot_to_target = norm(vec2(bot_to_target))
    good_angle = math.radians(-10) < angle_front_to_target < math.radians(10)
    on_ground = agent.info.my_car.on_ground and agent.info.my_car.pos[2] < 100
    going_fast = velocity_2d(agent.info.my_car.vel) > 1250
    target_not_in_goal = agent.info.my_goal.inside(target)
    return good_angle and distance_bot_to_target > 2000 and on_ground and going_fast and target_not_in_goal


def in_front_of_ball(agent):
    our_goal = agent.info.my_goal.center
    return distance_2d(agent.info.ball.pos, our_goal) < distance_2d(agent.info.my_car.pos, our_goal)


def boost_needed(initial_speed, goal_speed):
    p1 = 6.31e-06
    p2 = 0.010383
    p3 = 1.3183
    boost_initial = p1 * initial_speed ** 2 + p2 * initial_speed + p3
    boost_goal = p1 * goal_speed ** 2 + p2 * goal_speed + p3
    return boost_goal - boost_initial


def is_reachable(agent, location, eta):
    distance = distance_2d(agent.info.my_car.pos, location)
    time = (eta * agent.FPS)
    if time == 0:
        return False
    speed = distance / time
    if speed < 2300:
        if speed < 1399:
            return True
        return agent.info.my_car.boost > boost_needed(velocity_2d(agent.info.my_car.vel), speed)


def render_string(agent, string):
    agent.renderer.begin_rendering('The State')
    agent.renderer.draw_line_3d(agent.info.my_car.pos, agent.drive.target_pos, agent.renderer.black())
    agent.renderer.draw_string_2d(20, 20, 3, 3, string, agent.renderer.red())
    agent.renderer.end_rendering()
