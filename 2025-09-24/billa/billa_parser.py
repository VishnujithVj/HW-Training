import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright
from pymongo import MongoClient

# Config
DB_NAME = "billa_db"
URLS_COLLECTION = "product_url"
DETAILS_COLLECTION = "product_details"
OUTPUT_JSON = Path("product_details.json")
LOG_FILE = Path("parser.log")
REQUEST_TIMEOUT = 60_000  
DELAY_BETWEEN_REQUESTS = 0.5  

# MongoDB 
mongo_client = MongoClient("mongodb://localhost:27017")
db = mongo_client[DB_NAME]
urls_collection = db[URLS_COLLECTION]
details_collection = db[DETAILS_COLLECTION]

# Logging 
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

OUTPUT_JSON.touch(exist_ok=True)

# Helpers
async def extract_text(page, selector: str, by: str = "xpath") -> str | None:
    """Extract text by xpath or css selector."""
    try:
        if by == "xpath":
            el = await page.query_selector(f"xpath={selector}")
        else:
            el = await page.query_selector(selector)

        if el:
            txt = (await el.inner_text()).strip()
            return clean_text(txt)
    except Exception:
        return None
    return None


def clean_text(raw: str | None) -> str | None:
    """Clean extracted text with regex: remove labels, newlines, extra spaces."""
    if not raw:
        return None

    text = raw.strip()

    text = re.sub(r"^(Ingredients:|Zutaten:)\s*", "", text, flags=re.I)
    text = re.sub(r"^(Manufacturer:|Hersteller:)\s*", "", text, flags=re.I)

    text = re.sub(r"\s+", " ", text)

    return text if text else None


def make_doc(url: str, data: dict) -> dict:
    """Build structured document for Mongo + JSON."""
    return {
        "product_url": url,
        "title": data.get("title"),
        "price": data.get("price"),
        "description": data.get("description"),
        "ingredients": data.get("ingredients"),
        "manufacturer": data.get("manufacturer"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def save_to_mongo(doc: dict):
    """Insert doc into MongoDB (dedupe by product_url)."""
    try:
        query = {"product_url": doc["product_url"]}
        if details_collection.find_one(query) is None:
            details_collection.insert_one(doc)
        else:
            logging.debug(f"Skipping insert, already present: {doc['product_url']}")
    except Exception as e:
        logging.exception(f"MongoDB insert error for {doc.get('product_url')}: {e}")


def append_to_jsonl(doc: dict):
    """Append single-line JSON to product_details.json."""
    try:
        safe_doc = {k: v for k, v in doc.items() if k != "_id"}
        with OUTPUT_JSON.open("a", encoding="utf-8") as f:
            f.write(json.dumps(safe_doc, ensure_ascii=False) + "\n")
    except Exception as e:
        logging.exception(f"Failed to write to {OUTPUT_JSON}: {e}")


async def save_record(doc: dict):
    save_to_mongo(doc)
    append_to_jsonl(doc)


# Parser
async def parse_billa_products():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (compatible; BillaParser/1.0)"
        )
        page = await context.new_page()

        urls_cursor = urls_collection.find({}, {"product_url": 1})
        total_urls = urls_collection.count_documents({})
        logging.info(f"Found {total_urls} product URLs to parse")

        for url_doc in urls_cursor:
            url = url_doc["product_url"]
            logging.info(f"Parsing: {url}")

            try:
                await page.goto(url, timeout=REQUEST_TIMEOUT)
                await page.wait_for_load_state("networkidle", timeout=REQUEST_TIMEOUT)
            except Exception as e:
                logging.error(f"Failed to load {url}: {e}")
                continue

            title = await extract_text(page, "//h1")
            price = await extract_text(
                page,
                "//div[@data-test='product-price-type']//div[contains(@class,'__value')]",
            )
            description = await extract_text(
                page,
                "//div[contains(@class,'ws-product-slug-main__description-short')]",
            )

            ingredients = await extract_text(
                page,
                "//div[@class='ws-product-detail-row']//div[contains(text(),'Zutaten') or contains(text(),'Ingredients')]/following-sibling::div",
                by="xpath",
            )

            manufacturer = await extract_text(
                page,
                "//div[@class='ws-product-detail-row']//div[contains(text(),'Hersteller') or contains(text(),'Manufacturer')]/following-sibling::div",
                by="xpath",
            )

            data = {
                "title": title,
                "price": price,
                "description": description,
                "ingredients": ingredients,
                "manufacturer": manufacturer,
            }

            doc = make_doc(url, data)
            await save_record(doc)

            await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(parse_billa_products())

