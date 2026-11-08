
import logging
from dataclasses import dataclass

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
}


@dataclass
class TransformationResult:
    sales: pd.DataFrame
    cancellations: pd.DataFrame
    rejected: pd.DataFrame
    metrics: dict


def transform_data(df: pd.DataFrame) -> TransformationResult:
    """
    Clean, validate and classify retail transactions.

    Returns:
        TransformationResult containing sales,
        cancellations, rejected records and metrics.
    """

    logger.info("Starting data transformation")

    # 1. Validate input schema
    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    if df.empty:
        raise ValueError("Input DataFrame cannot be empty")

    # 2. Copy raw dataset to avoid mutation
    data = df.copy()
    total_input = len(data)

    # 3. Remove exact duplicate records
    data = data.drop_duplicates().copy()
    duplicate_count = total_input - len(data)

    logger.info("Removed %s duplicate records", duplicate_count)

    # 4. Normalize string columns
    text_columns = [
        "InvoiceNo",
        "StockCode",
        "Description",
        "Country",
    ]

    for column in text_columns:
        data[column] = (
            data[column]
            .astype("string")
            .str.strip()
        )
        data[column] = data[column].replace("", pd.NA)

    # 5. Normalize numeric and datetime columns
    data["Quantity"] = pd.to_numeric(
        data["Quantity"], errors="coerce"
    )

    data["UnitPrice"] = pd.to_numeric(
        data["UnitPrice"], errors="coerce"
    )

    data["InvoiceDate"] = pd.to_datetime(
        data["InvoiceDate"], errors="coerce"
    )

    data["CustomerID"] = pd.to_numeric(
        data["CustomerID"], errors="coerce"
    ).astype("Int64")

    # 6. Identify cancellation records
    cancellation_mask = (
        data["InvoiceNo"]
        .str.upper()
        .str.startswith("C")
        .fillna(False)
    )

    # 7. Validate shared transaction fields
    missing_required = data[
        ["InvoiceNo", "StockCode", "InvoiceDate",
         "Quantity", "UnitPrice"]
    ].isna().any(axis=1)

    # Validate both sales and cancellations
    invalid_common = (
        missing_required |
        (data["UnitPrice"] <= 0) |
        (data["Quantity"] == 0)
    ).fillna(True)

    # Sales must have positive quantities
    invalid_sales = (
        ~cancellation_mask &
        (data["Quantity"] < 0)
    ).fillna(False)

    # Cancellation lines should have negative quantities
    invalid_cancellations = (
        cancellation_mask &
        (data["Quantity"] >= 0)
    ).fillna(False)

    invalid_mask = (
        invalid_common |
        invalid_sales |
        invalid_cancellations
    )

    # 8. Separate rejected records
    rejected = data.loc[invalid_mask].copy()

    # Add audit reason
    rejected["rejection_reason"] = "Invalid transaction data"

    # 9. Separate valid cancellations
    cancellations = data.loc[
        ~invalid_mask & cancellation_mask
    ].copy()

    # 10. Separate valid sales
    sales = data.loc[
        ~invalid_mask & ~cancellation_mask
    ].copy()

    # 11. Calculate transaction amounts
    sales["total_amount"] = (
        sales["Quantity"] * sales["UnitPrice"]
    ).round(2)

    cancellations["total_amount"] = (
        cancellations["Quantity"] *
        cancellations["UnitPrice"]
    ).round(2)

    # 12. Flag missing customer information
    for frame in (sales, cancellations):
        frame["is_anonymous"] = (
            frame["CustomerID"].isna()
        )

    # 13. Collect transformation metrics
    metrics = {
        "input_rows": total_input,
        "duplicate_rows": duplicate_count,
        "sales_rows": len(sales),
        "cancellation_rows": len(cancellations),
        "rejected_rows": len(rejected),
    }

    metrics["output_rows"] = (
        metrics["sales_rows"] +
        metrics["cancellation_rows"] +
        metrics["rejected_rows"]
    )

    # 14. Data reconciliation
    assert (
        metrics["input_rows"] ==
        metrics["duplicate_rows"] +
        metrics["output_rows"]
    ), "Data reconciliation failed"

    logger.info("Transformation completed: %s", metrics)

    return TransformationResult(
        sales=sales,
        cancellations=cancellations,
        rejected=rejected,
        metrics=metrics,
    )
