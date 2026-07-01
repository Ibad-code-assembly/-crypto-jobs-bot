"""Scraper for remote3.co."""
import logging
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://remote3.co"


class Remote3Scraper(BaseScraper):
    """Scraper for remote3.co."""

    def __init__(self):
        super().__init__("remote3.co")

    async def fetch(self) -> List[Dict]:
        """Fetch jobs from remote3.co."""
        logger.info(f"Starting scraper: {self.source_site}")
        html = await self._fetch_with_backoff(BASE_URL, use_browser=True)
        if not html:
            logger.warning(f"[EMPTY] {self.source_site}: Failed to fetch page")
            return []

        try:
            from lxml import html as lxml_html
            tree = lxml_html.fromstring(html)
            jobs = []

            # Card container: div[class*="jobListItem"]
            # Confirmed: <div class="HomeJobsLayout_jobListItem__SorSN ">
            cards = tree.xpath("//div[contains(@class,'jobListItem')]")
            logger.info(f"[{self.source_site}] Found {len(cards)} job cards")

            for card in cards:
                try:
                    # Title: <h2 class="..jobTitle.."><a href="/remote-jobs/...">Title</a></h2>
                    title_link = card.xpath(".//a[contains(@href,'/remote-jobs/')]")
                    if not title_link:
                        continue

                    title = title_link[0].text_content().strip()
                    href = title_link[0].get("href", "")
                    if not title or not href:
                        continue

                    url = f"{BASE_URL}{href}" if not href.startswith("http") else href

                    # Company: <p class="body-small text-tertiary-white">Company Name</p>
                    # It is the first <p> inside the contentContainer
                    company_el = card.xpath(".//div[contains(@class,'contentContainer')]/p")
                    company = company_el[0].text_content().strip() if company_el else "Unknown"

                    # Location: look for "Worldwide" or "Remote" text
                    loc_el = card.xpath(".//*[contains(text(),'Remote') or contains(text(),'Worldwide') or contains(text(),'remote')]")
                    location = loc_el[0].text_content().strip() if loc_el else "Remote"
                    if len(location) > 30:
                        location = "Remote"

                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": url,
                        "listed_date": datetime.utcnow(),
                        "deadline": None,
                        "source_site": self.source_site,
                        "scraped_at": datetime.utcnow(),
                    })

                except Exception as e:
                    logger.debug(f"Error parsing card: {e}")
                    continue

            logger.info(f"[OK] {self.source_site}: Scraped {len(jobs)} jobs")
            return jobs

        except Exception as e:
            logger.error(f"Error parsing {self.source_site}: {e}")
            return []
