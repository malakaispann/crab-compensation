import logging

from pyspark.errors import PySparkException
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from crabcomp.config import Uri
from crabcomp.result import ErrorCode, Result

_data_schema = StructType(
    [
        StructField(name="Fiscal Year", dataType=IntegerType(), nullable=False),
        StructField(name="Agency Name", dataType=StringType(), nullable=False),
        StructField(name="Vendor Name", dataType=StringType(), nullable=False),
        StructField(name="Vendor Zip", dataType=StringType(), nullable=True),
        StructField(name="Amount", dataType=DoubleType(), nullable=False),
        StructField(name="Fiscal Period", dataType=IntegerType(), nullable=False),
        StructField(name="Date", dataType=TimestampType(), nullable=False),
        StructField(name="Category", dataType=StringType(), nullable=False),
    ]
)

_logger = logging.getLogger(__name__)


class OperationErrorCodes(ErrorCode):

    FAILED_READ = ErrorCode.auto()


def read_csv(session: SparkSession, uri: Uri) -> Result[DataFrame]:
    """Reads the data file.

    Args:
        session: an existing session.
        uri: the uri to the data file to read from.

    Returns:
        A cached dataframe read from the provided file.
    """
    _logger.debug(f"Reading in data from URI '{uri}'")

    try:
        dataframe = (
            session.read.schema(_data_schema)
            .option(
                "timestampFormat", "MM/dd/yyyy hh:mm:ss a"
            )  # Dataset uses human-readable time instead of ISO-time
            .csv(str(uri), header=True)
            .cache()
        )
    except PySparkException as exc:
        _logger.error(
            f"Failed to read datafile into dataframe. Error: {exc.getMessage()}"
        )
        return Result.failure(OperationErrorCodes.FAILED_READ)

    return Result.success(dataframe)
