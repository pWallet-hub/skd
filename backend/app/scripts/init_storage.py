"""Create the SeaweedFS buckets if they don't exist. Run automatically on backend start."""

import logging
import time

from botocore.exceptions import BotoCoreError, ClientError

from app.core.storage import ensure_buckets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("init_storage")


def main(retries: int = 15) -> None:
    for attempt in range(1, retries + 1):
        try:
            ensure_buckets()
            logger.info("Storage buckets ready")
            return
        except (BotoCoreError, ClientError) as exc:
            logger.warning("Storage not ready (attempt %s/%s): %s", attempt, retries, exc)
            time.sleep(2)
    raise SystemExit("Could not initialise object storage")


if __name__ == "__main__":
    main()
