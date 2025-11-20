import logging
import re
import time
from curl_cffi import requests
from mongoengine import connect
from items import ProductCategoryUrlItem, ProductUrlItem, ProductFailedItem
from settings import BASE_URL, HEADERS, MONGO_DB, MONGO_HOST

ABS_URL_RE = r'\\"absolute_url\\"\s*:\s*\\"([^"]+)\\"'
NEXT_RE = r'<a[^>]+href="([^"]+)"[^>]*>\s*<span class="me-4 hidden lg:inline-block">Next'


class ProductCrawler:
    def __init__(self):
        """Initialize MongoDB connection"""
        self.mongo = connect(db=MONGO_DB, host=MONGO_HOST)
        logging.info("MongoDB connected")

    def start(self):
        """Iterate over category URLs and crawl products"""
        metas = [{"url": item.url} for item in ProductCategoryUrlItem.objects()]

        for meta in metas:
            start_url = meta.get("url")
            logging.info(f"Crawling category: {start_url}")

            page_url = start_url
            while True:
                try:
                    r = requests.get(page_url, headers=HEADERS, impersonate="chrome120", timeout=25)
                    if r.status_code != 200:
                        logging.error(f"FAILED: {page_url} (fetch_failed)")
                        ProductFailedItem(url=page_url, reason="fetch_failed").save()
                        break

                    html = r.text
                    has_next, next_href = self.parse_item(html)

                    if not has_next:
                        break

                    page_url = BASE_URL.rstrip("/") + next_href
                    time.sleep(1)

                except Exception as e:
                    logging.error(f"Request error: {e}")
                    ProductFailedItem(url=page_url, reason="request_error").save()
                    break

        logging.info("Product crawling completed")

    def parse_item(self, html):
        """Extract product URLs and detect pagination"""
        matches = re.findall(ABS_URL_RE, html)
        urls = [BASE_URL.rstrip("/") + u for u in matches]

        for u in urls:
            self.save(u)

        nxt = re.search(NEXT_RE, html)
        if not nxt:
            return False, None

        next_href = nxt.group(1).replace("&amp;", "&")
        return True, next_href

    def save(self, url):
        """Save product URL to MongoDB"""
        ProductUrlItem(url=url).save()
        logging.info(f"Saved product URL: {url}")

    def close(self):
        logging.info("MongoDB connection closed")

if __name__ == "__main__":
    crawler = ProductCrawler()
    crawler.start()
    crawler.close()
