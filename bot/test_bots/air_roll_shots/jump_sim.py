import sys
from pathlib import Path

sys.path.insert(1, str(Path(__file__).absolute().parent.parent.parent))
from rlutilities.mechanics import Jump, Dodge
from rlutilities.simulation import Car
from rlutilities.linear_algebra import *

# gravity
g = 650
# jump acceleration
a = 1400


def get_height_at_time(t, d):
    """Get the height of a jump at a certain time t while holding jump for duration d"""
    c = 0.5 * (a - g) * (d ** 2) + 300 * d
    a2 = (a - g) * d + 300
    if 0 <= t <= d:
        return 0.5 * (a - g) * (t ** 2) + 300 * t
    elif d <= t:
        return 0.5 * (-g) * ((t - d) ** 2) + a2 * (t - d) + c
    return 0

car = Car()
car.on_ground = True
car.location = vec3(0.000000, -1252.049927, 18.639999)
car.velocity = vec3(0, 1270, 0.45)
car.rotation = mat3(-0.000000, -1.000000, -0.000000, 0.999982, -0.000000, 0.005944, -0.005944, -0.000000, 0.999982)
dodge = Dodge(car)
dodge.duration = 0.9
dodge.target = vec3(0, 0, 234)
for i in range(13):
    dodge.step(1 / 60)
    car.step(dodge.controls, 1 / 60)
    print(i * 1 / 60, car.location[2])
print(car.location)
print(dodge.timer)