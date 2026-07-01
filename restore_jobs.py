#!/usr/bin/env python3
"""Restore expired jobs as active for testing"""

from db.database import init_db, SessionLocal
from db.models import Job
from datetime import datetime, timedelta
from sqlalchemy import func

init_db()
db = SessionLocal()

print('\n' + '='*70)
print('RESTORING EXPIRED JOBS')
print('='*70 + '\n')

# Mark all jobs as active and set new deadlines
expired_jobs = db.query(Job).filter(Job.is_active == False).all()

print(f'[RESTORE] Restoring {len(expired_jobs)} expired jobs...')

for job in expired_jobs:
    job.is_active = True
    job.deadline = datetime.utcnow() + timedelta(days=30)

db.commit()

print(f'[OK] Jobs restored\n')

# Show stats
active = db.query(Job).filter(Job.is_active == True).count()
print(f'[STATS] Active jobs now: {active}\n')

coin_counts = db.query(
    Job.coin_ticker,
    func.count(Job.id).label('count')
).filter(
    Job.is_active == True,
    Job.coin_ticker != None
).group_by(Job.coin_ticker).order_by(
    func.count(Job.id).desc()
).all()

print('Jobs per coin:')
for ticker, count in coin_counts:
    print(f'  {ticker}: {count} jobs')

print()

unmapped = db.query(Job).filter(
    Job.is_active == True,
    Job.coin_ticker == None
).count()

if unmapped > 0:
    print(f'[NOTE] {unmapped} unmapped jobs (missing coin_ticker)')

db.close()

print('\n' + '='*70)
print('Now test /jobs command in Telegram!')
print('='*70 + '\n')
