from typing import List
from pydantic import BaseModel, Field, ConfigDict

# Shared configuration for all models to use camelCase in JSON
_model_config = ConfigDict(
    populate_by_name=True,
    serialize_by_alias=True,
)


class VendorSummary(BaseModel):
    """Summary of payments to a vendor."""

    model_config = _model_config

    vendor_name: str = Field(..., alias="vendorName", description="Name of the vendor")
    total_paid: float = Field(
        ..., alias="totalPaid", description="Total amount paid to the vendor"
    )
    transaction_count: int = Field(
        ...,
        alias="transactionCount",
        description="Number of transactions with the vendor",
    )


class CompensationStatistics(BaseModel):
    """General statistics for compensation data."""

    model_config = _model_config

    fiscal_year: int = Field(
        ..., alias="fiscalYear", description="The fiscal year being analyzed"
    )
    total_amount: float = Field(
        ..., alias="totalAmount", description="Total money paid"
    )
    average_transaction: float = Field(
        ..., alias="averageTransaction", description="Average transaction amount"
    )
    min_transaction: float = Field(
        ..., alias="minTransaction", description="Minimum transaction amount"
    )
    max_transaction: float = Field(
        ..., alias="maxTransaction", description="Maximum transaction amount"
    )
    transaction_count: int = Field(
        ..., alias="transactionCount", description="Total number of transactions"
    )


class CompensationAnalysis(CompensationStatistics):
    """Results of compensation analysis for a fiscal year."""

    top_vendors: List[VendorSummary] = Field(
        ..., alias="topVendors", description="Top 10 vendors by total amount paid"
    )
