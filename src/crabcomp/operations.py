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

DataSchema = StructType(
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


def read_csv(session: SparkSession, uri: Uri) -> DataFrame:
    """Reads the data file.

    Args:
        session: an existing session.
        uri: the uri to the data file to read from.

    Returns:
        A cached dataframe read from the provided file.
    """
    return (
        session.read.schema(DataSchema)
        .option(
            "timestampFormat", "MM/dd/yyyy hh:mm:ss a"
        )  # Dataset uses human-readable time instead of ISO-time
        .csv(str(uri), header=True)
        .cache()
    )
