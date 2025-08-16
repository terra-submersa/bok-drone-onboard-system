"""
GPS coordinate conversion utilities.
"""
from typing import Tuple
import pyproj
from bok_drone_onboard_system.survey.gps import GPSPoint

def wgs84_to_utm34n(gps_point: GPSPoint) -> Tuple[float, float, float]:
    """
    Convert WGS84 GPS coordinates to UTM zone 34N coordinates using pyproj.
    
    Args:
        gps_point: A GPSPoint object containing WGS84 coordinates (latitude, longitude, altitude)
        
    Returns:
        A tuple of three floats (x, y, z) representing the coordinates in UTM zone 34N
    """
    # Create a transformer from WGS84 to UTM zone 34N
    wgs84 = pyproj.CRS.from_epsg(4326)  # WGS84
    utm34n = pyproj.CRS.from_epsg(32634)  # UTM zone 34N
    
    # Create the transformer
    transformer = pyproj.Transformer.from_crs(wgs84, utm34n, always_xy=True)
    
    # Transform the coordinates
    x, y = transformer.transform(gps_point.longitude, gps_point.latitude)
    
    # The z coordinate (altitude) remains the same
    z = gps_point.altitude
    
    return (x, y, z)