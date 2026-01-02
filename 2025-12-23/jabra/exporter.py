import csv
import logging
from pymongo import MongoClient
from settings import (
    MONGO_URI, MONGO_DB, MONGO_COLLECTION_DATA,
    FILE_NAME, FILE_HEADERS
)


class JabraExporter:
    """Export Product Data to CSV"""

    def __init__(self, writer):
        self.mongo = MongoClient(MONGO_URI)
        self.db = self.mongo[MONGO_DB]
        self.collection = self.db[MONGO_COLLECTION_DATA]
        self.writer = writer

        logging.info("Exporter initialized")

    def start(self):
        self.writer.writerow(FILE_HEADERS)
        logging.info(f"Headers written: {FILE_HEADERS}")

        products = self.collection.find(no_cursor_timeout=True)

        count = 0
        for item in products:
            row = self.parse_item(item)
            if row:
                self.writer.writerow(row)
                count += 1

                if count % 100 == 0:
                    logging.info(f"Exported {count} products")

        logging.info(f"Export completed. Total products: {count}")

    def parse_item(self, item):
        # Basic fields (force string)
        product_name = str(item.get("product_name", "") or "")
        product_url = str(item.get("product_url", "") or "")
        sku = str(item.get("sku", "") or "")
        product_id = str(item.get("productId", "") or "")
        segment_type = str(item.get("segmentType", "") or "")
        warranty = str(item.get("warranty", "") or "")
        model = str(item.get("model", "") or "")

        # ---- IMAGES: CLEAN DICTS -> URL STRING ----
        images_list = item.get("images", [])
        image_urls = []

        if isinstance(images_list, list):
            for img in images_list:
                if isinstance(img, dict) and img.get("url"):
                    image_urls.append(str(img["url"]))
                elif isinstance(img, str):
                    image_urls.append(img)

        images = ", ".join(image_urls)

        # Prices
        selling_price = str(item.get("selling_price", "") or "")
        regular_price = str(item.get("regular_price", "") or "")
        currency = str(item.get("currency", "") or "")

        # Documents (already URLs → stringify)
        documents_list = item.get("documents", [])
        documents = ""
        if isinstance(documents_list, list):
            documents = " , ".join(str(d) for d in documents_list if d)

        # Section title
        section_title = str(item.get("section_title", "") or "")

        # ---- FEATURES: flatten to readable string ----
        features_list = item.get("features", [])
        features_out = []

        if isinstance(features_list, list):
            for f in features_list:
                if isinstance(f, dict):
                    title = f.get("title", "")
                    desc = f.get("description", "")
                    text = " ".join(x for x in [title, desc] if x)
                    if text:
                        features_out.append(text)
                elif isinstance(f, str):
                    features_out.append(f)

        features = " , ".join(features_out)

        return [
            product_name,
            product_url,
            sku,
            product_id,
            segment_type,
            warranty,
            model,
            images,
            selling_price,
            regular_price,
            currency,
            documents,
            section_title,
            features,
        ]

    def stop(self):
        self.mongo.close()
        logging.info("Exporter finished & MongoDB closed")


if __name__ == "__main__":
    output_file = f"{FILE_NAME}.csv"

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(
            f,
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL
        )

        exporter = JabraExporter(writer)
        exporter.start()
        exporter.stop()

    logging.info(f"Export saved to: {output_file}")
