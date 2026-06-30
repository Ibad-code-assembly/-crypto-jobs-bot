import asyncio
import logging
import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict
import httpx
from playwright.async_api import async_playwright, Browser

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Abstract base class for all job board scrapers."""

    def __init__(self, source_site: str):
        self.source_site = source_site
        self.browser: Browser = None
        self.http_client: httpx.AsyncClient = None
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        ]
        self.max_retries = 3
        self.base_delay = 1.0

    async def __aenter__(self):
        """Async context manager entry."""
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers=self._get_headers()
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.http_client:
            await self.http_client.aclose()
        if self.browser:
            await self.browser.close()

    def _get_headers(self) -> Dict[str, str]:
        """Return realistic request headers."""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def _add_delay(self):
        """Add random delay between requests (anti-bot measure)."""
        delay = self.base_delay + random.uniform(0.5, 2.0)
        await asyncio.sleep(delay)

    async def _fetch_with_backoff(self, url: str, use_browser: bool = False) -> str:
        """Fetch URL with exponential backoff for rate limiting."""
        for attempt in range(self.max_retries):
            try:
                if use_browser:
                    return await self._fetch_with_browser(url)
                else:
                    await self._add_delay()
                    response = await self.http_client.get(url, headers=self._get_headers())
                    response.raise_for_status()
                    logger.info(f"[OK] Fetched {url}")
                    return response.text
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    wait_time = self.base_delay ** (attempt + 1) + random.uniform(0, 1)
                    logger.warning(f"Rate limited (429). Waiting {wait_time:.1f}s before retry...")
                    await asyncio.sleep(wait_time)
                elif e.response.status_code == 403:
                    logger.error(f"Access forbidden (403) for {url}")
                    return None
                elif e.response.status_code == 404:
                    logger.warning(f"Page not found (404): {url}")
                    return None
                else:
                    logger.error(f"HTTP error {e.response.status_code} for {url}")
                    return None
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1}/{self.max_retries} for {url}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.base_delay ** (attempt + 1))
            except Exception as e:
                logger.error(f"Error fetching {url}: {str(e)}")
                return None

        logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
        return None

    async def _fetch_with_browser(self, url: str) -> str:
        """Fetch page using Playwright for JS-rendered content."""
        try:
            if not self.browser:
                playwright = await async_playwright().start()
                self.browser = await playwright.chromium.launch(headless=True)

            page = await self.browser.new_page()
            await page.set_extra_http_headers(self._get_headers())
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(random.uniform(1, 2))
            content = await page.content()
            await page.close()
            logger.info(f"[OK] Fetched (browser) {url}")
            return content
        except Exception as e:
            logger.error(f"Browser fetch failed for {url}: {str(e)}")
            return None

    @abstractmethod
    async def fetch(self) -> List[Dict]:
        """Fetch jobs from this source. Return List[Job dicts]."""
        pass

    async def run(self) -> List[Dict]:
        """Run scraper with error handling."""
        try:
            logger.info(f"Starting scraper: {self.source_site}")
            jobs = await self.fetch()
            logger.info(f"[OK] {self.source_site}: Scraped {len(jobs) if jobs else 0} jobs")
            return jobs or []
        except Exception as e:
            logger.error(f"Scraper {self.source_site} failed: {str(e)}", exc_info=True)
            return []
