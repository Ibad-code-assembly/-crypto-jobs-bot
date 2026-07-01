#!/usr/bin/env python3
"""Map existing jobs to coins"""

from db.database import init_db, SessionLocal
from db.queries import map_jobs_to_coins, get_all_active_jobs
from db.models import Job
from sqlalchemy import func

print('\n' + '='*70)
print('MAPPING EXISTING JOBS TO COINS')
print('='*70 + '\n')

init_db()
db = SessionLocal()

# Get unmapped jobs
unmapped_jobs = db.query(Job).filter(
    Job.is_active == True,
    Job.coin_ticker == None
).all()

print(f'[DATABASE] Found {len(unmapped_jobs)} unmapped jobs\n')

if unmapped_jobs:
    print('Jobs to be mapped:')
    for job in unmapped_jobs:
        print(f'  - {job.company}: {job.title[:50]}...')
    print()

    # Map them
    map_jobs_to_coins(unmapped_jobs, db)

    # Check results
    mapped_jobs = db.query(Job).filter(
        Job.is_active == True,
        Job.coin_ticker != None
    ).all()

    print(f'[MAPPED] Successfully mapped {len(mapped_jobs)} jobs\n')

    # Show stats
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
        print('Jobs per coin:')
        for ticker, count in coin_counts:
            print(f'  {ticker}: {count} jobs')
    else:
        print('[WARN] No jobs mapped to coins')
else:
    print('[INFO] No unmapped jobs found - all jobs are already mapped!')

db.close()

print('\n' + '='*70)
print('Now test /jobs command in Telegram!')
print('='*70 + '\n')
