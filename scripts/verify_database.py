
import logging

from sqlalchemy import create_engine, text

from config.settings import DATABASE_URL


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def verify_database():
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )

    try:
        with engine.connect() as connection:
            sales = connection.execute(
                text("SELECT COUNT(*) FROM sales")
            ).scalar_one()

            cancellations = connection.execute(
                text("SELECT COUNT(*) FROM cancellations")
            ).scalar_one()

            rejected = connection.execute(
                text("SELECT COUNT(*) FROM rejected")
            ).scalar_one()

            successful_runs = connection.execute(
                text("""
                    SELECT COUNT(*)
                    FROM pipeline_runs
                    WHERE status = 'SUCCESS'
                """)
            ).scalar_one()

        logger.info("Sales rows: %s", sales)
        logger.info("Cancellation rows: %s", cancellations)
        logger.info("Rejected rows: %s", rejected)
        logger.info("Successful ETL runs: %s", successful_runs)

        if sales <= 0:
            raise RuntimeError("Sales table is empty")

        if successful_runs <= 0:
            raise RuntimeError(
                "No successful pipeline execution found"
            )

        logger.info("Database verification passed")

    finally:
        engine.dispose()


if __name__ == "__main__":
    verify_database()
