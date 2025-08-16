import argparse
import logging
from datetime import datetime
from typing import Tuple

from dateutil import parser

from bok_drone_onboard_system.analysis.gps import wgs84_to_utm34n
from bok_drone_onboard_system.positioner.projector import calculate_pole_end_position
from bok_drone_onboard_system.survey import SurveyMeasure
from bok_drone_onboard_system.survey.data import db_conn, load_data

logger = logging.getLogger(__name__)


def parse_timestamp(timestamp_str):
    return datetime.fromisoformat(timestamp_str)


def project_measure(survey_measures: list[SurveyMeasure], pole_length) -> list[Tuple[datetime, Tuple[float, float, float], Tuple[float, float, float]]]:
    ret = []
    # Add data rows
    for measure in survey_measures:
        gps = measure.gps_Point

        # Skip if GPS data is missing
        if not gps:
            continue

        # Convert to UTM coordinates
        utm_coords = wgs84_to_utm34n(gps)
        projection = calculate_pole_end_position(measure.bno_quaternion, utm_coords, pole_length=pole_length)

        # Format timestamp
        timestamp_str = gps.timestamp.isoformat(timespec='milliseconds')

        ret.append((timestamp_str, utm_coords, projection))
    return ret


def plot_projected_measures(projected_measures: list[Tuple[datetime, Tuple[float, float, float], Tuple[float, float, float]]], png_file: str):
    """
    Plot the projected measures, which are in metrics coordinates, into a png_image
    Each projected measures element contains
        * a timestamp
        * the GPS point in UTM coordinates (meters)
        * the pole end position in UTM coordinates  (meters)

    The image shall contain:
    * a title with number of points, minmal and maximal timestamps
    * red dots for the GPS points
    * blue dots for the pole end positions
    * a scale to indicate to represent either 10cm, 1m or 10 meters. Whatever is the most relevant
    :param projected_measures:
    :return: None
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    import numpy as np
    from datetime import datetime
    
    # Check if there are any measures to plot
    if not projected_measures or len(projected_measures) == 0:
        logger.warning("No projected measures to plot")
        return
    
    # Extract data points
    gps_points = []
    pole_ends = []
    timestamps = []
    
    for timestamp_str, utm_coords, projection in projected_measures:
        if isinstance(timestamp_str, str):
            timestamp = datetime.fromisoformat(timestamp_str)
        else:
            timestamp = timestamp_str
        timestamps.append(timestamp)
        gps_points.append(utm_coords)
        pole_ends.append(projection)
    
    # Convert to numpy arrays for easier manipulation
    gps_points = np.array(gps_points)
    pole_ends = np.array(pole_ends)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Plot GPS points (red) and pole end positions (blue)
    ax.scatter(gps_points[:, 0], gps_points[:, 1], color='red', label='GPS Points', s=30)
    ax.scatter(pole_ends[:, 0], pole_ends[:, 1], color='blue', label='Pole End Positions', s=30)
    
    # Set equal aspect to ensure distances are represented correctly
    ax.set_aspect('equal')
    
    # Add labels
    ax.set_xlabel('UTM Easting (m)')
    ax.set_ylabel('UTM Northing (m)')
    
    # Determine min and max timestamps
    min_timestamp = min(timestamps)
    max_timestamp = max(timestamps)
    
    # Create title with number of points and timestamp range
    title = f"Survey Points: {len(projected_measures)}\n"
    title += f"Time Range: {min_timestamp.isoformat(timespec='milliseconds')} to {max_timestamp.isoformat(timespec='milliseconds')}"
    ax.set_title(title)
    
    # Add legend
    ax.legend()
    
    # Determine appropriate scale bar size
    x_range = np.max(np.concatenate([gps_points[:, 0], pole_ends[:, 0]])) - np.min(np.concatenate([gps_points[:, 0], pole_ends[:, 0]]))
    y_range = np.max(np.concatenate([gps_points[:, 1], pole_ends[:, 1]])) - np.min(np.concatenate([gps_points[:, 1], pole_ends[:, 1]]))
    
    # Choose scale based on the size of the plot area
    max_range = max(x_range, y_range)
    
    if max_range < 1:
        scale_size = 0.1  # 10 cm
        scale_text = "10 cm"
    elif max_range < 10:
        scale_size = 1.0  # 1 m
        scale_text = "1 m"
    else:
        scale_size = 10.0  # 10 m
        scale_text = "10 m"
    
    # Calculate scale bar position (bottom right corner)
    x_min = np.min(np.concatenate([gps_points[:, 0], pole_ends[:, 0]]))
    y_min = np.min(np.concatenate([gps_points[:, 1], pole_ends[:, 1]]))
    x_max = np.max(np.concatenate([gps_points[:, 0], pole_ends[:, 0]]))
    y_max = np.max(np.concatenate([gps_points[:, 1], pole_ends[:, 1]]))
    
    # Add some padding to the plot
    padding = max(x_range, y_range) * 0.05
    ax.set_xlim(x_min - padding, x_max + padding)
    ax.set_ylim(y_min - padding, y_max + padding)
    
    # Position scale bar in the bottom right corner
    scale_x = x_max - scale_size - padding
    scale_y = y_min + padding
    
    # Draw scale bar
    ax.add_patch(Rectangle((scale_x, scale_y), scale_size, scale_size/10, color='black'))
    ax.text(scale_x + scale_size/2, scale_y + scale_size/5, scale_text, 
            horizontalalignment='center', verticalalignment='bottom')
    
    # Save the plot to the specified file
    plt.savefig(png_file, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Plot saved to {png_file}")


def format_tsv_output(projected_measures: list[Tuple[datetime, Tuple[float, float, float], Tuple[float, float, float]]], include_header=True):
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

    for d in projected_measures:
        timestamp, utm_coords, projection = d
        lines.append(f"{timestamp}\t{utm_coords[0]}\t{utm_coords[1]}\t{utm_coords[2]}\t{projection[0]}\t{projection[1]}\t{projection[2]}")

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
    proj_measures = project_measure(measures, pole_length=100)
    tsv_output = format_tsv_output(proj_measures)
    print(tsv_output)


if __name__ == "__main__":
    main()
