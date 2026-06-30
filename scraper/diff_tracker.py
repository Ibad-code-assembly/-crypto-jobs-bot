import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from db.models import Job

logger = logging.getLogger(__name__)

DIFFS_FILE = Path(__file__).parent / "diffs.jsonl"


def _job_to_dict(job: Job) -> Dict:
    """Convert Job model to dict."""
    if isinstance(job, dict):
        return job
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "url": job.url,
        "source_site": job.source_site,
        "coin_ticker": job.coin_ticker,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


def save_diff(
    timestamp: datetime,
    new_jobs: List[Job],
    expired_jobs: List[Job],
    expired_count: int,
    source_summary: Dict
) -> None:
    """
    Save scrape diff to diffs.jsonl (one JSON object per line).

    Args:
        timestamp: When the scrape run happened
        new_jobs: List of newly added jobs
        expired_jobs: List of jobs that expired
        expired_count: Total count of expired jobs
        source_summary: Dict with per-site job counts
    """
    try:
        diff = {
            "timestamp": timestamp.isoformat() + "Z",
            "new_jobs": [_job_to_dict(j) for j in new_jobs],
            "expired_jobs": [_job_to_dict(j) for j in expired_jobs],
            "expired_count": expired_count,
            "total_new": len(new_jobs),
            "total_expired": expired_count,
            "source_summary": source_summary,
        }

        with open(DIFFS_FILE, "a") as f:
            f.write(json.dumps(diff) + "\n")

        logger.info(f"[DIFF] Saved: {len(new_jobs)} new, {expired_count} expired")

    except Exception as e:
        logger.error(f"Error saving diff: {str(e)}")


def read_latest_diff() -> Optional[Dict]:
    """Read the latest diff entry from diffs.jsonl."""
    if not DIFFS_FILE.exists():
        return None

    try:
        with open(DIFFS_FILE, "r") as f:
            lines = f.readlines()
            if not lines:
                return None
            return json.loads(lines[-1])
    except Exception as e:
        logger.error(f"Error reading latest diff: {str(e)}")
        return None


def read_diffs_since(hours: int) -> List[Dict]:
    """Read all diffs from the last N hours."""
    if not DIFFS_FILE.exists():
        return []

    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        diffs = []

        with open(DIFFS_FILE, "r") as f:
            for line in f:
                diff = json.loads(line)
                timestamp = datetime.fromisoformat(diff["timestamp"].replace("Z", "+00:00"))
                if timestamp >= cutoff:
                    diffs.append(diff)

        return diffs
    except Exception as e:
        logger.error(f"Error reading diffs since {hours}h: {str(e)}")
        return []


def get_diff_stats(hours: int = 24) -> Dict:
    """Get aggregated stats from diffs in last N hours."""
    diffs = read_diffs_since(hours)

    total_new = sum(d.get("total_new", 0) for d in diffs)
    total_expired = sum(d.get("total_expired", 0) for d in diffs)
    run_count = len(diffs)

    return {
        "period_hours": hours,
        "run_count": run_count,
        "total_new_jobs": total_new,
        "total_expired_jobs": total_expired,
        "avg_per_run": total_new / run_count if run_count > 0 else 0,
    }
