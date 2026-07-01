#!/usr/bin/env python3
"""Verify jobs are ready for /jobs command"""

from db.database import init_db, SessionLocal
from db.queries import get_job_count_by_coin

init_db()
db = SessionLocal()

coin_counts = get_job_count_by_coin(db)

print("\n" + "="*70)
print("JOBS COMMAND OUTPUT")
print("="*70)
print()

if coin_counts:
    total_jobs = sum(coin_counts.values())
    print(f"Jobs Available by Coin -- {total_jobs} total jobs")
    print()

    for idx, (coin, count) in enumerate(coin_counts.items(), 1):
        percentage = (count / total_jobs * 100) if total_jobs > 0 else 0
        print(f"{idx}. {coin}: {count} jobs ({percentage:.1f}%)")

    print()
    print(f"Total: {total_jobs} active jobs across {len(coin_counts)} coins")
else:
    print("No jobs available yet.")

print()
print("="*70)
print()

db.close()
