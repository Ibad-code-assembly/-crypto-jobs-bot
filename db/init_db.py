import logging
from .database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Initializing database...")
    init_db()
    logger.info("[OK] Database initialized successfully!")
