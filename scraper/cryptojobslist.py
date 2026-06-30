import logging
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class CryptoJobsListScraper(BaseScraper):
    """Scraper for cryptojobslist.com."""

    def __init__(self):
        super().__init__("cryptojobslist.com")
        self.url = "https://cryptojobslist.com"

    async def fetch(self) -> List[Dict]:
        """Fetch jobs from cryptojobslist.com."""
        html = await self._fetch_with_backoff(self.url, use_browser=True)
        if not html:
            return []

        try:
            from lxml import html as lxml_html
            tree = lxml_html.fromstring(html)

            jobs = []
            job_cards = tree.xpath("//div[@class='job-listing']")

            for card in job_cards:
                try:
                    title = card.xpath(".//a/@title")[0] if card.xpath(".//a/@title") else None
                    company = card.xpath(".//span[@class='company']/text()")[0].strip() if card.xpath(".//span[@class='company']/text()") else None
                    url = card.xpath(".//a/@href")[0] if card.xpath(".//a/@href") else None

                    if title and url:
                        jobs.append({
                            "title": title,
                            "company": company or "Unknown",
                            "location": "Remote",
                            "url": url,
                            "listed_date": None,
                            "deadline": None,
                            "source_site": self.source_site,
                            "scraped_at": datetime.utcnow()
                        })
                except Exception as e:
                    logger.warning(f"Error parsing job: {str(e)}")
                    continue

            return jobs
        except Exception as e:
            logger.error(f"Error parsing cryptojobslist: {str(e)}")
            return []
