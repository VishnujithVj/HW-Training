import logging
import time
from urllib.parse import urljoin
from parsel import Selector
from curl_cffi import requests
from pymongo import MongoClient
from settings import (
    BASE_URL,
    HEADERS,
    MONGO_DB,
    MONGO_COLLECTION_CATEGORY,
    MONGO_COLLECTION_PRODUCT_URL,
)


class Crawler:
    """Crawls product URLs from category pages"""

    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.mongo = self.client[MONGO_DB]
        logging.info("MongoDB connected")


    def start(self):
        categories = self.mongo[MONGO_COLLECTION_CATEGORY].find()
        for cat in categories:
            meta = {
                "category_name": cat["name"],
                "category_url": cat["url"],
                "page": 1,
            }
            self.crawl_category(meta)

    def crawl_category(self, meta):
        page = meta["page"]

        while True:
            url = (
                f"{meta['category_url']}?page={page}"
                if page > 1 else meta["category_url"]
            )

            response = None
            for attempt in range(1, 4): 
                try:
                    response = requests.get(
                        url,
                        headers=HEADERS,
                        impersonate="chrome124",
                        timeout=30,
                    )

                    if response.status_code == 200:
                        break

                    logging.warning(
                        f"HTTP {response.status_code} | Attempt {attempt} | {url}"
                    )

                except Exception as e:
                    logging.warning(
                        f"Request error | Attempt {attempt} | {url} | {e}"
                    )

                time.sleep(attempt * 2)

            if not response or response.status_code != 200:
                logging.error(f"Failed after retries: {url}")
                break

            if not self.parse_item(response, meta):
                break

            page += 1
            meta["page"] = page
            time.sleep(1)

    def parse_item(self, response, meta):
        sel = Selector(response.text)
        products = sel.xpath('//a[@class="od-product-card-image"]')

        if not products:
            return False

        for p in products:
            name = p.xpath('./@title').get()
            href = p.xpath('./@href').get()
            if not name or not href:
                continue

            url = urljoin(BASE_URL, href)

            if self.mongo[MONGO_COLLECTION_PRODUCT_URL].find_one({"url": url}):
                continue

            self.mongo[MONGO_COLLECTION_PRODUCT_URL].insert_one({
                "url": url,
                "product_name": name.strip(),
                "page_no": meta["page"],
                "category_name": meta["category_name"],
                "category_url": meta["category_url"],
            })

            logging.info(f"Saved product URL: {name.strip()}")

        return True

    def stop(self):
        self.client.close()
        logging.info("MongoDB closed")


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.stop()