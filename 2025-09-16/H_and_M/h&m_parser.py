import asyncio
import json
import logging
from pymongo import MongoClient
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# ----------------- CONFIG -----------------
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "hm_scraper"  # your DB name
URL_COLLECTION = "product_urls"  # URLs collected by crawler
DETAILS_COLLECTION = "product_details"
JSON_FILE = "product_details.json"
LOG_FILE = "parser.log"

HEADLESS = True
NAV_TIMEOUT = 90000  # Increase timeout for slow loading pages (ms)
ELEMENT_TIMEOUT = 60000  # Timeout for waiting specific elements

# ----------------- LOGGING -----------------
logger = logging.getLogger("hm_parser")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

# Console handler
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

# File handler
fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
fh.setFormatter(formatter)
logger.addHandler(fh)

# ----------------- MONGODB SETUP -----------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
url_col = db[URL_COLLECTION]
details_col = db[DETAILS_COLLECTION]

# ----------------- SCRAPER FUNCTION -----------------
async def scrape_product(page, url):
    product = {"url": url}
    try:
        await page.goto(url, timeout=NAV_TIMEOUT, wait_until="domcontentloaded")
        # Wait for product name to ensure page fully loaded
        await page.locator("xpath=//h1[contains(@class,'dfcd37')]").wait_for(timeout=ELEMENT_TIMEOUT)

        # XPath selectors
        product['name'] = await page.locator("xpath=//h1[contains(@class,'dfcd37')]").inner_text()
        product['price'] = await page.locator("xpath=//span[contains(@class,'eb0a80')]").inner_text()
        product['color'] = await page.locator("xpath=//p[contains(@class,'c67e97')]").inner_text()

        # Multiple sizes
        size_elements = await page.locator("xpath=//div[contains(@id,'sizeButton-')]/div").all_inner_texts()
        product['size'] = [s.strip() for s in size_elements if s.strip()]

        # Description
        product['description'] = await page.locator("xpath=//p[contains(@class,'e726c0')]").inner_text()

        # Reviews: attempt to click review buttons
        reviews_list = []
        review_buttons = await page.locator("xpath=//button[contains(@aria-label,'Reviews')]").all()
        for btn in review_buttons:
            try:
                await btn.click()
                review_texts = await page.locator("xpath=//div[contains(@class,'review')]").all_inner_texts()
                reviews_list.extend([r.strip() for r in review_texts if r.strip()])
            except Exception:
                continue
        product['reviews'] = reviews_list

        logger.info(f"Scraped successfully: {url}")

    except PlaywrightTimeoutError:
        logger.error(f"Timeout while scraping {url}")
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")

    return product

# ----------------- MAIN FUNCTION -----------------
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        page = await browser.new_page()

        urls = list(url_col.find({}))
        logger.info(f"Found {len(urls)} URLs to scrape.")

        for url_doc in urls:
            url = url_doc.get("product_url") or url_doc.get("url")
            if not url:
                continue

            logger.info(f"Scraping {url}")
            product_data = await scrape_product(page, url)

            # Insert into MongoDB
            try:
                details_col.update_one({"url": url}, {"$set": product_data}, upsert=True)
            except Exception as e:
                logger.error(f"MongoDB insert failed for {url}: {e}")

            # Append to JSON file line by line
            try:
                with open(JSON_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(product_data, ensure_ascii=False) + "\n")
            except Exception as e:
                logger.error(f"Failed to write JSON for {url}: {e}")

        await browser.close()
        logger.info("Scraping completed.")

# ----------------- RUN -----------------
if __name__ == "__main__":
    asyncio.run(main())
