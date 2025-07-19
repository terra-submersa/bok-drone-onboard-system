from unittest import TestCase

import numpy as np
from parameterized import parameterized

from bok_drone_onboard_system.positioner import Vector, vector_from_quaternion
from tests.positioner.test_resources import load_quaternions


class PositionerTest(TestCase):
    @staticmethod
    def average_from_sample(fname):
        given_quats = load_quaternions(fname)
        given_v_nat = Vector(1, 0, 0)

        vs = []
        for q in given_quats:
            vs.append(vector_from_quaternion(q, given_v_nat).np)

        stacked = np.stack(vs)
        means = np.mean(stacked, axis=0)
        stds = np.std(stacked, axis=0)
        return {
            'filename': fname,
            'means': means,
            'stddevs': stds
        }
        print(fname)
        print("\t".join(f'{t:+.3f}' for t in means))
        print("\t".join(f'{t:+.3f}' for t in stds))

    @parameterized.expand([
        "45-east.txt",
        "45-north.txt",
        "45-south.txt",
        "90-east.txt",
        "90-north.txt",
        "135-north.txt",
        "flat-east.txt",
        "flat-north.txt",
        "flat-south.txt",
    ])
    def test_vector_from_quaternion_45_east(self, fname):
        self.average_from_sample(fname)

        for i in range(3):
            self.assertLessEqual(self.average_from_sample(fname)['stddevs'][i], 0.05)
