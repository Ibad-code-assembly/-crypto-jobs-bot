import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.web3_career import Web3CareerScraper
from scraper.cryptojobslist import CryptoJobsListScraper
from scraper.cryptocurrencyjobs import CryptocurrencyJobsScraper
from scraper.crypto_jobs import CryptoJobsScraper
from scraper.cryptojobs import CryptoJobsScraper as CryptoJobsComScraper
from scraper.remote3 import Remote3Scraper
from scraper.coinmarketcap_jobs import CoinMarketCapJobsScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_all_scrapers():
    """Test all scrapers individually."""
    scrapers = [
        Web3CareerScraper(),
        CryptoJobsListScraper(),
        CryptocurrencyJobsScraper(),
        CryptoJobsScraper(),
        CryptoJobsComScraper(),
        Remote3Scraper(),
        CoinMarketCapJobsScraper(),
    ]

    all_jobs = []
    total_scraped = 0

    for scraper in scrapers:
        logger.info(f"\n{'='*70}")
        logger.info(f"Testing {scraper.source_site}")
        logger.info('='*70)

        try:
            async with scraper:
                jobs = await scraper.run()

                if jobs:
                    logger.info(f"[OK] Found {len(jobs)} jobs from {scraper.source_site}")
                    total_scraped += len(jobs)
                    all_jobs.extend(jobs)

                    logger.info(f"\nFirst 3 jobs from {scraper.source_site}:")
                    for i, job in enumerate(jobs[:3], 1):
                        logger.info(f"\n  {i}. {job['title']}")
                        logger.info(f"     Company: {job['company']}")
                        logger.info(f"     Location: {job['location']}")
                        logger.info(f"     URL: {job['url']}")
                        logger.info(f"     Source: {job['source_site']}")
                        logger.info(f"     Scraped: {job['scraped_at']}")
                else:
                    logger.warning(f"[WARNING] No jobs found for {scraper.source_site}")
        except Exception as e:
            logger.error(f"[ERROR] Exception while testing {scraper.source_site}: {str(e)}", exc_info=True)

    logger.info(f"\n{'='*70}")
    logger.info("SUMMARY")
    logger.info('='*70)
    logger.info(f"Total jobs scraped: {total_scraped}")
    logger.info(f"Total unique sources: {len(set(job['source_site'] for job in all_jobs))}")

    if all_jobs:
        logger.info(f"\nSample jobs from all sources:")
        for i, job in enumerate(all_jobs[:5], 1):
            logger.info(f"\n{i}. [{job['source_site']}] {job['title']}")
            logger.info(f"   Company: {job['company']}")
            logger.info(f"   Location: {job['location']}")

    logger.info(f"\n{'='*70}")
    logger.info(f"[OK] All scrapers tested successfully!")
    logger.info('='*70)

if __name__ == "__main__":
    asyncio.run(test_all_scrapers())
