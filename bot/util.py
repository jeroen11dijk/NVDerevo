"""Module with all the utility methods"""
import math

from rlutilities.linear_algebra import vec2, norm, dot, vec3, normalize


def distance_2d(vec_a, vec_b):
    """returns 2d distance between two vectors"""
    return norm(vec2(vec_a - vec_b))


def get_closest_small_pad(agent, location):
    """Gets the small boostpad closest to the bot"""
    pads = agent.small_boost_pads
    closest_pad = None
    distance = math.inf
    for pad in pads:
        if distance_2d(location, pad.location) < distance:
            distance = distance_2d(agent.info.my_car.location, pad.location)
            closest_pad = pad
    return closest_pad


def get_closest_big_pad(agent):
    """Gets the big boostpad closest to the bot"""
    pads = agent.boost_pads
    closest_pad = None
    distance = math.inf
    for pad in pads:
        if distance_2d(agent.info.my_car.location, pad.location) < distance:
            distance = distance_2d(agent.info.my_car.location, pad.location)
            closest_pad = pad
    return closest_pad


def line_backline_intersect(y_axis, origin, direction):
    """Returns the location where the ray intersects with the Y"""
    if abs(direction[1]) < 1e-10:
        direction[1] = 1e-10
    mult = (y_axis - origin[1]) / direction[1]
    return (origin + mult * direction)[0]


def sign(num):
    """Returns 1 if the number is bigger then 0 otherwise it returns -1"""
    if num <= 0:
        return -1
    return 1


def velocity_2d(velocity):
    """Returns the total 2d velocity given a velocity vector"""
    return norm(vec2(velocity))


def boost_needed(initial_speed, goal_speed):
    """Returns the boost amount you need to reach the target speed given the initial speed"""
    p_1 = 6.31e-06
    p_2 = 0.010383
    p_3 = 1.3183
    boost_initial = p_1 * initial_speed ** 2 + p_2 * initial_speed + p_3
    boost_goal = p_1 * goal_speed ** 2 + p_2 * goal_speed + p_3
    return boost_goal - boost_initial


def is_reachable(agent, location, eta):
    """Returns whether the bot can reach a certain location in time"""
    distance = distance_2d(agent.info.my_car.location, location)
    if eta == 0:
        return False
    speed = distance / eta
    if speed < 2300:
        if speed < 1399:
            return True
        return (agent.info.my_car.boost >
               boost_needed(velocity_2d(agent.info.my_car.velocity), speed))
    return None


def get_speed(agent, location):
    """Returns the target speed given a certain location"""
    car = agent.info.my_car
    local = dot(location - car.location, car.rotation)
    angle = cap(math.atan2(local[1], local[0]), -3, 3)
    distance = distance_2d(car.location, location)
    if distance > 2.5 * velocity_2d(car.velocity):
        return 2250
    return 2250 - (400 * (angle ** 2))


def can_dodge(agent, target):
    """Returns whether its wise to dodge"""
    bot_to_target = target - agent.info.my_car.location
    local_bot_to_target = dot(bot_to_target, agent.info.my_car.rotation)
    angle_front_to_target = math.atan2(local_bot_to_target[1], local_bot_to_target[0])
    distance_bot_to_target = norm(vec2(bot_to_target))
    good_angle = math.radians(-10) < angle_front_to_target < math.radians(10)
    on_ground = agent.info.my_car.on_ground and agent.info.my_car.location[2] < 100
    going_fast = velocity_2d(agent.info.my_car.velocity) > 1250
    target_not_in_goal = not agent.my_goal.inside(target)
    return (good_angle and distance_bot_to_target > 2000
           and on_ground and going_fast and target_not_in_goal)


def cap(num, low, high):
    """Caps x between a lower and upper bound"""
    return min(max(num, low), high)


def get_bounce(agent):
    """Returns the first reachable bounce"""
    for i in range(len(agent.bounces)):
        goal_to_ball = normalize(z_0(agent.bounces[i][0] - agent.their_goal.center))
        target = agent.bounces[i][0] + 40 * goal_to_ball
        if is_reachable(agent, target, agent.bounces[i][1]):
            return [target, agent.bounces[i][1]]
    return None


def z_0(vector):
    """Returns a vec3 with 0 on the z-axis"""
    return vec3(vector[0], vector[1], 0)


def lerp(a, b, t):
    return a + (b - a) * t
