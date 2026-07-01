"""Scraper for CryptocurrencyJobs.io."""
import logging
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class CryptocurrencyjobsioScraper(BaseScraper):
    """Scrape cryptocurrency jobs from CryptocurrencyJobs.io."""

    def __init__(self):
        super().__init__("cryptocurrencyjobs.io")

    async def fetch(self) -> List[Dict]:
        """Fetch CryptocurrencyJobs.io listings."""
        jobs = []

        try:
            url = "https://cryptocurrencyjobs.io"

            logger.info(f"Starting scraper: {self.source_site}")

            # Use browser for dynamic content
            html = await self._fetch_with_backoff(url, use_browser=True)
            if not html:
                logger.warning(f"[EMPTY] {self.source_site}: Failed to fetch page")
                return []

            from lxml import html as lxml_html

            tree = lxml_html.fromstring(html)

            # Extract job listings - look for common job card patterns
            job_elements = tree.xpath(
                "//div[contains(@class, 'job')] | "
                "//article[contains(@class, 'job')] | "
                "//li[contains(@class, 'listing')]"
            )

            for element in job_elements:
                try:
                    # Try multiple selectors for title
                    title_elem = element.xpath(".//h2 | .//h3 | .//a[contains(@class, 'title')]")
                    title = title_elem[0].text_content().strip() if title_elem else "Untitled"
                    if len(title) < 3:
                        continue

                    # Try multiple selectors for company
                    company_elem = element.xpath(".//span[@class='company'] | .//strong[1] | .//p[contains(@class, 'company')]")
                    company = company_elem[0].text_content().strip() if company_elem else "Unknown"

                    # Location
                    location_elem = element.xpath(".//span[contains(@class, 'location')] | .//span[contains(text(), 'Remote')]")
                    location = location_elem[0].text_content().strip() if location_elem else "Remote"

                    # URL
                    url_elem = element.xpath(".//a[contains(@href, '/job')]")
                    job_url = url_elem[0].get("href") if url_elem else ""
                    if not job_url.startswith("http"):
                        job_url = f"https://cryptocurrencyjobs.io{job_url}"

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
