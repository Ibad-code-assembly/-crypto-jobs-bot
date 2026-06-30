import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from db.database import init_db
from scraper.scheduler import JobScheduler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point - initialize and run scheduler."""
    logger.info("="*70)
    logger.info("CRYPTO JOBS BOT - SCHEDULER")
    logger.info("="*70)

    # Initialize database
    logger.info("\n[INIT] Initializing database...")
    init_db()
    logger.info("[OK] Database initialized")

    # Create scheduler
    logger.info("\n[SCHEDULER] Creating JobScheduler...")
    scheduler = JobScheduler()

    # Run first scrape immediately
    logger.info("\n[FIRST RUN] Running scrapers immediately...")
    result = await scheduler.run_all_scrapers()
    logger.info(f"[RESULT] New: {result['new']}, Updated: {result['updated']}, Expired: {result['expired']}")

    # Start periodic scheduler (60 minutes)
    logger.info("\n[SCHEDULER] Starting periodic scraping (every 60 minutes)...")
    await scheduler.start(interval_minutes=60)

    # Setup graceful shutdown
    def signal_handler(sig, frame):
        logger.info("\n[SHUTDOWN] Received shutdown signal...")
        asyncio.create_task(scheduler.stop())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Keep running
    logger.info("\n[RUNNING] Scheduler is running. Press Ctrl+C to stop.")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n[SHUTDOWN] Keyboard interrupt received")
        await scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())
