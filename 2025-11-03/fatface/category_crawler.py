import logging
from urllib.parse import urljoin
from curl_cffi import requests
from mongoengine import connect
from items import CategoryUrlItem
from settings import BASE_URL, API_URL, HEADERS, MONGO_DB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class CategoryCrawler:
    """Category Crawler"""

    def __init__(self):
        self.mongo = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        logging.info("MongoDB connected")

    def start(self):
        """Requesting Start url"""
        data = self.fetch_category_data()
        if not data:
            logging.error("No category data retrieved")
            return

        logging.info("Parsing category hierarchy...")
        categories = self.parse_categories(data)
        
        for category in categories:
            """ ITEM SAVE """
            item_data = {
                "category_title": category['category_title'],
                "subcategory_title": category['subcategory_title'],
                "category_url": category['category_url'],
                "subcategory_url": category['subcategory_url'],
            }
            
            try:
                item = CategoryUrlItem(**item_data)
                item.save()
                logging.info(f"Saved: {category['subcategory_url']}")
            except Exception as e:
                logging.error(f"Error saving category: {e}")

        logging.info(f"Saved {len(categories)} category records")

    def fetch_category_data(self):
        """Fetch category JSON data from API"""
        logging.info("Fetching category data from API...")
        
        response = requests.get(API_URL, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            return response.json().get("items", [])
        
        logging.error(f"API returned {response.status_code}")
        return []

    def parse_categories(self, data):
        """Extract categories and subcategories"""
        results = []

        def extract_items(items, parent_title="", parent_url=""):
            for item in items:
                title = item.get("title")
                target = item.get("target")
                
                if not title or not target:
                    continue

                url = urljoin(BASE_URL, target.strip())

                """ Only save subcategories (level >= 1) """
                if parent_title:
                    results.append({
                        "category_title": parent_title,
                        "subcategory_title": title,
                        "category_url": parent_url,
                        "subcategory_url": url,
                    })

                """ Recurse into nested items """
                if isinstance(item.get("items"), list):
                    current_parent = parent_title if parent_title else title
                    current_parent_url = parent_url if parent_url else url
                    extract_items(item["items"], current_parent, current_parent_url)

        extract_items(data)
        return results

    def close(self):
        """Close function for all module object closing"""
        self.mongo.close()


if __name__ == "__main__":
    crawler = CategoryCrawler()
    crawler.start()
    crawler.close()