import csv
import logging
from mongoengine import connect
from settings import (
    MONGO_DB,
    MONGO_COLLECTION_DATA,
    file_name,
    FILE_HEADERS
)


class Export:
    """Export product data to CSV"""

    def __init__(self, writer):
        self.mongo = connect(db=MONGO_DB, alias="default")
        self.writer = writer

    def start(self):
        # Write CSV headers
        self.writer.writerow(FILE_HEADERS)
        logging.info("Headers written")

        collection = self.mongo[MONGO_DB][MONGO_COLLECTION_DATA]

        cursor = collection.find(no_cursor_timeout=True)

        for doc in cursor:

            # Create a row template with all 126 headers blank
            row = {header: "" for header in FILE_HEADERS}

            # Map database fields to correct CSV headers
            row["unique_id"] = doc.get("unique_id", "")
            row["competitor_name"] = "arfigyelo"
            row["extraction_date"] = doc.get("extraction_date", "")
            row["product_name"] = doc.get("product_name", "")
            row["brand"] = doc.get("brand", "")
            row["grammage_quantity"] = doc.get("grammage_quantity", "")
            row["grammage_unit"] = doc.get("grammage_unit", "")
            row["selling_price"] = doc.get("selling_price", "")
            row["currency"] = "HUF"
            row["product_description"] = str(doc.get("product_description", ""))
            row["packaging"] = doc.get("packaging", "")
            row["image_url_1"] = doc.get("image_url1", "")
            row["image_url_2"] = doc.get("image_url2", "")
            row["competitor_product_key"] = doc.get("competitor_product_key", "")
            row["site_shown_uom"] = doc.get("site_shown_uom", "")
            row["product_unique_key"] = doc.get("product_unique_key", "")

            # Write row in header order
            self.writer.writerow([row[h] for h in FILE_HEADERS])

        cursor.close()
        logging.info("Export complete")
