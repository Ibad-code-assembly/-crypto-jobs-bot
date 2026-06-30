import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import SessionLocal, init_db
from db.models import Job, Subscription
from db.queries import (
    insert_or_update_jobs,
    mark_expired_jobs,
    get_jobs_by_coin,
    find_new_jobs,
    find_expiring_jobs,
    add_subscription,
    remove_subscription,
    get_user_subscriptions,
    get_subscribers_for_coin,
    job_exists,
    get_all_active_jobs,
    get_job_count,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_insert_and_dedup():
    """Test inserting jobs and deduplication."""
    logger.info("\n" + "="*70)
    logger.info("TEST 1: Insert Jobs and Deduplication")
    logger.info("="*70)

    db = SessionLocal()

    sample_jobs = [
        {
            "title": "Smart Contract Engineer",
            "company": "Uniswap Labs",
            "location": "Remote",
            "url": "https://example.com/job1",
            "source_site": "web3.career",
            "scraped_at": datetime.utcnow(),
            "coin_ticker": "UNI",
        },
        {
            "title": "Backend Developer",
            "company": "Chainlink",
            "location": "Remote",
            "url": "https://example.com/job2",
            "source_site": "cryptojobs.com",
            "scraped_at": datetime.utcnow(),
            "coin_ticker": "LINK",
        },
    ]

    # Insert new jobs
    new, updated = insert_or_update_jobs(sample_jobs, db)
    logger.info(f"[Result] Inserted: {new}, Updated: {updated}")
    assert new == 2 and updated == 0, "Should insert 2 new jobs"

    # Insert same jobs again (dedup test)
    new, updated = insert_or_update_jobs(sample_jobs, db)
    logger.info(f"[Result] Inserted: {new}, Updated: {updated}")
    assert new == 0 and updated == 2, "Should find 2 existing jobs (dedup)"

    logger.info("[OK] Deduplication test passed!")
    db.close()


def test_query_by_coin():
    """Test querying jobs by coin ticker."""
    logger.info("\n" + "="*70)
    logger.info("TEST 2: Query Jobs by Coin Ticker")
    logger.info("="*70)

    db = SessionLocal()

    jobs = get_jobs_by_coin("UNI", db)
    logger.info(f"[Result] Found {len(jobs)} jobs for UNI")
    assert len(jobs) >= 1, "Should find at least 1 UNI job"
    logger.info(f"[Sample] {jobs[0].title} @ {jobs[0].company}")

    logger.info("[OK] Query by coin test passed!")
    db.close()


def test_new_jobs():
    """Test finding new jobs."""
    logger.info("\n" + "="*70)
    logger.info("TEST 3: Find New Jobs (Last 24 Hours)")
    logger.info("="*70)

    db = SessionLocal()

    new_jobs = find_new_jobs(hours=24, db=db)
    logger.info(f"[Result] Found {len(new_jobs)} new jobs in last 24 hours")
    if new_jobs:
        logger.info(f"[Sample] {new_jobs[0].title} (created {new_jobs[0].created_at})")

    logger.info("[OK] Find new jobs test passed!")
    db.close()


def test_subscriptions():
    """Test subscription functions."""
    logger.info("\n" + "="*70)
    logger.info("TEST 4: Subscriptions")
    logger.info("="*70)

    db = SessionLocal()

    # Add subscriptions
    test_user_id = 12345
    success1 = add_subscription(test_user_id, "BTC", db)
    logger.info(f"[Result] Add BTC subscription: {success1}")
    assert success1, "Should add subscription"

    success2 = add_subscription(test_user_id, "ETH", db)
    logger.info(f"[Result] Add ETH subscription: {success2}")
    assert success2, "Should add second subscription"

    # Try adding duplicate
    success_dup = add_subscription(test_user_id, "BTC", db)
    logger.info(f"[Result] Add duplicate BTC subscription: {success_dup}")
    assert not success_dup, "Should reject duplicate subscription"

    # Get user subscriptions
    subs = get_user_subscriptions(test_user_id, db)
    logger.info(f"[Result] User {test_user_id} subscribed to: {subs}")
    assert set(subs) == {"BTC", "ETH"}, "Should have BTC and ETH"

    # Get subscribers for coin
    subscribers = get_subscribers_for_coin("BTC", db)
    logger.info(f"[Result] Subscribers for BTC: {subscribers}")
    assert test_user_id in subscribers, "User should be in BTC subscribers"

    # Remove subscription
    removed = remove_subscription(test_user_id, "BTC", db)
    logger.info(f"[Result] Remove BTC subscription: {removed}")
    assert removed, "Should remove subscription"

    subs_after = get_user_subscriptions(test_user_id, db)
    logger.info(f"[Result] User subscriptions after removal: {subs_after}")
    assert "BTC" not in subs_after, "BTC should be removed"

    logger.info("[OK] Subscription test passed!")
    db.close()


def test_job_existence():
    """Test job existence check."""
    logger.info("\n" + "="*70)
    logger.info("TEST 5: Job Existence Check")
    logger.info("="*70)

    db = SessionLocal()

    # Create a hash for existing job
    existing_job = db.query(Job).first()
    if existing_job:
        exists = job_exists(existing_job.job_hash, db)
        logger.info(f"[Result] Existing job exists: {exists}")
        assert exists, "Should find existing job"
    else:
        logger.warning("No jobs in database to test")

    # Test non-existent job
    fake_hash = "0" * 64
    exists_fake = job_exists(fake_hash, db)
    logger.info(f"[Result] Fake job exists: {exists_fake}")
    assert not exists_fake, "Should not find fake job"

    logger.info("[OK] Job existence test passed!")
    db.close()


def test_get_all_jobs():
    """Test getting all active jobs."""
    logger.info("\n" + "="*70)
    logger.info("TEST 6: Get All Active Jobs")
    logger.info("="*70)

    db = SessionLocal()

    all_jobs = get_all_active_jobs(db)
    count = get_job_count(db)
    logger.info(f"[Result] Total active jobs: {count}")
    logger.info(f"[Result] get_all_active_jobs returned: {len(all_jobs)}")
    assert len(all_jobs) == count, "Counts should match"

    if all_jobs:
        logger.info(f"[Samples]")
        for i, job in enumerate(all_jobs[:3], 1):
            logger.info(f"  {i}. {job.title} @ {job.company}")

    logger.info("[OK] Get all jobs test passed!")
    db.close()


def test_mark_expired():
    """Test marking jobs as expired."""
    logger.info("\n" + "="*70)
    logger.info("TEST 7: Mark Expired Jobs")
    logger.info("="*70)

    db = SessionLocal()

    # Get active jobs from web3.career
    web3_jobs = db.query(Job).filter(
        Job.source_site == "web3.career",
        Job.is_active == True
    ).all()

    if web3_jobs:
        urls_to_keep = [job.url for job in web3_jobs[:1]]
        expired_count = mark_expired_jobs("web3.career", urls_to_keep, db)
        logger.info(f"[Result] Marked {expired_count} jobs as expired")

        # Verify
        remaining = db.query(Job).filter(
            Job.source_site == "web3.career",
            Job.is_active == True
        ).count()
        logger.info(f"[Result] Remaining active jobs from web3.career: {remaining}")
    else:
        logger.info("[Skip] No web3.career jobs to test expiration")

    logger.info("[OK] Mark expired test passed!")
    db.close()


def run_all_tests():
    """Run all tests."""
    logger.info("\n" + "█"*70)
    logger.info("DATABASE LAYER TEST SUITE")
    logger.info("█"*70)

    try:
        # Initialize database
        logger.info("\nInitializing database...")
        init_db()
        logger.info("[OK] Database initialized")

        # Run tests
        test_insert_and_dedup()
        test_query_by_coin()
        test_new_jobs()
        test_subscriptions()
        test_job_existence()
        test_get_all_jobs()
        test_mark_expired()

        logger.info("\n" + "█"*70)
        logger.info("ALL TESTS PASSED!")
        logger.info("█"*70 + "\n")

    except AssertionError as e:
        logger.error(f"\n[FAILED] Test assertion failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n[FAILED] Test error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
