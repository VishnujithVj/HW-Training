import logging
import requests
from parsel import Selector
from urllib.parse import urljoin
from pymongo import MongoClient
from settings import BASE_URL, HEADERS, MONGO_DB, MONGO_COLLECTION_URL, MONGO_COLLECTION_PAGINATION, MONGO_COLLECTION_URL_FAILED, MONGO_COLLECTION_CATEGORY


class ProductCrawler:

    def __init__(self):
        self.client = MongoClient("localhost", 27017)
        self.mongo = self.client[MONGO_DB]

    def start(self):
        """Requesting Start url"""
        categories = list(self.mongo[MONGO_COLLECTION_CATEGORY].find({}, {"url": 1}))

        if not categories:
            logging.warning("No stored categories found!")
            return

        urls = [cat["url"] for cat in categories]

        for url in urls:
            meta = {}
            meta["category"] = url
            page = meta.get("page", 1)

            logging.info(f"PROCESSING CATEGORY → {url}")

            page_url = f"{url}/{page}"

            while True:
                logging.info(f"Page {page} → {page_url}")
                response = requests.get(page_url, headers=HEADERS, timeout=15)

                if response.status_code == 200:

                    try:
                        self.mongo[MONGO_COLLECTION_PAGINATION].insert_one({"url": page_url})
                    except:
                        pass

                    is_next = self.parse_item(response, meta)

                    if not is_next:
                        logging.info("Pagination completed")
                        break

                    page += 1
                    page_url = f"{url}/{page}"
                    meta["page"] = page

                else:
                    logging.error(f"Request failed → {page_url} (Status: {response.status_code})")

                    try:
                        self.mongo[MONGO_COLLECTION_URL_FAILED].insert_one(
                            {"url": page_url}
                        )
                    except:
                        pass

                    break

    def parse_item(self, response, meta):
        """Extract product URLs from listing page"""
        sel = Selector(response.text)

        PRODUCT_XPATH = '//div[contains(@class, "_list__")]/div/a/@href'

        product_urls = sel.xpath(PRODUCT_XPATH).getall()

        if not product_urls:
            logging.info("No products found - pagination finished.")
            return False

        for prod_href in product_urls:
            full_url = urljoin(BASE_URL, prod_href)

            """ITEM YIELD"""
            item = {}
            item['url'] = full_url
            item['category'] = meta.get('category')

            logging.info(f"LISTING → {full_url}")
            try:
                self.mongo[MONGO_COLLECTION_URL].insert_one(item)
            except:
                pass

        return True

    def close(self):
        self.client.close()
        logging.info("Product crawler finished.")


if __name__ == "__main__":
    crawler = ProductCrawler()
    crawler.start()
    crawler.close()
