import asyncio
import logging
from urllib.parse import urljoin
from pymongo import MongoClient
from playwright.async_api import async_playwright
import playwright_stealth 


USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"

HEADERS = {
    "user-agent": USER_AGENT,
    "accept-language": "en-US,en;q=0.9",
}


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)


class MongoHandler:
    def __init__(self, uri="mongodb://localhost:27017", db_name="hm_scrape"):
        client = MongoClient(uri)
        self.db = client[db_name]

    def save(self, collection, data, keys=("url",)):
        query = {k: data[k] for k in keys if k in data}
        self.db[collection].update_one(query, {"$set": data}, upsert=True)


class HMScraper:
    def __init__(self, mongo_uri="mongodb://localhost:27017", db_name="hm_scrape"):
        self.mongo = MongoHandler(mongo_uri, db_name)
        self.browser = None
        self.page = None
        self.base_url = "https://www2.hm.com/en_gb/index.html"

    async def start_browser(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page(extra_http_headers=HEADERS)
      

    async def close_browser(self):
        if self.browser:
            await self.browser.close()

    async def visit(self, url):
        try:
            response = await self.page.goto(url, timeout=60000)
            status = response.status if response else "No response"
            logging.info(f"Visited {url} | Status: {status}")
            await self.page.wait_for_load_state("networkidle")
            return status
        except Exception as e:
            logging.error(f"Failed to visit {url} | Error: {e}")
            return None

    async def extract_urls(self, selector, base_url, filter_product=False):
        elements = await self.page.query_selector_all(selector)
        urls = set()
        for el in elements:
            href = await el.get_attribute("href")
            if href:
                full_url = urljoin(base_url, href)
                if filter_product:
                    if "productpage." in full_url:
                        urls.add(full_url)
                else:
                    urls.add(full_url)
        return urls

    async def scrape(self):
        await self.start_browser()
        await self.visit(self.base_url)
        category_urls = await self.extract_urls("a.e7503a", self.base_url)
        logging.info(f"Found {len(category_urls)} categories")

        for cat_url in category_urls:
            self.mongo.save("categories", {"url": cat_url})
            await self.process_category(cat_url)

        await self.close_browser()

    async def process_category(self, cat_url):
        await self.visit(cat_url)
        subcat_urls = await self.extract_urls("a.a653a6", cat_url)
        logging.info(f"Category {cat_url} -> {len(subcat_urls)} subcategories")

        for sub_url in subcat_urls:
            self.mongo.save("subcategories", {"url": sub_url, "parent": cat_url})
            await self.process_subcategory(sub_url, cat_url)

    async def process_subcategory(self, sub_url, cat_url):
        await self.visit(sub_url)
        product_urls = await self.extract_urls("a.b79f1e", sub_url, filter_product=True)
        logging.info(f"Subcategory {sub_url} -> {len(product_urls)} products")

        for p_url in product_urls:
            self.mongo.save(
                "products",
                {"url": p_url, "subcategory": sub_url, "category": cat_url},
                keys=("url",)
            )


if __name__ == "__main__":
    scraper = HMScraper()
    asyncio.run(scraper.scrape())
