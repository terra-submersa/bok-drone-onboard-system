import argparse
import logging
import sqlite3
import time
from sqlite3 import Connection

from serial import Serial

from bok_drone_onboard_system.bno import load_bno
from bok_drone_onboard_system.survey.emlid_reader import GPSPoint, find_emlid_device, read_from_emlid

logger = logging.getLogger(__name__)


def db_conn(sqlite_filename: str) -> Connection:
    logger.info(f"Connecting to DB {sqlite_filename}")
    return sqlite3.connect(sqlite_filename)


def create_table_if_not_exists(conn: Connection)->Connection:
    logger.info("Creating table if not exists")
    stmt = """
           CREATE TABLE IF NOT EXISTS bno_data
           (
               timestamp TEXT
               PRIMARY KEY,
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


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="acquire data from survey with emlid + BNO08x and store in sqllite DB.")

    parser.add_argument(
        "--db",
        required=True,
        help="the path to the sqlite database file"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Do not read on BNO08x, but generate random data. "
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="the log level. Default is INFO. Options are: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    args = parser.parse_args()

    db_connection = db_conn(args.db)
    create_table_if_not_exists(db_connection)
    emlid_device = find_emlid_device()
    emlid_ser = Serial(emlid_device, 115200, timeout=1)

    def angle_and_save(gps_point: GPSPoint):
        quat = bno.quaternion
        append_measure(quat, gps_point, db_connection)

    bno = None
    i = 0
    while True:
        try:
            if not bno:
                bno = load_bno(args.mock)
                db_connection.close()
                db_connection = db_conn(args.db)
            if not emlid_device:
                emlid_device = find_emlid_device()
                emlid_ser = Serial(emlid_device, 115200, timeout=1)

            read_from_emlid(emlid_ser, angle_and_save)
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(3)
            bno = None


if __name__ == "__main__":
    main()
