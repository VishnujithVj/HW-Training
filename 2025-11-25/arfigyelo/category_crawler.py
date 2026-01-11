import logging
import requests
from mongoengine import connect
from items import ProductCategoryUrlItem
from settings import BASE_URL, HEADERS, MONGO_DB


class CategoryCrawler:
    """Category crawler"""

    def __init__(self):
        self.mongo = connect(db=MONGO_DB, alias="default")
        logging.info("MongoDB connected")
        self.api_url = "https://arfigyelo.gvh.hu/api/categories"
        

    def start(self):
        try:
            response = requests.get(self.api_url, headers=HEADERS, timeout=15)
        except Exception as e:
            logging.error(f"Request failed: {e}")
            return

        if response.status_code != 200:
            logging.error(f"Bad status {response.status_code}")
            return

        data = response.json()
        categories = data.get("categories", [])

        for cat in categories:
            self.parse_item(cat, parent=None)

        logging.info("Category crawling completed")

    def parse_item(self, item, parent=None):
        url = BASE_URL + item.get("path", "")

        try:
            ProductCategoryUrlItem(
                cat_id=item.get("id"),  
                url=url,
                name=item.get("name"),
                path=item.get("path"),
                parent=parent
            ).save()
        except Exception as e:
            logging.error(f"DB save error: {e}")

        for sub in item.get("categoryNodes", []):
            sub_url = BASE_URL + sub.get("path", "")
            try:
                ProductCategoryUrlItem(
                    cat_id=sub.get("id"),
                    url=sub_url,
                    name=sub.get("name"),
                    path=sub.get("path"),
                    parent=item.get("name")
                ).save()
            except Exception as e:
                logging.error(f"DB save error: {e}")

    def stop(self):
        self.mongo.close()
        logging.info("MongoDB connection closed")


if __name__ == "__main__":
    crawler = CategoryCrawler()
    crawler.start()
    crawler.stop()
