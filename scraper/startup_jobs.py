"""Scraper for Hacker News /jobs — filters for crypto/web3 listings."""
import logging
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

HN_JOBS_URL = "https://news.ycombinator.com/jobs"
HN_BASE = "https://news.ycombinator.com/"

CRYPTO_KEYWORDS = [
    "crypto", "blockchain", "web3", "defi", "nft", "bitcoin", "ethereum",
    "solana", "polygon", "layer 2", "l2", "dao", "token", "smart contract",
    "dex", "cex", "exchange", "wallet", "protocol", "on-chain", "onchain",
]


class StartupJobsScraper(BaseScraper):
    """Scrape Hacker News /jobs and filter for crypto/web3 roles."""

    def __init__(self):
        super().__init__("news.ycombinator.com")

    async def fetch(self) -> List[Dict]:
        logger.info(f"Starting scraper: {self.source_site}")
        html = await self._fetch_with_backoff(HN_JOBS_URL, use_browser=False)
        if not html:
            return []

        try:
            from lxml import html as lxml_html
            tree = lxml_html.fromstring(html)
            jobs = []

            # Each posting is a <tr class="athing">
            rows = tree.xpath("//tr[contains(@class,'athing')]")
            logger.info(f"[{self.source_site}] Found {len(rows)} HN job rows, filtering for crypto")

            for row in rows:
                try:
                    link_el = row.xpath(".//a[contains(@href,'item?id=')]")
                    if not link_el:
                        continue

                    title = link_el[0].text_content().strip()
                    if not title:
                        continue

                    # Only keep crypto/web3 relevant listings
                    title_lower = title.lower()
                    if not any(kw in title_lower for kw in CRYPTO_KEYWORDS):
                        continue

                    href = link_el[0].get("href", "")
                    url = href if href.startswith("http") else f"{HN_BASE}{href}"

                    # Company is embedded in the title — extract from "Company Is Hiring…"
                    # Typical format: "CompanyName (YC S24) Is Hiring …"
                    company = title.split(" Is Hiring")[0].split("(YC")[0].strip()
                    if len(company) > 50:
                        company = company[:50]

                    jobs.append({
                        "title": title[:100],
                        "company": company,
                        "location": "Remote / Various",
                        "url": url,
                        "listed_date": datetime.utcnow(),
                        "deadline": None,
                        "source_site": self.source_site,
                        "scraped_at": datetime.utcnow(),
                    })

                except Exception as e:
                    logger.debug(f"Error parsing HN row: {e}")

            logger.info(f"[OK] {self.source_site}: {len(jobs)} crypto jobs found")
            return jobs

        except Exception as e:
            logger.error(f"Error parsing {self.source_site}: {e}")
            return []
