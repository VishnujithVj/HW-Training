import asyncio
import json
import logging
import re
from pathlib import Path

from lxml import html
from pymongo import MongoClient
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

# Logging
LOG_FILE = "parser.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)

# MongoDB
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "logic_immo_db"
URL_COLLECTION = "product_urls"
DETAILS_COLLECTION = "product_details"
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
url_collection = db[URL_COLLECTION]
details_collection = db[DETAILS_COLLECTION]

DETAILS_JSON_FILE = Path("product_details.json")
DETAILS_JSON_FILE.touch(exist_ok=True)


# Helper
def clean_text(text: str) -> str:
    if not text:
        return None
    text = text.replace("\u00a0", " ").replace("\u202f", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


class LogicImmoParser:
    def __init__(self):
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/139.0.0.0 Safari/537.36"
            )
        }

    async def launch_browser(self) -> Browser:
        logging.info("Launching browser...")
        self.playwright = await async_playwright().start()
        browser = await self.playwright.chromium.launch(headless=False)
        return browser

    async def parse_listing(self, page: Page, url: str) -> dict:
        """Extract required fields from a listing page using lxml + XPath."""
        data = {"URL": url}
        try:
            # Navigate
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(3000)

            # --- Try clicking "show phone" button if present ---
            try:
                phone_button = page.locator('xpath=//button[@aria-label="Tel"]')
                if await phone_button.count() > 0:
                    await phone_button.first.click()
                    await page.wait_for_timeout(2000)
            except Exception:
                pass

            # --- Get page content ---
            content = await page.content()
            tree = html.fromstring(content)

            # --- Seller Phone ---
            phone_number = None
            phone_texts = tree.xpath('//div[@class="css-12m0k8p"]//text()')
            if phone_texts:
                raw_phone = phone_texts[0].strip()
                match = re.search(r"\+?\d[\d\s]+", raw_phone)
                if match:
                    phone_number = re.sub(r"\s+", "", match.group())
            # fallback JSON
            if not phone_number:
                phone_match = re.search(r'"phoneNumbers":\s*\[\s*"([^"]+)"\s*\]', content)
                if phone_match:
                    phone_number = phone_match.group(1).strip()
            data["seller_phone"] = phone_number

            # --- Email ---
            seller_email = tree.xpath('//a[contains(@href,"mailto:")]/text()')
            data["seller_email"] = clean_text(seller_email[0]) if seller_email else None

            # --- Property Type ---
            property_type = tree.xpath('//span[contains(@class,"css-1nxshv1")]/text()')
            data["property_type"] = clean_text(property_type[0]) if property_type else None

            # --- Property Size ---
            property_size = None
            size_nodes = tree.xpath('//div[contains(@class,"css-7tj8u")]/span/text()')
            if len(size_nodes) >= 5:
                property_size = clean_text(size_nodes[4])
            data["property_size"] = property_size

            # --- Price ---
            property_price = tree.xpath('//span[contains(@class,"css-9wpf20")]/text()')
            data["property_price"] = clean_text(property_price[0]) if property_price else None

            # --- City (static for now) ---
            data["city"] = "Franconville"

            logging.info(f"Extracted details for URL: {url}")
            return data

        except Exception as e:
            logging.error(f"Error extracting details from {url}: {e}")
            return None

    async def save_details(self, details: dict):
        if details:
            # Save to JSON
            with open(DETAILS_JSON_FILE, "a", encoding="utf-8") as f:
                json.dump(details, f, ensure_ascii=False)
                f.write("\n")
            logging.info(f"Saved to JSON: {details['URL']}")

            # Save to MongoDB
            if not details_collection.find_one({"URL": details["URL"]}):
                details_collection.insert_one(details)
                logging.info(f"Saved to MongoDB: {details['URL']}")

    async def parse(self):
        browser = await self.launch_browser()
        context: BrowserContext = await browser.new_context(extra_http_headers=self.headers)
        page: Page = await context.new_page()

        urls_cursor = url_collection.find({}, {"url": 1})
        for url_doc in urls_cursor:
            url = url_doc.get("url")
            if url:
                details = await self.parse_listing(page, url)
                await self.save_details(details)

        await browser.close()
        await self.playwright.stop()
        logging.info("Parsing finished.")


if __name__ == "__main__":
    parser = LogicImmoParser()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(parser.parse())
    finally:
        loop.close()
