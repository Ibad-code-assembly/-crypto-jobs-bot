"""Scraper for crypto.jobs — plain HTTP, no browser needed."""
import logging
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://crypto.jobs"


class CryptoJobsScraper(BaseScraper):
    """Scraper for crypto.jobs using plain HTTP (confirmed working without Playwright)."""

    def __init__(self):
        super().__init__("crypto.jobs")

    async def fetch(self) -> List[Dict]:
        logger.info(f"Starting scraper: {self.source_site}")
        html = await self._fetch_with_backoff(BASE_URL, use_browser=False)
        if not html:
            return []

        try:
            from lxml import html as lxml_html
            tree = lxml_html.fromstring(html)
            jobs = []

            # Confirmed selector: rows with class 'job' that have a job-url link
            rows = tree.xpath(
                "//tr[contains(@class,'job') and .//a[contains(@class,'job-url')]]"
            )
            logger.info(f"[{self.source_site}] Found {len(rows)} job rows")

            for row in rows:
                try:
                    # Title
                    title_el = row.xpath(".//p[contains(@class,'job-title')]/text()")
                    title = title_el[0].strip() if title_el else ""
                    if not title:
                        continue

                    # URL (absolute)
                    url_el = row.xpath(".//a[contains(@class,'job-url')][1]/@href")
                    url = url_el[0].strip() if url_el else ""
                    if not url:
                        continue
                    if not url.startswith("http"):
                        url = f"{BASE_URL}{url}"

                    # Company — schema.org hiringOrganization name span
                    company_el = row.xpath(".//span[@itemprop='name']/text()")
                    company = company_el[0].strip() if company_el else "Unknown"

                    # Location — any span/text containing "Remote" or location
                    loc_el = row.xpath(".//td[3]//text()")
                    location = " ".join(t.strip() for t in loc_el if t.strip()) or "Remote"

                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location[:100],
                        "url": url,
                        "listed_date": datetime.utcnow(),
                        "deadline": None,
                        "source_site": self.source_site,
                        "scraped_at": datetime.utcnow(),
                    })

                except Exception as e:
                    logger.debug(f"Error parsing row: {e}")

            logger.info(f"[OK] {self.source_site}: Scraped {len(jobs)} jobs")
            return jobs

        except Exception as e:
            logger.error(f"Error parsing {self.source_site}: {e}")
            return []
