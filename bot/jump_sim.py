import math
import sys
from pathlib import Path

import scipy
from pynverse import inversefunc

sys.path.insert(1, str(Path(__file__).absolute().parent.parent.parent))

# gravity
g = 650
# jump acceleration
a = 1400
# jump duration
d = 0.2

batmobile_resting_height = 18.65
boost_acceleration = 991.666


# Functions which calculates the height of your jump at time x with duration of d
# https://www.desmos.com/calculator/7qzakxxd61
def get_height_at_time(x):
    """Get the height of a jump at a certain time t"""
    c = 0.5 * (a - g) * (d ** 2) + 300 * d
    a2 = (a - g) * d + 300
    if 0 <= x <= d:
        return batmobile_resting_height + 0.5 * (a - g) * (x ** 2) + 300 * x
    elif d <= x:
        return batmobile_resting_height + 0.5 * (-g) * ((x - d) ** 2) + a2 * (x - d) + c
    return 0


# The inverse of the function above, so it gives the time at which you will reach height h with duration d
def get_time_at_height(y):
    f = lambda x: get_height_at_time(x)
    f_max = min(scipy.optimize.fmin(lambda x: -f(x), 0, disp=False), 1.4)
    f_inverse = inversefunc(f, domain=[0, f_max])
    if y < f_max:
        return f_inverse(y)
    else:
        return f_max


def get_height_at_time_boost(x, theta, boost_amount):
    """Get the height of a jump at a certain time t while boosting at angle theta for a given boost amount"""
    b = math.sin(theta) * boost_acceleration
    boost_amount = boost_amount - 6
    b_t = boost_amount / 33.3 + 0.2
    c = 0.5 * (a - g + b) * (d ** 2) + 300 * d
    a2 = (a - g + b) * d + 300
    p = 0.5 * (-g + b) * ((b_t - d) ** 2) + a2 * (b_t - d) + c
    a3 = -g * b_t + g * d + b * b_t - b * d + a2
    if 0 <= x <= d:
        return batmobile_resting_height + 0.5 * (a - g + b) * (x ** 2) + 300 * x
    elif d <= x <= b_t:
        return batmobile_resting_height + 0.5 * (-g + b) * ((x - d) ** 2) + a2 * (x - d) + c
    elif b_t <= x:
        return batmobile_resting_height + 0.5 * (-g) * ((x - b_t) ** 2) + a3 * (x - b_t) + p


# The inverse of the function above, so it gives the time at which you will reach height h with duration d
def get_time_at_height_boost(y, theta, boost_amount):
    f = lambda x: get_height_at_time_boost(x, theta, boost_amount)
    f_max = min(scipy.optimize.fmin(lambda x: -f(x), 0, disp=False)[0], 1.4)
    f_inverse = inversefunc(f, domain=[0, f_max])
    if y < f(f_max):
        return f_inverse(y)
    else:
        return f_max
