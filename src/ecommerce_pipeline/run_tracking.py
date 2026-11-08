
import hashlib
import json
import logging
from pathlib import Path

from sqlalchemy import Engine, text

logger = logging.getLogger(__name__)


def calculate_file_checksum(file_path: str | Path) -> str:
    """Calculate SHA-256 without loading the whole file into memory."""

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while chunk := file.read(1024 * 1024):
            sha256.update(chunk)

    return sha256.hexdigest()


def was_file_processed(
    engine: Engine,
    source_key: str,
    checksum: str,
) -> bool:
    """Check whether this file version was loaded successfully."""

    query = text("""
        SELECT EXISTS (
            SELECT 1
            FROM pipeline_runs
            WHERE source_key = :source_key
              AND file_checksum = :checksum
              AND status = 'SUCCESS'
        )
    """)

    with engine.connect() as connection:
        return bool(connection.execute(
            query,
            {"source_key": source_key, "checksum": checksum},
        ).scalar_one())


def start_run(
    engine: Engine,
    source_key: str,
    checksum: str,
) -> int:
    """Create a RUNNING execution record."""

    query = text("""
        INSERT INTO pipeline_runs (
            source_key,
            file_checksum,
            status
        )
        VALUES (
            :source_key,
            :checksum,
            'RUNNING'
        )
        RETURNING run_id
    """)

    with engine.begin() as connection:
        run_id = connection.execute(
            query,
            {"source_key": source_key, "checksum": checksum},
        ).scalar_one()

    logger.info("Started pipeline run: %s", run_id)

    return run_id


def finish_run_success(connection, run_id: int, metrics: dict):
    """Mark run successful within the data loading transaction."""

    connection.execute(
        text("""
            UPDATE pipeline_runs
            SET status = 'SUCCESS',
                finished_at = NOW(),
                duration_seconds =
                    EXTRACT(EPOCH FROM (NOW() - started_at)),
                metrics = CAST(:metrics AS JSONB),
                error_message = NULL
            WHERE run_id = :run_id
              AND status = 'RUNNING'
        """),
        {
            "run_id": run_id,
            "metrics": json.dumps(metrics),
        },
    )


def finish_run_failed(
    engine: Engine,
    run_id: int,
    error: Exception,
):
    """Record a failed execution in a separate transaction."""

    with engine.begin() as connection:
        connection.execute(
            text("""
                UPDATE pipeline_runs
                SET status = 'FAILED',
                    finished_at = NOW(),
                    duration_seconds =
                        EXTRACT(EPOCH FROM (NOW() - started_at)),
                    error_message = :error_message
                WHERE run_id = :run_id
                  AND status = 'RUNNING'
            """),
            {
                "run_id": run_id,
                "error_message": str(error)[:2000],
            },
        )

    logger.error("Pipeline run %s failed", run_id)
