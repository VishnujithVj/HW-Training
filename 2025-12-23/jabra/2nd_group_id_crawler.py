import logging
import time
from itertools import islice
from curl_cffi import requests
from pymongo import MongoClient
from settings import (
    PRODUCTS_BATCH_URL, PRODUCTS_BATCH_PARAMS, HEADERS,
    MONGO_URI, MONGO_DB, MONGO_COLLECTION_PRODUCT_IDS,
    MONGO_COLLECTION_GROUP_IDS, BATCH_SIZE, REQUEST_DELAY
)


class JabraGroupIdCrawler:
    """Crawling Group IDs and Pricing from Jabra API"""

    def __init__(self):
        """Initialize MongoDB connection"""
        self.mongo = MongoClient(MONGO_URI)
        self.db = self.mongo[MONGO_DB]
        
        self.product_col = self.db[MONGO_COLLECTION_PRODUCT_IDS]
        self.group_col = self.db[MONGO_COLLECTION_GROUP_IDS]
        
        logging.info("Group ID Crawler initialized")

    def start(self):
        """Start crawling group IDs"""
        
        """Fetch all product IDs"""
        product_ids = [
            p["product_id"]
            for p in self.product_col.find(
                {"product_id": {"$exists": True}},
                {"product_id": 1, "_id": 0},
            )
        ]

        logging.info(f"Total product IDs to process: {len(product_ids)}")

        """Process in batches"""
        for batch in self.chunk(product_ids, BATCH_SIZE):
            self.fetch_batch(batch)
            time.sleep(REQUEST_DELAY)

    def fetch_batch(self, batch):
        """Fetch batch of products"""
        
        sku_str = ",".join(batch)
        url = f"{PRODUCTS_BATCH_URL}/({sku_str})"

        logging.info(f"Fetching batch: {sku_str}")

        try:
            response = requests.get(
                url,
                headers=HEADERS,
                params=PRODUCTS_BATCH_PARAMS,
                impersonate="chrome",
                timeout=30,
            )

            """Handle 401 error"""
            if response.status_code == 401:
                logging.warning("401 received retrying without impersonation")
                response = requests.get(
                    url,
                    headers=HEADERS,
                    params=PRODUCTS_BATCH_PARAMS,
                    timeout=30,
                )

            if response.status_code != 200:
                logging.error(f"Failed with status: {response.status_code}")
                return

            data = response.json().get("data", [])
            
            for item in data:
                self.parse_item(item)
                
        except Exception as e:
            logging.error(f"Request failed for batch {sku_str}: {e}")

    def parse_item(self, item):
        """Parse and save group item"""
        
        doc = {
            "sku": item.get("c_sku"),
            "c_discountedPrice": item.get("c_discountedPrice"),
            "c_listedPrice": item.get("c_listedPrice"),
            "c_discountPercentage": item.get("c_discountPercentage"),
            "c_pimFamilyId": item.get("c_pimFamilyId"),
            "c_pimGroupId": item.get("c_pimGroupId"),
            "c_portfolio": item.get("c_portfolio"),
            "c_productId": item.get("c_productId"),
            "currency": item.get("currency"),
        }

        if doc["sku"] and doc["c_pimGroupId"]:
            try:
                self.group_col.insert_one(doc)
                logging.info(f"Saved group_id for SKU: {doc['sku']}")
            except Exception as e:
                logging.error(f"Failed to save group_id {doc['sku']}: {e}")

    def chunk(self, iterable, size):
        """Split iterable into chunks"""
        it = iter(iterable)
        while True:
            batch = list(islice(it, size))
            if not batch:
                break
            yield batch

    def stop(self):
        """Close MongoDB connection"""
        self.mongo.close()
        logging.info("Group ID Crawler finished & MongoDB closed")


if __name__ == "__main__":
    crawler = JabraGroupIdCrawler()
    crawler.start()
    crawler.stop()