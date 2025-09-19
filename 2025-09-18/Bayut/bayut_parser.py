import asyncio
import logging
import time
import json
import re
from pymongo import MongoClient
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# CONFIG
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "bayut_scraper"
URL_COLLECTION = "product_urls"      
DETAILS_COLLECTION = "product_details"  
OUTPUT_FILE = "bayut_product_details.json"

# MongoDB 
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
urls_col = db[URL_COLLECTION]
details_col = db[DETAILS_COLLECTION]

# Logging 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("parser.log"), logging.StreamHandler()],
)


async def safe_goto(page, url, retries=3):
    """Goto with retries"""
    for attempt in range(1, retries + 1):
        try:
            await page.goto(url, timeout=120000, wait_until="domcontentloaded")
            return True
        except TimeoutError:
            logging.warning(f"Timeout loading {url} (attempt {attempt}/{retries})")
            if attempt == retries:
                return False
            await asyncio.sleep(3)
    return False


async def extract_text(page, selector):
    """Extract inner text or return empty string"""
    try:
        el = page.locator(selector).first
        if await el.count() > 0:
            return (await el.inner_text()).strip()
    except Exception:
        return ""
    return ""


async def parse_property(page, url):
    ok = await safe_goto(page, url)
    if not ok:
        return None

    raw_ref = await extract_text(page, "span[aria-label='Reference']")
    reference_number = ""
    if raw_ref:
        match = re.search(r"(\d+)", raw_ref)
        if match:
            reference_number = match.group(1)

    data = {
        "reference_number": reference_number,
        "url": url,
        "broker_display_name": await extract_text(page, "a[aria-label='Agent name'] h2"),
        "broker": await extract_text(page, "h3[aria-label*='Agency name']"),
        "category": await extract_text(page, "ol.breadcrumb li:last-child"),
        "category_url": url.split("?")[0].rsplit("/", 1)[0],
        "title": await extract_text(page, "h1"),
        "description": await extract_text(page, "._812d3f30, .c-property-description"),
        "location": await extract_text(page, "div[aria-label='Property header']"),
        "price": await extract_text(page, "span[aria-label='Price']"),
        "currency": await extract_text(page, "span[aria-label='Currency']"),
        "price_per": await extract_text(page, "span[aria-label*='per']"),
        "bedrooms": await extract_text(page, "span._3458a9d4:has-text('Bed')"),
        "bathrooms": await extract_text(page, "span._3458a9d4:has-text('Bath')"),
        "furnished": await extract_text(page, "span[aria-label='Furnishing']"),
        "rera_permit_number": await extract_text(page, "span[aria-label='Permit number']"),
        "dtcm_licence": await extract_text(page, "span:has-text('DTCM Licence') + span"),
        "scraped_ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "amenities": [],
    }

    try:
        amenities = await page.locator(".c-amenities__item, .c20d971e").all_inner_texts()
        data["amenities"] = [a.strip() for a in amenities if a.strip()]
    except Exception:
        data["amenities"] = []

    for k, v in data.items():
        if v is None:
            data[k] = "" if k != "amenities" else []

    return data


async def save_to_json(data, filename):
    """Append one property to JSON file"""
    with open(filename, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


# MAIN
async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            locale="en-US"
        )
        page = await context.new_page()

        total = urls_col.count_documents({})
        logging.info(f"Found {total} product URLs to parse")

        cursor = urls_col.find({})
        for idx, doc in enumerate(cursor, start=1):
            url = doc.get("product_url") or doc.get("url")
            if not url:
                continue

            logging.info(f"[{idx}/{total}] Parsing {url}")

            try:
                data = await parse_property(page, url)
                if not data:
                    continue

                # Save to MongoDB
                details_col.update_one(
                    {"url": url},
                    {"$set": data},
                    upsert=True,
                )

                # Save to JSON
                await save_to_json(data, OUTPUT_FILE)

                logging.info(f"✅ Saved details for {url}")

            except Exception as e:
                logging.error(f"❌ Error parsing {url}: {e}")

            time.sleep(1)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
