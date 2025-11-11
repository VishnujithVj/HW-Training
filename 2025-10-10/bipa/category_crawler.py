import logging
import requests
from mongoengine import connect
from items import CategoryUrlItem
from settings import HEADERS, MONGO_DB


class CategoryCrawler:
    """Crawling Category URLs"""

    def __init__(self):
        """Initialize connections"""
        self.url = "https://www.bipa.at/resolve-url/navigation"
        self.mongo = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        logging.info("MongoDB connected successfully")

    def start(self):
        """Requesting Start url"""
        logging.info("Starting category crawler")

        response = requests.get(self.url, headers=HEADERS)
        if response.status_code == 200:
            categories_data = response.json()
            self.parse_item(categories_data)
        else:
            logging.error(f"Failed to fetch categories: {response.status_code}")
            
      

    def parse_item(self, categories, parent_url="", level="main"):
        """Parse categories recursively"""
        for category in categories:
            name = category.get("name")
            url = category.get("link")

            if name and url:
                """ Check if category already exists to avoid duplicates """
                existing_category = CategoryUrlItem.objects(url=url).first()
                if not existing_category:
                    """ ITEM YIELD """
                    item = CategoryUrlItem(
                        url=url,
                        name=name,
                        parent_url=parent_url,
                        level=level
                    )
                    item.save()
                    logging.info(f"Saved category: {name} (Level: {level})")
                else:
                    logging.info(f"Category already exists: {name}")

            """ Recursive parsing for sub categories with proper level tracking """
            sub_categories = category.get("childCategories", [])
            if sub_categories:
                next_level = "sub" if level == "main" else f"sub{level}"
                self.parse_item(sub_categories, url, next_level)

    def close(self):
        self.mongo.close()
        logging.info("Category crawler completed")


if __name__ == "__main__":
    crawler = CategoryCrawler()
    crawler.start()
    crawler.close()