import logging
import time
from itertools import islice
from curl_cffi import requests
from pymongo import MongoClient
from settings import (
    GROUP_ATTRIBUTES_URL, GROUP_ATTRIBUTES_PARAMS, HEADERS, BASE_URL,
    MONGO_URI, MONGO_DB, MONGO_COLLECTION_GROUP_IDS,
    MONGO_COLLECTION_PRODUCT_DETAILS, MONGO_COLLECTION_PRODUCT_URLS,
    BATCH_SIZE, REQUEST_DELAY
)


class JabraProductDetailsCrawler:
    """Crawling Product Details from Jabra API"""

    def __init__(self):
        """Initialize MongoDB connection"""
        self.mongo = MongoClient(MONGO_URI)
        self.db = self.mongo[MONGO_DB]

        self.group_col = self.db[MONGO_COLLECTION_GROUP_IDS]
        self.product_col = self.db[MONGO_COLLECTION_PRODUCT_DETAILS]
        self.product_url_col = self.db[MONGO_COLLECTION_PRODUCT_URLS]
        
        logging.info("Product Details Crawler initialized")

    def start(self):
        """Start crawling product details"""
        
        # Fetch all group IDs
        group_ids = [
            str(g["c_pimGroupId"])
            for g in self.group_col.find(
                {"c_pimGroupId": {"$exists": True}},
                {"c_pimGroupId": 1, "_id": 0},
            )
        ]

        logging.info(f"Total group IDs to process: {len(group_ids)}")

        # Process in batches
        for batch in self.chunk(group_ids, BATCH_SIZE):
            self.fetch_batch(batch)
            time.sleep(REQUEST_DELAY)

    def fetch_batch(self, batch):
        """Fetch batch of product details"""
        
        ids = "|".join(batch)
        params = {**GROUP_ATTRIBUTES_PARAMS, "ids": ids}

        logging.info(f"Fetching group batch: {ids}")

        try:
            response = requests.get(
                GROUP_ATTRIBUTES_URL,
                headers=HEADERS,
                params=params,
                impersonate="chrome",
                timeout=30,
            )

            if response.status_code != 200:
                logging.error(f"Failed with status: {response.status_code}")
                return

            data = response.json()
            
            for item in data:
                self.parse_item(item)
                
        except Exception as e:
            logging.error(f"Request failed for batch {ids}: {e}")

    def parse_item(self, item):
        """Parse and save product details"""
        
        doc = {
            "groupId": item.get("groupId"),
            "familyId": item.get("familyId"),
            "familyName": item.get("familyName"),
            "productId": item.get("productId"),
            "productName": item.get("productName"),
            "sku": item.get("sku"),
            "segmentType": item.get("segmentType"),
            "warranty": item.get("warranty"),
            "pageUrl": item.get("pageUrl"),
            "supportPageUrl": item.get("supportPageUrl"),
            "model": item.get("model"),
            "groupState": item.get("groupState"),
            "hasBluetoothPairingGuide": item.get("hasBluetoothPairingGuide"),
            "attributes": item.get("attributes"),
            "images": item.get("images"),
        }

        if doc["sku"] and doc["groupId"]:
            try:
                # Save full product details
                self.product_col.insert_one(doc)
                logging.info(f"Saved product details for SKU: {doc['sku']}")
                
                # Save product URL separately
                page_url = doc.get("pageUrl")
                sku = doc.get("sku")
                product_name = doc.get("productName")

                if page_url and sku:
                    product_url = f"{BASE_URL.rstrip('/')}{page_url}/buy?sku={sku}"

                    self.product_url_col.insert_one({
                        "product_name": product_name,
                        "product_url": product_url,
                        "sku": sku,
                    })
                    logging.info(f"Saved product URL for SKU: {sku}")
                    
            except Exception as e:
                logging.error(f"Failed to save product {doc['sku']}: {e}")

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
        logging.info("Product Details Crawler finished & MongoDB closed")


if __name__ == "__main__":
    crawler = JabraProductDetailsCrawler()
    crawler.start()
    crawler.stop()