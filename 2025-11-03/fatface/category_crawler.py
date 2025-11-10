import logging
from urllib.parse import urljoin
from curl_cffi import requests
from mongoengine import connect
from items import CategoryUrlItem
from settings import BASE_URL, API_URL, HEADERS, MONGO_DB

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

class CategoryCrawler:
    """Crawler to fetch and store category and subcategory URLs"""

    def __init__(self):
        self.mongo = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        logging.info("MongoDB connected")

    def start(self):
        """Fetch data from API"""
        response = requests.get(API_URL, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            logging.error(f"API returned {response.status_code}")
            return

        items = response.json().get("items", [])
        categories = self.parse_categories(items)
        self.save(categories)
        logging.info(f"Total saved: {len(categories)}")

    def parse_categories(self, items, parent_title="", parent_url=""):
        """Recursively extract category and subcategory URLs"""
        results = []

        for item in items:
            title = item.get("title")
            target = item.get("target")
            if not title or not target:
                continue

            full_url = urljoin(BASE_URL, target.strip())

            if parent_title:
                results.append({
                    "category_title": parent_title,
                    "subcategory_title": title,
                    "category_url": parent_url,
                    "subcategory_url": full_url,
                })

            child_items = item.get("items", [])
            if child_items:
                results.extend(self.parse_categories(child_items, parent_title or title, parent_url or full_url))
        return results
    
    def save(self, data):
        """Save extracted category records to MongoDB"""
        for record in data:
            try:
                CategoryUrlItem(**record).save()
                logging.info(f"Saved: {record['subcategory_url']}")
            except Exception as e:
                logging.error(f"Error saving record: {e}")

    def close(self):
        self.mongo.close()
        logging.info("MongoDB connection closed")

if __name__ == "__main__":
    crawler = CategoryCrawler()
    crawler.start()
    crawler.close()
