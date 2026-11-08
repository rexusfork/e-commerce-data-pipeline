
import logging

from ecommerce_pipeline.extract import extract_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    logger.info("E-Commerce Data Pipeline started")

    try:
        df = extract_data()

        logger.info("Preview of extracted data:")
        print(df.head(5).to_string(index=False))

        logger.info("Pipeline extraction stage completed")

    except Exception:
        logger.exception("Pipeline execution failed")
        raise


if __name__ == "__main__":
    main()
