import asyncio
import logging
from datetime import datetime
from typing import List, Dict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from scraper.cryptojobslist import CryptoJobsListScraper
from scraper.cryptocurrencyjobs import CryptocurrencyJobsScraper
from scraper.cryptojobs import CryptoJobsScraper as CryptoJobsComScraper
from scraper.remote3 import Remote3Scraper
from scraper.we_work_remotely import WeWorkRemotelyScraper
from scraper.github_jobs import GithubJobsScraper
from scraper.blockace import BlockaceScraper
from scraper.greenhouse import GreenhouseScraper
from scraper.crypto_jobs import CryptoJobsScraper
from scraper.startup_jobs import StartupJobsScraper
from scraper.twitter_jobs import TwitterJobsScraper
from scraper.coin_listings import (
    BinanceScraper, CoinbaseScraper, BybitScraper, OKXScraper,
    BitgetScraper, KrakenScraper, KuCoinScraper, GateIOScraper,
    MEXCScraper, HTXScraper
)
from db.database import SessionLocal
from db.queries import insert_or_update_jobs, mark_expired_jobs, map_jobs_to_coins, insert_or_update_new_coins
from scraper.diff_tracker import save_diff

logger = logging.getLogger(__name__)


class JobScheduler:
    """Scheduler for periodic job scraping across all crypto job boards."""

    def __init__(self):
        """Initialize scheduler with all scraper instances."""
        self.scheduler = AsyncIOScheduler()
        self.job_scrapers = [
            # Confirmed working — ordered fastest first
            CryptocurrencyJobsScraper(),   # cryptocurrencyjobs.co - 765 jobs (Algolia API)
            GreenhouseScraper(),           # greenhouse.io - 429 jobs (Coinbase, Ripple, Gemini…)
            WeWorkRemotelyScraper(),       # weworkremotely.com - 246 jobs
            GithubJobsScraper(),           # github.com - 52 jobs
            BlockaceScraper(),             # blockace.io - 70 jobs
            CryptoJobsListScraper(),       # cryptojobslist.com - 25 jobs
            Remote3Scraper(),              # remote3.co - 20 jobs
            CryptoJobsComScraper(),        # cryptojobs.com - 15 jobs
            CryptoJobsScraper(),           # crypto.jobs - 11 jobs (plain HTTP)
            StartupJobsScraper(),          # news.ycombinator.com/jobs - crypto-filtered
            TwitterJobsScraper(),          # twitter.com - job tweets from ~30 crypto accounts
            # Excluded: web3.career (Cloudflare), gitcoin.co / blockchainjobs.io (DNS fail),
            #           wellfound.com (DataDome CAPTCHA), coinmarketcap jobs (DNS fail)
        ]
        self.coin_scrapers = [
            # 10 exchange coin listing scrapers
            BinanceScraper(),
            CoinbaseScraper(),
            BybitScraper(),
            OKXScraper(),
            BitgetScraper(),
            KrakenScraper(),
            KuCoinScraper(),
            GateIOScraper(),
            MEXCScraper(),
            HTXScraper(),
        ]
        logger.info(f"Initialized JobScheduler with {len(self.job_scrapers)} job scrapers + {len(self.coin_scrapers)} coin scrapers")

    async def run_all_scrapers(self) -> Dict:
        """
        Run all scrapers (jobs + coins) and aggregate results.

        Returns:
            {
                "new": int,
                "updated": int,
                "expired": int,
                "mapped": int,
                "new_coins": int,
                "errors": list,
                "timestamp": datetime,
                "source_summary": dict
            }
        """
        logger.info(f"\n{'='*70}")
        logger.info("SCRAPE RUN STARTED (JOBS + COINS)")
        logger.info('='*70)

        db = SessionLocal()
        all_jobs = []
        all_coins = []
        errors = []
        source_jobs = {}
        source_coins = {}
        timestamp = datetime.utcnow()

        # ──── JOBS SCRAPING ────
        logger.info("\n[PHASE 1] SCRAPING JOBS...")
        for scraper in self.job_scrapers:
            try:
                logger.info(f"\nScraping {scraper.source_site}...")
                async with scraper:
                    jobs = await scraper.run()
                    if jobs:
                        logger.info(f"[OK] {scraper.source_site}: Found {len(jobs)} jobs")
                        all_jobs.extend(jobs)
                        source_jobs[scraper.source_site] = len(jobs)
                    else:
                        logger.warning(f"[EMPTY] {scraper.source_site}: No jobs found")
                        source_jobs[scraper.source_site] = 0

            except Exception as e:
                error_msg = f"{scraper.source_site}: {str(e)}"
                logger.error(f"[ERROR] {error_msg}")
                errors.append(error_msg)
                source_jobs[scraper.source_site] = None

        logger.info(f"\n[AGGREGATION] Total jobs from all scrapers: {len(all_jobs)}")

        # ──── COINS SCRAPING ────
        logger.info("\n[PHASE 2] SCRAPING NEW COIN LISTINGS...")
        for scraper in self.coin_scrapers:
            try:
                logger.info(f"\nScraping {scraper.source_site} for new coins...")
                async with scraper:
                    coins = await scraper.run()
                    if coins:
                        logger.info(f"[OK] {scraper.source_site}: Found {len(coins)} coins")
                        all_coins.extend(coins)
                        source_coins[scraper.source_site] = len(coins)
                    else:
                        logger.warning(f"[EMPTY] {scraper.source_site}: No coins found")
                        source_coins[scraper.source_site] = 0

            except Exception as e:
                error_msg = f"{scraper.source_site}: {str(e)}"
                logger.error(f"[ERROR] {error_msg}")
                errors.append(error_msg)
                source_coins[scraper.source_site] = None

        logger.info(f"\n[AGGREGATION] Total coins from all exchanges: {len(all_coins)}")

        # Insert/update jobs with deduplication tracking
        new_count, updated_count, duplicate_count = insert_or_update_jobs(all_jobs, db)

        # Insert/update coins with deduplication tracking
        new_coins_count, updated_coins_count, duplicate_coins_count = insert_or_update_new_coins(all_coins, db)

        # Map jobs to coins
        try:
            jobs_to_map = db.query(__import__('db.models', fromlist=['Job']).Job).filter(
                __import__('db.models', fromlist=['Job']).Job.coin_ticker == None
            ).all()

            if jobs_to_map:
                logger.info(f"\n[MAPPING] Mapping {len(jobs_to_map)} unmapped jobs...")
                mapped_jobs = map_jobs_to_coins(jobs_to_map, db)
                mapped_count = len([j for j in mapped_jobs if j.coin_ticker])
                logger.info(f"[OK] Mapped {mapped_count} jobs to coins")
            else:
                mapped_count = 0
                logger.info("[MAPPING] No unmapped jobs to process")
        except Exception as e:
            logger.error(f"[ERROR] Mapping failed: {str(e)}")
            mapped_count = 0

        # Mark expired jobs — ONLY when scraper returned > 0 results.
        # If a scraper returned 0 (failed connection or parse error), we have no
        # authoritative list to compare against, so we must NOT expire existing
        # jobs or they disappear from /jobs every time a site is unreachable.
        expired_count = 0
        for source_site, job_count in source_jobs.items():
            if job_count is not None and job_count > 0:
                try:
                    current_urls = [j["url"] for j in all_jobs if j["source_site"] == source_site]
                    expired = mark_expired_jobs(source_site, current_urls, db)
                    expired_count += expired
                except Exception as e:
                    logger.error(f"[ERROR] Marking expired for {source_site}: {str(e)}")

        logger.info(f"\n[SUMMARY]")
        logger.info(f"  JOBS:")
        logger.info(f"    New: {new_count}")
        logger.info(f"    Updated: {updated_count}")
        logger.info(f"    Duplicates: {duplicate_count}")
        logger.info(f"    Mapped: {mapped_count}")
        logger.info(f"    Expired: {expired_count}")
        logger.info(f"  COINS:")
        logger.info(f"    New listings: {new_coins_count}")
        logger.info(f"    Updated listings: {updated_coins_count}")
        logger.info(f"    Multi-exchange: {duplicate_coins_count}")
        logger.info(f"  ERRORS: {len(errors)}")

        # Space-saving summary
        if duplicate_count > 0:
            logger.info(f"\n[DEDUP-JOBS] ✅ Saved {duplicate_count} entries by detecting same job from multiple sources")
        if duplicate_coins_count > 0:
            logger.info(f"[DEDUP-COINS] ✅ Detected {duplicate_coins_count} coins listed on multiple exchanges")

        # Save diff
        try:
            # Get new and expired jobs
            from db.models import Job
            new_jobs = db.query(Job).filter(Job.created_at >= timestamp).all()
            save_diff(timestamp, new_jobs, [], expired_count, source_jobs)
        except Exception as e:
            logger.error(f"[ERROR] Saving diff: {str(e)}")

        db.close()

        logger.info(f"\n{'='*70}")
        logger.info("SCRAPE RUN COMPLETED")
        logger.info('='*70 + "\n")

        return {
            "new": new_count,
            "updated": updated_count,
            "duplicates": duplicate_count,
            "expired": expired_count,
            "mapped": mapped_count,
            "new_coins": new_coins_count,
            "errors": errors,
            "timestamp": timestamp,
            "source_summary": source_jobs,
            "coin_summary": source_coins,
        }

    async def start(self, interval_minutes: int = 60):
        """Start scheduler with periodic scraping."""
        logger.info(f"Starting scheduler (interval: {interval_minutes} minutes)")

        # Add job
        self.scheduler.add_job(
            self.run_all_scrapers,
            IntervalTrigger(minutes=interval_minutes),
            id="scrape_all_sites",
            name="Scrape all crypto job boards",
            misfire_grace_time=60,
        )

        # Start scheduler
        self.scheduler.start()
        logger.info("[OK] Scheduler started")

    async def stop(self):
        """Stop scheduler gracefully."""
        logger.info("Stopping scheduler...")
        self.scheduler.shutdown()
        logger.info("[OK] Scheduler stopped")
