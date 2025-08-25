import math
import sqlite3
from typing import Tuple
from scipy.optimize import minimize

from bok_drone_onboard_system.positioner import Vector, vector_from_quaternion


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


if __name__ == "__main__":
    db_name = "storage/bno08x-rt-prod.db"
    quats = read_quaternions(db_name, "2025-08-24T14:41:45", "2025-08-24T14:42:06")

    v_nat_0 = Vector(1, 0, 0)


    def abs_error(tp: Tuple[float, float]) -> float:
        vs = spherical_to_cartesian(tp[0], tp[1])
        v_nat = Vector(vs[0], vs[1], vs[2])
        vectors = [vector_from_quaternion((q['quat_i'], q['quat_j'], q['quat_k'], q['quat_real']), v_nat) for q in quats]
        n = len(vectors)
        avg_vect = sum(vectors)
        avg_vect /= n
        print(f"average: {avg_vect}")

        abs_error = 0
        for v in vectors:
            abs_error += avg_vect.colinearity(v)
        return abs_error


    vectors = [vector_from_quaternion((q['quat_i'], q['quat_j'], q['quat_k'], q['quat_real']), v_nat_0) for q in quats]
    n = len(vectors)
    avg_vect = sum(vectors)
    avg_vect /= n
    print(f"average: {avg_vect}")
    for v in vectors:
        print(v)

    print(f"error = {abs_error(cartesian_to_spherical((1, 0, 0)))}")

    initial_guess = cartesian_to_spherical((1, 0, 0))

    result = minimize(abs_error, initial_guess, method="Nelder-Mead")

    print("Best vs:", result.x)
    print(spherical_to_cartesian(result.x[0], result.x[1]))
    print("Minimum error:", result.fun)
