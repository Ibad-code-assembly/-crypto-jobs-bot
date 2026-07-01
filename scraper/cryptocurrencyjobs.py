"""Scraper for cryptocurrencyjobs.co — calls the Algolia API directly."""
import logging
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

ALGOLIA_URL = "https://8ehcb38y1u-dsn.algolia.net/1/indexes/*/queries"
ALGOLIA_HEADERS = {
    "x-algolia-api-key": "e3deada9c15551e6363ee91e7e7d59cc",
    "x-algolia-application-id": "8EHCB38Y1U",
    "Content-Type": "application/json",
    "Origin": "https://cryptocurrencyjobs.co",
    "Referer": "https://cryptocurrencyjobs.co/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}
BASE_URL = "https://cryptocurrencyjobs.co"


class CryptocurrencyJobsScraper(BaseScraper):
    """Scraper for cryptocurrencyjobs.co using Algolia Search API."""

    def __init__(self):
        super().__init__("cryptocurrencyjobs.co")

    async def fetch(self) -> List[Dict]:
        logger.info(f"Starting scraper: {self.source_site}")
        jobs = []
        page = 0

        while True:
            payload = {
                "requests": [{
                    "indexName": "jobs",
                    "params": f"hitsPerPage=200&page={page}&filters=NOT is_ad:true"
                }]
            }
            try:
                resp = await self.http_client.post(
                    ALGOLIA_URL,
                    json=payload,
                    headers=ALGOLIA_HEADERS,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.error(f"[{self.source_site}] Algolia API error (page {page}): {e}")
                break

            result = data.get("results", [{}])[0]
            hits = result.get("hits", [])
            nb_pages = result.get("nbPages", 1)

            logger.info(f"[{self.source_site}] Page {page}: {len(hits)} hits ({nb_pages} total pages)")

            for hit in hits:
                try:
                    if hit.get("is_ad"):
                        continue

                    title = hit.get("title", "").strip()
                    if not title:
                        continue

                    company = (hit.get("company") or {}).get("name", "Unknown").strip() or "Unknown"
                    permalink = hit.get("permalink", "")
                    if not permalink:
                        continue
                    url = f"{BASE_URL}{permalink}" if permalink.startswith("/") else permalink

                    # Location
                    loc_filters = hit.get("locationFilter") or []
                    location = ", ".join(loc_filters) if loc_filters else "Remote"

                    # Use actual listing date
                    date_str = hit.get("datePublished", "")
                    try:
                        listed_date = datetime.fromisoformat(date_str) if date_str else datetime.utcnow()
                    except Exception:
                        listed_date = datetime.utcnow()

                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": url,
                        "listed_date": listed_date,
                        "deadline": None,
                        "source_site": self.source_site,
                        "scraped_at": datetime.utcnow(),
                    })

                except Exception as e:
                    logger.debug(f"Error parsing hit: {e}")

            page += 1
            if page >= nb_pages or page >= 10:
                break

        logger.info(f"[OK] {self.source_site}: Scraped {len(jobs)} jobs")
        return jobs
