"""
Tests for GPS coordinate conversion utilities.
"""
import unittest
from parameterized import parameterized
import pyproj
from bok_drone_onboard_system.survey.gps import GPSPoint
from bok_drone_onboard_system.survey.analysis.gps import wgs84_to_utm34n


class TestGPSConversion(unittest.TestCase):
    """Test cases for GPS coordinate conversion functions."""

    @parameterized.expand([
        # Test case 1: Oslo, Norway (well within UTM zone 34N)
        # latitude, longitude, altitude, expected_x, expected_y
        (59.9139, 10.7522, 100.0, -71552.3, 6686227.6),
        # Test case 2: Kyiv, Ukraine (also in UTM zone 34N)
        (50.4501, 30.5234, 200.0, 1175521.9, 5632147.3),
        # Test case 3: Near the edge of zone 34N
        (55.0, 35.9, 300.0, 1449355.0, 6196864.5),
    ])
    def test_wgs84_to_utm34n(self, latitude, longitude, altitude, expected_x, expected_y):
        """Test the conversion from WGS84 to UTM zone 34N."""
        # Create a GPSPoint with test coordinates
        gps_point = GPSPoint(timestamp=0, latitude=latitude, longitude=longitude, altitude=altitude)
        
        # Convert using our function
        x, y, z = wgs84_to_utm34n(gps_point)
        
        # Verify the conversion is correct
        self.assertAlmostEqual(x, expected_x, delta=1.0)  # Allow 1 meter difference
        self.assertAlmostEqual(y, expected_y, delta=1.0)  # Allow 1 meter difference
        self.assertEqual(z, altitude)  # Altitude should remain unchanged
        
    def test_wgs84_to_utm34n_matches_pyproj_direct(self):
        """Test that our conversion matches direct pyproj conversion."""
        # Create test points
        test_points = [
            GPSPoint(timestamp=0, latitude=60.0, longitude=20.0, altitude=100.0),
            GPSPoint(timestamp=0, latitude=55.0, longitude=25.0, altitude=200.0),
            GPSPoint(timestamp=0, latitude=50.0, longitude=30.0, altitude=300.0),
        ]
        
        # Create a transformer directly for comparison
        wgs84 = pyproj.CRS.from_epsg(4326)  # WGS84
        utm34n = pyproj.CRS.from_epsg(32634)  # UTM zone 34N
        transformer = pyproj.Transformer.from_crs(wgs84, utm34n, always_xy=True)
        
        for point in test_points:
            # Convert using our function
            x1, y1, z1 = wgs84_to_utm34n(point)
            
            # Convert using pyproj directly
            x2, y2 = transformer.transform(point.longitude, point.latitude)
            
            # Compare results
            self.assertAlmostEqual(x1, x2, delta=0.001)  # Should be very close
            self.assertAlmostEqual(y1, y2, delta=0.001)  # Should be very close
            self.assertEqual(z1, point.altitude)  # Altitude should remain unchanged


if __name__ == '__main__':
    unittest.main()