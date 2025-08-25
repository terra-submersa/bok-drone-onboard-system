import unittest
from datetime import datetime
import pyproj
from bok_drone_onboard_system.survey.gps import GPSPoint


class TestGPSPoint(unittest.TestCase):
    def test_distance_to_same_point(self):
        """Test that distance to the same point is very close to zero."""
        point = GPSPoint(
            timestamp=datetime.now(),
            latitude=45.0,
            longitude=10.0,
            altitude=100.0
        )
        
        distance = point.distance_to(point)
        # Due to floating point precision, the distance might not be exactly 0.0
        # but should be very close to it
        self.assertAlmostEqual(distance, 0.0, delta=1e-9)
    
    def test_distance_to_known_points(self):
        """Test distance calculation with known points and distances."""
        # Test cases with known points and expected distances
        test_cases = [
            # Paris to London (about 344 km)
            {
                "point1": GPSPoint(
                    timestamp=datetime.now(),
                    latitude=48.8566,
                    longitude=2.3522,
                    altitude=0
                ),
                "point2": GPSPoint(
                    timestamp=datetime.now(),
                    latitude=51.5074,
                    longitude=-0.1278,
                    altitude=0
                ),
                "expected_distance": 344000,  # meters
                "tolerance": 1000  # 1 km tolerance
            },
            # New York to Los Angeles (about 3944 km)
            {
                "point1": GPSPoint(
                    timestamp=datetime.now(),
                    latitude=40.7128,
                    longitude=-74.0060,
                    altitude=0
                ),
                "point2": GPSPoint(
                    timestamp=datetime.now(),
                    latitude=34.0522,
                    longitude=-118.2437,
                    altitude=0
                ),
                "expected_distance": 3944000,  # meters
                "tolerance": 5000  # 5 km tolerance
            },
            # Short distance (about 1 km)
            {
                "point1": GPSPoint(
                    timestamp=datetime.now(),
                    latitude=45.0,
                    longitude=10.0,
                    altitude=0
                ),
                "point2": GPSPoint(
                    timestamp=datetime.now(),
                    latitude=45.009,
                    longitude=10.0,
                    altitude=0
                ),
                "expected_distance": 1000,  # meters
                "tolerance": 10  # 10 m tolerance
            }
        ]
        
        for test_case in test_cases:
            point1 = test_case["point1"]
            point2 = test_case["point2"]
            expected = test_case["expected_distance"]
            tolerance = test_case["tolerance"]
            
            distance = point1.distance_to(point2)
            
            self.assertAlmostEqual(
                distance, 
                expected, 
                delta=tolerance,
                msg=f"Distance between {point1} and {point2} should be approximately {expected} meters"
            )
    
    def test_distance_to_matches_pyproj_direct(self):
        """Test that our distance calculation matches direct pyproj calculation."""
        point1 = GPSPoint(
            timestamp=datetime.now(),
            latitude=45.0,
            longitude=10.0,
            altitude=100.0
        )
        
        point2 = GPSPoint(
            timestamp=datetime.now(),
            latitude=46.0,
            longitude=11.0,
            altitude=200.0
        )
        
        # Calculate distance using our method
        distance = point1.distance_to(point2)
        
        # Calculate distance using pyproj directly
        geod = pyproj.Geod(ellps="WGS84")
        _, _, direct_distance = geod.inv(
            point1.longitude, point1.latitude,
            point2.longitude, point2.latitude
        )
        
        # The distances should be exactly the same
        self.assertEqual(distance, direct_distance)


if __name__ == "__main__":
    unittest.main()