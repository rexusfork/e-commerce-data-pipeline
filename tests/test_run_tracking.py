
import pytest

from sqlalchemy import create_engine, text

from config.settings import DATABASE_URL
from ecommerce_pipeline.load import initialize_schema
from ecommerce_pipeline.run_tracking import (
    calculate_file_checksum,
    was_file_processed,
    start_run,
    finish_run_success,
    finish_run_failed,
)


@pytest.fixture
def db_engine():
    test_url = DATABASE_URL.set(database="ecommerce_test")

    assert test_url.database == "ecommerce_test"

    engine = create_engine(test_url)
    initialize_schema(engine)

    yield engine

    engine.dispose()


def test_checksum_is_deterministic(tmp_path):
    file_path = tmp_path / "sample.csv"
    file_path.write_text("id,amount\n1,100\n")

    checksum1 = calculate_file_checksum(file_path)
    checksum2 = calculate_file_checksum(file_path)

    assert checksum1 == checksum2
    assert len(checksum1) == 64


def test_checksum_changes_with_content(tmp_path):
    file_path = tmp_path / "sample.csv"
    file_path.write_text("original data")

    checksum1 = calculate_file_checksum(file_path)

    file_path.write_text("modified data")
    checksum2 = calculate_file_checksum(file_path)

    assert checksum1 != checksum2


def test_successful_file_tracking(db_engine):
    source_key = "test-source-success"
    checksum = "a" * 64

    run_id = start_run(db_engine, source_key, checksum)

    with db_engine.begin() as connection:
        finish_run_success(
            connection,
            run_id,
            {"input_rows": 10},
        )

    assert was_file_processed(
        db_engine, source_key, checksum
    ) is True

    with db_engine.connect() as connection:
        status = connection.execute(
            text("""
                SELECT status
                FROM pipeline_runs
                WHERE run_id = :run_id
            """),
            {"run_id": run_id},
        ).scalar_one()

    assert status == "SUCCESS"


def test_failed_file_can_retry(db_engine):
    source_key = "test-source-failed"
    checksum = "b" * 64

    run_id = start_run(db_engine, source_key, checksum)

    finish_run_failed(
        db_engine,
        run_id,
        RuntimeError("Simulated failure"),
    )

    assert was_file_processed(
        db_engine, source_key, checksum
    ) is False


def test_success_rollback(db_engine):
    source_key = "test-source-rollback"
    checksum = "c" * 64

    run_id = start_run(db_engine, source_key, checksum)

    with pytest.raises(RuntimeError):
        with db_engine.begin() as connection:
            finish_run_success(
                connection, run_id, {"rows": 5}
            )

            raise RuntimeError("Force rollback")

    with db_engine.connect() as connection:
        status = connection.execute(
            text("""
                SELECT status
                FROM pipeline_runs
                WHERE run_id = :run_id
            """),
            {"run_id": run_id},
        ).scalar_one()

    assert status == "RUNNING"
