import logging
import os
import sys

from typing import TypeVar

from pyspark.sql import SparkSession

from crabcomp.config import AppConfig
from crabcomp.log import configure_root_logger, reset_root_logger
from crabcomp.operations import read_csv
from crabcomp.result import Result

_logger = logging.getLogger(__name__)

T = TypeVar("Type")


def _try_unrecoverable_operation(result: Result[T], msg: str) -> T:
    """_summary_

    Args:
        msg: _description_
        code: _description_

    Returns:
        _description_
    """
    if result.is_failure or result.value is None:
        _logger.error(f"{msg}. Cause: {str(result.code)}. Exiting program.")
        sys.exit(1)

    return result.value


def main():

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

    dataframe = _try_unrecoverable_operation(
        read_csv(session, app_config.data_uri), "Data read failed"
    )

    dataframe.show()

    session.stop()


if __name__ == "__main__":
    main()
