from unittest import TestCase

import numpy as np
from parameterized import parameterized

from bok_drone_onboard_system.positioner import Vector, Position
from bok_drone_onboard_system.positioner.projector import calculate_pole_end_position
from tests.positioner.test_resources import load_quaternions


class ProjectorTest(TestCase):
    def test_calculate_pole_end_position_vertical(self):
        """Test with a vertical pole pointing straight up"""
        # Quaternion representing no rotation (identity)
        quaternion = (0.0, 0.0, 0.0, 1.0)
        utm_position = (100.0, 200.0, 50.0)
        pole_length = 2.0
        
        # Expected position: 2 meters in the x direction (based on v_nat = Vector(1, 0, 0))
        expected = (102.0, 200.0, 50.0)
        
        result = calculate_pole_end_position(quaternion, utm_position, pole_length)
        
        # Check each coordinate with a small tolerance
        for i in range(3):
            self.assertAlmostEqual(result[i], expected[i], places=5)
    
    def test_calculate_pole_end_position_45_degrees(self):
        """Test with a pole at 45 degrees in the x-z plane"""
        # Quaternion representing 45 degree rotation around y-axis
        # This rotates the x-axis 45 degrees up in the z direction
        quaternion = (0.0, 0.3826834, 0.0, 0.9238795)  # sin(45°/2), cos(45°/2)
        utm_position = (100.0, 200.0, 50.0)
        pole_length = 2.0
        
        result = calculate_pole_end_position(quaternion, utm_position, pole_length)
        
        # Verify the distance between points A and B is equal to pole_length
        position_a = np.array(utm_position)
        position_b = np.array(result)
        distance = np.linalg.norm(position_b - position_a)
        self.assertAlmostEqual(distance, pole_length, places=5)
        
        # Verify the direction is approximately 45 degrees in the x-z plane
        # The y coordinate should remain unchanged
        self.assertAlmostEqual(result[1], utm_position[1], places=5)
        
        # The change in x and z should be approximately equal
        dx = result[0] - utm_position[0]
        dz = result[2] - utm_position[2]
        self.assertAlmostEqual(abs(dx), abs(dz), delta=0.1)
    
    def test_calculate_pole_end_position_with_samples(self):
        """Test with sample quaternions from test resources"""
        # Test cases with sample files
        test_cases = [
            "flat-east.txt",
            "flat-north.txt",
            "flat-south.txt",
            "90-north.txt",
            "45-north.txt",
            "45-east.txt",
            "45-south.txt"
        ]
        
        for fname in test_cases:
            # Load sample quaternions
            quaternions = load_quaternions(fname)
            
            # Use the first quaternion from the sample
            quaternion = quaternions[0]
            utm_position = (100.0, 200.0, 50.0)
            pole_length = 2.0
            
            # Calculate the position at end B
            result = calculate_pole_end_position(quaternion, utm_position, pole_length)
            
            # Verify that the result is a valid position
            # The distance between position A and B should be approximately equal to pole_length
            position_a = np.array(utm_position)
            position_b = np.array(result)
            distance = np.linalg.norm(position_b - position_a)
            
            # Check that the distance is close to the pole length
            self.assertAlmostEqual(distance, pole_length, delta=0.01,
                                  msg=f"Distance between A and B should be {pole_length} for {fname}")