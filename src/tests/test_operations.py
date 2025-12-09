from unittest.mock import MagicMock

from pytest import fixture
from pyspark.errors import PySparkException
from pyspark.sql import DataFrame, SparkSession

from crabcomp.models import CompensationAnalysis, CompensationStatistics
from crabcomp.operations import (
    OperationErrorCodes,
    analyze_year_compensation,
    extract_general_statistics,
    extract_top_vendors,
    extract_year_dataframe,
    read_csv,
    write_analysis_json,
)


@fixture
def spark_session():
    """Create a mock Spark session."""
    return MagicMock(spec=SparkSession)


@fixture
def mock_dataframe():
    """Create a mock DataFrame."""
    return MagicMock(spec=DataFrame)


@fixture(scope="module")
def test_data_rows():
    """Sample data rows for testing."""
    return [
        # 2024 data
        {
            "Fiscal Year": 2024,
            "Agency Name": "foo",
            "Vendor Name": "Vendor Foo",
            "Vendor Zip": "12345",
            "Amount": 1000.0,
            "Fiscal Period": 1,
            "Date": "2024-01-01 00:00:00",
            "Category": "Services",
        },
        {
            "Fiscal Year": 2024,
            "Agency Name": "bar",
            "Vendor Name": "Vendor Bar",
            "Vendor Zip": "67890",
            "Amount": 3000.0,
            "Fiscal Period": 1,
            "Date": "2024-01-15 00:00:00",
            "Category": "Supplies",
        },
        {
            "Fiscal Year": 2024,
            "Agency Name": "foo",
            "Vendor Name": "Vendor Foo",
            "Vendor Zip": "12345",
            "Amount": 1500.0,
            "Fiscal Period": 2,
            "Date": "2024-02-01 00:00:00",
            "Category": "Services",
        },
        {
            "Fiscal Year": 2024,
            "Agency Name": "baz",
            "Vendor Name": "Vendor Baz",
            "Vendor Zip": "11111",
            "Amount": 500.0,
            "Fiscal Period": 2,
            "Date": "2024-02-15 00:00:00",
            "Category": "Equipment",
        },
        # 2023 data
        {
            "Fiscal Year": 2023,
            "Agency Name": "foo",
            "Vendor Name": "Vendor Foo",
            "Vendor Zip": "12345",
            "Amount": 3000.0,
            "Fiscal Period": 1,
            "Date": "2023-01-01 00:00:00",
            "Category": "Services",
        },
    ]


@fixture(scope="module")
def test_dataframe(spark, test_data_rows):
    """Create a test DataFrame from sample data - cached at module level."""
    df = spark.createDataFrame(test_data_rows)
    df.cache()
    return df


class TestReadCsv:

    def test_Returns_success_result_With_dataframe_When_read_successful(
        self, spark_session, mock_dataframe
    ):
        spark_session.read.schema.return_value.option.return_value.csv.return_value.cache.return_value = (
            mock_dataframe
        )

        result = read_csv(spark_session, "s3://foo/bar.csv")

        assert result.is_success
        assert result.value == mock_dataframe
        spark_session.read.schema.return_value.option.return_value.csv.assert_called_once_with(
            "s3://foo/bar.csv", header=True
        )

    def test_Returns_failure_result_With_failed_read_code_When_spark_exception_raised(
        self, spark_session
    ):
        # Mock the side effect to raise PySparkException
        def raise_spark_exception(*_, **__):
            raise PySparkException("Test error")

        spark_session.read.schema.side_effect = raise_spark_exception

        result = read_csv(spark_session, "s3://foo/bar.csv")

        assert result.is_failure
        assert result.code == OperationErrorCodes.FAILED_READ
        assert result.value is None


class TestExtractYearDataframe:

    def test_Returns_success_result_With_filtered_dataframe_When_data_exists_for_year(
        self, test_dataframe
    ):
        result = extract_year_dataframe(test_dataframe, 2024)

        assert result.is_success
        assert result.value.count() == 4
        # Verify all rows are from 2024
        years = result.value.select("Fiscal Year").distinct().collect()
        assert len(years) == 1
        assert years[0]["Fiscal Year"] == 2024

    def test_Returns_failure_result_With_invalid_year_code_When_no_data_for_year(
        self, test_dataframe
    ):
        result = extract_year_dataframe(test_dataframe, 2025)

        assert result.is_failure
        assert result.code == OperationErrorCodes.INVALID_YEAR


@fixture(scope="module")
def year_2024_df(test_dataframe):
    """Cached 2024 data for multiple tests."""
    df = test_dataframe.filter(test_dataframe["Fiscal Year"] == 2024)
    df.cache()
    return df


class TestExtractGeneralStatistics:

    def test_Returns_correct_statistics_for_year_data(self, year_2024_df):
        result = extract_general_statistics(year_2024_df, 2024)

        assert result.is_success
        stats = result.value
        assert isinstance(stats, CompensationStatistics)
        assert stats.fiscal_year == 2024
        assert stats.total_amount == 6000.0  # 1000 + 3000 + 1500 + 500
        assert stats.average_transaction == 1500.0  # 6000 / 4
        assert stats.min_transaction == 500.0
        assert stats.max_transaction == 3000.0
        assert stats.transaction_count == 4


class TestExtractTopVendors:

    def test_Returns_vendors_sorted_by_total_amount(self, year_2024_df):
        result = extract_top_vendors(year_2024_df, limit=3)

        assert result.is_success
        vendors = result.value
        assert len(vendors) == 3

        # Check vendor order and values
        assert vendors[0].vendor_name == "Vendor Bar"
        assert vendors[0].total_paid == 3000.0
        assert vendors[0].transaction_count == 1

        assert vendors[1].vendor_name == "Vendor Foo"
        assert vendors[1].total_paid == 2500.0  # 1000 + 1500
        assert vendors[1].transaction_count == 2

        assert vendors[2].vendor_name == "Vendor Baz"
        assert vendors[2].total_paid == 500.0
        assert vendors[2].transaction_count == 1

    def test_Returns_limited_number_of_vendors(self, year_2024_df):
        result = extract_top_vendors(year_2024_df, limit=2)

        assert result.is_success
        assert len(result.value) == 2


class TestAnalyzeYearCompensation:

    def test_Returns_complete_analysis_for_valid_year(self, test_dataframe):
        result = analyze_year_compensation(test_dataframe, 2024)

        assert result.is_success
        analysis = result.value
        assert isinstance(analysis, CompensationAnalysis)

        # Check statistics
        assert analysis.fiscal_year == 2024
        assert analysis.total_amount == 6000.0
        assert analysis.average_transaction == 1500.0
        assert analysis.min_transaction == 500.0
        assert analysis.max_transaction == 3000.0
        assert analysis.transaction_count == 4

        # Check vendors (should return all 3 vendors since we have only 3)
        assert len(analysis.top_vendors) == 3
        assert analysis.top_vendors[0].vendor_name == "Vendor Bar"
        assert analysis.top_vendors[0].total_paid == 3000.0

    def test_Returns_failure_for_invalid_year(self, test_dataframe):
        result = analyze_year_compensation(test_dataframe, 2025)

        assert result.is_failure
        assert result.code == OperationErrorCodes.INVALID_YEAR

    def test_Handles_single_transaction_year(self, test_dataframe):
        result = analyze_year_compensation(test_dataframe, 2023)

        assert result.is_success
        analysis = result.value
        assert analysis.fiscal_year == 2023
        assert analysis.total_amount == 3000.0
        assert analysis.average_transaction == 3000.0
        assert analysis.min_transaction == 3000.0
        assert analysis.max_transaction == 3000.0
        assert analysis.transaction_count == 1
        assert len(analysis.top_vendors) == 1
        assert analysis.top_vendors[0].vendor_name == "Vendor Foo"


@fixture(scope="module")
def sample_analysis():
    """Create a sample CompensationAnalysis for testing - cached at module level."""
    return CompensationAnalysis(
        fiscal_year=2024,
        total_amount=100000.0,
        average_transaction=5000.0,
        min_transaction=100.0,
        max_transaction=25000.0,
        transaction_count=20,
        top_vendors=[
            {
                "vendor_name": "Test Vendor 1",
                "total_paid": 50000.0,
                "transaction_count": 10,
            },
            {
                "vendor_name": "Test Vendor 2",
                "total_paid": 30000.0,
                "transaction_count": 5,
            },
        ],
    )


class TestWriteAnalysisJson:

    def test_Returns_success_When_write_successful(
        self, spark_session, sample_analysis
    ):
        # Create mocks for the write chain
        mock_coalesce_result = MagicMock()
        mock_write_result = MagicMock()

        # Set up the chain
        spark_session.createDataFrame.return_value.coalesce.return_value = (
            mock_coalesce_result
        )
        mock_coalesce_result.write.mode.return_value = mock_write_result

        result = write_analysis_json(spark_session, sample_analysis, "s3://output/path")

        assert result.is_success
        assert result.value is None

        # Verify the DataFrame was created with the correct data
        spark_session.createDataFrame.assert_called_once()
        call_args = spark_session.createDataFrame.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0]["fiscalYear"] == 2024
        assert call_args[0]["totalAmount"] == 100000.0

        # Verify write chain was called correctly
        spark_session.createDataFrame.return_value.coalesce.assert_called_once_with(1)
        mock_coalesce_result.write.mode.assert_called_once_with("overwrite")
        mock_write_result.json.assert_called_once_with("s3://output/path")

    def test_Returns_failure_With_failed_write_code_When_spark_exception_raised(
        self, spark_session, sample_analysis
    ):
        # Mock the side effect to raise PySparkException
        def raise_spark_exception(*args, **kwargs):
            raise PySparkException("Test write error")

        spark_session.createDataFrame.side_effect = raise_spark_exception

        result = write_analysis_json(spark_session, sample_analysis, "s3://output/path")

        assert result.is_failure
        assert result.code == OperationErrorCodes.FAILED_WRITE
        assert result.value is None
