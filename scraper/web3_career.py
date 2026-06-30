import logging
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class Web3CareerScraper(BaseScraper):
    """Scraper for web3.career job board."""

    def __init__(self):
        super().__init__("web3.career")
        self.url = "https://web3.career"

    async def fetch(self) -> List[Dict]:
        """Fetch jobs from web3.career."""
        html = await self._fetch_with_backoff(self.url, use_browser=True)
        if not html:
            return []

        try:
            from lxml import html as lxml_html
            tree = lxml_html.fromstring(html)

            jobs = []
            job_cards = tree.xpath("//div[@class='job-card']")

            for card in job_cards:
                try:
                    title = card.xpath(".//h2/text()")[0].strip() if card.xpath(".//h2/text()") else None
                    company = card.xpath(".//span[@class='company']/text()")[0].strip() if card.xpath(".//span[@class='company']/text()") else None
                    location = card.xpath(".//span[@class='location']/text()")[0].strip() if card.xpath(".//span[@class='location']/text()") else "Remote"
                    url = card.xpath(".//a/@href")[0] if card.xpath(".//a/@href") else None

                    if title and company and url:
                        jobs.append({
                            "title": title,
                            "company": company,
                            "location": location,
                            "url": url,
                            "listed_date": None,
                            "deadline": None,
                            "source_site": self.source_site,
                            "scraped_at": datetime.utcnow()
                        })
                except Exception as e:
                    logger.warning(f"Error parsing job card: {str(e)}")
                    continue

            return jobs
        except Exception as e:
            logger.error(f"Error parsing web3.career: {str(e)}")
            return []
