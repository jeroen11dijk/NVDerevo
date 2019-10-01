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
