#!/usr/bin/env python3
"""Find exact working selectors for each site."""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.async_api import async_playwright
from lxml import html as lxml_html

async def get_html(url, wait=3000):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(wait)
            return await page.content()
        finally:
            await browser.close()

async def test_remote3():
    print("\n" + "="*60 + "\nREMOTE3.CO\n" + "="*60)
    html = await get_html("https://remote3.co")
    tree = lxml_html.fromstring(html)

    links = tree.xpath("//a[contains(@href,'/remote-jobs/') and not(contains(@href,'search')) and not(contains(@href,'category'))]")
    print(f"Job links: {len(links)}")
    for link in links[:8]:
        href = link.get('href','')
        title = ' '.join(link.text_content().split())[:80]
        # Try to find company in parent
        parent = link.getparent()
        parent_text = ' '.join(parent.text_content().split()) if parent is not None else ''
        print(f"  Title: {title[:60]}")
        print(f"  URL:   https://remote3.co{href}")
        print(f"  Parent: {parent_text[:80]}")
        print()

async def test_cryptojobslist():
    print("\n" + "="*60 + "\nCRYPTOJOBSLIST.COM\n" + "="*60)
    html = await get_html("https://cryptojobslist.com")
    tree = lxml_html.fromstring(html)

    # Try table-based selector
    tables = tree.xpath("//table[contains(@class,'job-preview-inline-table')]")
    print(f"Job tables: {len(tables)}")
    for t in tables[:3]:
        title_el = t.xpath(".//*[contains(@class,'job-title-text')]")
        company_el = t.xpath(".//*[contains(@class,'job-company-name-text')]")
        link_el = t.xpath(".//a[contains(@href,'/jobs/')]")
        title = title_el[0].text_content().strip() if title_el else "?"
        company = company_el[0].text_content().strip() if company_el else "?"
        link = link_el[0].get('href','') if link_el else "?"
        print(f"  Title: {title}  |  Company: {company}  |  URL: {link}")

    # Also try container divs
    divs = tree.xpath("//*[contains(@class,'job-title-text')]")
    print(f"\nElements with 'job-title-text': {len(divs)}")
    for d in divs[:5]:
        print(f"  [{d.tag}] {d.text_content().strip()[:80]}")
        # Walk up to find the container
        p = d.getparent()
        while p is not None:
            link = p.xpath(".//a[contains(@href,'/jobs/')]")
            if link:
                print(f"    URL: {link[0].get('href')}")
                break
            p = p.getparent()

async def test_cryptocurrencyjobs():
    print("\n" + "="*60 + "\nCRYPTOCURRENCYJOBS.CO\n" + "="*60)
    html = await get_html("https://cryptocurrencyjobs.co", wait=4000)
    tree = lxml_html.fromstring(html)

    # Algolia hit items
    hits = tree.xpath("//*[contains(@class,'ais-Hits-item')]")
    print(f"Algolia hits: {len(hits)}")
    for hit in hits[:4]:
        # Print all text nodes and links
        links = hit.xpath(".//a/@href")
        text = ' '.join(hit.text_content().split())[:200]
        print(f"  Text: {text[:120]}")
        print(f"  Links: {links[:3]}")
        print()

    # Also try all links
    job_links = tree.xpath("//a[contains(@href,'cryptocurrencyjobs.co') or contains(@href,'/job/')]")
    print(f"Job links: {len(job_links)}")
    for l in job_links[:5]:
        print(f"  {l.get('href')}  |  {' '.join(l.text_content().split())[:60]}")

async def test_weworkremotely():
    print("\n" + "="*60 + "\nWEWORKREMOTELY.COM\n" + "="*60)
    # Try the blockchain category page instead of search
    html = await get_html("https://weworkremotely.com/categories/remote-blockchain-jobs", wait=2000)
    tree = lxml_html.fromstring(html)

    listings = tree.xpath("//li[.//a[contains(@href,'/remote-jobs/listings/')]]")
    print(f"Job listings: {len(listings)}")
    for li in listings[:5]:
        link = li.xpath(".//a[contains(@href,'/remote-jobs/listings/')]")
        if link:
            href = link[0].get('href','')
            text = ' '.join(li.text_content().split())[:120]
            print(f"  URL: https://weworkremotely.com{href}")
            print(f"  Text: {text[:100]}")
            print()

    # Also check span.company and span.title
    companies = tree.xpath("//span[@class='company']")
    titles = tree.xpath("//span[@class='title']")
    print(f"Companies: {len(companies)}  |  Titles: {len(titles)}")
    for i in range(min(3, len(titles))):
        t = titles[i].text_content().strip()
        c = companies[i].text_content().strip() if i < len(companies) else "?"
        print(f"  {t} @ {c}")

async def main():
    await test_remote3()
    await test_cryptojobslist()
    await test_cryptocurrencyjobs()
    await test_weworkremotely()

asyncio.run(main())
