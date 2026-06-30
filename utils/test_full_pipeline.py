import logging
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import SessionLocal
from db.models import Job
from db.queries import insert_or_update_jobs, map_jobs_to_coins, get_all_active_jobs
from utils.coin_mapper import get_unmatched_companies, clear_unmatched_log

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_full_pipeline():
    """Test complete pipeline: insert jobs -> map to coins -> verify."""
    logger.info("\n" + "="*70)
    logger.info("FULL PIPELINE TEST: Jobs -> Coin Mapping -> Database Verification")
    logger.info("="*70)

    db = SessionLocal()

    # Clear unmatched log for clean test
    clear_unmatched_log()

    # Step 1: Create sample jobs
    logger.info("\n[STEP 1] Create Sample Jobs")
    logger.info("-" * 70)

    sample_jobs = [
        {
            "title": "Smart Contract Developer",
            "company": "Chainlink Labs",
            "location": "Remote",
            "url": "https://example.com/job/chainlink-dev",
            "source_site": "web3.career",
            "scraped_at": datetime.utcnow(),
        },
        {
            "title": "Backend Engineer",
            "company": "Uniswap Labs",
            "location": "New York, NY",
            "url": "https://example.com/job/uniswap-backend",
            "source_site": "cryptojobs.com",
            "scraped_at": datetime.utcnow(),
        },
        {
            "title": "Governance Lead",
            "company": "Aave",
            "location": "Remote",
            "url": "https://example.com/job/aave-governance",
            "source_site": "web3.career",
            "scraped_at": datetime.utcnow(),
        },
        {
            "title": "Product Manager",
            "company": "Coinbase",
            "location": "San Francisco, CA",
            "url": "https://example.com/job/coinbase-pm",
            "source_site": "cryptojobslist.com",
            "scraped_at": datetime.utcnow(),
        },
        {
            "title": "Full Stack Engineer",
            "company": "Some Random Company",
            "location": "Remote",
            "url": "https://example.com/job/random-fullstack",
            "source_site": "web3.career",
            "scraped_at": datetime.utcnow(),
        },
    ]

    new_count, updated_count = insert_or_update_jobs(sample_jobs, db)
    logger.info(f"[Result] Inserted: {new_count}, Updated: {updated_count}")

    # Step 2: Retrieve jobs from database
    logger.info("\n[STEP 2] Retrieve Jobs from Database")
    logger.info("-" * 70)

    all_jobs = get_all_active_jobs(db)
    logger.info(f"[Result] Total active jobs: {len(all_jobs)}")

    # Step 3: Map jobs to coins
    logger.info("\n[STEP 3] Map Jobs to Coins")
    logger.info("-" * 70)

    sample_jobs_obj = [job for job in all_jobs if job.company in [
        "Chainlink Labs", "Uniswap Labs", "Aave", "Coinbase", "Some Random Company"
    ]]

    logger.info(f"Jobs to map: {len(sample_jobs_obj)}")
    for job in sample_jobs_obj:
        logger.info(f"  - {job.company} (current ticker: {job.coin_ticker})")

    # Call map_jobs_to_coins
    mapped_jobs = map_jobs_to_coins(sample_jobs_obj, db)

    logger.info(f"[Result] Mapped {len(mapped_jobs)} jobs")

    # Step 4: Verify mappings
    logger.info("\n[STEP 4] Verify Coin Mappings")
    logger.info("-" * 70)

    expected_mappings = {
        "Chainlink Labs": "LINK",
        "Uniswap Labs": "UNI",
        "Aave": "AAVE",
        "Coinbase": None,  # Should not have an alias, fuzzy might work
        "Some Random Company": None,
    }

    passed = 0
    failed = 0

    for job in mapped_jobs:
        expected = expected_mappings.get(job.company)
        actual = job.coin_ticker

        # For Coinbase, allow fuzzy match (if it exists)
        if job.company == "Coinbase" and actual is not None:
            logger.info(f"[OK] {job.company:<25} -> {actual:<6} (fuzzy matched)")
            passed += 1
        elif actual == expected:
            logger.info(f"[PASS] {job.company:<25} -> {actual if actual else 'None':<6}")
            passed += 1
        else:
            logger.info(f"[FAIL] {job.company:<25} -> {actual if actual else 'None':<6} (expected: {expected})")
            failed += 1

    # Step 5: Check database persistence
    logger.info("\n[STEP 5] Verify Database Persistence")
    logger.info("-" * 70)

    db.refresh(mapped_jobs[0])  # Force refresh from DB
    db_jobs = db.query(Job).filter(
        Job.company.in_(["Chainlink Labs", "Uniswap Labs", "Aave"])
    ).all()

    logger.info(f"[Result] Found {len(db_jobs)} jobs in database with coin_ticker")
    for job in db_jobs:
        logger.info(f"  - {job.company:<25} -> {job.coin_ticker}")

    # Step 6: Check unmatched log
    logger.info("\n[STEP 6] Check Unmatched Companies Log")
    logger.info("-" * 70)

    unmatched = get_unmatched_companies()
    logger.info(f"[Result] Unmatched entries: {len(unmatched)}")
    if unmatched:
        logger.info("Entries:")
        for entry in unmatched:
            logger.info(f"  {entry}")
    else:
        logger.info("(No unmatched companies)")

    db.close()

    # Results
    logger.info("\n" + "="*70)
    logger.info(f"PIPELINE TEST RESULTS: {passed} passed, {failed} failed")
    logger.info("="*70 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = test_full_pipeline()
    sys.exit(0 if success else 1)
