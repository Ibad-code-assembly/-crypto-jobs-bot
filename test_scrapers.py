#!/usr/bin/env python3
"""Test each scraper individually and report results."""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SCRAPERS = [
    ("cryptocurrencyjobs.co","scraper.cryptocurrencyjobs",     "CryptocurrencyJobsScraper"),
    ("greenhouse.io",        "scraper.greenhouse",             "GreenhouseScraper"),
    ("weworkremotely.com",   "scraper.we_work_remotely",       "WeWorkRemotelyScraper"),
    ("github.com",           "scraper.github_jobs",            "GithubJobsScraper"),
    ("blockace.io",          "scraper.blockace",               "BlockaceScraper"),
    ("cryptojobslist.com",   "scraper.cryptojobslist",         "CryptoJobsListScraper"),
    ("remote3.co",           "scraper.remote3",                "Remote3Scraper"),
    ("cryptojobs.com",       "scraper.cryptojobs",             "CryptoJobsScraper"),
    ("crypto.jobs",          "scraper.crypto_jobs",            "CryptoJobsScraper"),
    ("ycombinator.com/jobs", "scraper.startup_jobs",           "StartupJobsScraper"),
    ("twitter.com",          "scraper.twitter_jobs",           "TwitterJobsScraper"),
]

async def test_scraper(name, module_path, class_name):
    print(f"\n{'='*55}")
    print(f"TESTING: {name}")
    print('='*55)
    try:
        import importlib
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        scraper = cls()

        async with scraper:
            jobs = await scraper.run()

        print(f"[OK] Found {len(jobs)} jobs")
        if jobs:
            for j in jobs[:3]:
                title = (j.get('title') or '')[:55]
                company = (j.get('company') or '')[:25]
                location = (j.get('location') or '')[:20]
                url = (j.get('url') or '')[:60]
                print(f"  - {title}")
                print(f"    Company: {company}  |  Location: {location}")
                print(f"    URL: {url}")
            if len(jobs) > 3:
                print(f"  ... and {len(jobs)-3} more")
        else:
            print("  [WARN] No jobs returned")

        return len(jobs)

    except Exception as e:
        print(f"[ERROR] {e}")
        return 0

async def main():
    print("\nCRYPTO JOBS BOT - SCRAPER TEST SUITE")
    print("="*55)

    results = {}
    for name, module, cls in SCRAPERS:
        count = await test_scraper(name, module, cls)
        results[name] = count

    print("\n" + "="*55)
    print("SUMMARY")
    print("="*55)
    total = 0
    for name, count in results.items():
        status = "[OK]" if count > 0 else "[FAIL]"
        print(f"  {status} {name}: {count} jobs")
        total += count
    print(f"\n  Total: {total} jobs from {sum(1 for c in results.values() if c > 0)} sources")

asyncio.run(main())
