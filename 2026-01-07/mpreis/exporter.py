import csv
import logging
import re
from pymongo import MongoClient


# CONFIG
MONGO_DB = "mpreis_db"
MONGO_COLLECTION_DATA = "product_data"
FILE_NAME = "mpreis_2026_01_08_sample.csv"
EXPORT_LIMIT = 100   

FILE_HEADERS = [
    "url",
    "product_name",
    "brand",
    "category_url",
    "size",
    "price",
    "price_per_unit",
    "ingredients",
    "allergens",
    "product_features",
]

# ======================
# HELPER
# ======================
def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()

def clean_price_per_unit(text):
    """
    Convert '3,56€ /kg' -> '3.56/kg'
    """
    if not text:
        return ""

    text = str(text)

    # replace comma with dot (decimal)
    text = text.replace(",", ".")

    # remove euro symbol
    text = text.replace("€", "")

    # remove spaces
    text = re.sub(r"\s+", "", text)

    return text.strip()



def clean_ingredients(text):
    """
    Remove ONLY asterisk characters (*, **, ***, ****)
    without removing any surrounding text.
    """
    if not text:
        return ""
    text = re.sub(r"\*", "", str(text))
    return re.sub(r"\s+", " ", text).strip()



# ======================
# EXPORT CLASS
# ======================
class Export:
    """Export MongoDB product_data to CSV"""

    def __init__(self, writer):
        self.mongo = MongoClient("mongodb://localhost:27017/")[MONGO_DB]
        self.writer = writer

    def start(self):
        """Export as CSV file"""
        self.writer.writerow(FILE_HEADERS)
        logging.info(f"CSV Headers written: {FILE_HEADERS}")

        seen_urls = set()
        count = 0

        cursor = (
            self.mongo[MONGO_COLLECTION_DATA]
            .find({}, no_cursor_timeout=True)
            .limit(EXPORT_LIMIT * 2)  
        )

        for item in cursor:
            url = item.get("url")
            if not url or url in seen_urls:
                continue

            seen_urls.add(url)

            data = [
                clean_text(url),
                clean_text(item.get("product_name")),
                clean_text(item.get("brand")),
                clean_text(item.get("category_url")),
                clean_text(item.get("size")),
                clean_text(item.get("price")),
                clean_price_per_unit(item.get("price_per_unit")),
                clean_ingredients(item.get("Ingredients")),
                clean_text(item.get("Allergens")),
                clean_text(item.get("Product_features")),
            ]

            self.writer.writerow(data)
            count += 1

            if count >= EXPORT_LIMIT:
                break

        logging.info(f"Exported {count} unique product URLs")

# ======================
# RUN EXPORT
# ======================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    with open(FILE_NAME, "w", encoding="utf-8", newline="") as file:
        writer_file = csv.writer(file, delimiter=",", quotechar='"')
        exporter = Export(writer_file)
        exporter.start()

    logging.info(f"Export completed: {FILE_NAME}")
