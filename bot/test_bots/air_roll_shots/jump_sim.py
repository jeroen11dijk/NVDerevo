import sys
from math import sqrt, floor
from pathlib import Path

sys.path.insert(1, str(Path(__file__).absolute().parent.parent.parent))

# gravity
g = 650
# jump acceleration
a = 1400

batmobile_resting_height = 18.65


# Functions which calculates the height of your jump at time x with duration of d
# https://www.desmos.com/calculator/7qzakxxd61
def get_height_at_time(x, d):
    """Get the height of a jump at a certain time t while holding jump for duration d"""
    c = 0.5 * (a - g) * (d ** 2) + 300 * d
    a2 = (a - g) * d + 300
    if 0 <= x <= d:
        return batmobile_resting_height + 0.5 * (a - g) * (x ** 2) + 300 * x
    elif d <= x:
        return batmobile_resting_height + 0.5 * (-g) * ((x - d) ** 2) + a2 * (x - d) + c
    return 0


# The inverse of the function above, so it gives the time at which you will reach height h with duration d
def get_time_at_height(y, d):
    if 0 <= y <= get_height_at_time(d, d):
        return -0.4 + 0.011547 * sqrt(20*y + 827)
    elif y <= get_height_at_time(0.8923, d):
        return 0.892308 - 0.0034401 * sqrt(64849 - 260 * y)
    else:
        # If the target height is above the maximal height return the time for the maxima and see if you might reach it
        return get_time_at_height(get_height_at_time(0.8923, 0.2), 0.2)