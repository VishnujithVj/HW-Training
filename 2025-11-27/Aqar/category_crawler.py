import logging
import requests
from parsel import Selector
from urllib.parse import urljoin
from pymongo import MongoClient
from settings import BASE_URL, HEADERS, MONGO_DB, MONGO_COLLECTION_CATEGORY


class CategoryCrawler:

    def __init__(self):
        self.client = MongoClient("localhost", 27017)
        self.mongo = self.client[MONGO_DB]
    
    def start(self):
        urls = [BASE_URL]
    
        for url in urls:
            meta = {}
            meta['source_url'] = url   
            logging.info("Loading homepage...")

            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code == 200:
                self.parse_item(response, meta)
            else:
                logging.error(f"Failed to load {url}: {response.status_code}")
    
    def parse_item(self, response, meta):
        """Extract category URLs from homepage"""
        sel = Selector(response.text)
        
        # XPATH
        CATEGORY_XPATH = '//div[contains(@class, "_list__")]/a'
        CATEGORY_NAME_XPATH = 'string(.)'
        CATEGORY_HREF_XPATH = './@href'
        
        # EXTRACT
        categories = sel.xpath(CATEGORY_XPATH)
        
        if not categories:
            logging.warning("No categories found!")
            return False
        
        for cat in categories:
            category_name = cat.xpath(CATEGORY_NAME_XPATH).get().strip()
            category_href = cat.xpath(CATEGORY_HREF_XPATH).get()
            category_url = urljoin(meta['source_url'], category_href).rstrip("/")
            
            # ITEM YIELD
            item = {}
            item['url'] = category_url
            item['name'] = category_name
            
            logging.info(f"CATEGORY → {category_name} → {category_url}")
            
            logging.info(item)
            try:
                self.mongo[MONGO_COLLECTION_CATEGORY].insert_one(item)
            except:
                pass
      
        return True
    
    def close(self):
        self.client.close()
        logging.info("Category crawler finished.")


if __name__ == "__main__":
    crawler = CategoryCrawler()
    crawler.start()
    crawler.close()