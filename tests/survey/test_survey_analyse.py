import os
import tempfile
from datetime import datetime
from unittest import TestCase

import numpy as np
from parameterized import parameterized

from bok_drone_onboard_system.survey_analyse import plot_projected_measures


class TestSurveyAnalyse(TestCase):
    def setUp(self):
        # Create a temporary directory for test outputs
        self.test_dir = tempfile.mkdtemp()

    def create_test_data(self, num_points=10):
        """Create test data for plotting"""
        projected_measures = []
        
        # Create a base timestamp
        base_timestamp = datetime(2025, 8, 16, 14, 5, 0)
        
        # Create a grid of points
        for i in range(num_points):
            # Create timestamp with increasing seconds
            timestamp = base_timestamp.replace(second=base_timestamp.second + i)
            
            # Create UTM coordinates (GPS position)
            utm_x = 500000.0 + i * 0.5  # 0.5m spacing
            utm_y = 4000000.0 + i * 0.5
            utm_z = 100.0
            utm_coords = (utm_x, utm_y, utm_z)
            
            # Create pole end position (1m away in x direction)
            pole_x = utm_x + 1.0
            pole_y = utm_y
            pole_z = utm_z
            pole_position = (pole_x, pole_y, pole_z)
            
            projected_measures.append((timestamp, utm_coords, pole_position))
        
        return projected_measures

    def test_plot_projected_measures_empty_data(self):
        """Test plotting with empty data"""
        output_file = os.path.join(self.test_dir, "empty_plot.png")
        
        # Call function with empty data
        plot_projected_measures([], output_file)
        
        # File should not be created since there's no data to plot
        self.assertFalse(os.path.exists(output_file))

    def test_plot_projected_measures_single_point(self):
        """Test plotting with a single data point"""
        output_file = os.path.join(self.test_dir, "single_point_plot.png")
        
        # Create a single data point
        timestamp = datetime(2025, 8, 16, 14, 5, 0)
        utm_coords = (500000.0, 4000000.0, 100.0)
        pole_position = (500001.0, 4000000.0, 100.0)
        data = [(timestamp, utm_coords, pole_position)]
        
        # Plot the data
        plot_projected_measures(data, output_file)
        
        # Check that the file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Check that the file has content (size > 0)
        self.assertGreater(os.path.getsize(output_file), 0)

    def test_plot_projected_measures_multiple_points(self):
        """Test plotting with multiple data points"""
        output_file = os.path.join(self.test_dir, "multiple_points_plot.png")
        
        # Create test data with 10 points
        data = self.create_test_data(10)
        
        # Plot the data
        plot_projected_measures(data, output_file)
        
        # Check that the file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Check that the file has content (size > 0)
        self.assertGreater(os.path.getsize(output_file), 0)

    @parameterized.expand([
        ("small_scale", 0.5, "10 cm"),  # Small scale (< 1m)
        ("medium_scale", 5.0, "1 m"),   # Medium scale (1-10m)
        ("large_scale", 50.0, "10 m"),  # Large scale (>10m)
    ])
    def test_plot_projected_measures_different_scales(self, name, spacing, expected_scale):
        """Test plotting with different scales"""
        output_file = os.path.join(self.test_dir, f"{name}_plot.png")
        
        # Create test data with different spacing between points
        projected_measures = []
        base_timestamp = datetime(2025, 8, 16, 14, 5, 0)
        
        for i in range(5):
            timestamp = base_timestamp.replace(second=base_timestamp.second + i)
            utm_x = 500000.0 + i * spacing
            utm_y = 4000000.0 + i * spacing
            utm_z = 100.0
            utm_coords = (utm_x, utm_y, utm_z)
            
            pole_x = utm_x + spacing/10  # Pole end is spacing/10 away
            pole_y = utm_y
            pole_z = utm_z
            pole_position = (pole_x, pole_y, pole_z)
            
            projected_measures.append((timestamp, utm_coords, pole_position))
        
        # Plot the data
        plot_projected_measures(projected_measures, output_file)
        
        # Check that the file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Check that the file has content (size > 0)
        self.assertGreater(os.path.getsize(output_file), 0)
        
        # Note: We can't easily check the scale text in the image programmatically
        # This would require image processing or OCR, which is beyond the scope of this test