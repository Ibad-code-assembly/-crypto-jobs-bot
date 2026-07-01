#!/usr/bin/env python3
"""Test /jobs command output"""

from db.database import init_db, SessionLocal
from db.queries import get_jobs_grouped_by_coin
from bot.formatters import format_jobs_by_coin

init_db()
db = SessionLocal()

grouped_jobs = get_jobs_grouped_by_coin(db)

print("\n" + "="*70)
print("JOBS COMMAND OUTPUT")
print("="*70 + "\n")

message = format_jobs_by_coin(grouped_jobs)
print(message)

print("\n" + "="*70 + "\n")

db.close()
