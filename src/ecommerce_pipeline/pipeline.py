
import logging

from sqlalchemy import create_engine, text

from config.settings import DATABASE_URL
from ecommerce_pipeline.extract import extract_data
from ecommerce_pipeline.transform import transform_data
from ecommerce_pipeline.load import initialize_schema, load_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    logger.info("E-Commerce ETL Pipeline started")

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )

    try:
        # Extract
        logger.info("STEP 1: Extract")
        raw_df = extract_data()

        # Transform
        logger.info("STEP 2: Transform")
        result = transform_data(raw_df)

        for key, value in result.metrics.items():
            logger.info("%s: %s", key, value)

        # Initialize database
        logger.info("STEP 3: Initialize schema")
        initialize_schema(engine)

        # Load
        logger.info("STEP 4: Load")
        load_metrics = load_data(result, engine)

        for key, value in load_metrics.items():
            logger.info("%s: %s", key, value)

        # Verify persisted counts
        logger.info("STEP 5: Verify database")

        with engine.connect() as connection:
            for table in ("sales", "cancellations", "rejected"):
                count = connection.execute(
                    text(f"SELECT COUNT(*) FROM {table}")
                ).scalar_one()

                logger.info("%s persisted rows: %s", table, count)

        logger.info("ETL Pipeline completed successfully")

    except Exception:
        logger.exception("ETL Pipeline failed")
        raise

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
