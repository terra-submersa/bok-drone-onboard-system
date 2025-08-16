import sqlite3
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from parameterized import parameterized

from bok_drone_onboard_system.survey import SurveyMeasure
from bok_drone_onboard_system.survey.data import load_data, create_table_if_not_exists, TABLE_NAME
from bok_drone_onboard_system.survey.gps import GPSPoint


class TestLoadData(unittest.TestCase):
    def setUp(self):
        # Create in-memory database for testing
        self.conn = sqlite3.connect(":memory:")
        create_table_if_not_exists(self.conn)
        
        # Sample data for testing
        self.now = datetime.now()
        self.sample_data = [
            (self.now - timedelta(hours=2), (0.1, 0.2, 0.3, 0.4), 10.1, 20.1, 100.1),  # 2 hours ago
            (self.now - timedelta(hours=1), (0.2, 0.3, 0.4, 0.5), 10.2, 20.2, 100.2),  # 1 hour ago
            (self.now, (0.3, 0.4, 0.5, 0.6), 10.3, 20.3, 100.3),                       # now
            (self.now + timedelta(hours=1), (0.4, 0.5, 0.6, 0.7), 10.4, 20.4, 100.4),  # 1 hour from now
        ]
        
        # Insert sample data
        for timestamp, quat, lat, lon, alt in self.sample_data:
            self.conn.execute(
                f"INSERT INTO {TABLE_NAME} (timestamp, quat_i, quat_j, quat_k, quat_real, gps_lat, gps_lon, gps_alt) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (timestamp.isoformat(timespec='milliseconds'), *quat, lat, lon, alt)
            )
        self.conn.commit()
        
        # Sample with None values for testing only_defined parameter
        self.conn.execute(
            f"INSERT INTO {TABLE_NAME} (timestamp, quat_i, quat_j, quat_k, quat_real, gps_lat, gps_lon, gps_alt) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ((self.now + timedelta(minutes=30)).isoformat(timespec='milliseconds'), None, None, None, None, 10.5, 20.5, 100.5)
        )
        self.conn.commit()
    
    def tearDown(self):
        self.conn.close()
    
    def test_load_all_data(self):
        """Test loading all data without filters"""
        results = load_data(self.conn, None, None)
        
        # Should return 5 records (4 complete + 1 with None quaternion)
        self.assertEqual(len(results), 5)
        
        # Verify first record
        first = results[0]
        self.assertIsInstance(first, SurveyMeasure)
        self.assertEqual(first.gps_Point.latitude, 10.1)
        self.assertEqual(first.gps_Point.longitude, 20.1)
        self.assertEqual(first.gps_Point.altitude, 100.1)
        self.assertEqual(first.bno_quaternion, (0.1, 0.2, 0.3, 0.4))
    
    @parameterized.expand([
        ("start_only", timedelta(hours=-1.5), None, 4),  # From 1.5 hours ago to now (includes the None record)
        ("end_only", None, timedelta(hours=-0.5), 2),    # From beginning to 0.5 hours ago
        ("start_and_end", timedelta(hours=-1.5), timedelta(hours=0.5), 2),  # From 1.5 hours ago to 0.5 hours from now
    ])
    def test_load_data_with_time_filters(self, name, start_delta, end_delta, expected_count):
        """Test loading data with different time filters"""
        start = None if start_delta is None else self.now + start_delta
        end = None if end_delta is None else self.now + end_delta
        
        results = load_data(self.conn, start, end)
        self.assertEqual(len(results), expected_count)
    
    def test_load_data_only_defined(self):
        """Test loading only defined data (with both GPS and BNO data)"""
        results = load_data(self.conn, None, None, only_defined=True)
        
        # Should return all records with defined quaternions (excluding the one with None quaternion)
        # We have 4 records with complete data
        self.assertEqual(len(results), 4)
        
        # Verify all records have defined GPS and BNO data
        for measure in results:
            self.assertTrue(measure.is_defined())
    
    @patch('bok_drone_onboard_system.survey.SurveyMeasure.is_defined')
    def test_only_defined_logic(self, mock_is_defined):
        """Test that only_defined parameter correctly filters results"""
        # Make is_defined() return False for all measures
        mock_is_defined.return_value = False
        
        # With only_defined=True, should return empty list
        results = load_data(self.conn, None, None, only_defined=True)
        self.assertEqual(len(results), 0)
        
        # With only_defined=False, should return all records
        results = load_data(self.conn, None, None, only_defined=False)
        self.assertEqual(len(results), 5)


if __name__ == '__main__':
    unittest.main()