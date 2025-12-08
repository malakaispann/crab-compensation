"""Shared test fixtures and configuration."""

import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark():
    """Create a single Spark session for all tests."""
    spark = (
        SparkSession.builder.appName("test")
        .master("local[1]")
        .config(
            "spark.sql.shuffle.partitions", "1"
        )  # We'll be using small datasets so avoid the default
        # ~200 partitions to improve performance
        .getOrCreate()
    )
    yield spark
    spark.stop()
