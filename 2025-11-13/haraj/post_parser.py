import logging
import re
from curl_cffi import requests
from mongoengine import connect
from parsel import Selector
from settings import HEADERS, MONGO_DB, MONGO_HOST
from items import PropertyPostItem, PropertyPostUrlItem


class Parser:
    """Extract only DealApp ID + URLs"""
    DEALAPP_RE = re.compile(r"dealapp\.sa/.*/ad-details/(\d+)")

    def __init__(self):
        self.mongo = connect(alias="default", db=MONGO_DB, host=MONGO_HOST)
        logging.info("MongoDB connected")

    def start(self):
        """Load post URLs from DB and parse"""
        posts = PropertyPostUrlItem.objects()
        logging.info(f"Found {posts.count()} posts to parse")

        for post in posts:
            url = post.url
            logging.info(f"Requesting: {url}")
            try:
                response = requests.get(url, headers=HEADERS, impersonate="chrome120", timeout=20)
            except Exception as e:
                logging.error(f"Request failed: {e}")
                continue

            if response:
                self.parse_item(url, response)
            else:
                logging.warning(f"Failed getting URL: {url}")

    def parse_item(self, url, response):
        """Extract DealApp ad ID and build ad URL"""
        matches = self.DEALAPP_RE.findall(response.text)
        ad_id = matches[0] if matches else None

        if not ad_id:
            logging.warning(f"No DealApp ID found - {url}")
            return False

        dealapp_url = f"https://dealapp.sa/ar/ad-details/{ad_id}"

        item = PropertyPostItem(
            url=url,
            dealapp_ad_id=str(ad_id),
            dealapp_api_url=dealapp_url
        )

        item.save()
        logging.info(f"Saved - dealapp_id={ad_id}")

        return True

    def close(self):
        self.mongo.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = Parser()
    parser.start()
    parser.close()
