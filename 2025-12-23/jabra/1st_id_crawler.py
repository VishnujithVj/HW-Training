import logging
import time
from curl_cffi import requests
from pymongo import MongoClient
from settings import (
    PRODUCT_SEARCH_URL, PRODUCT_SEARCH_PARAMS, HEADERS,
    MONGO_URI, MONGO_DB, MONGO_COLLECTION_PRODUCT_IDS
)


class JabraProductIdCrawler:
    """Crawling Product IDs from Jabra API"""

    def __init__(self):
        """Initialize MongoDB connection"""
        self.mongo = MongoClient(MONGO_URI)
        self.db = self.mongo[MONGO_DB]
        self.collection = self.db[MONGO_COLLECTION_PRODUCT_IDS]
        
        self.start_index = 0
        self.total = None
        
        logging.info("Product ID Crawler initialized")

    def start(self):
        """Start crawling product IDs"""
        
        while True:
            params = PRODUCT_SEARCH_PARAMS.copy()
            params["start"] = self.start_index
            
            logging.info(f"Fetching products | start={self.start_index}")

            try:
                response = requests.get(
                    PRODUCT_SEARCH_URL,
                    headers=HEADERS,
                    params=params,
                    impersonate="chrome",
                    timeout=30,
                )

                if response.status_code != 200:
                    logging.error(f"Failed with status: {response.status_code}")
                    break

                data = response.json()

                if self.total is None:
                    self.total = data.get("total", 0)
                    logging.info(f"Total products: {self.total}")

                hits = data.get("hits", [])
                if not hits:
                    logging.info("No more products found")
                    break

                for hit in hits:
                    self.parse_item(hit)

                self.start_index += params["count"]
                
                if self.start_index >= self.total:
                    logging.info("All products fetched")
                    break

                time.sleep(0.25)
                
            except Exception as e:
                logging.error(f"Request failed: {e}")
                break

    def parse_item(self, hit):
        """Parse and save product item"""
        
        product_id = hit.get("product_id")
        if not product_id:
            return

        """Skip if already exists"""
        if self.collection.find_one({"product_id": product_id}):
            logging.info(f"Product {product_id} already exists, skipping")
            return

        item = {
            "product_id": product_id,
            "product_name": hit.get("product_name"),
            "price": hit.get("price"),
            "price_per_unit": hit.get("price_per_unit"),
            "currency": hit.get("currency"),
        }

        try:
            self.collection.insert_one(item)
            logging.info(f"Saved product_id: {product_id}")
        except Exception as e:
            logging.error(f"Failed to save {product_id}: {e}")

    def stop(self):
        """Close MongoDB connection"""
        self.mongo.close()
        logging.info("Product ID Crawler finished & MongoDB closed")


if __name__ == "__main__":
    crawler = JabraProductIdCrawler()
    crawler.start()
    crawler.stop()