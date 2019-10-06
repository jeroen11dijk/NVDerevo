import sys
from math import sqrt
from pathlib import Path

sys.path.insert(1, str(Path(__file__).absolute().parent.parent.parent))

# gravity
g = 650
# jump acceleration
a = 1400


def get_height_at_time(x, d):
    """Get the height of a jump at a certain time t while holding jump for duration d"""
    c = 0.5 * (a - g) * (d ** 2) + 300 * d
    a2 = (a - g) * d + 300
    if 0 <= x <= d:
        return 0.5 * (a - g) * (x ** 2) + 300 * x
    elif d <= x:
        return 0.5 * (-g) * ((x - d) ** 2) + a2 * (x - d) + c
    return 0


def get_time_at_height(y, d):
    if 0 <= y <= get_height_at_time(d, d):
        return -0.4 + (sqrt(y + 60) / (5 * sqrt(15)))
    elif y <= get_height_at_time(0.8923, d):
        return 0.892308 - 0.0153846 * sqrt(3000 - 13 * y)
    else:
        return 0

