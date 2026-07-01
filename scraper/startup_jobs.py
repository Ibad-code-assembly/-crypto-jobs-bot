"""Scraper for startup crypto jobs from various platforms."""
import logging
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class StartupJobsScraper(BaseScraper):
    """Scrape crypto startup jobs from Y Combinator, Startup boards, etc."""

    def __init__(self):
        super().__init__("startupjobs.com")

    async def fetch(self) -> List[Dict]:
        """Fetch startup job listings with crypto focus."""
        jobs = []

        try:
            url = "https://news.ycombinator.com/jobs"

            logger.info(f"Starting scraper: {self.source_site}")

            # Fetch with browser for dynamic content
            html = await self._fetch_with_backoff(url, use_browser=True)
            if not html:
                logger.warning(f"[EMPTY] {self.source_site}: Failed to fetch page")
                return []

            from lxml import html as lxml_html

            tree = lxml_html.fromstring(html)

            # HN uses specific structure for job postings
            job_elements = tree.xpath("//tr[@class='athing']")

            for element in job_elements:
                try:
                    # Title and link
                    title_elem = element.xpath(".//span[@class='titleline']//a")
                    if not title_elem:
                        continue

                    title = title_elem[0].text_content().strip()
                    job_url = title_elem[0].get("href", "")

                    # Filter for crypto/blockchain keywords
                    crypto_keywords = ["crypto", "blockchain", "web3", "defi", "nft", "ethereum", "bitcoin", "solana"]
                    if not any(kw.lower() in title.lower() for kw in crypto_keywords):
                        continue

                    # Metadata row
                    meta_elem = element.xpath("./following-sibling::tr[1]//span[@class='metaText']")
                    meta_text = meta_elem[0].text_content() if meta_elem else ""

                    # Parse meta (usually: "points by user | time ago | hide")
                    parts = meta_text.split("|")
                    company = "HN Community"
                    location = "Remote"

                    job = {
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": job_url,
                        "listed_date": datetime.utcnow(),
                        "deadline": None,
                        "source_site": self.source_site,
                        "scraped_at": datetime.utcnow(),
                    }

                    jobs.append(job)

                except Exception as e:
                    logger.debug(f"Error parsing job: {str(e)}")
                    continue

            logger.info(f"[OK] {self.source_site}: Scraped {len(jobs)} jobs")
            return jobs

        except Exception as e:
            logger.error(f"Scraper failed for {self.source_site}: {str(e)}")
            logger.warning(f"[EMPTY] {self.source_site}: No jobs found")
            return []

    async def close(self):
        """Close browser and HTTP client."""
        if self.browser:
            await self.browser.close()
        if self.http_client:
            await self.http_client.aclose()
