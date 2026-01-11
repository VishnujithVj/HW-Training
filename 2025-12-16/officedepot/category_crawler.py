import logging
from urllib.parse import urljoin
from parsel import Selector
from curl_cffi import requests
from pymongo import MongoClient
from settings import (
    BASE_URL,
    HEADERS,
    MONGO_DB,
    MONGO_COLLECTION_CATEGORY,
)


class Crawler:
    """Crawls category URLs from Office Depot homepage"""

    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.mongo = self.client[MONGO_DB]
        logging.info("MongoDB connected")

    def start(self):
        response = requests.get(
            BASE_URL,
            headers=HEADERS,
            impersonate="chrome124",
            timeout=30,
        )

        if response.status_code != 200:
            logging.error(f"Homepage failed: {response.status_code}")
            return

        self.parse_item(response)

    def parse_item(self, response):
        sel = Selector(response.text)
        categories = sel.xpath('//a[@class="od-menu-link"]')

        if not categories:
            logging.warning("No categories found")
            return


        for cat in categories:
            name = cat.xpath("normalize-space(@title)").get()
            if not name:
                name = cat.xpath("normalize-space(.)").get()

            href = cat.xpath("./@href").get()

            if not name or not href:
                continue

            self.mongo[MONGO_COLLECTION_CATEGORY].insert_one({
                "name": name,
                "url": urljoin(BASE_URL, href),
            })

            logging.info(f"Saved category: {name}")

    def stop(self):
        self.client.close()
        logging.info("MongoDB closed")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    crawler = Crawler()
    crawler.start()
    crawler.stop()
