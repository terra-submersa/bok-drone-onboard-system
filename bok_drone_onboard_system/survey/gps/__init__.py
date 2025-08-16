class GPSPoint:
    def __init__(self, timestamp, latitude, longitude, altitude):
        self.timestamp = timestamp
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude

    def __repr__(self):
        return f"timestamp={self.timestamp}, latitude={self.latitude}, longitude={self.longitude}, altitude={self.altitude}"
