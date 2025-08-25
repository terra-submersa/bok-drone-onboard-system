from datetime import datetime
from enum import IntEnum
from typing import Optional, Tuple


class GPSPoint:
    def __init__(self, timestamp: datetime, latitude, longitude, altitude):
        self.timestamp = timestamp
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude

    def __repr__(self):
        return f"{self.timestamp.isoformat(timespec='milliseconds')} ({self.longitude:.7f}, {self.latitude:.7f}, {self.altitude:.2f})"

    def distance_to(self, other: "GPSPoint") -> float:
        """
        Calculate the distance between this GPS point and another GPS point in meters.
        
        Args:
            other: Another GPSPoint object
            
        Returns:
            Distance in meters between the two points
        """
        import pyproj

        # Create a geodesic calculator using the WGS84 ellipsoid
        geod = pyproj.Geod(ellps="WGS84")

        # Calculate the forward and backward azimuths and distance
        _, _, distance = geod.inv(
            self.longitude, self.latitude,
            other.longitude, other.latitude
        )

        return distance


class GPSPointFifo:
    _stack: list[GPSPoint]
    n: int

    def __init__(self, n: int):
        self._stack = []
        self.n = n

    def push(self, point: GPSPoint):
        self._stack.append(point)
        if len(self._stack) > self.n:
            self._stack.pop(0)

    def __len__(self):
        return len(self._stack)

    def __getitem__(self, item):
        return self._stack[item]

    def average(self) -> GPSPoint | None:
        if len(self) == 0:
            return None

        avg_lat = sum(p.latitude for p in self._stack) / len(self)
        avg_lon = sum(p.longitude for p in self._stack) / len(self)
        avg_altitude = sum(p.altitude for p in self._stack) / len(self)
        return GPSPoint(None, avg_lat, avg_lon, avg_altitude)


class SolutionQuality(IntEnum):
    NONE = 0
    FIX = 1
    FLOAT = 2
    SBAS = 3
    DGPS = 4
    SINGLE = 5
    PPS = 6

    @property
    def label(self) -> str:
        return {
            SolutionQuality.NONE: "No position",
            SolutionQuality.FIX: "FIX",
            SolutionQuality.FLOAT: "FLOAT",
            SolutionQuality.SBAS: "SBAS",
            SolutionQuality.DGPS: "DGPS",
            SolutionQuality.SINGLE: "SINGLE",
            SolutionQuality.PPS: "PPS",
        }[self]

    def __repr__(self):
        return self.label

    @classmethod
    def from_value(cls, value: int) -> Optional["SolutionQuality"]:
        try:
            return cls(value)
        except ValueError:
            return None


class EmlidEntry:
    gps_point: GPSPoint
    std_dev: Tuple[float, float, float]
    solution_status: SolutionQuality

    def __init__(self, gps_point: GPSPoint, std_dev: Tuple[float, float, float], solution_status: SolutionQuality):
        self.gps_point = gps_point
        self.std_dev = std_dev
        self.solution_status = solution_status

    def error_horizontal(self) -> float:
        return (self.std_dev[0] + self.std_dev[1]) / 2

    def __repr__(self):
        return f"{self.gps_point} err={self.error_horizontal():.3f} {self.solution_status.label}"
