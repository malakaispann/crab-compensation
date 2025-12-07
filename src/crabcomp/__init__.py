import logging
import os

from pyspark.sql import SparkSession

from crabcomp.config import AppConfig
from crabcomp.log import configure_logger
from crabcomp.operations import read_csv

_logger = logging.getLogger(__name__)


def configure_application() -> AppConfig:
    """_summary_

    Returns:
        _description_
    """
    app_config = AppConfig.model_validate(os.environ)

    configure_logger(app_config.level, _logger)

    _logger.debug("Configuration")
    return app_config


def main():

    app_config = configure_application()

    session = SparkSession.builder.appName("Crab Compensation").getOrCreate()
    df = read_csv(session, app_config.data_uri)

    session.stop()


if __name__ == "__main__":
    main()
