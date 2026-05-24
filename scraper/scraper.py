"""
scraper.py — Playwright-based scraper for KJSIT website
Handles JS-rendered content, tab clicks, dynamic syllabus pages
"""

import asyncio
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse
from collections import deque

BASE_URL = "https://kjsit.somaiya.edu.in"
DOMAIN   = "kjsit.somaiya.edu.in"

# ── Priority pages (always scraped, in order) ─────────────────────────────────
PRIORITY_PAGES = [
    "https://kjsit.somaiya.edu.in/en/introduction",
    "https://kjsit.somaiya.edu.in/en/vision-mission",
    "https://kjsit.somaiya.edu.in/en/principal-words",
    "https://kjsit.somaiya.edu.in/en/goverence-administration",
    "https://kjsit.somaiya.edu.in/en/governance-structure",
    "https://kjsit.somaiya.edu.in/en/placement",
    "https://kjsit.somaiya.edu.in/en/campus-invite",
    "https://kjsit.somaiya.edu.in/en/examination-overview",
    "https://kjsit.somaiya.edu.in/en/ordinance-rules",
    "https://kjsit.somaiya.edu.in/en/result",
    "https://kjsit.somaiya.edu.in/en/result-analysis",
    "https://kjsit.somaiya.edu.in/en/academic-overview",
    "https://kjsit.somaiya.edu.in/en/academic-calendar",
    "https://kjsit.somaiya.edu.in/en/about-library",
    "https://kjsit.somaiya.edu.in/en/infrastructure",
    "https://kjsit.somaiya.edu.in/en/committes",
    "https://kjsit.somaiya.edu.in/en/student-committees",
    "https://kjsit.somaiya.edu.in/en/student-support-systems",
    "https://kjsit.somaiya.edu.in/en/co-curricular-activities",
    "https://kjsit.somaiya.edu.in/en/extracurricular-activities",
    "https://kjsit.somaiya.edu.in/en/internship",
    "https://kjsit.somaiya.edu.in/en/alumni_overview",
    "https://kjsit.somaiya.edu.in/en/faqs",
    "https://kjsit.somaiya.edu.in/en/contact-us",
    "https://kjsit.somaiya.edu.in/en/contact-us/contact-directory",
    "https://kjsit.somaiya.edu.in/en/notices",
    "https://kjsit.somaiya.edu.in/en/forms",
    "https://kjsit.somaiya.edu.in/en/about-research-development-cell",
    "https://kjsit.somaiya.edu.in/en/institutions_innovation_council",
    "https://kjsit.somaiya.edu.in/en/center-of-excellence",
    "https://kjsit.somaiya.edu.in/en/software_development_cell",
    "https://kjsit.somaiya.edu.in/en/mou",
    "https://kjsit.somaiya.edu.in/en/awards-honors",
    "https://kjsit.somaiya.edu.in/en/nirf",
    "https://kjsit.somaiya.edu.in/en/mandatory-disclosure",
    "https://kjsit.somaiya.edu.in/en/fra",
    "https://kjsit.somaiya.edu.in/en/admission/first-year-bachelor-of-engineering",
    "https://kjsit.somaiya.edu.in/en/admission/second-year-bachelor-of-engineering",
]

# ── Programme pages with JS tabs (special handling) ───────────────────────────
PROGRAMME_PAGES = [
    "https://kjsit.somaiya.edu.in/en/programme/electronics-and-telecommunication-engineering",
    "https://kjsit.somaiya.edu.in/en/programme/computer-engineering",
    "https://kjsit.somaiya.edu.in/en/programme/information-technology-engineering",
    "https://kjsit.somaiya.edu.in/en/programme/be-in-artificial-intelligence-and-data-science",
    "https://kjsit.somaiya.edu.in/en/programme/artificial-intelligence",
]

# ── Skip patterns for general crawl ──────────────────────────────────────────
SKIP_PATTERNS = [
    "login", "portal", "newsletter", "gallery", "old",
    ".pdf", "staff-directory", "faculty-directory",
    "view-events", "events/", "grievance", "covid",
    "media", "scholarship", "notices?",
]


# ── Clean extracted text ──────────────────────────────────────────────────────
def clean_text(raw: str, url: str, title: str = "") -> str:
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    meaningful = [l for l in lines if len(l) > 20]
    body = "\n".join(meaningful)
    return f"Page: {url}\nTitle: {title}\n\n{body}"


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.netloc != DOMAIN:
        return False
    url_lower = url.lower()
    return not any(skip in url_lower for skip in SKIP_PATTERNS)


# ── Scrape a single normal page ───────────────────────────────────────────────
async def scrape_page(page, url: str) -> str | None:
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(1500)   # let JS settle

        title = await page.title()

        # Remove nav/footer noise
        await page.evaluate("""
            ['nav','footer','header','script','style','noscript','iframe','form']
            .forEach(tag => document.querySelectorAll(tag)
            .forEach(el => el.remove()))
        """)

        # Try content containers in order
        for selector in ["main", "article", ".field--name-body",
                         ".view-content", ".container", "body"]:
            el = page.locator(selector).first
            if await el.count() > 0:
                text = await el.inner_text()
                if len(text.strip()) > 100:
                    return clean_text(text, url, title)

        return None
    except Exception as e:
        print(f"  ❌ {url} — {e}")
        return None


# ── Scrape programme page — clicks ALL tabs to expose JS content ──────────────
async def scrape_programme_page(page, url: str) -> str | None:
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)

        title = await page.title()
        all_text_parts = [f"Page: {url}\nTitle: {title}\n"]

        # ✅ Only click tabs inside the main content area, max 15 tabs
        tab_selectors = [
            "main .nav-tabs li a",
            "main [data-toggle='tab']",
            "main .vthmstab",
            "main li[role='tab']",
            ".programme-tabs a",
        ]

        clicked_tabs = set()

        for selector in tab_selectors:
            tabs = page.locator(selector)
            count = await tabs.count()

            # ✅ Cap at 15 to avoid nav pollution
            count = min(count, 15)

            for i in range(count):
                tab = tabs.nth(i)
                tab_text = (await tab.inner_text(timeout=3000)).strip()

                if not tab_text or tab_text in clicked_tabs:
                    continue
                clicked_tabs.add(tab_text)

                try:
                    await tab.click(timeout=5000)          # ✅ short timeout per click
                    await page.wait_for_timeout(600)

                    for content_sel in [".tab-content", ".tab-pane.active",
                                        ".accordion-body", "main"]:
                        el = page.locator(content_sel).first
                        if await el.count() > 0:
                            text = await el.inner_text(timeout=5000)
                            if len(text.strip()) > 50:
                                all_text_parts.append(
                                    f"\n--- {tab_text} ---\n{text.strip()}"
                                )
                                break
                except Exception:
                    continue   # ✅ skip broken tabs silently, don't crash

        # Fallback — grab full page text anyway
        await page.evaluate("""
            ['nav','footer','header','script','style'].forEach(tag =>
            document.querySelectorAll(tag).forEach(el => el.remove()))
        """)
        body_text = await page.locator("body").inner_text(timeout=8000)
        all_text_parts.append(f"\n--- Full Page ---\n{body_text[:3000]}")

        combined = "\n".join(all_text_parts)
        lines = [l.strip() for l in combined.splitlines()
                 if l.strip() and len(l.strip()) > 15]
        return "\n".join(lines)

    except Exception as e:
        print(f"  ❌ Programme page {url} — {e}")
        return None
    
# ── Extract links from current page ──────────────────────────────────────────
async def get_links(page, base_url: str) -> set[str]:
    hrefs = await page.eval_on_selector_all(
        "a[href]",
        "els => els.map(e => e.href)"
    )
    links = set()
    for href in hrefs:
        parsed = urlparse(href)
        if DOMAIN in parsed.netloc:
            clean = parsed._replace(fragment="", query="").geturl()
            links.add(clean)
    return links


# ── Main crawl function ───────────────────────────────────────────────────────
async def crawl_async(start_url: str, max_depth: int = 2,
                      max_pages: int = 80) -> list[tuple[str, str]]:
    results = []
    visited = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (compatible; KJSITBot/1.0)"
        )
        page = await context.new_page()

        # ── Phase 1: Programme pages (tab clicking) ───────────────────────────
        print(f"\n🎓 Phase 1: Scraping {len(PROGRAMME_PAGES)} programme pages (JS tabs)...")
        for url in PROGRAMME_PAGES:
            if url in visited:
                continue
            print(f"  ✅ {url}")
            visited.add(url)
            text = await scrape_programme_page(page, url)
            if text and len(text) > 100:
                results.append((url, text))

        # ── Phase 2: Priority pages ───────────────────────────────────────────
        print(f"\n📌 Phase 2: Scraping {len(PRIORITY_PAGES)} priority pages...")
        for url in PRIORITY_PAGES:
            if url in visited:
                continue
            print(f"  ✅ {url}")
            visited.add(url)
            text = await scrape_page(page, url)
            if text and len(text) > 100:
                results.append((url, text))

        # ── Phase 3: General crawl ────────────────────────────────────────────
        print(f"\n🕷️  Phase 3: General crawl from {start_url}...")
        queue = deque([(start_url, 0)])

        while queue and len(visited) < max_pages:
            url, depth = queue.popleft()
            if depth > max_depth or url in visited:
                continue

            visited.add(url)
            print(f"  🔍 (depth {depth}): {url}")

            text = await scrape_page(page, url)
            if text and len(text) > 100:
                results.append((url, text))

            if depth < max_depth:
                links = await get_links(page, url)
                for link in links:
                    if link not in visited and is_valid_url(link):
                        queue.append((link, depth + 1))

        await browser.close()

    print(f"\n✅ Crawl complete — {len(results)} pages scraped.")
    return results


# ── Sync wrapper (called by ingest.py) ───────────────────────────────────────
def crawl(start_url: str, max_depth: int = 2,
          max_pages: int = 80) -> list[tuple[str, str]]:
    return asyncio.run(crawl_async(start_url, max_depth, max_pages))


# ── Test ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pages = crawl("https://kjsit.somaiya.edu.in/en", max_depth=1, max_pages=5)
    print("\n--- SAMPLE ---")
    if pages:
        print(pages[0][1][:800])