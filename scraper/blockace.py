"""Scraper for blockace.io — static HTML, no browser needed."""
import logging
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://blockace.io"


class BlockaceScraper(BaseScraper):
    """Scraper for blockace.io crypto jobs."""

    def __init__(self):
        super().__init__("blockace.io")

    async def fetch(self) -> List[Dict]:
        logger.info(f"Starting scraper: {self.source_site}")
        html = await self._fetch_with_backoff(BASE_URL, use_browser=False)
        if not html:
            return []

        try:
            from lxml import html as lxml_html
            tree = lxml_html.fromstring(html)
            jobs = []

            # Each job card is a full <a> link wrapping h3 (title) and p (company)
            cards = tree.xpath("//a[contains(@href,'/jobs/')]")
            logger.info(f"[{self.source_site}] Found {len(cards)} job cards")

            for card in cards:
                try:
                    url = card.get("href", "")
                    if not url or "/jobs/" not in url:
                        continue

                    title_el = card.xpath(".//*[contains(@class,'Title')]")
                    company_el = card.xpath(".//*[contains(@class,'Company')]")
                    loc_el = card.xpath(".//*[contains(@class,'Location')]")

                    title = title_el[0].text_content().strip() if title_el else ""
                    company = company_el[0].text_content().strip() if company_el else "Unknown"
                    location = loc_el[0].text_content().strip() if loc_el else "Remote"

                    if not title or len(title) < 3:
                        continue

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

            logger.info(f"[OK] {self.source_site}: Scraped {len(jobs)} jobs")
            return jobs

        except Exception as e:
            logger.error(f"Error parsing {self.source_site}: {e}")
            return []
