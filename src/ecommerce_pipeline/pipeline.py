
import logging

from ecommerce_pipeline.extract import extract_data
from ecommerce_pipeline.transform import transform_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    logger.info("E-Commerce Data Pipeline started")

    try:
        # Step 1: Extract
        raw_df = extract_data()

        # Step 2: Transform
        result = transform_data(raw_df)

        # Step 3: Show transformation metrics
        logger.info("Transformation Summary:")

        for key, value in result.metrics.items():
            logger.info("%s: %s", key, value)

        # Step 4: Preview sales
        print("\n--- SALES PREVIEW ---")
        print(result.sales.head(5).to_string(index=False))

        # Step 5: Preview cancellations
        print("\n--- CANCELLATION PREVIEW ---")
        print(
            result.cancellations.head(5).to_string(index=False)
        )

        logger.info("Extract & Transform completed successfully")

    except Exception:
        logger.exception("Pipeline execution failed")
        raise


if __name__ == "__main__":
    main()
