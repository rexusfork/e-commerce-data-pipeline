
import pandas as pd
import pytest

from pandera.errors import SchemaErrors

from ecommerce_pipeline.transform import transform_data
from ecommerce_pipeline.quality import validate_quality


@pytest.fixture
def transformed_sample():
    df = pd.DataFrame({
        "InvoiceNo": ["1001", "1002", "C1003", "1004"],
        "StockCode": ["A01", "B01", "C01", "D01"],
        "Description": ["A", "B", "C", "D"],
        "Quantity": [2, 3, -1, 1],
        "InvoiceDate": ["2024-01-01"] * 4,
        "UnitPrice": [10.0, 5.0, 10.0, 5.0],
        "CustomerID": [101, None, 103, 104],
        "Country": ["United Kingdom"] * 4,
    })

    return transform_data(df)


def test_quality_success(transformed_sample):
    metrics = validate_quality(transformed_sample)

    assert metrics["quality_passed"] is True


def test_negative_sales_quantity(transformed_sample):
    transformed_sample.sales.loc[
        transformed_sample.sales.index[0],
        "Quantity",
    ] = -10

    with pytest.raises(SchemaErrors):
        validate_quality(transformed_sample)


def test_invalid_unit_price(transformed_sample):
    transformed_sample.sales.loc[
        transformed_sample.sales.index[0],
        "UnitPrice",
    ] = 0

    with pytest.raises(SchemaErrors):
        validate_quality(transformed_sample)


def test_reconciliation_failure(transformed_sample):
    transformed_sample.metrics["input_rows"] += 1

    with pytest.raises(ValueError, match="reconciliation"):
        validate_quality(transformed_sample)


def test_rejected_rate_threshold(transformed_sample):
    transformed_sample.metrics["rejected_rows"] = 2
    transformed_sample.metrics["output_rows"] = 6
    transformed_sample.metrics["input_rows"] = 6

    with pytest.raises(ValueError, match="Rejected rate"):
        validate_quality(transformed_sample)
