"""
Scraper using the public Greenhouse.io Jobs API.
No auth needed — all boards are publicly readable.
"""
import logging
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# Greenhouse board slugs for major crypto companies.
# Endpoint: https://boards-api.greenhouse.io/v1/boards/{SLUG}/jobs
CRYPTO_COMPANIES = [
    "coinbase",
    "ripple",
    "gemini",
    "bitgo",
    "fireblocks",
    "consensys",
    "paradigm",
    "kraken",
    "anchorage",
    "alchemy",
    "chainalysis",
    "opensea",
    "moonpay",
    "blockdaemon",
    "dfinity",
    "starkware",
    "aztec-labs",
    "celestia",
    "celo",
    "hedera",
]

BASE = "https://boards-api.greenhouse.io/v1/boards"


class GreenhouseScraper(BaseScraper):
    """Fetch jobs from Greenhouse-hosted boards of crypto companies."""

    def __init__(self):
        super().__init__("greenhouse.io")

    async def fetch(self) -> List[Dict]:
        logger.info(f"Starting scraper: {self.source_site}")
        jobs = []

        for slug in CRYPTO_COMPANIES:
            try:
                url = f"{BASE}/{slug}/jobs"
                resp = await self.http_client.get(url, headers={"Accept": "application/json"})
                if resp.status_code != 200:
                    logger.debug(f"[{self.source_site}] {slug}: {resp.status_code}")
                    continue

                data = resp.json()
                raw_jobs = data.get("jobs", [])
                logger.info(f"[{self.source_site}] {slug}: {len(raw_jobs)} jobs")

                for job in raw_jobs:
                    try:
                        title = job.get("title", "").strip()
                        if not title:
                            continue

                        job_url = job.get("absolute_url", "")
                        if not job_url:
                            continue

                        # Location from offices list or metadata
                        offices = job.get("offices", [])
                        location = offices[0].get("name", "Remote") if offices else "Remote"

                        # Company name = the board slug (prettified)
                        company = slug.replace("-", " ").title()

                        # Listed date from updated_at
                        date_str = job.get("updated_at", "")
                        try:
                            listed_date = datetime.fromisoformat(
                                date_str.replace("Z", "+00:00")
                            ).replace(tzinfo=None) if date_str else datetime.utcnow()
                        except Exception:
                            listed_date = datetime.utcnow()

                        jobs.append({
                            "title": title,
                            "company": company,
                            "location": location,
                            "url": job_url,
                            "listed_date": listed_date,
                            "deadline": None,
                            "source_site": self.source_site,
                            "scraped_at": datetime.utcnow(),
                        })

                    except Exception as e:
                        logger.debug(f"Error parsing job from {slug}: {e}")

            except Exception as e:
                logger.warning(f"[{self.source_site}] Failed for {slug}: {e}")

        logger.info(f"[OK] {self.source_site}: Scraped {len(jobs)} jobs total")
        return jobs
