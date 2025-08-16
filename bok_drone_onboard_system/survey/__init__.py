from typing import Tuple

from serial import Serial

from bok_drone_onboard_system.survey.emlid_reader import read_from_emlid, find_emlid_device
from bok_drone_onboard_system.survey.gps import GPSPoint


class SurveyMeasure:
    gps_Point: GPSPoint
    bno_quaternion: Tuple[float, float, float, float]

    def __init__(self, gps_point: GPSPoint, bno_quaternion: Tuple[float, float, float, float]):
        self.gps_Point = gps_point
        self.bno_quaternion = bno_quaternion

    def has_gps(self):
        return self.gps_Point is not None

    def has_bno(self):
        if self.bno_quaternion is None:
            return False
        # Check if any component is None
        return all(component is not None for component in self.bno_quaternion)

    def is_defined(self):
        return self.has_gps() and self.has_bno()

    def project(self, length: float):
        pass


if __name__ == "__main__":
    # Find the EMLID device
    emlid_device = find_emlid_device()

    if emlid_device:
        print(f"EMLID device found at: {emlid_device}")
        try:
            ser = Serial(emlid_device, 115200, timeout=1)
            read_from_emlid(ser, lambda x: print(x))
        except Exception as e:
            print(f"Error connecting to EMLID device: {e}")
    else:
        print("No EMLID device found. Please check the connection.")
