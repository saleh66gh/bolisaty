import logging
import os

os.makedirs("Logs", exist_ok=True)

logging.basicConfig(
    filename="Logs/bolisaty.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("bolisaty")