import asyncio
import logging
import time
import json
from typing import List, Dict
from urllib.parse import urljoin

import psutil
from pymongo import MongoClient
from playwright.async_api import async_playwright, Page, Response, TimeoutError as PlaywrightTimeoutError

# ---------- Configurations ----------
START_URL = "https://www2.hm.com/en_in/index.html"
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "hm_scraper"
COLLECTION_PRODUCTS = "product_urls"

NAV_TIMEOUT = 30000  # ms
HEADLESS = True

# Browser-like headers
HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "user-agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    ),
    "sec-ch-ua": '"Chromium";v="139", "Google Chrome";v="139", "Not=A?Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "referer": "https://www.google.com/",
}

# ---------- Logging ----------
logger = logging.getLogger("hm_scraper")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

file_handler = logging.FileHandler("crawler.log", mode="a", encoding="utf-8")
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# ---------- MongoDB Setup ----------
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
coll_products = db[COLLECTION_PRODUCTS]
coll_products.create_index("product_url", unique=True)

# ---------- Helpers ----------
def system_snapshot() -> Dict:
    proc = psutil.Process()
    mem = psutil.virtual_memory()
    return {
        "timestamp": time.time(),
        "rss_bytes": proc.memory_info().rss,
        "system_total_mem": mem.total,
        "system_used_percent": mem.percent,
        "cpu_percent": psutil.cpu_percent(interval=None),
    }


async def record_response_metadata(url: str, response: Response | None, extra: Dict = None):
    meta = {
        "url": url,
        "timestamp": time.time(),
        "system": system_snapshot(),
    }
    if response:
        try:
            meta.update({
                "status": response.status,
                "ok": response.ok,
                "url_final": response.url,
            })
        except Exception as e:
            meta["response_error"] = str(e)
    else:
        meta.update({"status": None, "ok": False})
    if extra:
        meta.update(extra)
    logger.info(f"Response meta: {meta}")


def normalize_url(base: str, href: str) -> str:
    if not href:
        return None
    href = href.strip()
    if href.startswith("javascript:") or href.startswith("mailto:"):
        return None
    return urljoin(base, href)


async def safe_goto(page: Page, url: str, timeout: int = NAV_TIMEOUT) -> Response | None:
    start = time.perf_counter()
    response = None
    try:
        response = await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        elapsed = time.perf_counter() - start
        await record_response_metadata(url, response, extra={"elapsed_s": elapsed})
        logger.info("Visited %s (status=%s, time=%.2fs)", url, response.status if response else None, elapsed)
    except PlaywrightTimeoutError:
        logger.error("Timeout while loading %s", url)
    except Exception:
        logger.exception("Error while loading %s", url)
    return response


# ---------- Scraping Logic ----------
async def extract_category_urls(page: Page) -> List[Dict]:
    """Extract only main categories: Women, Men, Kids, Home"""
    await page.wait_for_load_state("domcontentloaded")
    cats = await page.eval_on_selector_all(
        "a[href*='/en_in/']",
        "els => els.map(e => ({ href: e.getAttribute('href'), text: e.textContent.trim() }))"
    )
    categories = []
    for c in cats:
        if c["href"] and any(c["href"].startswith(cat) for cat in ["/en_in/women", "/en_in/men", "/en_in/kids", "/en_in/home"]):
            url = normalize_url(page.url, c["href"])
            categories.append({"url": url, "name": c["text"]})
    logger.info("Found %d categories", len(categories))
    return categories


async def extract_subcategory_urls(page: Page) -> List[Dict]:
    """Extract subcategories (like Dresses, Jeans, Tops)"""
    await page.wait_for_load_state("domcontentloaded")
    subs = await page.eval_on_selector_all(
        "a[href*='/shop-by-product/']",
        "els => els.map(e => ({ href: e.getAttribute('href'), text: e.textContent.trim() }))"
    )
    found = []
    for s in subs:
        url = normalize_url(page.url, s["href"])
        if url:
            found.append({"url": url, "name": s["text"]})
    logger.info("Found %d subcategories on %s", len(found), page.url)
    return found


async def extract_product_detail_urls(page: Page) -> List[str]:
    """Extract final product detail page URLs (contain productpage.)"""
    await page.wait_for_load_state("domcontentloaded")
    anchors = await page.query_selector_all("a[href*='productpage.']")
    found = set()
    for a in anchors:
        href = await a.get_attribute("href")
        url = normalize_url(page.url, href)
        if url:
            found.add(url)
    return list(found)


async def crawl_products_in_listing(page: Page, cat: Dict, sub: Dict) -> List[Dict]:
    """Crawl product detail pages for a given subcategory"""
    all_products = []
    page_num = 1

    while True:
        url = f"{sub['url']}&page={page_num}" if "?" in sub["url"] else f"{sub['url']}?page={page_num}"
        resp = await safe_goto(page, url)
        if not resp or resp.status >= 400:
            break

        products = await extract_product_detail_urls(page)
        if not products:
            break

        for prod in products:
            doc = {
                "category_url": cat["url"],
                "subcategory_url": sub["url"],
                "product_url": prod,
                "scraped_ts": time.time(),
            }
            try:
                coll_products.update_one({"product_url": prod}, {"$setOnInsert": doc}, upsert=True)
                all_products.append(doc)

                # append to JSON file one by one
                with open("product_urls.json", "a", encoding="utf-8") as f:
                    f.write(json.dumps(doc, ensure_ascii=False) + "\n")

            except Exception:
                logger.exception("Failed to insert %s", prod)

        logger.info("Page %d -> %d products", page_num, len(products))
        page_num += 1

    return all_products


async def process():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(
            user_agent=HEADERS["user-agent"],
            extra_http_headers=HEADERS,
            viewport={"width": 1366, "height": 768},
            locale="en-US",
            timezone_id="Asia/Kolkata",
            java_script_enabled=True,
        )

        page = await context.new_page()
        logger.info("Starting crawl from %s", START_URL)
        resp = await safe_goto(page, START_URL)
        if resp is None or (resp and resp.status >= 400):
            logger.error("Failed to fetch start page. Aborting.")
            await browser.close()
            return

        categories = await extract_category_urls(page)
        for cat in categories:
            resp = await safe_goto(page, cat["url"])
            if not resp or resp.status >= 400:
                continue

            subcats = await extract_subcategory_urls(page)
            for sub in subcats:
                await crawl_products_in_listing(page, cat, sub)

        await browser.close()


# ---------- Run ----------
if __name__ == "__main__":
    start_time = time.time()
    try:
        asyncio.run(process())
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
    except Exception:
        logger.exception("Unhandled exception in scraper")
    finally:
        total = time.time() - start_time
        logger.info("Total runtime: %.2fs", total)
        try:
            snap = system_snapshot()
            logger.info("Final system snapshot: %s", snap)
        except Exception:
            logger.exception("Failed to capture final system snapshot")
