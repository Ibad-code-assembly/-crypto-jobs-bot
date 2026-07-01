#!/usr/bin/env python3
"""Inspect cryptocurrencyjobs.co Algolia hit structure."""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.async_api import async_playwright
from lxml import html as lxml_html, etree

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        await page.goto("https://cryptocurrencyjobs.co", wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(4000)
        html = await page.content()
        await browser.close()

    tree = lxml_html.fromstring(html)
    hits = tree.xpath("//li[contains(@class,'ais-Hits-item')]")

    print(f"Total hits: {len(hits)}\n")

    # Inspect hits 1-4 (skip 0 which is often an ad)
    for i, hit in enumerate(hits[1:5], 1):
        print(f"--- Hit {i} ---")
        # All links
        links = hit.xpath(".//a")
        for link in links[:3]:
            href = link.get('href','')
            text = ' '.join(link.text_content().split())[:80]
            print(f"  <a href='{href}'> {text}")
        # All headings
        for tag in ['h1','h2','h3','h4','span','p']:
            els = hit.xpath(f".//{tag}")
            for el in els[:4]:
                cls = el.get('class','')[:40]
                text = ' '.join(el.text_content().split())[:60]
                if text:
                    print(f"  <{tag} class='{cls}'> {text}")
        print()

asyncio.run(main())
