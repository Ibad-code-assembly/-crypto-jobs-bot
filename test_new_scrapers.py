#!/usr/bin/env python3
"""Test the new scrapers."""

import asyncio
import logging
from scraper.scheduler import JobScheduler
from db.database import init_db, SessionLocal
from db.models import Job
from sqlalchemy import func

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    print("\n" + "="*70)
    print("TESTING NEW SCRAPERS (13 job boards)")
    print("="*70 + "\n")

    print("Original 7 boards:")
    print("  1. web3.career")
    print("  2. cryptojobslist.com")
    print("  3. cryptocurrencyjobs.co")
    print("  4. crypto.jobs")
    print("  5. cryptojobs.com")
    print("  6. remote3.co")
    print("  7. jobs.coinmarketcap.com")
    print("\nNew 6 boards:")
    print("  8. gitcoin.co")
    print("  9. wellfound.com")
    print("  10. blockchainjobs.io")
    print("  11. cryptocurrencyjobs.io")
    print("  12. weworkremotely.com")
    print("  13. startupjobs (Y Combinator)")
    print()

    init_db()

    print("Initializing scheduler with 13 scrapers...")
    scheduler = JobScheduler()
    print(f"[OK] {len(scheduler.scrapers)} scrapers initialized\n")

    print("Running scrapers (this may take 2-3 minutes)...\n")
    result = await scheduler.run_all_scrapers()

    print("\n" + "="*70)
    print("RESULTS")
    print("="*70 + "\n")

    print(f"Total jobs fetched: {result['new'] + result['updated']}")
    print(f"  - New: {result['new']}")
    print(f"  - Updated: {result['updated']}")
    print(f"  - Mapped to coins: {result['mapped']}")
    print(f"  - Unmapped: {result['unmapped']}")
    print()

    # Show per-source breakdown
    print("Jobs per source:")
    for source, count in sorted(result['source_summary'].items()):
        print(f"  {source}: {count} jobs")

    # Show database stats
    db = SessionLocal()
    total_active = db.query(Job).filter(Job.is_active == True).count()

    coin_counts = db.query(
        Job.coin_ticker,
        func.count(Job.id).label('count')
    ).filter(
        Job.is_active == True,
        Job.coin_ticker != None
    ).group_by(Job.coin_ticker).order_by(
        func.count(Job.id).desc()
    ).all()

    print()
    print(f"Database stats:")
    print(f"  Total active jobs: {total_active}")
    print(f"  Coins with jobs: {len(coin_counts)}")

    if coin_counts:
        print()
        print("Top coins by job count:")
        for ticker, count in coin_counts[:10]:
            print(f"    {ticker}: {count} jobs")

    db.close()

    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
