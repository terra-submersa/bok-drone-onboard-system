import argparse
import logging
from datetime import datetime

from dateutil import parser

from bok_drone_onboard_system.analysis.gps import wgs84_to_utm34n
from bok_drone_onboard_system.positioner.projector import calculate_pole_end_position
from bok_drone_onboard_system.survey.data import db_conn, load_data

logger = logging.getLogger(__name__)


def parse_timestamp(timestamp_str):
    return datetime.fromisoformat(timestamp_str)


def format_tsv_output(survey_measures, include_header=True):
    """
    Format survey measures as TSV output.
    
    Args:
        survey_measures: List of SurveyMeasure objects, which are defined
        include_header: Whether to include a header row
        
    Returns:
        String containing TSV formatted data
    """
    lines = []

    # Add header if requested
    if include_header:
        lines.append("timestamp\ttutm_x\tutm_y\tutm_z\tproj_x\tproj_y\tproj_z")

    # Add data rows
    for measure in survey_measures:
        gps = measure.gps_Point

        # Skip if GPS data is missing
        if not gps:
            continue

        # Convert to UTM coordinates
        utm_coords = wgs84_to_utm34n(gps)
        projection = calculate_pole_end_position(measure.bno_quaternion, utm_coords, 2.57)

        # Format timestamp
        timestamp_str = gps.timestamp.isoformat(timespec='milliseconds')

        # Create TSV line
        line = f"{timestamp_str}\t{utm_coords[0]}\t{utm_coords[1]}\t{utm_coords[2]}\t{projection[0]}\t{projection[1]}\t{projection[2]}"
        lines.append(line)

    return "\n".join(lines)


def main():
    """
    Main function to analyze survey data and output as TSV.
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Analyze survey data and output as TSV.")

    parser.add_argument(
        "--db",
        required=True,
        help="the path to the sqlite database file"
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Start timestamp in ISO format (e.g., 2023-01-01T00:00:00)"
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End timestamp in ISO format (e.g., 2023-01-01T23:59:59)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="the log level. Default is INFO. Options are: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )

    args = parser.parse_args()

    # Set log level
    log_level = getattr(logging, args.log_level.upper())
    logging.basicConfig(level=log_level)

    # Connect to database
    db_connection = db_conn(args.db)

    # Parse timestamps if provided
    start = parse_timestamp(args.start) if args.start else None
    end = parse_timestamp(args.end) if args.end else None

    # Load data from database
    logger.info(f"Loading data from {args.db}")
    logger.info(f"Start: {start}, End: {end}")
    measures = load_data(db_connection, start, end, True)
    logger.info(f"Loaded {len(measures)} survey measures")

    # Format and print TSV output
    tsv_output = format_tsv_output(measures)
    print(tsv_output)


if __name__ == "__main__":
    main()
