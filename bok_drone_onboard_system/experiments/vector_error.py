import math
import sqlite3
from typing import Tuple

import numpy as np
from scipy.optimize import minimize

from bok_drone_onboard_system.positioner import Vector, vector_from_quaternion, Position


def read_quaternions(db_path, start: str, end: str):
    stmt = """select *
              from bno_data
              where timestamp >= ? and timestamp <= ? """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Makes rows behave like dicts
    cursor = conn.cursor()
    cursor.execute(stmt, (start, end))

    # Convert to list of dicts
    rows = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return rows


def spherical_to_cartesian(theta, phi):
    return (
        math.cos(phi) * math.sin(theta),
        math.sin(phi) * math.sin(theta),
        math.cos(theta)
    )


def cartesian_to_spherical(vs: Tuple[float, float, float]) -> Tuple[float, float]:
    x, y, z = vs
    r = math.sqrt(x ** 2 + y ** 2 + z ** 2)
    if r == 0:
        return 0.0, 0.0, 0.0  # undefined direction, just return zeros
    theta = math.acos(z / r)  # polar angle [0, π]
    phi = math.atan2(y, x)  # azimuth angle [-π, π]
    return theta, phi


def average_vector(vs: list[Vector]) -> Vector:
    n = len(vs)
    av = sum(vs)
    av /= n
    return av


def read_quaternions_between(start: str, end: str) -> list[Tuple[float, float, float, float]]:
    db_name = "storage/bno08x-rt-dev.db"
    return [(float(q['quat_i']), float(q['quat_j']), float(q['quat_k']), float(q['quat_real'])) for q in read_quaternions(db_name, start, end)]


def vectors_from_quaternions(quaternions: list[Tuple[float, float, float, float]], v_nat: Vector) -> list[Vector]:
    return [vector_from_quaternion((q[0], q[1], q[2], q[3]), v_nat) for q in quaternions]


def error_on_average(vectors: list[Vector], pole_length: float) -> Tuple[float, float]:
    v_avg = average_vector(vectors)
    p_0 = Position(0, 0, 0)
    p_avg = p_0 + v_avg * pole_length

    dists = [p_avg.distance_to(p_0 + v * pole_length) for v in vectors]
    return round(float(np.mean(dists)), 4), round(float(np.std(dists)), 4)


def optimal_v_nat(quats: list[Tuple[float, float, float, float]], v_init: Vector = Vector(1, 0, 0)) -> Vector:
    def abs_error(tp: Tuple[float, float]) -> float:
        vs = spherical_to_cartesian(tp[0], tp[1])
        v_nat = Vector(vs[0], vs[1], vs[2])
        vectors = vectors_from_quaternions(quats, v_nat=v_nat)

        avg_vect = average_vector(vectors)

        abs_error = 0
        for v in vectors:
            abs_error += avg_vect.colinearity(v)
        return abs_error

    initial_guess = cartesian_to_spherical((v_init.x, v_init.y, v_init.z))
    result = minimize(abs_error, initial_guess, method="Nelder-Mead")
    return Vector(*spherical_to_cartesian(result.x[0], result.x[1]))


if __name__ == "__main__":
    intervals = [
        ("2025-08-31T13:32:08", "2025-08-31T13:33:04"),
        ("2025-08-31T13:34:15", "2025-08-31T13:34:55"),
        ("2025-08-31T13:56:22", "2025-08-31T13:57:11"),
    ]

    calibration_int = 0
    print(f"calibration interval: {intervals[calibration_int]}")
    quats_calibration = read_quaternions_between(intervals[calibration_int][0], intervals[calibration_int][1])

    v_nat_0 = Vector(1, 0, 0)
    v_nat_opt = optimal_v_nat(quats_calibration, v_init=v_nat_0)

    print(f"optimal v_nat: {v_nat_opt}")

    for (i, interval) in enumerate(intervals):
        print(f"interval {i}: {interval}")
        quats = read_quaternions_between(interval[0], interval[1])

        vs_0 = vectors_from_quaternions(quats, v_nat_0)
        vs_opt = vectors_from_quaternions(quats, v_nat_opt)

        v_avg_0 = average_vector(vs_0)
        v_avg_opt = average_vector(vs_opt)
        len_pole = 2

        print(f"error on average {v_nat_0}: {error_on_average(vs_0, len_pole)}")
        print(f"error on otimized {v_nat_opt}: {error_on_average(vs_opt, len_pole)}")
