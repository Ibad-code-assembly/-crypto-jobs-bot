#!/usr/bin/env python3
"""Deep inspect each site to find exact job selectors."""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.async_api import async_playwright
from lxml import html as lxml_html

async def get_html(url, wait=3000):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(wait)
            html = await page.content()
        finally:
            await browser.close()
    return html

def show_element(el, depth=0):
    tag = el.tag
    cls = el.get('class','')[:60]
    href = el.get('href','')[:80]
    text = ' '.join(el.text_content().split())[:100]
    print(f"{'  '*depth}<{tag} class='{cls}' href='{href}'>  {text}")

async def inspect_remote3():
    print("\n" + "="*60)
    print("REMOTE3.CO - Deep Inspect")
    print("="*60)
    html = await get_html("https://remote3.co")
    tree = lxml_html.fromstring(html)

    # Show all links that look like job listings
    job_links = tree.xpath("//a[contains(@href, '/remote-jobs/') and not(contains(@href, 'search'))]")
    print(f"Job links found: {len(job_links)}")
    for link in job_links[:5]:
        href = link.get('href','')
        text = ' '.join(link.text_content().split())[:80]
        print(f"  href={href}  text={text[:60]}")

    # Find job card containers
    cards = tree.xpath("//div[contains(@class,'JobCard') or contains(@class,'job-card') or contains(@class,'JobItem') or contains(@class,'jobItem')]")
    print(f"\nJob cards: {len(cards)}")
    for c in cards[:3]:
        show_element(c)
        for child in list(c)[:5]:
            show_element(child, 1)

async def inspect_cryptojobslist():
    print("\n" + "="*60)
    print("CRYPTOJOBSLIST.COM - Deep Inspect")
    print("="*60)
    html = await get_html("https://cryptojobslist.com")
    tree = lxml_html.fromstring(html)

    # Look for job rows/cards
    candidates = [
        "//tr[contains(@class,'job')]",
        "//div[contains(@class,'JobRow') or contains(@class,'job-row')]",
        "//li[contains(@class,'job')]",
        "//div[@data-id]",
        "//article",
    ]
    for sel in candidates:
        els = tree.xpath(sel)
        if els:
            print(f"\n[MATCH] {sel} -> {len(els)} elements")
            for el in els[:3]:
                show_element(el)
                links = el.xpath(".//a/@href")
                print(f"  links: {links[:3]}")

    # Show unique class names containing 'job'
    all_classes = set()
    for el in tree.xpath("//*[@class]"):
        for c in el.get('class','').split():
            if 'job' in c.lower() or 'listing' in c.lower() or 'position' in c.lower():
                all_classes.add(c)
    print(f"\nJob-related classes: {sorted(all_classes)[:20]}")

async def inspect_weworkremotely():
    print("\n" + "="*60)
    print("WEWORKREMOTELY.COM - Deep Inspect")
    print("="*60)
    html = await get_html("https://weworkremotely.com/remote-jobs/search?term=crypto")
    tree = lxml_html.fromstring(html)

    # Show all anchor links that look like job listings
    job_links = tree.xpath("//a[contains(@href,'/remote-jobs/listings/')]")
    print(f"Job links: {len(job_links)}")
    for link in job_links[:5]:
        href = link.get('href','')
        text = ' '.join(link.text_content().split())[:80]
        print(f"  {href}  |  {text[:60]}")

    # Look for job listing containers
    candidates = [
        "//li[contains(@class,'feature')]",
        "//li[.//a[contains(@href,'/remote-jobs/listings/')]]",
        "//section//li",
    ]
    for sel in candidates:
        els = tree.xpath(sel)
        if els:
            print(f"\n[MATCH] {sel} -> {len(els)}")
            for el in els[:3]:
                show_element(el)
                for ch in list(el)[:4]:
                    show_element(ch, 1)

async def inspect_cryptocurrencyjobs():
    print("\n" + "="*60)
    print("CRYPTOCURRENCYJOBS.CO - Deep Inspect")
    print("="*60)
    html = await get_html("https://cryptocurrencyjobs.co")
    tree = lxml_html.fromstring(html)

    # Show all links with /job in href
    job_links = tree.xpath("//a[contains(@href,'/job/') or contains(@href,'/jobs/')]")
    print(f"Job links: {len(job_links)}")
    for link in job_links[:5]:
        href = link.get('href','')
        text = ' '.join(link.text_content().split())[:80]
        print(f"  {href}  |  {text[:60]}")

    # Check classes
    all_classes = set()
    for el in tree.xpath("//*[@class]"):
        for c in el.get('class','').split():
            if any(kw in c.lower() for kw in ['job','listing','card','position','row','item']):
                all_classes.add(c)
    print(f"\nJob-related classes: {sorted(all_classes)[:25]}")

async def main():
    await inspect_remote3()
    await inspect_cryptojobslist()
    await inspect_weworkremotely()
    await inspect_cryptocurrencyjobs()
    print("\n" + "="*60 + "\nDone\n")

asyncio.run(main())
