import argparse
import logging
import os
import sys

from pathlib import Path
from typing import TypeVar

from pyspark.sql import SparkSession

from crabcomp.config import AppConfig
from crabcomp.log import configure_root_logger, reset_root_logger
from crabcomp.operations import read_csv, analyze_year_compensation, write_analysis_json
from crabcomp.result import Result

_logger = logging.getLogger(__name__)

T = TypeVar("T")

# Suppress noisy PySpark logs
logging.getLogger("py4j").setLevel(logging.WARNING)
logging.getLogger("pyspark").setLevel(logging.WARNING)
logging.getLogger("py4j.java_gateway").setLevel(logging.WARNING)
logging.getLogger("py4j.clientserver").setLevel(logging.WARNING)


def _try_unrecoverable_operation(
    result: Result[T], msg: str, nullish_ok: bool = False
) -> T:
    """_summary_

    Args:
        msg: _description_
        code: _description_

    Returns:
        _description_
    """
    if result.is_failure or (not nullish_ok and result.value is None):
        _logger.error(f"{msg}. Cause: {str(result.code)}. Exiting program.")
        sys.exit(1)

    return result.value


def _valid_year(year_string):
    """Validate that the year is within the available data range."""
    year = int(year_string)
    if year < 2008 or year > 2024:
        raise argparse.ArgumentTypeError(
            f"Year {year} is out of range. Data is available from 2008 to 2024."
        )
    return year


def main():
    """Main entry point for the crab compensation analysis CLI."""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Analyze Maryland state compensation data for a specific fiscal year"
    )
    parser.add_argument(
        "-y",
        "--year",
        type=_valid_year,
        required=True,
        help="Fiscal year to analyze (2008-2024)",
    )

    args = parser.parse_args()

    # Ensure logging pre-configuration
    configure_root_logger()

    _logger.info("Starting Crab Compensation Engine")

    _logger.info("Extracting and applying configuration from environment")

    app_config = _try_unrecoverable_operation(
        AppConfig.extract(os.environ), "Application configuration failed"
    )

    reset_root_logger()
    configure_root_logger(app_config.log_level)

    _logger.info("Creating distributed session manager.")
    session = SparkSession.builder.appName("Crab Compensation").getOrCreate()

    # Configure checkpointing for fault tolerance
    checkpoint_dir = f"{str(app_config.output_uri)}/checkpoints"
    session.sparkContext.setCheckpointDir(checkpoint_dir)
    _logger.info(f"Checkpoint directory set to: {checkpoint_dir}")

    dataframe = _try_unrecoverable_operation(
        read_csv(session, app_config.data_uri), "Data read failed"
    )

    _logger.info("Beginning data analysis.")

    # Analyze the data for the specified year
    analysis = _try_unrecoverable_operation(
        analyze_year_compensation(dataframe, args.year),
        f"Analysis failed for year {args.year}",
    )

    # Write the analysis output to the configured output URI
    _try_unrecoverable_operation(
        write_analysis_json(session, analysis, app_config.output_uri),
        "Failed to write analysis results",
        nullish_ok=True,
    )

    session.stop()


if __name__ == "__main__":
    main()
