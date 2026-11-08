
import logging
import time

from pathlib import Path
from sqlalchemy import create_engine
from ecommerce_pipeline.quality import validate_quality

from config.settings import DATABASE_URL
from ecommerce_pipeline.extract import (
    DEFAULT_DATASET_PATH,
    extract_data,
)
from ecommerce_pipeline.transform import transform_data
from ecommerce_pipeline.load import initialize_schema, load_data
from ecommerce_pipeline.run_tracking import (
    calculate_file_checksum,
    was_file_processed,
    start_run,
    finish_run_success,
    finish_run_failed,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    start_time = time.perf_counter()

    file_path = Path(DEFAULT_DATASET_PATH).resolve()
    source_key = str(file_path)

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )

    run_id = None

    try:
        logger.info("E-Commerce ETL Pipeline started")

        # 1. Create tables if needed
        initialize_schema(engine)

        # 2. Validate source file and calculate checksum
        if not file_path.is_file():
            raise FileNotFoundError(
                f"Dataset not found: {file_path}"
            )

        checksum = calculate_file_checksum(file_path)

        logger.info("Source checksum: %s", checksum)

        # 3. Skip unchanged file
        if was_file_processed(engine, source_key, checksum):
            logger.info(
                "SKIPPED: This file version was already processed"
            )
            return

        # 4. Start execution tracking
        run_id = start_run(engine, source_key, checksum)

        # 5. Extract
        extract_start = time.perf_counter()
        raw_df = extract_data(file_path)
        extract_seconds = time.perf_counter() - extract_start

        # 6. Transform
        transform_start = time.perf_counter()
        result = transform_data(raw_df)
        transform_seconds = time.perf_counter() - transform_start
        
        # 7. Data Quality Gate
        quality_start = time.perf_counter()

        quality_metrics = validate_quality(result)

        quality_seconds = (
            time.perf_counter() - quality_start
        )

        logger.info(
            "Quality validation completed in %.3f seconds",
            quality_seconds,
)

        # 7. Load + mark success atomically
        load_start = time.perf_counter()

        with engine.begin() as connection:
            load_metrics = load_data(
                result,
                engine,
                connection=connection,
            )

            load_seconds = time.perf_counter() - load_start

            
            metrics = {
                **result.metrics,
                **load_metrics,
                **quality_metrics,
                "extract_seconds": round(extract_seconds, 3),
                "transform_seconds": round(transform_seconds, 3),
                "quality_seconds": round(quality_seconds, 3),
                "load_seconds": round(load_seconds, 3),
            }


            finish_run_success(
                connection,
                run_id,
                metrics,
            )

        logger.info("Pipeline run %s SUCCESS", run_id)

        for key, value in metrics.items():
            logger.info("%s: %s", key, value)

    except Exception as exc:
        logger.exception("ETL Pipeline failed")

        if run_id is not None:
            try:
                finish_run_failed(engine, run_id, exc)
            except Exception:
                logger.exception(
                    "Failed to persist FAILED status"
                )

        raise

    finally:
        duration = time.perf_counter() - start_time

        logger.info(
            "Total execution time: %.2f seconds",
            duration,
        )

        engine.dispose()


if __name__ == "__main__":
    main()
