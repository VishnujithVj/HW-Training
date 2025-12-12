import time
import logging
import requests
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from settings import (MONGO_URI,MONGO_DB,MONGO_COLLECTION_CATEGORY,MONGO_COLLECTION_URLS,MONGO_COLLECTION_URL_FAILED,HEADERS,PRODUCT_SEARCH_API,DEFAULT_QS,)

logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s:%(message)s",datefmt="%Y-%m-%d %H:%M:%S",)


class ProductCrawler:
    """Crawling Product URLs from Aldi Product Search API"""

    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.mongo = self.client[MONGO_DB]
        logging.info("MongoDB connection established successfully")

    def start(self):
        """Load categories from database"""
        categories = list(self.mongo[MONGO_COLLECTION_CATEGORY].find({}))

        if not categories:
            logging.warning("No categories found. Please run category_crawler first.")
            return False

        logging.info(f"Found {len(categories)} categories to process")

        """Process each category"""
        for cat in categories:
            cat_name = cat.get("category_name")
            cat_key = cat.get("category_key")
            subcategories = cat.get("subcategories", [])

            if not cat_name or not cat_key:
                logging.warning("Skipping category with missing name or key")
                continue

            """If no subcategories, crawl the category directly"""
            if not subcategories:
                logging.info(f"Crawling category (no subcategories): {cat_name}")
                self.parse_item(cat_name, None, cat_key)
                continue

            """Crawl each subcategory"""
            for sub in subcategories:
                sub_name = sub.get("name")
                sub_key = sub.get("key")

                if not sub_key:
                    logging.warning(f"Skipping subcategory with missing key: {sub_name}")
                    continue

                logging.info(f"Crawling subcategory: {cat_name} / {sub_name}")
                self.parse_item(cat_name, sub_name, sub_key)

        logging.info("Product URL crawl completed successfully")
        return True

    def parse_item(self, category_name, subcategory_name, category_key):
        """Fetch products using offset-based pagination"""
        offset = 0
        total_products = 0

        while True:
            params = DEFAULT_QS.copy()
            params["categoryKey"] = category_key
            params["offset"] = offset

            try:
                response = requests.get(
                    PRODUCT_SEARCH_API,
                    params=params,
                    headers=HEADERS,
                    timeout=20
                )

                if response.status_code == 400:
                    logging.info(f"No products found for {category_name}/{subcategory_name}")
                    break

                response.raise_for_status()

                data = response.json().get("data", [])

                if not data:
                    logging.info(f"No more products - pagination finished for {category_name}/{subcategory_name}")
                    break

                """Process each product"""
                for product in data:
                    sku = product.get("sku")
                    slug = product.get("urlSlugText")
                    name = product.get("name")

                    if not sku or not slug:
                        logging.warning(f"Skipping product with missing SKU or slug: {name}")
                        continue

                    product_url = f"https://www.aldi.co.uk/product/{slug}-{sku}"

                    doc = {
                        "category": category_name,
                        "subcategory": subcategory_name,
                        "product_name": name,
                        "product_url": product_url,
                        "sku": str(sku),
                    }

                    try:
                        self.mongo[MONGO_COLLECTION_URLS].insert_one(doc)
                        total_products += 1
                        logging.info(f"Inserted URL [{total_products}]: {product_url}")
                    except PyMongoError:
                        logging.debug(f"Duplicate URL skipped: {product_url}")

                offset += DEFAULT_QS.get("limit", 30)
                time.sleep(0.2)

            except requests.RequestException as e:
                error_msg = f"Request error for category key={category_key}, offset={offset}: {e}"
                logging.error(error_msg)

                self.mongo[MONGO_COLLECTION_URL_FAILED].insert_one({
                    "url": PRODUCT_SEARCH_API,
                    "reason": error_msg,
                })
            except Exception as e:
                logging.error(f"Unexpected error: {e}")

        logging.info(
            f"Completed {category_name}/{subcategory_name} - Total products: {total_products}"
        )

    def close(self):
        self.client.close()
        logging.info("ProductCrawler stopped - MongoDB connection closed")


if __name__ == "__main__":
    crawler = ProductCrawler()
    crawler.start()
    crawler.close()
