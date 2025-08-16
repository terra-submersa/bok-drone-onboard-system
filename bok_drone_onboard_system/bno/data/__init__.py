import logging
import sqlite3
from datetime import datetime, timezone
from sqlite3 import Connection

logger = logging.getLogger(__name__)

TABLE_NAME= "bno_data"


def db_conn(sqlite_filename: str) -> Connection:
    logger.info(f"Connecting to DB {sqlite_filename}")
    return sqlite3.connect(sqlite_filename)


def create_table_if_not_exists(conn: Connection):
    logger.info("Creating table if not exists")
    stmt = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        timestamp TEXT PRIMARY KEY,
        quat_i REAL,
        quat_j REAL,
        quat_k REAL,
        quat_real REAL
    )"""
    conn.execute(stmt)
    conn.commit()
    return conn


def append_measure(quaternion: tuple, conn: Connection):
    current_time = datetime.now(timezone.utc)
    timestamp = current_time.isoformat(timespec='milliseconds')

    conn.execute(
        f"INSERT INTO {TABLE_NAME} (timestamp, quat_i, quat_j, quat_k, quat_real) VALUES (?, ?, ?, ?, ?)",
        (timestamp, *quaternion),
    )
    conn.commit()
