import logging
import random
import time
from urllib.parse import urljoin
from parsel import Selector
from curl_cffi import requests
from mongoengine import connect
from items import ProductUrlItem, ProductFailedItem
from settings import HEADERS, BASE_URL, MONGO_DB


class Crawler:
    """Crawling Urls"""

    def __init__(self):
        self.mongo = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        logging.info("MongoDB connected successfully")

    def fetch(self, url):
        response = requests.get(url, headers=HEADERS, impersonate="chrome120", timeout=30)
        return response.text if response.status_code == 200 else ""

    def start(self):
        """Requesting Start url"""
        logging.info(" Starting REWE crawler ")

        home_html = self.fetch(BASE_URL)
        categories = Selector(text=home_html).xpath('//nav//a[contains(@href,"/c/")]/@href').extract()
        logging.info(f"Found {len(categories)} categories")

        for cat in categories[5:]:
            meta = {'category_url': urljoin(BASE_URL, cat)}
            logging.info(f"Category: {meta['category_url']}")
            self.parse_category(meta)


    def parse_category(self, meta):
        """Parse category page"""
        cat_html = self.fetch(meta['category_url'])
        subcats = Selector(text=cat_html).xpath('//a[contains(@class,"plr-CategoryNavigationTile__Item")]/@href').extract() or [meta['category_url']]
        
        for sub in subcats:
            meta['subcategory_url'] = urljoin(BASE_URL, sub)
            logging.info(f"  Subcategory: {meta['subcategory_url']}")
            
            page = meta.get("page", 1)
            while True:
                is_next = self.parse_subcategory(meta)
                if not is_next:
                    logging.info("Pagination completed")
                    break
                
                page += 1
                meta["page"] = page

    def parse_subcategory(self, meta):
        """Parse subcategory page with products"""
        html = self.fetch(meta['subcategory_url'])
        products = Selector(text=html).xpath('//a[contains(@class,"a-pt__product-tile__link")]/@href').extract()
        
        if products:
            logging.info(f"    Found {len(products)} products")
            for product_url in products:
                item = {}
                item['url'] = urljoin(BASE_URL, product_url)
                item['category_url'] = meta.get('category_url')
                item['subcategory_url'] = meta.get('subcategory_url')
                
                try:
                    # save
                    ProductUrlItem(**item).save()
                    logging.info(f"Saved: {item['url']}")

                except Exception as e:
                    logging.error(f"Save error for {item['url']}: {e}")

            # Next page
            next_page = Selector(text=html).xpath('//a[contains(@class,"plr-pagination-button-right")]/@href').extract_first()
            if next_page:
                meta['subcategory_url'] = urljoin(BASE_URL, next_page)
                time.sleep(random.uniform(1, 2))
                return True
            return False
        return False

    def failed(self, url):
        ProductFailedItem(url=url).save()
        logging.warning(f"Failed URL saved: {url}")

    def close(self):
        """Close function for all module object closing"""
        logging.info("Crawler finished")

if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()
 