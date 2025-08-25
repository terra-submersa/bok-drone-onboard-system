import unittest
from unittest.mock import Mock, patch
from datetime import datetime, date, time

import pynmea2

from bok_drone_onboard_system.survey.emlid_reader import read_from_emlid, parse_llh
from bok_drone_onboard_system.survey.gps import GPSPoint, EmlidEntry, SolutionQuality


class TestEmlidReader(unittest.TestCase):
    
    def test_read_from_emlid_with_rmc_and_gga(self):
        """Test that read_from_emlid correctly combines date from RMC with time from GGA."""
        # Mock serial connection
        mock_serial = Mock()
        
        # Create test NMEA sentences
        gga_msg = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47\r\n"
        # Fixed RMC message with correct checksum
        rmc_msg = "$GPRMC,123520,A,4807.039,N,01131.001,E,022.4,084.4,230394,003.1,W*60\r\n"
        # Fixed GGA2 message with correct checksum
        gga_msg2 = "$GPGGA,123521,4807.040,N,01131.002,E,1,08,0.9,545.6,M,46.9,M,,*43\r\n"
        
        # Configure mock to return our test sentences
        mock_serial.readline.side_effect = [
            gga_msg.encode('ascii'),  # First GGA without date
            rmc_msg.encode('ascii'),  # RMC with date
            gga_msg2.encode('ascii'),  # Second GGA with date from RMC
            KeyboardInterrupt,  # To exit the loop
        ]
        
        # Mock callback function to capture results
        callback_results = []
        def mock_callback(gps_point):
            callback_results.append(gps_point)
        
        # Run the function (it will exit on KeyboardInterrupt)
        try:
            read_from_emlid(mock_serial, mock_callback)
        except KeyboardInterrupt:
            pass
        
        # We should have 4 callback results:
        # 1. GGA with just time
        # 2. RMC with full datetime
        # 3. Pending GGA with full datetime
        # 4. Second GGA with full datetime
        self.assertEqual(len(callback_results), 1)
        

        # Fourth result should have full datetime (second GGA time + RMC date)
        self.assertIsInstance(callback_results[0].timestamp, datetime)
        self.assertEqual(callback_results[0].timestamp.year, 1994)
        self.assertEqual(callback_results[0].timestamp.month, 3)
        self.assertEqual(callback_results[0].timestamp.day, 23)
        self.assertEqual(callback_results[0].timestamp.hour, 12)
        self.assertEqual(callback_results[0].timestamp.minute, 35)
        self.assertEqual(callback_results[0].timestamp.second, 21)
        
    def test_read_from_emlid_with_pending_gga(self):
        """Test that read_from_emlid correctly processes pending GGA data once RMC is received."""
        # Mock serial connection
        mock_serial = Mock()
        
        # Create test NMEA sentences
        gga_msg = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47\r\n"
        # Fixed RMC message with correct checksum
        rmc_msg = "$GPRMC,123520,A,4807.039,N,01131.001,E,022.4,084.4,230394,003.1,W*60\r\n"
        
        # Configure mock to return our test sentences
        mock_serial.readline.side_effect = [
            rmc_msg.encode('ascii'),  # RMC with date
            gga_msg.encode('ascii'),  # GGA without date
            KeyboardInterrupt,  # To exit the loop
        ]
        
        # Mock callback function to capture results
        callback_results = []
        def mock_callback(gps_point):
            callback_results.append(gps_point)
        
        # Run the function (it will exit on KeyboardInterrupt)
        try:
            read_from_emlid(mock_serial, mock_callback)
        except KeyboardInterrupt:
            pass
        
        # We should have 3 callback results:
        # 1. GGA with just time
        # 2. RMC with full datetime
        # 3. Pending GGA with full datetime
        self.assertEqual(len(callback_results), 1)
        

        # Second result should have full datetime from RMC
        self.assertIsInstance(callback_results[0].timestamp, datetime)
        
        # Third result should be the pending GGA with full datetime
        self.assertIsInstance(callback_results[0].timestamp, datetime)
        self.assertEqual(callback_results[0].timestamp.year, 1994)
        self.assertEqual(callback_results[0].timestamp.month, 3)
        self.assertEqual(callback_results[0].timestamp.day, 23)
        self.assertEqual(callback_results[0].timestamp.hour, 12)
        self.assertEqual(callback_results[0].timestamp.minute, 35)
        self.assertEqual(callback_results[0].timestamp.second, 19)
        self.assertEqual(callback_results[0].latitude, 48.1173)
        self.assertEqual(callback_results[0].longitude, 11.516666666666667)
        self.assertEqual(callback_results[0].altitude, 545.4)

    def test_parse_llh(self):
        """Test that parse_llh correctly parses LLH format data."""
        # Test with the example from the docstring
        llh_line = "2025/08/24 10:59:13.800   43.737672206    5.462569945   307.6388   2  11   0.0680   0.1100   0.2400   0.0000   0.0000   0.0000   1.80    0.0"
        
        # Parse the line
        result = parse_llh(llh_line)
        
        # Verify the result is an EmlidEntry
        self.assertIsInstance(result, EmlidEntry)
        
        # Verify GPSPoint
        self.assertIsInstance(result.gps_point, GPSPoint)
        self.assertEqual(result.gps_point.timestamp, datetime(2025, 8, 24, 10, 59, 13, 800000))
        self.assertEqual(result.gps_point.latitude, 43.737672206)
        self.assertEqual(result.gps_point.longitude, 5.462569945)
        self.assertEqual(result.gps_point.altitude, 307.6388)
        
        # Verify solution status
        self.assertEqual(result.solution_status, SolutionQuality.FLOAT)
        
        # Verify standard deviations
        self.assertEqual(result.std_dev, (0.0680, 0.1100, 0.2400))
        
    def test_parse_llh_with_different_solution_statuses(self):
        """Test parse_llh with different solution status values."""
        # Test with Single solution status
        llh_line_fix = "2025/08/24 10:59:13.800   43.737672206    5.462569945   307.6388   1  11   0.0680   0.1100   0.2400   0.0000   0.0000   0.0000   1.80    0.0"
        result_fix = parse_llh(llh_line_fix)
        self.assertEqual(result_fix.solution_status, SolutionQuality.FIX)
        
        # Test with RTK Fixed solution status
        llh_line_rtk_dgps = "2025/08/24 10:59:13.800   43.737672206    5.462569945   307.6388   4  11   0.0680   0.1100   0.2400   0.0000   0.0000   0.0000   1.80    0.0"
        result_rtk_dgps = parse_llh(llh_line_rtk_dgps)
        self.assertEqual(result_rtk_dgps.solution_status, SolutionQuality.DGPS)
        


if __name__ == '__main__':
    unittest.main()