import asyncio
import logging
import json
import time
from urllib.parse import urljoin
from pymongo import MongoClient
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# ========== CONFIG ==========
BASE_URL = "https://www.bayut.sa/en"
OUTPUT_FILE = "bayut_product_urls.json"

# Property types to include (match Bayut URL slugs)
PROPERTY_TYPES = [
    "apartments", "villas", "floors", "residential-buildings", "residential-lands",
    "houses", "rest-houses", "chalets", "rooms", "townhouses"
]

# MongoDB setup
client = MongoClient("mongodb://localhost:27017")
db = client["bayut_scraper"]
product_urls_col = db["product_urls"]

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("crawler.log"), logging.StreamHandler()],
)

# ========== HELPERS ==========
async def safe_goto(page, url, retries=3):
    """Goto with retries and relaxed wait condition"""
    for attempt in range(1, retries + 1):
        try:
            await page.goto(url, timeout=120000, wait_until="domcontentloaded")
            return True
        except PlaywrightTimeoutError:
            logging.warning(f"Timeout loading {url} (attempt {attempt}/{retries})")
            if attempt == retries:
                return False
            await asyncio.sleep(3)
    return False


async def extract_links(page, xpath_expr, filter_keywords=None):
    """Extract links from page using XPath and optional keyword filtering"""
    links = set()
    elements = await page.locator(f"xpath={xpath_expr}").all()
    for el in elements:
        href = await el.get_attribute("href")
        if href:
            full_url = urljoin(BASE_URL, href)
            if not filter_keywords or any(k in full_url for k in filter_keywords):
                links.add(full_url)
    return list(links)


# ========== STEP 1: CATEGORIES ==========
async def extract_category_urls(page):
    if not await safe_goto(page, BASE_URL):
        return []
    categories = await extract_links(page, "//a[@href]", ["/for-sale/", "/to-rent/"])
    categories = list(set([c.split("?")[0] for c in categories]))  # clean dupes
    logging.info(f"Found {len(categories)} category URLs")
    return categories


# ========== STEP 2: SUBCATEGORIES ==========
async def extract_subcategory_urls(page, category_url):
    if not await safe_goto(page, category_url):
        return []
    subcategories = await extract_links(page, "//a[@href]", PROPERTY_TYPES)
    subcategories = list(set([s.split("?")[0] for s in subcategories]))
    logging.info(f"{category_url} → {len(subcategories)} subcategories")
    return subcategories


# ========== STEP 3: PRODUCT URLS with PAGINATION ==========
async def extract_product_urls(page, category_url, subcategory_url, json_file):
    page_num = 1
    total_saved = 0

    while True:
        url = f"{subcategory_url}?page={page_num}"
        ok = await safe_goto(page, url)
        if not ok:
            break

        page_products = await extract_links(page, "//a[@href]", ["/property/"])
        if not page_products:
            logging.info(f"No products on {url}, stopping pagination.")
            break

        logging.info(f"{subcategory_url} page {page_num} → {len(page_products)} products")

        for product_url in page_products:
            record = {
                "category_url": category_url,
                "subcategory_url": subcategory_url,
                "product_url": product_url,
                "page": page_num,
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

            # Save to MongoDB (upsert to avoid duplicates)
            product_urls_col.update_one(
                {"product_url": product_url},
                {"$set": record},
                upsert=True,
            )

            # Save to JSON incrementally
            json_file.write(json.dumps(record, ensure_ascii=False) + "\n")
            json_file.flush()

            total_saved += 1
            logging.info(f"Saved → {product_url}")

        page_num += 1
        time.sleep(1)  # polite delay

    logging.info(f"Total saved for {subcategory_url}: {total_saved}")


# ========== MAIN PIPELINE ==========
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

        categories = await extract_category_urls(page)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as json_file:
            for cat in categories:
                subcats = await extract_subcategory_urls(page, cat)

                if not subcats:  # if no subcategories, use category directly
                    subcats = [cat]

                for sub in subcats:
                    await extract_product_urls(page, cat, sub, json_file)
                    time.sleep(1)  # polite delay

        logging.info(f"All data saved incrementally to {OUTPUT_FILE}")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
