#!/usr/bin/env python3
"""Check what's in the database"""

from db.database import init_db, SessionLocal
from db.models import Job, Coin
from sqlalchemy import func

init_db()
db = SessionLocal()

print('\n' + '='*70)
print('DATABASE CHECK')
print('='*70 + '\n')

# Count coins
coins = db.query(Coin).count()
print(f'[COINS] Total in database: {coins}')
if coins == 0:
    print('       ⚠️ No coins! Need to fetch from CoinGecko')
else:
    sample = db.query(Coin).limit(5).all()
    print('       Sample coins:')
    for coin in sample:
        print(f'         - {coin.symbol} ({coin.name})')

print()

# Count jobs total
total_jobs = db.query(Job).count()
print(f'[JOBS] Total in database: {total_jobs}')

if total_jobs > 0:
    # Count by status
    active = db.query(Job).filter(Job.is_active == True).count()
    expired = db.query(Job).filter(Job.is_active == False).count()
    print(f'       Active: {active}, Expired: {expired}')

    # Count by mapped
    mapped = db.query(Job).filter(Job.coin_ticker != None).count()
    unmapped = db.query(Job).filter(Job.coin_ticker == None).count()
    print(f'       Mapped: {mapped}, Unmapped: {unmapped}')

    print()
    print('       Active jobs by coin:')
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
        for ticker, count in coin_counts[:10]:
            print(f'         {ticker}: {count}')
    else:
        print('         (no mapped jobs)')

    print()
    print('       Sample jobs:')
    jobs = db.query(Job).limit(5).all()
    for job in jobs:
        coin_text = f" [{job.coin_ticker}]" if job.coin_ticker else "[UNMAPPED]"
        print(f'         - {job.title[:40]}... @ {job.company} {coin_text}')
else:
    print('       ⚠️ No jobs in database!')

db.close()

print('\n' + '='*70 + '\n')
