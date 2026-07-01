"""Scraper for cryptojobs.com."""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://cryptojobs.com"


class CryptoJobsScraper(BaseScraper):
    """Scraper for cryptojobs.com."""

    def __init__(self):
        super().__init__("cryptojobs.com")

    async def fetch(self) -> List[Dict]:
        """Fetch jobs from cryptojobs.com."""
        logger.info(f"Starting scraper: {self.source_site}")

        # Use custom browser fetch with longer wait (JS-heavy site)
        from playwright.async_api import async_playwright
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.set_extra_http_headers(self._get_headers())
                await page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(3)
                html = await page.content()
                await browser.close()
        except Exception as e:
            logger.error(f"[{self.source_site}] Browser fetch failed: {e}")
            return []

        if not html:
            return []

        try:
            from lxml import html as lxml_html
            tree = lxml_html.fromstring(html)
            jobs = []

            # Try multiple selectors - cryptojobs.com uses article or div containers
            cards = (
                tree.xpath("//article[.//a[contains(@href,'/job/')]]") or
                tree.xpath("//div[contains(@class,'job-card')][.//a]") or
                tree.xpath("//div[contains(@class,'job-item')][.//a]") or
                tree.xpath("//li[contains(@class,'job')][.//a]")
            )
            logger.info(f"[{self.source_site}] Found {len(cards)} job cards")

            for card in cards:
                try:
                    # Title: first heading or link text
                    title_el = (
                        card.xpath(".//h2//text()") or
                        card.xpath(".//h3//text()") or
                        card.xpath(".//a[contains(@href,'/job/')]//text()")
                    )
                    title = " ".join(title_el).strip() if title_el else ""
                    if not title or len(title) < 3:
                        continue

                    # URL
                    link_el = (
                        card.xpath(".//a[contains(@href,'/job/')]") or
                        card.xpath(".//a[@href and string-length(@href) > 5]")
                    )
                    href = link_el[0].get("href", "") if link_el else ""
                    if not href:
                        continue
                    url = href if href.startswith("http") else f"{BASE_URL}{href}"

                    # Company
                    company_el = (
                        card.xpath(".//*[contains(@class,'company')]//text()") or
                        card.xpath(".//span[contains(@class,'employer')]//text()")
                    )
                    company = " ".join(company_el).strip() if company_el else "Unknown"
                    if not company or len(company) < 2:
                        company = "Unknown"

                    # Location
                    loc_el = card.xpath(".//*[contains(@class,'location')]//text()")
                    location = " ".join(loc_el).strip() if loc_el else "Remote"

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
