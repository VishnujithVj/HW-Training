import logging
from parsel import Selector
from urllib.parse import urljoin
from curl_cffi import requests
from mongoengine import connect
from settings import HEADERS, MONGO_DB,MONGO_HOST
from items import PropertyCategoryItem


class Crawler:
    """Crawling Subcategory URLs"""
    def __init__(self):
        self.mongo = connect(alias="default",db=MONGO_DB,host=MONGO_HOST)
        logging.info("MongoDB connected")

    def start(self):
        START_URL = "https://haraj.com.sa/tags/%D8%AD%D8%B1%D8%A7%D8%AC%20%D8%A7%D9%84%D8%B9%D9%82%D8%A7%D8%B1"
        logging.info(f"Requesting: {START_URL}")

        try:
            res = requests.get(START_URL, headers=HEADERS, timeout=30)
        except Exception as e:
            logging.error(f"Request failed: {e}")
            return

        if res.status_code != 200:
            logging.error(f"Failed: {res.status_code}")
            return

        meta = {"category": "Haraj Real Estate Main Category"}
        self.parse_item(res.text, meta)

    def parse_item(self, html):
        sel = Selector(html)
        subcats = sel.xpath('//div[contains(@class,"bg-background") and contains(@class,"relative")]//a/@href').getall()

        if not subcats:
            logging.warning("No subcategory links found")
            return False

        saved = 0
        seen = set()
        for link in subcats:
            full_url = urljoin("https://haraj.com.sa", link)
            if full_url in seen:
                continue
        seen.add(full_url)
        try:
            PropertyCategoryItem(url=full_url).save()
            saved += 1
            logging.info(f"Saved: {full_url}")
        except Exception as e:
            logging.error(f"DB Insert failed: {e}")


        logging.info(f"Total subcategories extracted: {saved}")
        return True


    def close(self):
        self.mongo.close()

if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()