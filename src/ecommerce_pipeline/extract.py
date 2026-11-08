
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DATASET_PATH = (
    PROJECT_ROOT / "data" / "raw" / "Online Retail.xlsx"
)

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


def extract_data(file_path: str | Path = DEFAULT_DATASET_PATH) -> pd.DataFrame:
    """
    Extract raw transaction data from an Excel file.

    Args:
        file_path: Location of the Excel dataset.

    Returns:
        DataFrame containing raw transaction records.

    Raises:
        FileNotFoundError: Dataset does not exist.
        ValueError: Dataset is empty or missing required columns.
        RuntimeError: Excel file cannot be read.
    """

    path = Path(file_path)

    logger.info("Starting data extraction: %s", path)

    # 1. Check file existence
    if not path.is_file():
        logger.error("Dataset not found: %s", path)
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )

    # 2. Read raw Excel data
    try:
        df = pd.read_excel(
            path,
            engine="openpyxl",
            dtype={
                "InvoiceNo": str,
                "StockCode": str,
            },
        )

    except (OSError, ValueError, ImportError, KeyError) as exc:
        logger.exception("Failed to read dataset")
        raise RuntimeError(
            f"Unable to read Excel dataset: {path}"
        ) from exc

    # 3. Validate dataset
    if df.empty:
        logger.error("Dataset is empty")
        raise ValueError("Dataset cannot be empty")

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        logger.error(
            "Missing required columns: %s",
            sorted(missing_columns),
        )

        raise ValueError(
            f"Missing columns: {sorted(missing_columns)}"
        )

    # 4. Log extraction result
    logger.info("Extraction completed successfully")
    logger.info("Total rows: %s", len(df))
    logger.info("Total columns: %s", len(df.columns))
    logger.info("Memory usage: %.2f MB",
                df.memory_usage(deep=True).sum() / (1024 ** 2))

    return df
