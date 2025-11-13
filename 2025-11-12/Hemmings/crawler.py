import time
import logging
from urllib.parse import urljoin
from parsel import Selector
from curl_cffi import requests
from mongoengine import connect
from items import ProductUrlItem
from settings import BASE_URL, HEADERS, MONGO_DB


class Crawler:
    """Crawl all product URLs from category pages"""

    def __init__(self):
        self.mongo = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        logging.info(" MongoDB connected")

    def start(self):
        page = 1
        next_url = BASE_URL

        while next_url:
            logging.info(f" Fetching page {page}: {next_url}")
       
            response = requests.get(next_url, headers=HEADERS, impersonate="chrome120", timeout=30)
            if response.status_code != 200:
                logging.warning(f" Request failed with {response.status_code}")
                break

            sel = Selector(response.text)
            product_links = sel.xpath('//div[contains(@class,"shadow-md") and contains(@class,"overflow-hidden")]/a[@href]/@href').getall()

            if not product_links:
                logging.info("No product URLs found on this page.")
                break

            count = 0
            for link in product_links:
                full_url = urljoin(BASE_URL, link)
                if not ProductUrlItem.objects(url=full_url):
                    ProductUrlItem(url=full_url).save()
                    count += 1

            logging.info(f" Saved {count} new URLs from page {page}")

            """Pagination handling"""
            next_page = sel.xpath('//a[@rel="next"]/@href').get()
            if next_page:
                next_url = urljoin(BASE_URL, next_page)
                page += 1
                time.sleep(2)
            else:
                logging.info(" No more pages found.")
                break

    def close(self):
        self.mongo.close()
        logging.info(" MongoDB connection closed")


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()
