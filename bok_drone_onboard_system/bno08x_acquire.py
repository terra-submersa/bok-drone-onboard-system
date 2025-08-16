import argparse
import logging
import time

from bok_drone_onboard_system.bno import load_bno
from bok_drone_onboard_system.bno.data import db_conn, create_table_if_not_exists, append_measure
from bok_drone_onboard_system.positioner import Vector, vector_from_quaternion

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="acquire data from BNO08x and store in sqllite DB.")

    parser.add_argument(
        "--db",
        required=True,
        help="the path to the sqlite database file"
    )
    parser.add_argument(
        "-s",
        "--show-orientation",
        action="store_true",
        help="display the x,y,z vector of the orientation."
    )
    parser.add_argument(
        "-p",
        "--period",
        type=float,
        default=0.1,
        help="How often to read data from BNO08x is seconds. Default is 0.1 second."
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
    show_orientation = args.show_orientation
    v_nat = Vector(1, 0, 0)

    connection = db_conn(args.db)
    create_table_if_not_exists(connection)
    bno = None
    i = 0
    while True:
        try:
            if not bno:
                bno = load_bno(args.mock)
                connection.close()
                connection = db_conn(args.db)
            i += 1
            quat = bno.quaternion
            if show_orientation:
                v = vector_from_quaternion(quat, v_nat)
                print(v)
            append_measure(quat, connection)
            if i % 1000 == 0:
                logger.info(f"Appended {i} measurements")
            time.sleep(args.period)
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(3)
            bno = None


if __name__ == "__main__":
    main()
