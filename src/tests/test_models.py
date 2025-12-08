"""Tests for Pydantic models serialization/deserialization."""

import json
from crabcomp.models import VendorSummary, CompensationStatistics, CompensationAnalysis


class TestVendorSummary:
    """Tests for VendorSummary model serialization."""

    def test_Serializes_to_camelCase_json(self):
        vendor_name = "Test Vendor"
        total_paid = 10000.50
        transaction_count = 5

        vendor = VendorSummary(
            vendor_name=vendor_name,
            total_paid=total_paid,
            transaction_count=transaction_count,
        )

        json_str = vendor.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed == {
            "vendorName": vendor_name,
            "totalPaid": total_paid,
            "transactionCount": transaction_count,
        }

    def test_Deserializes_from_camelCase_json(self):
        vendor_name = "Test Vendor"
        total_paid = 10000.50
        transaction_count = 5

        json_data = {
            "vendorName": vendor_name,
            "totalPaid": total_paid,
            "transactionCount": transaction_count,
        }

        vendor = VendorSummary.model_validate(json_data)

        assert vendor.vendor_name == vendor_name
        assert vendor.total_paid == total_paid
        assert vendor.transaction_count == transaction_count


class TestCompensationStatistics:
    """Tests for CompensationStatistics model serialization."""

    def test_Serializes_to_camelCase_json(self):
        fiscal_year = 2024
        total_amount = 50000.0
        average_transaction = 500.0
        min_transaction = 10.0
        max_transaction = 5000.0
        transaction_count = 100

        stats = CompensationStatistics(
            fiscal_year=fiscal_year,
            total_amount=total_amount,
            average_transaction=average_transaction,
            min_transaction=min_transaction,
            max_transaction=max_transaction,
            transaction_count=transaction_count,
        )

        json_str = stats.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed == {
            "fiscalYear": fiscal_year,
            "totalAmount": total_amount,
            "averageTransaction": average_transaction,
            "minTransaction": min_transaction,
            "maxTransaction": max_transaction,
            "transactionCount": transaction_count,
        }

    def test_Deserializes_from_camelCase_json(self):
        fiscal_year = 2024
        total_amount = 50000.0
        average_transaction = 500.0
        min_transaction = 10.0
        max_transaction = 5000.0
        transaction_count = 100

        json_data = {
            "fiscalYear": fiscal_year,
            "totalAmount": total_amount,
            "averageTransaction": average_transaction,
            "minTransaction": min_transaction,
            "maxTransaction": max_transaction,
            "transactionCount": transaction_count,
        }

        stats = CompensationStatistics.model_validate(json_data)

        assert stats.fiscal_year == fiscal_year
        assert stats.total_amount == total_amount
        assert stats.average_transaction == average_transaction
        assert stats.min_transaction == min_transaction
        assert stats.max_transaction == max_transaction
        assert stats.transaction_count == transaction_count


class TestCompensationAnalysis:

    def test_Serializes_nested_models_to_camelCase(self):
        fiscal_year = 2024
        total_amount = 3000.0
        average_transaction = 1500.0
        min_transaction = 1000.0
        max_transaction = 2000.0
        transaction_count = 2

        vendor_a_name = "Vendor A"
        vendor_a_paid = 1000.0
        vendor_a_count = 1

        vendor_b_name = "Vendor B"
        vendor_b_paid = 2000.0
        vendor_b_count = 2

        vendors = [
            VendorSummary(
                vendor_name=vendor_a_name,
                total_paid=vendor_a_paid,
                transaction_count=vendor_a_count,
            ),
            VendorSummary(
                vendor_name=vendor_b_name,
                total_paid=vendor_b_paid,
                transaction_count=vendor_b_count,
            ),
        ]

        analysis = CompensationAnalysis(
            fiscal_year=fiscal_year,
            total_amount=total_amount,
            average_transaction=average_transaction,
            min_transaction=min_transaction,
            max_transaction=max_transaction,
            transaction_count=transaction_count,
            top_vendors=vendors,
        )

        json_str = analysis.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed == {
            "fiscalYear": fiscal_year,
            "totalAmount": total_amount,
            "averageTransaction": average_transaction,
            "minTransaction": min_transaction,
            "maxTransaction": max_transaction,
            "transactionCount": transaction_count,
            "topVendors": [
                {
                    "vendorName": vendor_a_name,
                    "totalPaid": vendor_a_paid,
                    "transactionCount": vendor_a_count,
                },
                {
                    "vendorName": vendor_b_name,
                    "totalPaid": vendor_b_paid,
                    "transactionCount": vendor_b_count,
                },
            ],
        }

    def test_Deserializes_from_camelCase_json(self):
        fiscal_year = 2024
        total_amount = 3000.0
        average_transaction = 1500.0
        min_transaction = 1000.0
        max_transaction = 2000.0
        transaction_count = 2

        vendor_a_name = "Vendor A"
        vendor_a_paid = 1000.0
        vendor_a_count = 1

        vendor_b_name = "Vendor B"
        vendor_b_paid = 2000.0
        vendor_b_count = 2

        json_data = {
            "fiscalYear": fiscal_year,
            "totalAmount": total_amount,
            "averageTransaction": average_transaction,
            "minTransaction": min_transaction,
            "maxTransaction": max_transaction,
            "transactionCount": transaction_count,
            "topVendors": [
                {
                    "vendorName": vendor_a_name,
                    "totalPaid": vendor_a_paid,
                    "transactionCount": vendor_a_count,
                },
                {
                    "vendorName": vendor_b_name,
                    "totalPaid": vendor_b_paid,
                    "transactionCount": vendor_b_count,
                },
            ],
        }

        analysis = CompensationAnalysis.model_validate(json_data)

        assert analysis.fiscal_year == fiscal_year
        assert analysis.total_amount == total_amount
        assert analysis.average_transaction == average_transaction
        assert analysis.min_transaction == min_transaction
        assert analysis.max_transaction == max_transaction
        assert analysis.transaction_count == transaction_count
        assert len(analysis.top_vendors) == 2
        assert analysis.top_vendors[0].vendor_name == vendor_a_name
        assert analysis.top_vendors[0].total_paid == vendor_a_paid
        assert analysis.top_vendors[0].transaction_count == vendor_a_count
        assert analysis.top_vendors[1].vendor_name == vendor_b_name
        assert analysis.top_vendors[1].total_paid == vendor_b_paid
        assert analysis.top_vendors[1].transaction_count == vendor_b_count
