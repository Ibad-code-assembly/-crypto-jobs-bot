"""Scraper for crypto job postings via GitHub Search API."""
import logging
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

JOB_TITLE_KEYWORDS = [
    "engineer", "developer", "develo", "dev ", " dev", "backend", "frontend",
    "fullstack", "full stack", "solidity", "rust", "python", "golang",
    "smart contract", "blockchain", "defi", "web3", "protocol", "infra",
    "security", "researcher", "architect", "lead", "senior", "junior",
    "intern", "analyst", "designer", "product", "manager", "hiring",
    "looking for", "we are hiring", "join us", "join our", "open position",
    "job opening", "role", "opportunity", "position",
]


class GithubJobsScraper(BaseScraper):
    """Scrape crypto job postings from GitHub Search API (no auth required)."""

    def __init__(self):
        super().__init__("github.com")
        self.api_base = "https://api.github.com"
        self.api_headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CryptoJobsBot/1.0",
        }

    async def fetch(self) -> List[Dict]:
        """Fetch crypto job postings via GitHub Search API."""
        jobs = []
        seen_urls = set()

        logger.info(f"Starting scraper: {self.source_site}")

        # Check rate limit first
        remaining = await self._check_rate_limit()
        if remaining < 5:
            logger.warning(f"[GITHUB] Rate limit too low ({remaining} remaining). Skipping.")
            return []

        jobs += await self._search_hiring_issues(seen_urls)
        jobs += await self._search_job_repos(seen_urls)

        logger.info(f"[OK] {self.source_site}: Scraped {len(jobs)} jobs")
        return jobs

    async def _check_rate_limit(self) -> int:
        """Return remaining GitHub API requests."""
        try:
            r = await self.http_client.get(
                f"{self.api_base}/rate_limit", headers=self.api_headers
            )
            if r.status_code == 200:
                return r.json().get("rate", {}).get("remaining", 0)
        except Exception:
            pass
        return 0

    async def _search_hiring_issues(self, seen_urls: set) -> List[Dict]:
        """Search GitHub issues that are actual crypto hiring posts."""
        jobs = []

        # Targeted queries that find real job postings
        queries = [
            '"we are hiring" blockchain web3 is:issue is:open',
            '"hiring" "blockchain" "engineer" is:issue is:open',
            '"job opening" crypto web3 is:issue is:open',
            '"open position" defi ethereum is:issue is:open',
            'label:hiring blockchain is:issue is:open',
        ]

        for query in queries:
            try:
                await self._add_delay()
                url = f"{self.api_base}/search/issues?q={query}&sort=created&order=desc&per_page=20"
                response = await self.http_client.get(url, headers=self.api_headers)

                if response.status_code == 403:
                    logger.warning("[GITHUB] Rate limited on issue search")
                    break

                if response.status_code != 200:
                    continue

                items = response.json().get("items", [])

                for item in items:
                    try:
                        job_url = item.get("html_url", "")
                        if job_url in seen_urls:
                            continue
                        seen_urls.add(job_url)

                        title = item.get("title", "").strip()
                        if not title or len(title) < 5:
                            continue

                        # Must look like a job posting
                        title_lower = title.lower()
                        body_lower = (item.get("body") or "").lower()
                        combined = title_lower + " " + body_lower

                        if not any(kw in combined for kw in JOB_TITLE_KEYWORDS):
                            continue

                        # Extract company from org name
                        repo_url = item.get("repository_url", "")
                        org_name = repo_url.split("/")[-2] if "/" in repo_url else "Unknown"
                        company = org_name.replace("-", " ").title()

                        # Parse date
                        created_at = item.get("created_at", "")
                        try:
                            listed_date = datetime.fromisoformat(
                                created_at.replace("Z", "+00:00")
                            ).replace(tzinfo=None)
                        except Exception:
                            listed_date = datetime.utcnow()

                        jobs.append({
                            "title": title,
                            "company": company,
                            "location": "Remote",
                            "url": job_url,
                            "listed_date": listed_date,
                            "deadline": None,
                            "source_site": self.source_site,
                            "scraped_at": datetime.utcnow(),
                        })

                    except Exception as e:
                        logger.debug(f"[GITHUB] Error parsing issue: {e}")
                        continue

            except Exception as e:
                logger.error(f"[GITHUB] Issue search error: {e}")
                continue

        logger.info(f"[GITHUB] Issues: found {len(jobs)} job postings")
        return jobs

    async def _search_job_repos(self, seen_urls: set) -> List[Dict]:
        """Search GitHub repos that curate crypto job listings."""
        jobs = []

        # Repos that list crypto/web3 jobs
        queries = [
            "crypto jobs blockchain topic:jobs",
            "web3 hiring awesome blockchain topic:blockchain",
            "defi jobs remote topic:web3",
        ]

        for query in queries:
            try:
                await self._add_delay()
                url = f"{self.api_base}/search/repositories?q={query}&sort=updated&order=desc&per_page=15"
                response = await self.http_client.get(url, headers=self.api_headers)

                if response.status_code == 403:
                    logger.warning("[GITHUB] Rate limited on repo search")
                    break

                if response.status_code != 200:
                    continue

                repos = response.json().get("items", [])

                for repo in repos:
                    try:
                        repo_url = repo.get("html_url", "")
                        if repo_url in seen_urls:
                            continue
                        seen_urls.add(repo_url)

                        name = repo.get("name", "")
                        description = (repo.get("description") or "").strip()
                        owner = repo.get("owner", {}).get("login", "Unknown")

                        # Only include repos that clearly aggregate jobs
                        desc_lower = description.lower()
                        name_lower = name.lower()
                        if not any(kw in desc_lower + name_lower for kw in [
                            "job", "hiring", "career", "position", "work", "employment"
                        ]):
                            continue

                        updated_at = repo.get("updated_at", "")
                        try:
                            listed_date = datetime.fromisoformat(
                                updated_at.replace("Z", "+00:00")
                            ).replace(tzinfo=None)
                        except Exception:
                            listed_date = datetime.utcnow()

                        title = description[:80] if description else f"Crypto Jobs: {name}"
                        company = owner.replace("-", " ").title()

                        jobs.append({
                            "title": title,
                            "company": company,
                            "location": "Remote",
                            "url": repo_url,
                            "listed_date": listed_date,
                            "deadline": None,
                            "source_site": self.source_site,
                            "scraped_at": datetime.utcnow(),
                        })

                    except Exception as e:
                        logger.debug(f"[GITHUB] Error parsing repo: {e}")
                        continue

            except Exception as e:
                logger.error(f"[GITHUB] Repo search error: {e}")
                continue

        logger.info(f"[GITHUB] Repos: found {len(jobs)} job listings")
        return jobs

    async def close(self):
        if self.http_client:
            await self.http_client.aclose()
