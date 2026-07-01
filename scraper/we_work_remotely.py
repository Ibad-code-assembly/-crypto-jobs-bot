"""Scraper for We Work Remotely crypto jobs."""
import logging
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class WeWorkRemotelyScraper(BaseScraper):
    """Scrape remote crypto jobs from We Work Remotely."""

    def __init__(self):
        super().__init__("weworkremotely.com")

    async def fetch(self) -> List[Dict]:
        """Fetch We Work Remotely job listings."""
        jobs = []

        try:
            # Search for crypto/blockchain/web3 jobs
            url = "https://weworkremotely.com/remote-jobs/search?term=crypto"

            logger.info(f"Starting scraper: {self.source_site}")

            # Use browser for dynamic content
            html = await self._fetch_with_backoff(url, use_browser=True)
            if not html:
                logger.warning(f"[EMPTY] {self.source_site}: Failed to fetch page")
                return []

            from lxml import html as lxml_html

            tree = lxml_html.fromstring(html)

            # Extract job listings
            job_elements = tree.xpath("//div[contains(@class, 'job') or contains(@class, 'listing')]")

            for element in job_elements:
                try:
                    # Title
                    title_elem = element.xpath(".//h3 | .//h2 | .//a[contains(@class, 'heading')]")
                    title = title_elem[0].text_content().strip() if title_elem else "Untitled"
                    if len(title) < 3:
                        continue

                    # Company
                    company_elem = element.xpath(".//a[contains(@class, 'company')] | .//p[1]")
                    company = company_elem[0].text_content().strip() if company_elem else "Unknown"

                    # Location/Type (We Work Remotely lists them)
                    location_elem = element.xpath(".//span[contains(@class, 'location')] | .//span[contains(text(), 'Remote')]")
                    location = location_elem[0].text_content().strip() if location_elem else "Remote"

                    # URL
                    url_elem = element.xpath(".//a[contains(@href, '/remote-jobs/')]")
                    job_url = url_elem[0].get("href") if url_elem else ""
                    if not job_url.startswith("http"):
                        job_url = f"https://weworkremotely.com{job_url}"

                    if not job_url or job_url.startswith("javascript"):
                        continue

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
