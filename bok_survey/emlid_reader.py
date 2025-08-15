import re
import sys
from typing import Callable

import pynmea2
from  serial.tools import list_ports
from serial import Serial


class GPSPoint:
    def __init__(self, timestamp, latitude, longitude, altitude):
        self.timestamp = timestamp
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude

    def __repr__(self):
        return f"timestamp={self.timestamp}, latitude={self.latitude}, longitude={self.longitude}, altitude={self.altitude}"


def read_from_emlid(connection: Serial, callback: Callable):
    """
    Read NMEA2 data from EMLID device via serial connection and print lat, lon, altitude and precise time.

    Args:
        connection: Serial connection to the EMLID device
    """
    try:
        while True:
            # Read a line from the serial connection
            line = connection.readline().decode('ascii', errors='replace').strip()

            # Skip empty lines
            if not line:
                continue

            # Try to parse the NMEA sentence
            try:
                msg = pynmea2.parse(line)

                # GGA message contains latitude, longitude, and altitude
                if isinstance(msg, pynmea2.GGA):
                    callback(GPSPoint(msg.timestamp, msg.latitude, msg.longitude, msg.altitude))

            except pynmea2.ParseError:
                # Skip lines that can't be parsed
                continue

    except KeyboardInterrupt as e:
        print("Stopping EMLID data reading")
        raise e
    except Exception as e:
        print(f"Error reading from EMLID: {e}")
        raise e


def find_emlid_device():
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
        return emlid_ports[0]

    # No EMLID device found
    return None
