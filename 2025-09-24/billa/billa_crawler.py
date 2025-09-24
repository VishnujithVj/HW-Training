import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright
from pymongo import MongoClient

# Config 
START_URL = "https://shop.billa.at/"
DB_NAME = "billa_db"
COLLECTION_NAME = "product_url"
OUTPUT_JSON = Path("product_urls.json")
LOG_FILE = Path("crawler.log")
REQUEST_TIMEOUT = 60_000 
DELAY_BETWEEN_REQUESTS = 0.5 

# MongoDB
mongo_client = MongoClient("mongodb://localhost:27017")
db = mongo_client[DB_NAME]
urls_collection = db[COLLECTION_NAME]

# Logging 
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

OUTPUT_JSON.touch(exist_ok=True)


async def extract_hrefs_from_page(page, xpath: str) -> list:
    """Collect hrefs via XPath expression."""
    try:
        hrefs = await page.eval_on_selector_all(
            f"xpath={xpath}",
            "els => els.map(e => e.getAttribute('href'))"
        )
        return hrefs or []
    except Exception:
        return []


def resolve_links(base: str, hrefs: list) -> list:
    """Resolve relative hrefs to absolute, dedupe and keep only same-host links."""
    resolved = []
    for href in hrefs:
        if not href:
            continue
        abs_url = urljoin(base, href)
        if urlparse(abs_url).netloc == urlparse(START_URL).netloc:
            resolved.append(abs_url)

    seen, out = set(), []
    for u in resolved:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def make_doc(category_url, subcategory_url, product_url):
    """Build the structured document for DB/file."""
    return {
        "category_url": category_url,
        "subcategory_url": subcategory_url,
        "product_url": product_url,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def save_to_mongo(doc: dict):
    """Insert doc into MongoDB (dedupe by product_url)."""
    try:
        query = {"product_url": doc["product_url"]}
        if urls_collection.find_one(query) is None:
            urls_collection.insert_one(doc)
        else:
            logging.debug(f"Skipping insert, already present: {doc['product_url']}")
    except Exception as e:
        logging.exception(f"MongoDB insert error for {doc.get('product_url')}: {e}")


def append_to_jsonl(doc: dict):
    """Append single-line JSON to product_urls.json (without Mongo _id)."""
    try:
    
        safe_doc = {k: v for k, v in doc.items() if k != "_id"}

        with OUTPUT_JSON.open("a", encoding="utf-8") as f:
            f.write(json.dumps(safe_doc, ensure_ascii=False) + "\n")
    except Exception as e:
        logging.exception(f"Failed to write to {OUTPUT_JSON}: {e}")


async def save_record(doc: dict):
    """Save one record to Mongo + JSON file."""
    save_to_mongo(doc)
    append_to_jsonl(doc)


# Crawler
async def crawl_billa():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (compatible; BillaCrawler/1.0)")
        page = await context.new_page()

        
        logging.info(f"Visiting start url: {START_URL}")
        try:
            await page.goto(START_URL, timeout=REQUEST_TIMEOUT)
            await page.wait_for_load_state("networkidle", timeout=REQUEST_TIMEOUT)
        except Exception as e:
            logging.error(f"Failed to load {START_URL}: {e}")
            return

        # collect category URLs
        category_hrefs = await extract_hrefs_from_page(
            page, "//a[contains(@href, '/aktionen') or contains(@href, '/sortiment') or contains(@href, '/kategorie')]"
        )
        category_links = resolve_links(START_URL, category_hrefs)
        logging.info(f"Found {len(category_links)} categories")

        # iterate categories
        for cat_url in category_links:
            await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
            logging.info(f"Category: {cat_url}")
            try:
                await page.goto(cat_url, timeout=REQUEST_TIMEOUT)
                await page.wait_for_load_state("networkidle", timeout=REQUEST_TIMEOUT)
            except Exception as e:
                logging.error(f"Failed category {cat_url}: {e}")
                continue

            # collect subcategories
            sub_hrefs = await extract_hrefs_from_page(page, "//a[contains(@href, '/kategorie/')]")
            sub_links = resolve_links(cat_url, sub_hrefs)
            logging.info(f"  Found {len(sub_links)} subcategories")

            # iterate subcategories
            for sub_url in sub_links:
                await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
                logging.info(f"  Subcategory: {sub_url}")
                try:
                    await page.goto(sub_url, timeout=REQUEST_TIMEOUT)
                    await page.wait_for_load_state("networkidle", timeout=REQUEST_TIMEOUT)
                except Exception as e:
                    logging.error(f"Failed subcategory {sub_url}: {e}")
                    continue

                # collect product URLs
                prod_hrefs = await extract_hrefs_from_page(page, "//a[contains(@href, '/produkte/')]")
                prod_links = resolve_links(sub_url, prod_hrefs)
                logging.info(f" Found {len(prod_links)} products")

                for prod_url in prod_links:
                    await asyncio.sleep(DELAY_BETWEEN_REQUESTS / 2)
                    doc = make_doc(cat_url, sub_url, prod_url)
                    await save_record(doc)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(crawl_billa())
