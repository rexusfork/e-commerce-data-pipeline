
import hashlib
import json
import logging
from decimal import Decimal
from pathlib import Path

import pandas as pd
from sqlalchemy import Engine, text

from ecommerce_pipeline.transform import TransformationResult

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]


def normalize_value(value):
    """Convert Pandas values into stable serializable values."""

    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    return str(value)


def generate_source_hash(row: pd.Series) -> str:
    """Generate a deterministic fingerprint from source fields."""

    payload = {
        column: normalize_value(row[column])
        for column in SOURCE_COLUMNS
    }

    serialized = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def prepare_transaction_rows(df: pd.DataFrame) -> list[dict]:
    """Prepare validated sales or cancellation records."""

    rows = []

    for _, row in df.iterrows():
        customer_id = row["CustomerID"]

        rows.append({
            "source_hash": generate_source_hash(row),
            "invoice_no": str(row["InvoiceNo"]),
            "stock_code": str(row["StockCode"]),
            "description": normalize_value(row["Description"]),
            "quantity": Decimal(str(row["Quantity"])),
            "invoice_date": row["InvoiceDate"].to_pydatetime(),
            "unit_price": Decimal(str(row["UnitPrice"])),
            "total_amount": Decimal(str(row["total_amount"])),
            "customer_id": (
                None if pd.isna(customer_id)
                else int(customer_id)
            ),
            "country": normalize_value(row["Country"]),
            "is_anonymous": bool(row["is_anonymous"]),
        })

    return rows


def prepare_rejected_rows(df: pd.DataFrame) -> list[dict]:
    """Preserve rejected records for auditing."""

    rows = []

    for _, row in df.iterrows():
        raw_record = {
            column: normalize_value(row[column])
            for column in SOURCE_COLUMNS
        }

        rows.append({
            "source_hash": generate_source_hash(row),
            "raw_record": json.dumps(raw_record, ensure_ascii=False),
            "rejection_reason": str(row["rejection_reason"]),
        })

    return rows


def initialize_schema(engine: Engine) -> None:
    """Create database tables and indexes."""

    schema_file = PROJECT_ROOT / "sql" / "schema.sql"
    schema_sql = schema_file.read_text(encoding="utf-8")

    # The current schema contains simple SQL statements
    # without semicolons inside procedural SQL or strings.
    statements = [
        statement.strip()
        for statement in schema_sql.split(";")
        if statement.strip()
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.exec_driver_sql(statement)

    logger.info("Database schema initialized")


INSERT_TRANSACTION_SQL = text("""
    INSERT INTO {table} (
        source_hash,
        invoice_no,
        stock_code,
        description,
        quantity,
        invoice_date,
        unit_price,
        total_amount,
        customer_id,
        country,
        is_anonymous
    )
    VALUES (
        :source_hash,
        :invoice_no,
        :stock_code,
        :description,
        :quantity,
        :invoice_date,
        :unit_price,
        :total_amount,
        :customer_id,
        :country,
        :is_anonymous
    )
    ON CONFLICT (source_hash) DO NOTHING
""".replace("{table}", "sales"))

# Table names are fixed in code, never supplied by users.
CANCELLATION_SQL = text(
    INSERT_TRANSACTION_SQL.text.replace(
        "INSERT INTO sales",
        "INSERT INTO cancellations"
    )
)

INSERT_REJECTED_SQL = text("""
    INSERT INTO rejected (
        source_hash,
        raw_record,
        rejection_reason
    )
    VALUES (
        :source_hash,
        CAST(:raw_record AS JSONB),
        :rejection_reason
    )
    ON CONFLICT (source_hash) DO NOTHING
""")


def insert_batches(connection, statement, rows, batch_size=1000):
    """Insert records in manageable batches."""

    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]
        connection.execute(statement, batch)



def load_data(
    result: TransformationResult,
    engine: Engine,
    connection=None,
) -> dict:
    """
    Load transformed datasets into PostgreSQL.

    If a connection is provided, use the caller's
    transaction. Otherwise, create a new transaction.
    """

    logger.info("Starting data loading")

    sales_rows = prepare_transaction_rows(result.sales)

    cancellation_rows = prepare_transaction_rows(
        result.cancellations
    )

    rejected_rows = prepare_rejected_rows(result.rejected)

    def execute_load(conn):
        insert_batches(
            conn,
            INSERT_TRANSACTION_SQL,
            sales_rows,
        )

        insert_batches(
            conn,
            CANCELLATION_SQL,
            cancellation_rows,
        )

        insert_batches(
            conn,
            INSERT_REJECTED_SQL,
            rejected_rows,
        )

    if connection is not None:
        execute_load(connection)
    else:
        with engine.begin() as conn:
            execute_load(conn)

    metrics = {
        "sales_attempted": len(sales_rows),
        "cancellations_attempted": len(cancellation_rows),
        "rejected_attempted": len(rejected_rows),
    }

    logger.info("Data loading completed: %s", metrics)

    return metrics

