"""Demo script showing bot output for all commands."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import SessionLocal
from db.queries import get_jobs_by_coin, find_new_jobs, get_user_subscriptions
from bot.formatters import (
    format_start_message,
    format_new_jobs,
    format_expiring_jobs,
    format_subscriptions,
)


def demo():
    """Show bot output for all commands."""
    print("\n" + "="*70)
    print("CRYPTO JOBS BOT - COMMAND DEMO")
    print("="*70)

    db = SessionLocal()

    # /start
    print("\n" + "-"*70)
    print("COMMAND: /start")
    print("-"*70)
    print(format_start_message())

    # /coin UNI
    print("\n" + "-"*70)
    print("COMMAND: /coin UNI")
    print("-"*70)
    jobs = get_jobs_by_coin("UNI", db)
    if jobs:
        from bot.formatters import format_jobs_list
        print(format_jobs_list(jobs, f"🪙 UNI — {len(jobs)} active jobs"))
        print("\n[Detailed card for first job:]")
        from bot.formatters import format_job_card
        print(format_job_card(jobs[0]))
    else:
        print("🪙 UNI\n\nNo active jobs found.")

    # /new
    print("\n" + "-"*70)
    print("COMMAND: /new")
    print("-"*70)
    new_jobs = find_new_jobs(hours=24, db=db)
    if new_jobs:
        print(format_new_jobs(new_jobs))
    else:
        print("[OK] No new jobs in the last 24 hours")

    # /expiring
    print("\n" + "-"*70)
    print("COMMAND: /expiring")
    print("-"*70)
    from db.queries import find_expiring_jobs
    expiring_jobs = find_expiring_jobs(hours=48, db=db)
    if expiring_jobs:
        print(format_expiring_jobs(expiring_jobs))
    else:
        print("[OK] No jobs expiring in the next 48 hours")

    # /subscribe
    print("\n" + "-"*70)
    print("COMMAND: /subscribe ETH")
    print("-"*70)
    from db.queries import add_subscription
    success = add_subscription(99999, "ETH", db)
    if success:
        print("[OK] Subscribed to ETH\n\nYou'll get notifications for new ETH jobs!")
    else:
        print("[INFO] You're already subscribed to ETH.")

    # /mysubs
    print("\n" + "-"*70)
    print("COMMAND: /mysubs")
    print("-"*70)
    subs = get_user_subscriptions(99999, db)
    print(format_subscriptions(subs))

    # /unsubscribe
    print("\n" + "-"*70)
    print("COMMAND: /unsubscribe ETH")
    print("-"*70)
    from db.queries import remove_subscription
    success = remove_subscription(99999, "ETH", db)
    if success:
        print("[OK] Unsubscribed from ETH")
    else:
        print("[INFO] You're not subscribed to ETH.")

    db.close()

    print("\n" + "="*70)
    print("BOT READY FOR DEPLOYMENT")
    print("="*70 + "\n")


if __name__ == "__main__":
    demo()
