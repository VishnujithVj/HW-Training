#!/usr/bin/env python3
"""
Billa Crawler with Pagination
-----------------------------
- Extracts category, subcategory, and product URLs (with pagination) from Billa Shop
- Saves records incrementally to:
    * MongoDB collection (product_urls)
    * product_urls.json (one JSON object per line)
    * crawler.log (logging)
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from datetime import datetime, timezone
from playwright.async_api import async_playwright
from pymongo import MongoClient


# ---------------- Logging ----------------
LOG_FILE = "crawler.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ---------------- Output Files ----------------
OUTPUT_JSON = Path("product_urls.json")
OUTPUT_JSON.touch(exist_ok=True)

# ---------------- MongoDB Setup ----------------
client = MongoClient("mongodb://localhost:27017")
db = client["billa_site_db"]
product_urls_col = db["product_urls"]

# ---------------- Selectors (XPath) ----------------
CATEGORY_URL = "https://shop.billa.at/kategorie"
XPATH_CATEGORY = "//a[contains(@class,'ws-category-tree-navigation-button')]"
XPATH_SUBCATEGORY = "//a[contains(@data-test,'category-tree-navigation-button')]"
XPATH_PRODUCT = "//a[contains(@class,'ws-product-tile__link')]"
XPATH_NEXT_PAGE = "//a[contains(@aria-label,'Next page')]"


# ---------------- Save Helpers ----------------

def save_record(category_url: str, subcategory_url: str, product_url: str):
    """Save record to JSON and MongoDB"""
    inserted_at = datetime.now(timezone.utc)

    record = {
        "category_url": category_url,
        "subcategory_url": subcategory_url,
        "product_url": product_url,
        "inserted_at": inserted_at,  # datetime for Mongo
    }

    # Save to JSON (convert datetime → string)
    json_record = {
        **record,
        "inserted_at": inserted_at.isoformat()
    }
    with open(OUTPUT_JSON, "a", encoding="utf-8") as f:
        f.write(json.dumps(json_record, ensure_ascii=False) + "\n")

    # Save to MongoDB (datetime stored natively)
    if not product_urls_col.find_one({"product_url": product_url}):
        product_urls_col.insert_one(record)


async def scrape_billa():
    logging.info("🚀 Starting Billa crawler...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (compatible; BillaCrawler/1.0)"
        )
        page = await context.new_page()

        # ---------------- Load Category Page ----------------
        logging.info(f"Navigating to {CATEGORY_URL}")
        response = await page.goto(CATEGORY_URL, timeout=60000)
        if response:
            logging.info(f"✅ Loaded {CATEGORY_URL} [status={response.status}]")
        else:
            logging.error(f"❌ Failed to load {CATEGORY_URL}")
            return

        # ---------------- Extract Category URLs ----------------
        category_links = await page.eval_on_selector_all(
            XPATH_CATEGORY,
            "elements => elements.map(el => el.href)"
        )
        logging.info(f"Found {len(category_links)} category URLs")

        # ---------------- Loop through Categories ----------------
        for category_url in category_links:
            try:
                logging.info(f"➡️ Visiting category: {category_url}")
                resp_cat = await page.goto(category_url, timeout=60000)
                if resp_cat:
                    logging.info(f"✅ Loaded {category_url} [status={resp_cat.status}]")
                else:
                    logging.warning(f"⚠️ No response for {category_url}")
                    continue

                # Extract Subcategory URLs
                subcategory_links = await page.eval_on_selector_all(
                    XPATH_SUBCATEGORY,
                    "elements => elements.map(el => el.href)"
                )
                logging.info(f"Found {len(subcategory_links)} subcategories in {category_url}")

                # ---------------- Loop through Subcategories ----------------
                for sub_url in subcategory_links:
                    try:
                        logging.info(f"➡️ Visiting subcategory: {sub_url}")
                        await page.goto(sub_url, timeout=60000)

                        # Loop through pagination
                        while True:
                            # Extract product URLs
                            product_links = await page.eval_on_selector_all(
                                XPATH_PRODUCT,
                                "elements => elements.map(el => el.href)"
                            )
                            logging.info(f"Found {len(product_links)} products in {sub_url}")

                            for product_url in product_links:
                                save_record(category_url, sub_url, product_url)
                                logging.info(f"💾 Saved product: {product_url}")

                            # Check for pagination "next page"
                            next_button = await page.query_selector(XPATH_NEXT_PAGE)
                            if next_button:
                                next_href = await next_button.get_attribute("href")
                                if next_href:
                                    logging.info(f"➡️ Going to next page: {next_href}")
                                    await page.goto(next_href, timeout=60000)
                                    continue
                            break  # No more pages

                    except Exception as e:
                        logging.error(f"❌ Error in subcategory {sub_url}: {e}")

            except Exception as e:
                logging.error(f"❌ Error in category {category_url}: {e}")

        await browser.close()
        logging.info("🎉 Crawler finished successfully!")


if __name__ == "__main__":
    asyncio.run(scrape_billa())
