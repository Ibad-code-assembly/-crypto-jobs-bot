"""Scraper for Gitcoin bounties/jobs."""
import logging
import httpx
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class GitcoinScraper(BaseScraper):
    """Scrape bounties and grants from Gitcoin."""

    def __init__(self):
        super().__init__("gitcoin.co")

    async def fetch(self) -> List[Dict]:
        """Fetch Gitcoin bounties via API."""
        jobs = []

        try:
            # Gitcoin API for bounties (open issues)
            api_url = "https://gitcoin.co/api/v1/bounties/?bounty_type=Feature,Bug,Security&is_open=true&limit=100"

            logger.info(f"Starting scraper: {self.source_site}")
            await self._add_delay()

            response = await self.http_client.get(api_url)
            response.raise_for_status()
            data = response.json()

            bounties = data.get("results", [])
            logger.info(f"[OK] Fetched {len(bounties)} bounties from Gitcoin")

            for bounty in bounties:
                try:
                    # Extract job info from bounty
                    title = bounty.get("title", "").strip()
                    if not title:
                        continue

                    description = bounty.get("description", "")
                    url = bounty.get("url", "")
                    if not url:
                        url = f"https://gitcoin.co/issue/{bounty.get('pk')}"

                    # Extract company (funder)
                    funder = bounty.get("bounty_owner_profile", {})
                    company = funder.get("handle", "Gitcoin Community")

                    # Extract location
                    location = "Remote"

                    # Extract dates
                    created = bounty.get("created_on")
                    listed_date = datetime.fromisoformat(created.replace("Z", "+00:00")) if created else datetime.utcnow()

                    deadline_str = bounty.get("expires_date")
                    deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00")) if deadline_str else None

                    job = {
                        "title": f"Bounty: {title}",
                        "company": company,
                        "location": location,
                        "url": url,
                        "listed_date": listed_date,
                        "deadline": deadline,
                        "source_site": self.source_site,
                        "scraped_at": datetime.utcnow(),
                    }

                    jobs.append(job)

                except Exception as e:
                    logger.debug(f"Error parsing bounty: {str(e)}")
                    continue

            logger.info(f"[OK] {self.source_site}: Scraped {len(jobs)} jobs")
            return jobs

        except Exception as e:
            logger.error(f"Browser fetch failed for {self.source_site}: {str(e)}")
            logger.warning(f"[EMPTY] {self.source_site}: No jobs found")
            return []

    async def close(self):
        """Close HTTP client."""
        if self.http_client:
            await self.http_client.aclose()
