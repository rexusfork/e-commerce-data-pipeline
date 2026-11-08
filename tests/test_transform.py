
import pandas as pd
import pytest

from ecommerce_pipeline.transform import transform_data


@pytest.fixture
def sample_transactions():
    return pd.DataFrame({
        "InvoiceNo": [
            "536365",
            "536365",
            "536366",
            "C536367",
            "536368",
            "536369",
            "536370",
            "536370",
        ],
        "StockCode": [
            "A01", "B01", "C01", "D01",
            "E01", "F01", "G01", "G01",
        ],
        "Description": [
            "Product A", "Product B", "Product C",
            "Product D", "Product E", "Product F",
            "Product G", "Product G",
        ],
        "Quantity": [
            2, 3, 1, -2, 1, -3, 2, 2
        ],
        "InvoiceDate": [
            "2010-12-01 08:26:00"
        ] * 8,
        "UnitPrice": [
            10.0, 5.0, 20.0, 10.0,
            0.0, 5.0, 8.0, 8.0,
        ],
        "CustomerID": [
            17850, 17850, None, 17850,
            17850, 17850, 17850, 17850,
        ],
        "Country": ["United Kingdom"] * 8,
    })


def test_remove_exact_duplicates(sample_transactions):
    result = transform_data(sample_transactions)

    assert result.metrics["duplicate_rows"] == 1


def test_preserve_invoice_line_items(sample_transactions):
    result = transform_data(sample_transactions)

    lines = result.sales[
        result.sales["InvoiceNo"] == "536365"
    ]

    assert len(lines) == 2


def test_missing_customer_is_preserved(sample_transactions):
    result = transform_data(sample_transactions)

    row = result.sales[
        result.sales["InvoiceNo"] == "536366"
    ].iloc[0]

    assert bool(row["is_anonymous"]) is True


def test_cancellation_classification(sample_transactions):
    result = transform_data(sample_transactions)

    assert len(result.cancellations) == 1
    assert (
        result.cancellations.iloc[0]["InvoiceNo"]
        == "C536367"
    )


def test_invalid_price_is_rejected(sample_transactions):
    result = transform_data(sample_transactions)

    rejected = result.rejected["InvoiceNo"].tolist()

    assert "536368" in rejected


def test_negative_sales_quantity_is_rejected(sample_transactions):
    result = transform_data(sample_transactions)

    rejected = result.rejected["InvoiceNo"].tolist()

    assert "536369" in rejected


def test_total_amount_calculation(sample_transactions):
    result = transform_data(sample_transactions)

    row = result.sales[
        result.sales["StockCode"] == "A01"
    ].iloc[0]

    assert row["total_amount"] == 20.0


def test_reconciliation(sample_transactions):
    result = transform_data(sample_transactions)
    m = result.metrics

    assert m["input_rows"] == (
        m["duplicate_rows"] + m["output_rows"]
    )


def test_missing_required_column(sample_transactions):
    invalid = sample_transactions.drop(
        columns=["InvoiceNo"]
    )

    with pytest.raises(ValueError, match="Missing required"):
        transform_data(invalid)


def test_empty_dataframe(sample_transactions):
    empty = sample_transactions.iloc[0:0]

    with pytest.raises(ValueError, match="empty"):
        transform_data(empty)
