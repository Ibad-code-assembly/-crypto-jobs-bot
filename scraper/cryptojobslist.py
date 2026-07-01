"""Scraper for cryptojobslist.com."""
import logging
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://cryptojobslist.com"


class CryptoJobsListScraper(BaseScraper):
    """Scraper for cryptojobslist.com."""

    def __init__(self):
        super().__init__("cryptojobslist.com")

    async def fetch(self) -> List[Dict]:
        """Fetch jobs from cryptojobslist.com."""
        logger.info(f"Starting scraper: {self.source_site}")
        html = await self._fetch_with_backoff(BASE_URL, use_browser=True)
        if not html:
            logger.warning(f"[EMPTY] {self.source_site}: Failed to fetch page")
            return []

        try:
            from lxml import html as lxml_html
            tree = lxml_html.fromstring(html)
            jobs = []

            # Container: <tr role="button"> - confirmed 25 rows with stable class names
            rows = tree.xpath("//tr[@role='button']")
            logger.info(f"[{self.source_site}] Found {len(rows)} job rows")

            for row in rows:
                try:
                    # Title: element with class job-title-text
                    title_el = row.xpath(".//*[contains(@class,'job-title-text')]")
                    if not title_el:
                        continue
                    title = title_el[0].text_content().strip()
                    if not title:
                        continue

                    # URL: href on the title element or its ancestor <a>
                    href = title_el[0].get("href", "")
                    if not href:
                        parent_a = title_el[0].xpath("ancestor::a[1]")
                        href = parent_a[0].get("href", "") if parent_a else ""
                    if not href:
                        continue
                    url = f"{BASE_URL}{href}" if not href.startswith("http") else href

                    # Company: element with class job-company-name-text
                    company_el = row.xpath(".//*[contains(@class,'job-company-name-text')]")
                    company = company_el[0].text_content().strip() if company_el else "Unknown"

                    # Location: look for Remote text in any span/td
                    location = "Remote"
                    for el in row.xpath(".//span | .//td"):
                        txt = el.text_content().strip()
                        if txt and len(txt) < 40 and any(w in txt.lower() for w in ["remote", "onsite", "hybrid", "worldwide"]):
                            location = txt
                            break

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
                    logger.debug(f"Error parsing row: {e}")
                    continue

            logger.info(f"[OK] {self.source_site}: Scraped {len(jobs)} jobs")
            return jobs

        except Exception as e:
            logger.error(f"Error parsing {self.source_site}: {e}")
            return []
