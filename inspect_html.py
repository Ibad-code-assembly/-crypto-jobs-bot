#!/usr/bin/env python3
"""Get raw HTML around job elements for remote3 and cryptojobslist."""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.async_api import async_playwright
from lxml import html as lxml_html, etree

async def get_html(url, wait=3000):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(wait)
            return await page.content()
        finally:
            await browser.close()

async def remote3_structure():
    print("="*60 + "\nREMOTE3 - HTML around first job link\n" + "="*60)
    html = await get_html("https://remote3.co")
    tree = lxml_html.fromstring(html)

    links = tree.xpath("//a[contains(@href,'/remote-jobs/') and string-length(@href) > 15]")
    if links:
        link = links[0]
        # Walk up 3 levels to find the card container
        el = link
        for i in range(4):
            parent = el.getparent()
            if parent is None:
                break
            raw = etree.tostring(parent, encoding='unicode')[:600]
            print(f"Level {i+1} parent <{parent.tag}> class='{parent.get('class','')[:50]}':")
            print(raw[:400])
            print()
            el = parent

async def cryptojobslist_structure():
    print("="*60 + "\nCRYPTOJOBSLIST - HTML around job title element\n" + "="*60)
    html = await get_html("https://cryptojobslist.com")
    tree = lxml_html.fromstring(html)

    title_els = tree.xpath("//*[contains(@class,'job-title-text')]")
    if title_els:
        el = title_els[0]
        # Walk up to find container with company
        for i in range(5):
            parent = el.getparent()
            if parent is None:
                break
            raw = etree.tostring(parent, encoding='unicode')[:800]
            company_els = parent.xpath(".//*[contains(@class,'job-company-name-text')]")
            time_els = parent.xpath(".//*[contains(@class,'job-time-since-creation')]")
            if company_els or time_els:
                print(f"FOUND at level {i+1}: <{parent.tag}> class='{parent.get('class','')[:60]}'")
                if company_els:
                    print(f"  Company: {company_els[0].text_content().strip()}")
                if time_els:
                    print(f"  Time: {time_els[0].text_content().strip()}")
                print(raw[:600])
                break
            el = parent

async def cryptocurrencyjobs_structure():
    print("="*60 + "\nCRYPTOCURRENCYJOBS.CO - Algolia hit structure\n" + "="*60)
    html = await get_html("https://cryptocurrencyjobs.co", wait=4000)
    tree = lxml_html.fromstring(html)

    hits = tree.xpath("//*[contains(@class,'ais-Hits-item')]")
    if hits:
        raw = etree.tostring(hits[1], encoding='unicode')[:1000]
        print(f"Hit element: <{hits[1].tag}> class='{hits[1].get('class','')[:60]}'")
        print(raw)

async def main():
    await remote3_structure()
    await cryptojobslist_structure()
    await cryptocurrencyjobs_structure()

asyncio.run(main())
