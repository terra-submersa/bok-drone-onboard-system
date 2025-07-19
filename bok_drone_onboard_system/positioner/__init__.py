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

    @property
    def np(self):
        return np.array([self.x, self.y, self.z])

    def __repr__(self):
        return f"V\t{self.x:+.3f}\t{self.y:+.3f}\t{self.z:+.3f}"


def vector_from_quaternion(q, local_direction: Vector)-> Vector:
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


