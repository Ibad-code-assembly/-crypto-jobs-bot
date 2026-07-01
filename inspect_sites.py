#!/usr/bin/env python3
"""Inspect actual rendered HTML from each job site to find correct selectors."""
import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from playwright.async_api import async_playwright

SITES = {
    "cryptocurrencyjobs.co": "https://cryptocurrencyjobs.co",
    "remote3.co": "https://remote3.co",
    "weworkremotely.com": "https://weworkremotely.com/remote-jobs/search?term=crypto",
    "cryptojobslist.com": "https://cryptojobslist.com",
    "cryptojobs.com": "https://cryptojobs.com",
    "web3.career": "https://web3.career",
}

async def inspect(name, url):
    print(f"\n{'='*60}")
    print(f"SITE: {name}")
    print(f"URL: {url}")
    print('='*60)
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            await page.goto(url, wait_until='networkidle', timeout=25000)
            await page.wait_for_timeout(2000)
            html = await page.content()
            await browser.close()

        # Find job-related patterns in the HTML
        from lxml import html as lxml_html
        tree = lxml_html.fromstring(html)

        # Try common job container selectors
        selectors = [
            "//article",
            "//div[contains(@class,'job')]",
            "//li[contains(@class,'job')]",
            "//div[contains(@class,'listing')]",
            "//div[contains(@class,'card')]",
            "//tr[contains(@class,'job')]",
            "//div[contains(@class,'position')]",
            "//div[contains(@class,'opening')]",
            "//a[contains(@href,'/job')]",
            "//a[contains(@href,'/jobs/')]",
        ]

        found_any = False
        for sel in selectors:
            elements = tree.xpath(sel)
            if elements:
                el = elements[0]
                # Get all text content
                text = ' '.join(el.text_content().split())[:200]
                cls = el.get('class','')
                tag = el.tag
                print(f"[FOUND] {sel} -> {len(elements)} elements")
                print(f"  Tag: <{tag}> class='{cls}'")
                print(f"  Text: {text[:150]}")

                # Look for links inside
                links = el.xpath(".//a/@href")
                if links:
                    print(f"  Links: {links[:3]}")
                found_any = True
                break  # show first match only per selector type

        if not found_any:
            print("[NONE] No job containers found with common selectors")
            # Show body structure
            body = tree.xpath("//body")
            if body:
                body_html = lxml_html.tostring(body[0], encoding='unicode')[:1500]
                print(f"Body snippet:\n{body_html}")

    except Exception as e:
        print(f"[ERROR] {str(e)}")

async def main():
    for name, url in SITES.items():
        await inspect(name, url)

asyncio.run(main())
