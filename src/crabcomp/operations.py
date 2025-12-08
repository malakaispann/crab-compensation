import logging

from pyspark.errors import PySparkException
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from crabcomp.config import Uri
from crabcomp.models import CompensationAnalysis, CompensationStatistics, VendorSummary
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
    """Error codes specific to data operations."""

    FAILED_READ = ErrorCode.auto()
    FAILED_ANALYSIS = ErrorCode.auto()
    INVALID_YEAR = ErrorCode.auto()


def read_csv(session: SparkSession, uri: Uri) -> Result[DataFrame]:
    """Reads the data file.

    Args:
        session: an existing session.
        uri: the uri to the data file to read from.

    Returns:
        A cached dataframe read from the provided file.
    """
    _logger.info(f"Reading in data from URI '{uri}'")

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

    _logger.info("Read operation successful.")
    return Result.success(dataframe)


def extract_year_dataframe(dataframe: DataFrame, year: int) -> Result[DataFrame]:
    """Extract and validate dataframe for a specific fiscal year.

    Args:
        dataframe: The dataframe containing payment data
        year: The fiscal year to filter for

    Returns:
        A Result containing the cached DataFrame for the specified year
    """
    _logger.debug(f"Extracting data for fiscal year {year}")

    try:
        # Filter data for the specified year and cache for reuse
        year_dataframe = dataframe.filter(functions.col("Fiscal Year") == year).cache()

        # Check if we have data for this year
        count = year_dataframe.count()
        if count == 0:
            _logger.error(f"No data found for fiscal year {year}")
            year_dataframe.unpersist()
            return Result.failure(OperationErrorCodes.INVALID_YEAR)

        return Result.success(year_dataframe)

    except PySparkException as exc:
        _logger.error(f"Failed to extract year data. Error: {exc.getMessage()}")
        return Result.failure(OperationErrorCodes.FAILED_ANALYSIS)


def extract_general_statistics(
    year_dataframe: DataFrame, fiscal_year: int
) -> Result[CompensationStatistics]:
    """Extract general statistics from year dataframe.

    Args:
        year_dataframe: The cached dataframe for a specific year
        fiscal_year: The fiscal year being analyzed

    Returns:
        A Result containing CompensationStatistics
    """
    _logger.debug("Extracting general statistics")

    try:
        # Calculate aggregate statistics
        stats = year_dataframe.agg(
            functions.sum("Amount").alias("total_amount"),
            functions.avg("Amount").alias("average_transaction"),
            functions.min("Amount").alias("min_transaction"),
            functions.max("Amount").alias("max_transaction"),
            functions.count("Amount").alias("transaction_count"),
        ).collect()[0]

        return Result.success(
            CompensationStatistics(
                fiscal_year=fiscal_year,
                total_amount=float(stats["total_amount"]),
                average_transaction=float(stats["average_transaction"]),
                min_transaction=float(stats["min_transaction"]),
                max_transaction=float(stats["max_transaction"]),
                transaction_count=int(stats["transaction_count"]),
            )
        )

    except PySparkException as exc:
        _logger.error(f"Failed to extract statistics. Error: {exc.getMessage()}")
        return Result.failure(OperationErrorCodes.FAILED_ANALYSIS)


def extract_top_vendors(
    year_dataframe: DataFrame, limit: int = 10
) -> Result[list[VendorSummary]]:
    """Extract top vendors by total amount paid.

    Args:
        year_dataframe: The cached dataframe for a specific year
        limit: Number of top vendors to return. Defaults to 10.

    Returns:
        A Result containing a list of VendorSummary objects
    """
    _logger.debug(f"Extracting top {limit} vendors")

    try:
        # Create vendor aggregation dataframe and cache it
        vendor_agg_dataframe = (
            year_dataframe.groupBy("Vendor Name")
            .agg(
                functions.sum("Amount").alias("total_paid"),
                functions.count("Amount").alias("transaction_count"),
            )
            .cache()
        )

        # Get top vendors by total amount paid
        top_vendors = (
            vendor_agg_dataframe.orderBy(functions.desc("total_paid"))
            .limit(limit)
            .collect()
        )

        # Unpersist cached dataframe
        vendor_agg_dataframe.unpersist()

        # Create VendorSummary objects for top vendors
        vendor_summaries = [
            VendorSummary(
                vendor_name=row["Vendor Name"],
                total_paid=float(row["total_paid"]),
                transaction_count=int(row["transaction_count"]),
            )
            for row in top_vendors
        ]

        return Result.success(vendor_summaries)

    except PySparkException as exc:
        _logger.error(f"Failed to extract top vendors. Error: {exc.getMessage()}")
        return Result.failure(OperationErrorCodes.FAILED_ANALYSIS)


def analyze_year_compensation(
    dataframe: DataFrame, year: int
) -> Result[CompensationAnalysis]:
    """Analyze compensation data for a specific fiscal year.

    Args:
        dataframe: The dataframe containing payment data
        year: The fiscal year to analyze

    Returns:
        A Result containing CompensationAnalysis for the specified year
    """
    _logger.info(f"Analyzing compensation data for fiscal year {year}")

    # Extract dataframe for the specified year
    if (year_dataframe_result := extract_year_dataframe(dataframe, year)).is_failure:
        return year_dataframe_result

    year_dataframe = year_dataframe_result.value

    # Extract general statistics
    if (stats_result := extract_general_statistics(year_dataframe, year)).is_failure:
        year_dataframe.unpersist()
        return stats_result

    stats = stats_result.value

    # Extract top vendors
    if (vendors_result := extract_top_vendors(year_dataframe)).is_failure:
        year_dataframe.unpersist()
        return vendors_result

    # Unpersist the year dataframe as we're done with it
    year_dataframe.unpersist()

    # Create and return the analysis result using model unpacking
    analysis = CompensationAnalysis(
        **stats.model_dump(),
        top_vendors=vendors_result.value,
    )

    _logger.info(f"Successfully analyzed data for fiscal year {year}")
    return Result.success(analysis)
