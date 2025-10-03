import asyncio
import logging
from typing import List, Dict

from lxml import html
from pymongo import MongoClient, errors
from playwright.async_api import async_playwright, Page

MONGODB_URI = "mongodb://localhost:27017"
DB_NAME = "snitch_db"
URL_COLLECTION = "product_urls"
DETAILS_COLLECTION = "product_details"
LOG_FILE = "parser.log"

EXTRA_HTTP_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "connection": "keep-alive",
    "origin": "https://www.snitch.com",
    "referer": "https://www.snitch.com/",
    "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
}

BROWSER_HEADLESS = False
PAGE_TIMEOUT = 60000  


class SnitchParser:
    def __init__(self, mongo_uri: str, db_name: str):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
        )
        self.logger = logging.getLogger("SnitchParser")
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.url_collection = self.db[URL_COLLECTION]
        self.details_collection = self.db[DETAILS_COLLECTION]
        try:
            self.details_collection.create_index("url", unique=True)
        except Exception as e:
            self.logger.warning(f"Could not create index: {e}")

    async def fetch_page_content(self, page: Page, url: str) -> str:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
            try:
                await page.wait_for_load_state("networkidle", timeout=15000) 
            except Exception:
                self.logger.warning(f"Network idle timeout for {url}, continuing...")
            content = await page.content()
            return content
        except Exception as e:
            self.logger.error(f"Error loading {url}: {e}")
            return ""


    def parse_product_details(self, html_text: str, product_type: str) -> Dict:
        tree = html.fromstring(html_text)

        # Product name and price
        name_xpath = '//div[contains(@class,"flex justify-between items-center mb-4")]/h1/text()'
        price_xpath = '//div[contains(@class,"flex justify-between items-center mb-4")]/div/p/text()'
        product_name = tree.xpath(name_xpath)
        product_price = tree.xpath(price_xpath)
        product_name = product_name[0].strip() if product_name else ""
        product_price = product_price[0].strip() if product_price else ""

        # Rating
        rating_xpath = '//div[contains(@class,"flex items-center gap-0.5 bg-black")]/span[1]/text()'
        rating = tree.xpath(rating_xpath)
        rating = rating[0].strip() if rating else ""

        # Colors
        colors_xpath = '//div[h1[contains(text(),"COLORS")]]//img/@src'
        colors = tree.xpath(colors_xpath)

        # Sizes
        sizes_xpath = '//div[contains(@class,"flex flex-row justify-center flex-wrap")]/span/div/span/text()'
        sizes = [s.strip() for s in tree.xpath(sizes_xpath)]

        # Collapsible details: description, size & fit, wash care, specification, SKU
        base_xpath = '//div[contains(@class,"Collapsible__contentInner")]//div[contains(@class,"border-b")]'
        collapsible = tree.xpath(base_xpath)
        description = size_fit = wash_care = specification = sku = ""
        if collapsible:
            desc_xpath = './/p[@class="py-2" and contains(@style,"Light")]/text()'
            description_texts = collapsible[0].xpath(desc_xpath)
            if description_texts:
                description = description_texts[0].strip()

            size_fit_xpath = './/div[p[contains(text(),"Size & Fit")]]/p[not(contains(text(),"Size & Fit"))]/text()'
            size_fit_texts = collapsible[0].xpath(size_fit_xpath)
            size_fit = " ".join([t.strip() for t in size_fit_texts])

            wash_xpath = './/div[p[contains(text(),"Wash care")]]/p[not(contains(text(),"Wash care"))]/text()'
            wash_care_texts = collapsible[0].xpath(wash_xpath)
            wash_care = " ".join([t.strip() for t in wash_care_texts])

            spec_xpath = './/div[p[contains(text(),"Specification")]]/p/text()'
            spec_texts = collapsible[0].xpath(spec_xpath)
            specification = ", ".join([t.strip() for t in spec_texts])

            sku_xpath = './/span[contains(text(),"SKU")]/text()'
            sku_texts = collapsible[0].xpath(sku_xpath)
            sku = sku_texts[0].replace("SKU:", "").strip() if sku_texts else ""

        return {
            "product_type": product_type,
            "product_name": product_name,
            "price": product_price,
            "rating": rating,
            "colors": colors,
            "sizes": sizes,
            "description": description,
            "size_fit": size_fit,
            "wash_care": wash_care,
            "specification": specification,
            "sku": sku,
        }

    def save_to_db(self, url: str, product_type: str, details: Dict):
        doc = {"url": url, "product_type": product_type, **details}
        try:
            self.details_collection.insert_one(doc)
            self.logger.info(f"Inserted: {url}")
        except errors.DuplicateKeyError:
            self.logger.debug(f"Duplicate skipped: {url}")
        except Exception as e:
            self.logger.error(f"Error saving {url}: {e}")

    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=BROWSER_HEADLESS)
            context = await browser.new_context(extra_http_headers=EXTRA_HTTP_HEADERS)
            page = await context.new_page()


            urls_cursor = self.url_collection.find({}, {"url": 1, "source": 1})
            for doc in urls_cursor: 
                url = doc.get("url")
                product_type = doc.get("source", "")
                if not url:
                    continue
                html_text = await self.fetch_page_content(page, url)
                if html_text:
                    details = self.parse_product_details(html_text, product_type)
                    self.save_to_db(url, product_type, details)

            await browser.close()
            self.logger.info("Parsing finished.")


async def main():
    parser = SnitchParser(MONGODB_URI, DB_NAME)
    await parser.run()


if __name__ == "__main__":
    asyncio.run(main())
