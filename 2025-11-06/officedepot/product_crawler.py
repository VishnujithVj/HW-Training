import logging
import time
from urllib.parse import urljoin
from parsel import Selector
from curl_cffi import requests
from mongoengine import connect
from items import ProductUrlItem, CategoryUrlItem
from settings import BASE_URL, HEADERS, MONGO_DB


class Crawler:
    """Crawling product URLs from category pages and save."""

    def __init__(self):
        self.mongo = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        logging.info("MongoDB connected successfully.")

    def start(self):
        categories = CategoryUrlItem.objects.all()
        if not categories:
            logging.warning("No categories found in MongoDB.")
            return
        for category in categories:
            meta = { "category_name": category.name, "category_url": category.url, "page": 1, }
            
            logging.info(f"Starting crawl for category: {category.name}")
            self.crawl_category(meta)

    def crawl_category(self, meta):
        """Handle pagination and call parser for each category page."""
        page = meta.get("page", 1)
        total = 0

        while True:
            url = f"{meta['category_url']}?page={page}" if page > 1 else meta["category_url"]

            response = requests.get(url, headers=HEADERS, impersonate="chrome124", timeout=30)
            if response.status_code != 200:
                logging.warning(f"HTTP {response.status_code} at {url}")
                break
            has_next = self.parse_item(response, meta)
            if not has_next:
                logging.info(f"No more pages for category: {meta['category_name']}")
                break

            page += 1
            meta["page"] = page
            total += 1
            time.sleep(1)
            
        logging.info(f"Completed: {meta['category_name']} (Total pages crawled: {total})")

    def parse_item(self, response, meta):
        """Parse products from a single category page and save them."""
        sel = Selector(response.text)
        product_elements = sel.xpath('//a[@class="od-product-card-image"]')
        if not product_elements:
            return False

        saved_count = 0
        for product in product_elements:
            name = product.xpath('./@title').get()
            href = product.xpath('./@href').get()
            if not (name and href):
                continue
            full_url = urljoin(BASE_URL, href)
            """Skip duplicates"""
            if ProductUrlItem.objects(url=full_url):
                continue
            ProductUrlItem(
                url=full_url,
                product_name=name.strip(),
                page_no=meta.get("page"),
                category_url=meta["category_url"],
                category_name=meta["category_name"],
            ).save()

            saved_count += 1
            logging.info(f"Saved: {name.strip()}")

        logging.info(f"Page {meta.get('page')} → {saved_count} new products saved.")
        return bool(saved_count)

    def close(self):
        self.mongo.close()
        logging.info("MongoDB connection closed.")

if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    crawler = Crawler()
    crawler.start()
    crawler.close()
