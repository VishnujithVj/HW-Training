import requests
import logging
from items import CategoryUrlItem
from settings import HEADERS

class CategoryCrawler:
    """Crawling Categories"""

    def __init__(self):
        self.url = "https://www.bipa.at/resolve-url/navigation"
        self.cookies = {
            'OptanonAlertBoxClosed': '2025-10-20T10:04:09.055Z',
            'usid_AT': '22ba7b8d-30d6-44d2-9d3e-6cae00a296bb',
        }

    def start(self):
        """Requesting Start url"""
        logging.info("Starting category crawler")
        
        try:
            response = requests.get(self.url, headers=HEADERS, cookies=self.cookies)
            if response.status_code == 200:
                categories_data = response.json()
                self.parse_categories(categories_data)
                logging.info("Category crawling completed successfully")
            else:
                logging.error(f"Failed to fetch categories: {response.status_code}")
        except Exception as e:
            logging.error(f"Error in category crawler: {e}")

    def parse_categories(self, categories, name=None, parent_url=None, level="main"):
        """Parse categories recursively"""
        for category in categories:
            name = category.get("name")
            url = category.get("link")
            
            if name and url:
        
                category_item = CategoryUrlItem(
                    url=url,
                    name=name,
                    parent_url=parent_url,
                    level=level
                )
                category_item.save()
                logging.info(f"Saved category: {name} (Level: {level})")

            child_categories = category.get("childCategories", [])
            if child_categories:
                next_level = "sub" if level == "main" else "subsub"
                self.parse_categories(child_categories, name, url, next_level)

    def close(self):
        """Close function"""
        logging.info("Category crawler completed")


if __name__ == "__main__":
    crawler = CategoryCrawler()
    crawler.start()
    crawler.close()