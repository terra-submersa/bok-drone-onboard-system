import argparse
import logging

from bok_drone_onboard_system.survey.emlid_reader import stream_from_emlid_llh
from bok_drone_onboard_system.survey.gps import GPSPointFifo

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="follow emlid rover data RT")

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="the log level. Default is INFO. Options are: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    args = parser.parse_args()

    host = "192.168.1.79"
    port = 9001

    n = 20
    fifo = GPSPointFifo(n)
    for e in stream_from_emlid_llh(host, port):
        if len(fifo) == n:
            avg = fifo.average()
            print(f"{e} -> {avg.distance_to(e.gps_point):2.3f}")
        fifo.push(e.gps_point)


if __name__ == "__main__":
    main()
