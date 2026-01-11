import logging
import time
import requests
from datetime import datetime
from mongoengine import connect
from requests.exceptions import RequestException

from items import ProductItem, ProductCategoryUrlItem, ProductFailedItem
from settings import HEADERS, MONGO_DB


class Crawler:
    """Product crawler"""

    def __init__(self):
        self.mongo = connect(db=MONGO_DB, alias="default")
        logging.info("MongoDB connected")

        self.api_url = (
            "https://arfigyelo.gvh.hu/api/products-by-category/{catid}"
            "?limit=24&offset={offset}&order=unitAmount_asc"
        )

        self.categories = list(ProductCategoryUrlItem.objects())
        logging.info(f"Loaded {len(self.categories)} categories")

    def start(self):
        for cat in self.categories:
            if not cat.parent:
                continue

            try:
                cat_id = cat.cat_id
            except Exception:
                logging.error(f"Invalid category path: {cat.path}")
                continue

            logging.info(f"START → {cat.parent} → {cat.name} (ID={cat_id})")
            self.parse_item(cat_id)

        logging.info("Product crawling completed")

    def extract_uom(self, brand_name):
        """
        Extracts a UOM like 450g, 1kg, 500ml from brand name.
        """
        if not brand_name:
            return ""

        import re
        match = re.search(r"(\d+\s?(g|kg|ml|l))", brand_name.lower())
        return match.group(1) if match else ""

    def parse_item(self, category_id):
        offset = 0

        while True:
            url = self.api_url.format(catid=category_id, offset=offset)

            try:
                response = requests.get(url, headers=HEADERS, timeout=20)
            except RequestException:
                ProductFailedItem(url=url).save()
                logging.error(f"FAILED → {url}")
                break

            if response.status_code != 200:
                ProductFailedItem(url=url).save()
                logging.error(f"Bad status {response.status_code} → {url}")
                break

            data = response.json()
            products = data.get("products", [])
            total = data.get("count", 0)

            if not products:
                break

            for p in products:
                product_id = p.get("id")
                name = p.get("name")

                # Convert min price
                min_price = p.get("minUnitPrice")
                selling_price = "" if min_price is None else str(min_price)

                packaging = p.get("packaging")
                unit = p.get("unit")
                brand = p.get("brand")

                # Extract UOM from brand
                uom = self.extract_uom(brand)

                # Build product_description
                description_list = []
                for chain in p.get("pricesOfChainStores", []):
                    store = chain.get("name")
                    for pr in chain.get("prices", []):
                        description_list.append({
                            "store": store,
                            "amount": pr.get("amount")
                        })

                item_data = {
                    "unique_id": product_id,
                    "competitor_name": "arfigyelo",
                    "extraction_date": datetime.utcnow().date(),
                    "product_name": name,
                    "grammage_quantity": packaging,
                    "grammage_unit": unit,
                    "selling_price": selling_price,
                    "currency": "HUF",
                    "product_description": description_list,
                    "packaging": packaging,
                    "image_url1": p.get("imageUrl"),
                    "image_url2": p.get("imageUrl"),
                    "competitor_product_key": product_id,
                    "site_shown_uom": uom,
                    "product_unique_key": f"{product_id}P",
                }

                ProductItem(**item_data).save()

            offset += 24
            if offset >= total:
                break

            time.sleep(0.3)

    def stop(self):
        self.mongo.close()
        logging.info("MongoDB closed")


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.stop()
