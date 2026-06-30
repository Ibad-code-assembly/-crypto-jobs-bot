import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import init_db, SessionLocal
from db.models import Job
from scraper.scheduler import JobScheduler
from scraper.diff_tracker import read_latest_diff, read_diffs_since, get_diff_stats

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_scheduler():
    """Test scheduler with manual run."""
    logger.info("\n" + "█"*70)
    logger.info("SCHEDULER TEST: Manual Run")
    logger.info("█"*70)

    # Initialize database
    logger.info("\n[INIT] Initializing database...")
    init_db()

    # Create scheduler
    logger.info("\n[SCHEDULER] Creating JobScheduler...")
    scheduler = JobScheduler()

    # Run scrapers once
    logger.info("\n[RUN 1] Starting first scrape run...")
    result1 = await scheduler.run_all_scrapers()

    logger.info(f"\n[RESULT 1]")
    logger.info(f"  New: {result1['new']}")
    logger.info(f"  Updated: {result1['updated']}")
    logger.info(f"  Mapped: {result1['mapped']}")
    logger.info(f"  Expired: {result1['expired']}")
    logger.info(f"  Errors: {len(result1['errors'])}")
    if result1['errors']:
        for err in result1['errors']:
            logger.info(f"    - {err}")

    logger.info(f"\n[SOURCES]")
    for source, count in result1['source_summary'].items():
        logger.info(f"  {source}: {count}")

    # Check database
    db = SessionLocal()
    total_jobs = db.query(Job).filter(Job.is_active == True).count()
    mapped_jobs = db.query(Job).filter(
        Job.is_active == True,
        Job.coin_ticker != None
    ).count()
    logger.info(f"\n[DATABASE]")
    logger.info(f"  Total active jobs: {total_jobs}")
    logger.info(f"  Jobs with coin_ticker: {mapped_jobs}")

    # Check diff file
    latest_diff = read_latest_diff()
    logger.info(f"\n[DIFF FILE]")
    if latest_diff:
        logger.info(f"  Latest diff timestamp: {latest_diff['timestamp']}")
        logger.info(f"  New jobs in diff: {latest_diff['total_new']}")
        logger.info(f"  Expired count: {latest_diff['total_expired']}")
    else:
        logger.info(f"  No diffs found")

    # Wait a bit and run again to test dedup
    logger.info(f"\n[WAIT] Waiting 2 seconds before second run...")
    await asyncio.sleep(2)

    logger.info(f"\n[RUN 2] Starting second scrape run (dedup test)...")
    result2 = await scheduler.run_all_scrapers()

    logger.info(f"\n[RESULT 2 - DEDUP CHECK]")
    logger.info(f"  New: {result2['new']} (should be 0 - all jobs already exist)")
    logger.info(f"  Updated: {result2['updated']} (should be > 0 - reactivating existing)")
    logger.info(f"  Mapped: {result2['mapped']}")
    logger.info(f"  Expired: {result2['expired']}")

    # Check if dedup worked
    db.close()
    db = SessionLocal()
    total_jobs_after = db.query(Job).filter(Job.is_active == True).count()
    logger.info(f"\n[DEDUP VERIFICATION]")
    logger.info(f"  Jobs before: {total_jobs}")
    logger.info(f"  Jobs after: {total_jobs_after}")
    logger.info(f"  Increase: {total_jobs_after - total_jobs} (should be 0 if dedup worked)")

    if result2['new'] == 0:
        logger.info(f"  [OK] Deduplication working correctly!")
    else:
        logger.warning(f"  [WARNING] Found new jobs on second run - may indicate dedup issue")

    # Check diffs
    all_diffs = read_diffs_since(1)
    logger.info(f"\n[DIFFS]")
    logger.info(f"  Total diffs in last hour: {len(all_diffs)}")

    stats = get_diff_stats(1)
    logger.info(f"\n[STATS - Last Hour]")
    logger.info(f"  Run count: {stats['run_count']}")
    logger.info(f"  Total new: {stats['total_new_jobs']}")
    logger.info(f"  Total expired: {stats['total_expired_jobs']}")
    logger.info(f"  Average per run: {stats['avg_per_run']:.1f}")

    db.close()

    logger.info(f"\n" + "█"*70)
    logger.info("SCHEDULER TEST COMPLETED")
    logger.info("█"*70 + "\n")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_scheduler())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        sys.exit(1)
