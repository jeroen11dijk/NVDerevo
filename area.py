from enum import Enum

from RLUtilities.LinearAlgebra import vec2, vec3


class AreaName(Enum):
    CORNER = 1
    BOX = 2
    WALL = 3
    HALF = 4


class Area:

    def __init__(self, name: AreaName, corner1: vec2, corner2: vec2):
        self.name = name
        self.min_x = min(corner1[0], corner2[0])
        self.max_x = max(corner1[0], corner2[0])
        self.min_y = min(corner1[1], corner2[1])
        self.max_y = max(corner1[1], corner2[1])

    def __str__(self):
        return str(self.name)

    def is_inside(self, point: vec3):
        return self.min_x <= point[0] <= self.max_x and self.min_y <= point[1] <= self.max_y
