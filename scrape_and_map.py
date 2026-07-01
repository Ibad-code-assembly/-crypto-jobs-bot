#!/usr/bin/env python3
"""Scrape jobs from all sources and map to coins"""

import asyncio
import logging
from scraper.scheduler import JobScheduler
from db.database import init_db, SessionLocal
from db.queries import get_all_active_jobs
from db.models import Job
from sqlalchemy import func

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_scrape():
    print('\n' + '='*70)
    print('RUNNING FULL SCRAPE & COIN MAPPING')
    print('='*70 + '\n')

    print('[SCRAPER] Initializing database...')
    init_db()
    print('[OK] Database initialized\n')

    print('[SCRAPER] Creating scheduler with all 7 job board scrapers...')
    scheduler = JobScheduler()
    print('[OK] Scheduler created\n')

    print('[SCRAPER] Running all scrapers from 7 job boards...')
    print('  1. Web3.Career')
    print('  2. CryptoJobsList')
    print('  3. CryptocurrencyJobs')
    print('  4. CryptoJobs')
    print('  5. CryptoJobs')
    print('  6. Remote3')
    print('  7. CoinMarketCap Jobs')
    print()

    result = await scheduler.run_all_scrapers()

    print('='*70)
    print('SCRAPE RESULTS:')
    print('='*70)
    print(f'[NEW]      {result["new"]} new jobs fetched')
    print(f'[UPDATED]  {result["updated"]} updated jobs')
    print(f'[EXPIRED]  {result["expired"]} expired jobs')
    print(f'[MAPPED]   {result["mapped"]} jobs mapped to coins')
    print(f'[UNMAPPED] {result["unmapped"]} jobs without coin match')
    print()

    # Show database stats
    db = SessionLocal()

    all_jobs = get_all_active_jobs(db)
    print(f'[DATABASE] Total active jobs: {len(all_jobs)}')
    print()

    # Count by coin
    coin_counts = db.query(
        Job.coin_ticker,
        func.count(Job.id).label('count')
    ).filter(
        Job.is_active == True,
        Job.coin_ticker != None
    ).group_by(Job.coin_ticker).order_by(
        func.count(Job.id).desc()
    ).all()

    if coin_counts:
        print('Jobs available per coin:')
        for ticker, count in coin_counts:
            print(f'  {ticker}: {count} jobs')
        print()
    else:
        print('[WARN] No jobs matched to coins yet')
        print()

    db.close()

    print('='*70)
    print('SCRAPE COMPLETE!')
    print('='*70)
    print()
    print('Now test in Telegram:')
    print('  1. Send /jobs -> See job statistics')
    print('  2. Send /coin BTC -> See Bitcoin jobs')
    print('  3. Send /new -> See new jobs (last 30 days)')
    print()

if __name__ == "__main__":
    asyncio.run(run_scrape())
