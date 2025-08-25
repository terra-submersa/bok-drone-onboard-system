import math

import numpy as np
from scipy.spatial.transform import Rotation as R


class Vector:
    x: float
    y: float
    z: float

    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y, self.z + other.z)
        return NotImplemented

    def __radd__(self, other):
        if other == 0:
            return self
        return self.__add__(other)

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return Vector(self.x / other, self.y / other, self.z / other)
        return NotImplemented


    def dot(self, other):
        return self.x*other.x + self.y*other.y + self.z*other.z

    def norm(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def colinearity(self, other) -> float:
        """
        0 if colinear, 1 perpendicular"""
        cos_theta = self.dot(other) / (self.norm() * other.norm())
        return 1 - abs(cos_theta)


    @property
    def np(self):
        return np.array([self.x, self.y, self.z])

    def __repr__(self):
        return f"V\t{self.x:+.4f}\t{self.y:+.4f}\t{self.z:+.4f}"


def vector_from_quaternion(q, local_direction: Vector) -> Vector:
    rotation = R.from_quat(q)
    v_local = local_direction.np
    v_world = rotation.apply(v_local)
    return Vector(*v_world)


class Position:
    x: float
    y: float
    z: float

    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def plus(self, v: Vector):
        return Position(self.x + v.x, self.y + v.y, self.z + v.z)

    @property
    def np(self):
        return np.array([self.x, self.y, self.z])

    def __repr__(self):
        return f"P\t{self.x:+.3f}\t{self.y:+.3f}\t{self.z:+.3f}"
