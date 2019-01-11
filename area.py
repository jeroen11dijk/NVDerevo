import itertools
from enum import Enum

from RLUtilities.LinearAlgebra import vec2, vec3

from util import sign


class AreaName(Enum):
    CORNER = 1
    BOX = 2
    WALL = 3
    HALF = 4


class Area:

    def __init__(self, name: AreaName, x: int, y: int, corner1: vec2, corner2: vec2):
        self.name = name
        self.x = x
        self.y = y
        self.min_x = min(corner1[0], corner2[0])
        self.max_x = max(corner1[0], corner2[0])
        self.min_y = min(corner1[1], corner2[1])
        self.max_y = max(corner1[1], corner2[1])

    def __str__(self):
        return str(self.name)

    def to_string(self, agent):
        name = str(self.name)
        if sign(agent.team) == self.y:
            half = "Our"
        elif self.y == 0:
            half = ""
        else:
            half = "Their"
        if sign(agent.team) * self.x == 1:
            side = "right"
        elif sign(agent.team) * self.x == -1:
            side = "left"
        else:
            side = ""
        return half + " " + side + " " + name

    def is_inside(self, point: vec3):
        return self.min_x <= point[0] <= self.max_x and self.min_y <= point[1] <= self.max_y


def get_area():
    areas = []
    for x, y in itertools.product([-1, 1], [-1, 1]):
        areas.append(Area(AreaName.CORNER, x, y, vec2(x * 1788.0, y * 2300.0), vec2(x * 4096.0, y * 5120.0)))
    areas.append(Area(AreaName.BOX, 0, 1, vec2(1788.0, 2300.0), vec2(-1788.0, 5120.0)))
    areas.append(Area(AreaName.BOX, 0, -1, vec2(1788.0, -2300.0), vec2(-1788.0, -5120.0)))
    areas.append(Area(AreaName.WALL, 1, 0, vec2(3072.0, -2300.0), vec2(4096.0, 2300.0)))
    areas.append(Area(AreaName.WALL, -1, 0, vec2(-3072.0, -2300.0), vec2(-4096.0, 2300.0)))
    areas.append(Area(AreaName.HALF, 0, 1, vec2(3072.0, 0.0), vec2(-3072.0, 2300.0)))
    areas.append(Area(AreaName.HALF, 0, -1, vec2(3072.0, -2300.0), vec2(-3072.0, 0.0)))
    return areas
