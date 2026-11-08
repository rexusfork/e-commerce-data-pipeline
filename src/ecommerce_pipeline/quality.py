
import logging

import pandas as pd
import pandera.pandas as pa

from ecommerce_pipeline.transform import TransformationResult

logger = logging.getLogger(__name__)

# Maximum rejected records as a share of output rows.
MAX_REJECTED_RATE = 0.20


# Schema for valid sales
sales_schema = pa.DataFrameSchema(
    {
        "InvoiceNo": pa.Column(nullable=False),
        "StockCode": pa.Column(nullable=False),
        "InvoiceDate": pa.Column(
            pa.DateTime,
            nullable=False,
        ),
        "Quantity": pa.Column(
            checks=pa.Check.gt(0),
            nullable=False,
        ),
        "UnitPrice": pa.Column(
            checks=pa.Check.gt(0),
            nullable=False,
        ),
        "total_amount": pa.Column(
            checks=pa.Check.gt(0),
            nullable=False,
        ),
        "is_anonymous": pa.Column(
            bool,
            nullable=False,
        ),
    },
    strict=False,
)


# Schema for cancellation transactions
cancellation_schema = pa.DataFrameSchema(
    {
        "InvoiceNo": pa.Column(nullable=False),
        "StockCode": pa.Column(nullable=False),
        "InvoiceDate": pa.Column(
            pa.DateTime,
            nullable=False,
        ),
        "Quantity": pa.Column(
            checks=pa.Check.lt(0),
            nullable=False,
        ),
        "UnitPrice": pa.Column(
            checks=pa.Check.gt(0),
            nullable=False,
        ),
        "total_amount": pa.Column(
            checks=pa.Check.lt(0),
            nullable=False,
        ),
    },
    strict=False,
)


def validate_quality(result: TransformationResult) -> dict:
    """
    Validate transformed datasets before loading.

    Raises:
        pandera.errors.SchemaError or SchemaErrors
        when DataFrame validation fails.
        ValueError when business quality rules fail.
    """

    logger.info("Starting data quality validation")

    # 1. Validate sales and cancellation schemas
    sales_schema.validate(result.sales, lazy=True)

    cancellation_schema.validate(
        result.cancellations,
        lazy=True,
    )

    # 2. Validate that sales exist
    if result.sales.empty:
        raise ValueError(
            "Data quality failed: sales dataset is empty"
        )

    # 3. Check source data reconciliation
    metrics = result.metrics

    expected = (
        metrics["duplicate_rows"]
        + metrics["sales_rows"]
        + metrics["cancellation_rows"]
        + metrics["rejected_rows"]
    )

    if expected != metrics["input_rows"]:
        raise ValueError(
            "Data quality failed: row reconciliation mismatch"
        )

    # 4. Validate cancellation invoice prefix
    if not result.cancellations.empty:
        valid_prefix = (
            result.cancellations["InvoiceNo"]
            .astype("string")
            .str.upper()
            .str.startswith("C")
            .fillna(False)
        )

        if not valid_prefix.all():
            raise ValueError(
                "Cancellation invoice prefix validation failed"
            )

    # 5. Calculate rejected data rate
    processed_rows = metrics["output_rows"]

    rejected_rate = (
        metrics["rejected_rows"] / processed_rows
        if processed_rows > 0
        else 0.0
    )

    if rejected_rate > MAX_REJECTED_RATE:
        raise ValueError(
            f"Rejected rate {rejected_rate:.2%} "
            f"exceeds threshold {MAX_REJECTED_RATE:.2%}"
        )

    # 6. Track missing customer identifiers
    anonymous_count = int(
        result.sales["is_anonymous"].sum()
    )

    anonymous_rate = (
        anonymous_count / len(result.sales)
    )

    # 7. Return monitoring metrics
    quality_metrics = {
        "quality_passed": True,
        "rejected_rate": round(rejected_rate, 4),
        "anonymous_rate": round(anonymous_rate, 4),
        "anonymous_sales_rows": anonymous_count,
        "max_rejected_rate": MAX_REJECTED_RATE,
    }

    logger.info(
        "Data quality validation passed: %s",
        quality_metrics,
    )

    return quality_metrics
