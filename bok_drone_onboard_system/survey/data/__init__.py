import logging
import sqlite3
from datetime import datetime
from sqlite3 import Connection

from bok_drone_onboard_system.survey import SurveyMeasure
from bok_drone_onboard_system.survey.gps import GPSPoint

logger = logging.getLogger(__name__)


def db_conn(sqlite_filename: str) -> Connection:
    logger.info(f"Connecting to DB {sqlite_filename}")
    return sqlite3.connect(sqlite_filename)


def create_table_if_not_exists(conn: Connection) -> Connection:
    logger.info("Creating table if not exists")
    stmt = """
           CREATE TABLE IF NOT EXISTS bno_data
           (
               timestamp TEXT PRIMARY KEY,
               quat_i REAL,
               quat_j REAL,
               quat_k REAL,
               quat_real REAL,
               gps_lat REAL,
               gps_lon REAL,
               gps_alt REAL
           )"""
    conn.execute(stmt)
    conn.commit()
    return conn


def append_measure(quaternion: tuple, gps_point: GPSPoint, conn: Connection):
    timestamp = None if gps_point.timestamp is None else gps_point.timestamp.isoformat(timespec='milliseconds')

    conn.execute(
        "INSERT INTO bno_data (timestamp, quat_i, quat_j, quat_k, quat_real, gps_lat, gps_lon, gps_alt) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (timestamp, *quaternion, gps_point.latitude, gps_point.longitude, gps_point.altitude),
    )
    conn.commit()


def load_data(
        conn: Connection,
        start: datetime | None, end: datetime | None,
        only_defined:bool=False
) -> list[SurveyMeasure]:
    """ survey data from the database

    :param conn: sqlite datbase connection
    :param start: inclusive starting timestamp. If None, start from the beginning of the survey.
    :param end: exclusive ending timestamp. If None, end at the end of the survey.
    :param only_defined: if True, only return SurveyMeasure when defined.
    :return: list of SurveyMeasure
    """
    query = "SELECT timestamp, quat_i, quat_j, quat_k, quat_real, gps_lat, gps_lon, gps_alt FROM bno_data"
    params = []
    
    # Add timestamp filters if provided
    conditions = []
    if start is not None:
        conditions.append("timestamp >= ?")
        params.append(start.isoformat(timespec='milliseconds'))
    if end is not None:
        conditions.append("timestamp < ?")
        params.append(end.isoformat(timespec='milliseconds'))
    
    # Add conditions to query if any exist
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    # Execute query
    cursor = conn.execute(query, params)
    
    # Process results
    results = []
    for row in cursor.fetchall():
        timestamp_str, quat_i, quat_j, quat_k, quat_real, gps_lat, gps_lon, gps_alt = row
        
        # Parse timestamp if it exists
        timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else None
        
        # Create GPSPoint
        gps_point = GPSPoint(timestamp, gps_lat, gps_lon, gps_alt)
        
        # Create quaternion tuple
        quaternion = (quat_i, quat_j, quat_k, quat_real)
        
        # Create SurveyMeasure
        measure = SurveyMeasure(gps_point, quaternion)
        
        # Add to results if it meets the criteria
        if not only_defined or measure.is_defined():
            results.append(measure)
    
    return results
