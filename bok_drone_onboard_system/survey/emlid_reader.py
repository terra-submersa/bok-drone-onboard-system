import logging
import re
import sys
import socket
from typing import Callable, Generator
from datetime import datetime

import pynmea2
from serial.tools import list_ports
from serial import Serial

from bok_drone_onboard_system.survey.gps import GPSPoint, EmlidEntry, SolutionQuality

logger = logging.getLogger(__name__)


def stream_from_emlid_llh(host: str, port: int) -> Generator[EmlidEntry, None, None]:
    encoding = "ascii"
    with socket.create_connection((host, port), timeout=3) as sock:
        # make a buffered, file-like wrapper so we can .readline()
        f = sock.makefile("rb", buffering=1)  # line-buffered
        for raw in f:
            line = raw.rstrip(b"\r\n").decode(encoding, errors="replace")
            if not line:
                continue
            yield parse_llh(line)


def read_from_emlid(connection: Serial, callback: Callable):
    """
    Read NMEA2 data from EMLID device via serial connection and print lat, lon, altitude and precise time.
    Uses RMC messages to get date information and combines it with GGA messages for complete timestamp.
    
    The function processes both GGA and RMC NMEA messages:
    - GGA messages provide time, latitude, longitude, and altitude
    - RMC messages provide date information along with time and position
    
    When an RMC message is received, its date information is stored and used to create
    full datetime objects for subsequent GGA messages. If a GGA message is received before
    any RMC message, it's stored temporarily and processed once date information becomes available.

    Args:
        connection: Serial connection to the EMLID device
        callback: Callable function to process the GPS data
    """
    try:
        # Store the latest date from RMC messages
        latest_date = None

        while True:
            # Read a line from the serial connection
            line = connection.readline().decode('ascii', errors='replace').strip()

            # Skip empty lines
            if not line:
                continue

            # Try to parse the NMEA sentence
            try:
                msg = pynmea2.parse(line)

                # RMC message contains date information
                if isinstance(msg, pynmea2.RMC):
                    latest_date = msg.datestamp


                # GGA message contains latitude, longitude, and altitude
                elif isinstance(msg, pynmea2.GGA):
                    if latest_date:
                        # Combine date from RMC with time from GGA
                        full_datetime = datetime.combine(latest_date, msg.timestamp)
                        callback(GPSPoint(full_datetime, msg.latitude, msg.longitude, msg.altitude))

            except pynmea2.ParseError:
                # Skip lines that can't be parsed
                continue

    except KeyboardInterrupt as e:
        print("Stopping EMLID data reading")
        raise e
    except Exception as e:
        print(f"Error reading from EMLID: {e}")
        raise e


def _split_llh_line(line: str) -> list:
    """
    Split an LLH line into its components, handling the special case of timestamp with space.
    
    Args:
        line: The LLH line to split
        
    Returns:
        List of parts from the LLH line
    """
    # Split the line by multiple spaces
    parts = [part for part in re.split(r'\s+', line) if part]

    # Handle the special case of timestamp with space
    if len(parts) > 14:  # If we have more parts than expected, the timestamp has a space
        date_str = parts[0]
        time_str = parts[1]
        timestamp_str = f"{date_str} {time_str}"
        # Shift the parts list to account for the split timestamp
        parts = [timestamp_str] + parts[2:]

    return parts


def _parse_gps_point(parts: list) -> GPSPoint:
    """
    Parse GPS point information from LLH line parts.
    
    Args:
        parts: List of parts from the LLH line
        
    Returns:
        GPSPoint object with timestamp, latitude, longitude, and altitude
    """
    # Parse timestamp
    timestamp = datetime.strptime(parts[0], "%Y/%m/%d %H:%M:%S.%f")

    # Parse coordinates
    latitude = float(parts[1])
    longitude = float(parts[2])
    height = float(parts[3])

    return GPSPoint(timestamp, latitude, longitude, height)


def _parse_solution_status(parts: list) -> SolutionQuality:
    """
    Parse solution status from LLH line parts.
    
    Args:
        parts: List of parts from the LLH line
        
    Returns:
        SolutionQuality enum value
    """
    solution_status_value = int(parts[4])
    return SolutionQuality.from_value(solution_status_value)


def _parse_std_dev(parts: list) -> tuple:
    """
    Parse standard deviations from LLH line parts.
    
    Args:
        parts: List of parts from the LLH line
        
    Returns:
        Tuple of standard deviations (sdn, sde, sdu)
    """
    return (float(parts[6]), float(parts[7]), float(parts[8]))


def parse_llh(line: str) -> EmlidEntry:
    """
    Parse a line of EMLID data from LLH format
    An LLH linbe line contains the estimated receiver position in Latitude–Longitude–Height (LLH) coordinates, separated by multiple spaces (except for timstampe, which comes with milliseonds as, for example, "2025/08/24 10:59:13.800".
    <time>   <latitude>   <longitude>   <height>   <Q>   <ns>   <sdn>   <sde>   <sdu>   <sdne>   <sdeu>   <sdun>   <age>   <ratio>
    Meaning of Each Field
	1.	time – GPS time
	2.	latitude – latitude in degrees
	3.	longitude – longitude in degrees
	4.	height – ellipsoidal height in meters
	5.	Q – solution status:
	•	1 = Single
	•	2 = DGPS
	•	4 = RTK Fixed
	•	5 = RTK Float
	6.	ns – number of satellites used in solution
	7.	sdn, sde, sdu – standard deviations of latitude, longitude, and height (m)
	8.	sdne, sdeu, sdun – covariance terms (m²)
	9.	age – age of differential (s), for RTK solutions
	10.	ratio – ambiguity resolution ratio factor (higher = more reliable fix)

    Example
    2025/08/24 10:59:13.800   43.737672206    5.462569945   307.6388   2  11   0.0680   0.1100   0.2400   0.0000   0.0000   0.0000   1.80    0.0
    """
    parts = _split_llh_line(line)
    gps_point = _parse_gps_point(parts)
    solution_status = _parse_solution_status(parts)
    std_dev = _parse_std_dev(parts)

    return EmlidEntry(gps_point, std_dev, solution_status)


def find_emlid_device():
    return "/dev/cu.tsreachrover"
    """
    Find the EMLID device USB file descriptor on both macOS and Raspberry Pi.

    Returns:
        str: Path to the EMLID device or None if not found
    """
    # Get all available serial ports
    ports = list(list_ports.comports())

    # EMLID devices typically appear as:
    # - macOS: /dev/tty.usbmodem* or /dev/cu.usbmodem*
    # - Raspberry Pi: /dev/ttyACM* or /dev/ttyUSB*

    # Check if we're on macOS or Raspberry Pi
    is_macos = sys.platform == 'darwin'
    is_raspberry_pi = sys.platform == 'linux' and 'arm' in sys.platform

    # Define patterns to look for based on platform
    if is_macos:
        patterns = [r'(tty|cu)\.usbmodem']
    elif is_raspberry_pi:
        patterns = [r'ttyACM', r'ttyUSB']
    else:
        # For other platforms, try both patterns
        patterns = [r'(tty|cu)\.usbmodem', r'ttyACM', r'ttyUSB']

    # Try to find EMLID device by checking device names
    emlid_ports = []
    for port in ports:
        # Check if the port matches any of our patterns
        for pattern in patterns:
            if re.search(pattern, port.device):
                # If the device has "emlid" in its description or hardware ID, it's very likely our device
                if hasattr(port, 'description') and 'emlid' in port.description.lower():
                    return port.device
                if hasattr(port, 'hwid') and 'emlid' in port.hwid.lower():
                    return port.device

                # Otherwise, add it to potential candidates
                emlid_ports.append(port.device)

    # If we found any potential candidates, return the first one
    if emlid_ports:
        logger.info(f"Found EMLID device at: {emlid_ports[0]}")
        return emlid_ports[0]

    # No EMLID device found
    logger.info("No EMLID device found. Please check the connection.")
    return None
