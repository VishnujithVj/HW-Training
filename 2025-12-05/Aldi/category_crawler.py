import logging
import requests
from pymongo import MongoClient
from settings import (CATEGORY_API,HEADERS,MONGO_URI,MONGO_DB,MONGO_COLLECTION_CATEGORY,)

logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s:%(message)s",datefmt="%Y-%m-%d %H:%M:%S",)


class CategoryCrawler:
    """Crawling Product Categories from Aldi Category API"""

    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.mongo = self.client[MONGO_DB]
        logging.info("MongoDB connection established successfully")

    def start(self):
        """Fetch category API"""

        logging.info(f"Requesting: {CATEGORY_API}")
        response = requests.get(CATEGORY_API, headers=HEADERS, timeout=20)
        response.raise_for_status()

        data = response.json().get("data", [])

        if not data:
            logging.warning("No categories found in API response")
            return False

        logging.info(f"Found {len(data)} top-level categories")

        """Collect ALL categories (removed index-based logic)"""
        for category in data:
            self.parse_item(category)

        logging.info("Category crawling completed successfully")
        return True


    def parse_item(self, category_data):
        """Parse and store a single category with its subcategories"""

        category_name = category_data.get("name", "")
        category_key = category_data.get("key", "")
        category_slug = category_data.get("urlSlugText", "")

        if not category_name or not category_key:
            logging.warning("Skipping category with missing name or key")
            return

        subcategories = []
        for sub in category_data.get("children", []):
            subcategories.append({
                "name": sub.get("name"),
                "key": sub.get("key"),
                "slug": sub.get("urlSlugText"),
            })

        doc = {
            "category_name": category_name,
            "category_key": category_key,
            "category_slug": category_slug,
            "subcategories": subcategories,
        }

        self.mongo[MONGO_COLLECTION_CATEGORY].insert_one(doc)
        logging.info(f"Inserted category: {category_name} with {len(subcategories)} subcategories")

    def close(self):
        self.client.close()
        logging.info("CategoryCrawler stopped - MongoDB connection closed")


if __name__ == "__main__":
    crawler = CategoryCrawler()
    crawler.start()
    crawler.close()
