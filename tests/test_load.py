
import pandas as pd
import pytest

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from config.settings import DATABASE_URL
from ecommerce_pipeline.transform import transform_data
from ecommerce_pipeline.load import initialize_schema, load_data


@pytest.fixture
def db_engine():
    # Always use a dedicated testing database.
    test_url = DATABASE_URL.set(database="ecommerce_test")
    engine = create_engine(test_url, pool_pre_ping=True)

    if engine.url.database != "ecommerce_test":
        raise RuntimeError("Unsafe integration test database")

    try:
        initialize_schema(engine)

        with engine.begin() as conn:
            conn.execute(text(
                "TRUNCATE TABLE sales, cancellations, rejected"
            ))

        yield engine

    finally:
        with engine.begin() as conn:
            conn.execute(text(
                "TRUNCATE TABLE sales, cancellations, rejected"
            ))

        engine.dispose()


@pytest.fixture
def sample_result():
    df = pd.DataFrame({
        "InvoiceNo": ["1001", "1002", "C1003", "1004"],
        "StockCode": ["A01", "B01", "C01", "D01"],
        "Description": ["A", "B", "C", "D"],
        "Quantity": [2, 3, -1, 1],
        "InvoiceDate": ["2024-01-01"] * 4,
        "UnitPrice": [10.0, 5.0, 10.0, 0.0],
        "CustomerID": [101, 102, 103, None],
        "Country": ["United Kingdom"] * 4,
    })

    return transform_data(df)


def count_rows(engine, table):
    # Fixed table names only.
    assert table in {"sales", "cancellations", "rejected"}

    with engine.connect() as conn:
        return conn.execute(
            text(f"SELECT COUNT(*) FROM {table}")
        ).scalar_one()


def test_load_success(db_engine, sample_result):
    load_data(sample_result, db_engine)

    assert count_rows(db_engine, "sales") == 2
    assert count_rows(db_engine, "cancellations") == 1
    assert count_rows(db_engine, "rejected") == 1


def test_load_is_idempotent(db_engine, sample_result):
    load_data(sample_result, db_engine)
    load_data(sample_result, db_engine)

    assert count_rows(db_engine, "sales") == 2
    assert count_rows(db_engine, "cancellations") == 1
    assert count_rows(db_engine, "rejected") == 1


def test_transaction_rollback(db_engine, sample_result):
    # Inject invalid data to trigger PostgreSQL CHECK.
    sample_result.sales.loc[
        sample_result.sales.index[1], "Quantity"
    ] = -999

    with pytest.raises(IntegrityError):
        load_data(sample_result, db_engine)

    # All inserts must be rolled back.
    assert count_rows(db_engine, "sales") == 0
    assert count_rows(db_engine, "cancellations") == 0
    assert count_rows(db_engine, "rejected") == 0
