"""Scraper for Wellfound (formerly AngelList) crypto jobs."""
import logging
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class WellfoundScraper(BaseScraper):
    """Scrape startup jobs from Wellfound (crypto/blockchain focus)."""

    def __init__(self):
        super().__init__("wellfound.com")

    async def fetch(self) -> List[Dict]:
        """Fetch Wellfound job listings."""
        jobs = []

        try:
            # Wellfound lists jobs, search for crypto/blockchain
            url = "https://wellfound.com/jobs?query=crypto"

            logger.info(f"Starting scraper: {self.source_site}")

            # Use browser for dynamic content
            html = await self._fetch_with_backoff(url, use_browser=True)
            if not html:
                logger.warning(f"[EMPTY] {self.source_site}: Failed to fetch page")
                return []

            from lxml import html as lxml_html

            tree = lxml_html.fromstring(html)

            # Extract job listings (Wellfound structure)
            job_elements = tree.xpath("//div[@class='job-card']")

            for element in job_elements:
                try:
                    title_elem = element.xpath(".//h2[@class='job-title']")
                    title = title_elem[0].text_content().strip() if title_elem else "Untitled"

                    company_elem = element.xpath(".//a[@class='company-name']")
                    company = company_elem[0].text_content().strip() if company_elem else "Unknown"

                    location_elem = element.xpath(".//span[@class='location']")
                    location = location_elem[0].text_content().strip() if location_elem else "Remote"

                    url_elem = element.xpath(".//a[contains(@href, '/jobs/')]")
                    job_url = url_elem[0].get("href") if url_elem else ""
                    if not job_url.startswith("http"):
                        job_url = f"https://wellfound.com{job_url}"

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
