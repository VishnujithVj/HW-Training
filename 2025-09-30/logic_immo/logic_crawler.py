import asyncio
import json
import logging
from pathlib import Path
from pymongo import MongoClient
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import urllib.parse

# Logging
LOG_FILE = "crawler.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# MongoDB
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "logic_immo_db"
COLLECTION_NAME = "product_urls"
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]


JSON_FILE = Path("product_urls.json")
JSON_FILE.touch(exist_ok=True)


class LogicImmoCrawler:
    def __init__(self, start_url: str, max_pages: int = 8):
        self.start_url = start_url
        self.max_pages = max_pages

        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json; charset=utf-8",
            "Origin": "https://www.logic-immo.com",
            "Referer": start_url,
            "Sec-CH-UA": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Linux"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Cookie": "leads_counter_buy=1; datadome=seCHUG0refx3Myq6qIlroeHMebuvRABcyyrPvL30H_TkaJHvGrHsdwvz6H2Upe_eYxZSwFq31KzSnVoP1XXvwGgjbSsOks2WMqB6WReUQr3G7hNal0qG6WiILPnQP1GH; _dd_s=aid=9244bf32-6415-4a7d-9e3a-0f23a9995111&logs=0&expire=1759224655249"
        }


    async def launch_browser(self) -> Browser:
        logging.info("Launching browser...")
        self.playwright = await async_playwright().start()
        browser = await self.playwright.chromium.launch(headless=False)
        return browser

    
    async def extract_urls_from_page(self, page: Page):
        """Extract product URLs from data-base attribute"""
        buttons = await page.query_selector_all('//button[@data-base]')
        urls = []
        for btn in buttons:
            data_base = await btn.get_attribute("data-base")
            if data_base:
                full_url = urllib.parse.unquote(data_base)
                urls.append(full_url)
        logging.info(f"Found {len(urls)} URLs on current page")
        return urls

    
    async def save_to_mongo_and_file(self, url: str):
        if url:
            if not collection.find_one({"url": url}):
                collection.insert_one({"url": url})
            with open(JSON_FILE, "a", encoding="utf-8") as f:
                json.dump({"url": url}, f)
                f.write("\n")
            logging.info(f"Saved URL: {url}")

    # Main Crawl
    async def crawl(self):
        browser = await self.launch_browser()
        context: BrowserContext = await browser.new_context(extra_http_headers=self.headers)
        page: Page = await context.new_page()

        for page_no in range(1, self.max_pages + 1):
            current_url = f"{self.start_url}&page={page_no}"
            try:
                response = await page.goto(current_url, timeout=60000)
                status = response.status if response else "No Response"
                logging.info(f"Accessed {current_url} - Status: {status}")

                urls_on_page = await self.extract_urls_from_page(page)
                for url in urls_on_page:
                    await self.save_to_mongo_and_file(url)

            except Exception as e:
                logging.error(f"Error crawling {current_url}: {e}")
                break

        await browser.close()
        await self.playwright.stop()
        logging.info("Crawling finished.")


if __name__ == "__main__":
    START_URL = "https://www.logic-immo.com/classified-search?distributionTypes=Buy&estateTypes=House,Apartment&locations=AD08FR36790&priceMin=200000&projectTypes=Resale&m=homepage_relaunch_my_last_search_classified_search_result"

    crawler = LogicImmoCrawler(START_URL, max_pages=8)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(crawler.crawl())
    finally:
        loop.close()
