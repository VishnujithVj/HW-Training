import logging
import json
from curl_cffi import requests
from items import ProductCategoryUrlItem
from settings import BASE_URL, HEADERS, MONGO_DB, MONGO_HOST
from mongoengine import connect

API_URL = "https://gcc.luluhypermarket.com/api/client/menus/generate/?depth_height=4"


class CategoryCrawler:
    def __init__(self):
        """Initialize MongoDB connection"""
        self.mongo = connect(db=MONGO_DB, host=MONGO_HOST)
        logging.info("MongoDB connected")

    def start(self):
        """Fetch categories and begin parsing"""

        try:
            r = requests.get(
                API_URL,
                headers=HEADERS,
                impersonate="chrome120",
                timeout=20
            )
        except Exception as e:
            logging.error(f"Category API request failed: {e}")
            return

        if r.status_code != 200:
            logging.error(f"Category API failed {r.status_code} - {r.text}")
            return

        try:
            data = r.json()
        except Exception:
            logging.error("Failed to parse JSON from category API")
            return

        menu = data.get("menu", [])
        if not isinstance(menu, list):
            logging.error("Menu format invalid")
            return

        logging.info("Fetched category menu (%d items)", len(menu))

        # Parse items
        self.parse_item(menu)

        logging.info("Category crawling completed")

    def parse_item(self, menu):
        """Convert flat menu list → nested hierarchy and save"""

        nodes = {}
        roots = []

        # Create nodes dictionary
        for item in menu:
            pk = item.get("pk")
            if pk is None:
                continue  # skip invalid items

            nodes[pk] = {
                "label": item.get("label", ""),
                "url": item.get("url"),
                "level": item.get("level"),
                "children": []
            }

        # Link parent → children
        for pk, node in nodes.items():
            parent = node["parent_pk"]
            if parent in nodes:
                nodes[parent]["children"].append(node)
            else:
                roots.append(node)

        # Save hierarchy
        self.save(roots)

    def save(self, categories, indent=0):
        """Recursively save categories"""

        for cat in categories:
            url_path = cat.get("url")

            # Save only if URL exists
            if url_path:
                full_url = BASE_URL.rstrip("/") + url_path

                try:
                    ProductCategoryUrlItem(
                        url=full_url,
                        label=cat.get("label"),
                        level=str(cat.get("level")),
                    ).save()

                    logging.info(
                        "Saved category URL: %s (level %s)",
                        full_url,
                        cat.get("level"),
                    )
                except Exception as e:
                    logging.error(f"Mongo save failed for {full_url}: {e}")

            # Recursively save children
            if cat.get("children"):
                self.save(cat["children"], indent + 4)

    def close(self):
        logging.info("MongoDB connection closed")


if __name__ == "__main__":
    crawler = CategoryCrawler()
    crawler.start()
    crawler.close()
