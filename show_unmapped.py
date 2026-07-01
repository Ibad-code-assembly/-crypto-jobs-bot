#!/usr/bin/env python3
"""Show unmapped jobs and map them"""

from db.database import init_db, SessionLocal
from db.models import Job
from db.queries import map_jobs_to_coins

init_db()
db = SessionLocal()

print('\n' + '='*70)
print('UNMAPPED JOBS')
print('='*70 + '\n')

unmapped = db.query(Job).filter(
    Job.is_active == True,
    Job.coin_ticker == None
).all()

print(f'Found {len(unmapped)} unmapped jobs:\n')

for job in unmapped:
    print(f'  Company: {job.company}')
    print(f'  Title: {job.title}')
    print()

if unmapped:
    print('Mapping to coins...\n')
    map_jobs_to_coins(unmapped, db)
    print('[OK] Mapped\n')

# Show final stats
from sqlalchemy import func

coin_counts = db.query(
    Job.coin_ticker,
    func.count(Job.id).label('count')
).filter(
    Job.is_active == True,
    Job.coin_ticker != None
).group_by(Job.coin_ticker).order_by(
    func.count(Job.id).desc()
).all()

print('Final stats - Jobs per coin:')
total = 0
for ticker, count in coin_counts:
    print(f'  {ticker}: {count}')
    total += count

still_unmapped = db.query(Job).filter(
    Job.is_active == True,
    Job.coin_ticker == None
).count()

if still_unmapped > 0:
    print(f'\n⚠️  Still unmapped: {still_unmapped} jobs')

print(f'\nTotal mapped jobs: {total}')

db.close()

print('\n' + '='*70 + '\n')
