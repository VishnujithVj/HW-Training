import csv
import logging
import re
from pymongo import MongoClient

# ======================
# CONFIG
# ======================
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "nykka_db"
COLLECTION_NAME = "product_data"

FILE_NAME = "nykaa_2026_01_06_sample.csv"

FILE_HEADERS = [
    "product_url",
    "product_name",
    "brand_name",
    "sku",
    "product_id",
    "package_size",
    "selling_price",
    "regular_price",
    "currency",
    "discount",
    "promotion_description",
    "rating_count",
    "review_count",
    "breadcrumbs",
    "description",
    "ingredients",
    "how_to_use",
    "images",
]


lFILE_NAME = "nykka_2026_01_05_sample.csv"
EXPORT_LIMIT = 200
CURRENCY = "INR"

logging.basicConfig(level=logging.INFO)

# ======================
# UTILS
# ======================
def clean_price(value):
    """
    ₹1,314 -> 1314
    """
    if not value:
        return ""
    value = str(value)
    value = re.sub(r"[^\d]", "", value)
    return value or ""

# ======================
# EXPORT CLASS
# ======================
class Export:
    def __init__(self, writer):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db[COLLECTION_NAME]
        self.writer = writer

    def start(self):
        logging.info("Starting Nykaa CSV export")

        self.writer.writerow(FILE_HEADERS)

        seen_product_ids = set()
        exported_count = 0

        for item in self.collection.find(no_cursor_timeout=True):
            product_id = item.get("product_id")

            # skip duplicates
            if not product_id or product_id in seen_product_ids:
                continue

            seen_product_ids.add(product_id)

            selling_price = clean_price(item.get("selling_price"))
            regular_price = clean_price(item.get("regular_price"))

            images = item.get("images") or []
            if isinstance(images, list):
                images = ",".join(images)

            row = [
                item.get("product_url", ""),
                item.get("product_name", ""),
                item.get("brand_name", ""),
                item.get("sku", ""),
                product_id,
                item.get("package_size", ""),
                selling_price,
                regular_price,
                CURRENCY,
                item.get("discount", ""),
                item.get("promotion_description", ""),
                item.get("rating_count", ""),
                item.get("review_count", ""),
                item.get("breadcrumbs", ""),
                item.get("description", ""),
                item.get("ingredients", ""),
                item.get("how_to_use", ""),
                images,
            ]

            self.writer.writerow(row)
            exported_count += 1

            # stop at 200 unique products
            if exported_count >= EXPORT_LIMIT:
                break

        logging.info(f"Export completed successfully (unique products: {exported_count})")

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    with open(FILE_NAME, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(
            file,
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL
        )
        export = Export(writer)
        export.start()