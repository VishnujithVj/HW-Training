import logging
import requests
from items import CategoryUrlItem
from settings import HEADERS, COOKIES


class CategoryCrawler:
    """Crawling Category URLs"""

    # INIT
    def __init__(self):
        self.url = "https://www.bipa.at/resolve-url/navigation"
        self.mongo = '' 

    # START
    def start(self):
        """Start crawling category URLs"""
        logging.info("Starting category crawler")

        response = requests.get(self.url, headers=HEADERS, cookies=COOKIES)
        if response.status_code == 200:
            categories_data = response.json()
            self.parse_item(categories_data)
        else:
            logging.error(f"Failed to fetch categories: {response.status_code}")
            
        self.close()

    # CLOSE
    def close(self):
        """Close connections"""
        if self.mongo:
            self.mongo.close()

        logging.info("Category crawler completed")


    # PARSE ITEM
    def parse_item(self, categories, parent_url="", level="main"):
        """Parse categories recursively"""
        for category in categories:
            name = category.get("name")
            url = category.get("link")

            if name and url:
                item = CategoryUrlItem(
                    url=url,
                    name=name,
                    parent_url=parent_url,
                    level=level
                )
        
                item.save()
                logging.info(f"Saved category: {name} (Level: {level})")

            # Recursive parsing for sub categories
            sub_categories = category.get("childCategories", [])
            if sub_categories:
                next_level = "sub" if level == "main" else "subsub"
                self.parse_item(sub_categories, url, next_level)


# ENTRY POINT
if __name__ == "__main__":
    crawler = CategoryCrawler()
    crawler.start()
