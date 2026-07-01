"""Scraper for We Work Remotely - blockchain/crypto category."""
import logging
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# Blockchain/crypto category page (search returns 0 results)
CATEGORY_URL = "https://weworkremotely.com/categories/remote-blockchain-crypto-jobs"
BASE_URL = "https://weworkremotely.com"


class WeWorkRemotelyScraper(BaseScraper):
    """Scraper for weworkremotely.com blockchain/crypto jobs."""

    def __init__(self):
        super().__init__("weworkremotely.com")

    async def fetch(self) -> List[Dict]:
        """Fetch blockchain/crypto jobs from We Work Remotely."""
        logger.info(f"Starting scraper: {self.source_site}")
        html = await self._fetch_with_backoff(CATEGORY_URL, use_browser=True)
        if not html:
            logger.warning(f"[EMPTY] {self.source_site}: Failed to fetch page")
            return []

        try:
            from lxml import html as lxml_html
            tree = lxml_html.fromstring(html)
            jobs = []

            # Container: <li class="new-listing-container ...">
            # Confirmed by agent: 248 items on the category page
            listings = tree.xpath("//li[contains(@class,'new-listing-container')]")
            logger.info(f"[{self.source_site}] Found {len(listings)} listings")

            for li in listings:
                try:
                    # Title: <span class="new-listing__header__title__text">
                    title_el = li.xpath(".//*[contains(@class,'new-listing__header__title__text')]")
                    if not title_el:
                        continue
                    title = title_el[0].text_content().strip()
                    if not title:
                        continue

                    # URL: <a class="listing-link--unlocked" href="/remote-jobs/...">
                    link_el = li.xpath(".//a[contains(@class,'listing-link')]")
                    if not link_el:
                        link_el = li.xpath(".//a[contains(@href,'/remote-jobs/')]")
                    if not link_el:
                        continue
                    href = link_el[0].get("href", "")
                    url = f"{BASE_URL}{href}" if not href.startswith("http") else href

                    # Company: <p class="new-listing__company-name">
                    company_el = li.xpath(".//*[contains(@class,'new-listing__company-name')]")
                    company = company_el[0].text_content().strip() if company_el else "Unknown"

                    # Location: <p class="new-listing__company-headquarters">
                    loc_el = li.xpath(".//*[contains(@class,'new-listing__company-headquarters')]")
                    location = loc_el[0].text_content().strip() if loc_el else "Remote"

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
                    logger.debug(f"Error parsing listing: {e}")
                    continue

            logger.info(f"[OK] {self.source_site}: Scraped {len(jobs)} jobs")
            return jobs

        except Exception as e:
            logger.error(f"Error parsing {self.source_site}: {e}")
            return []
