import csv
import logging
import os
import re
from mongoengine import connect
from items import ProductItem
from settings import MONGO_DB, FILE_NAME, FILE_HEADERS

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s",  datefmt="%Y-%m-%d %H:%M:%S",)

class Export:
    """Post-Processing Exporter"""

    def __init__(self, writer):
        self.mongo = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        logging.info("MongoDB connected")
        self.writer = writer

    def start(self):
        """Export as CSV file"""

        self.writer.writerow(FILE_HEADERS)
        logging.info(f"CSV Header written with {len(FILE_HEADERS)} columns")

        products = ProductItem.objects()
        total_products = products.count()
        logging.info(f"Exporting {total_products} products")

        for idx, item in enumerate(products, 1):
            if idx % 100 == 0:
                logging.info(f"Exported {idx}/{total_products} products")
                
            record = item.to_mongo().to_dict()
            row = []

            for field in FILE_HEADERS:
                value = record.get(field, "")

                """Clean product_description field"""
                if field == "product_description":
                    value = self.clean_description(value)

                """(Normalize None → "")"""
                if value is None:
                    value = ""

                """Convert non-string types safely"""
                if isinstance(value, (list, dict)):
                    value = str(value)

                row.append(value)

            """Ensure exactly correct number of fields"""
            total_fields = len(FILE_HEADERS)
            if len(row) < total_fields:
                row += [""] * (total_fields - len(row))
            elif len(row) > total_fields:
                row = row[:total_fields]

            self.writer.writerow(row)

        logging.info(f"Export completed. Saved {total_products} records")

    def clean_description(self, text):
        """Clean unwanted symbols, emojis, and ad text from product description."""
        if not text:
            return ""

        """Remove emojis and non-standard symbols"""
        text = re.sub(r"[^\x00-\x7F]+", " ", text)

        """Remove ad-related words/phrases"""
        text = re.sub(
            r"(online kaufen|jetzt kaufen|gratis versand|click & collect|später zahlen)",
            "",
            text,
            flags=re.IGNORECASE,
        )

        """Replace multiple spaces and strip """
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def close(self):
        """Close connections"""
        logging.info("Export completed")


if __name__ == "__main__":
    """ Create exports directory if it doesn't exist """
    os.makedirs("exports", exist_ok=True)
    file_path = f"exports/{FILE_NAME}.csv"
    
    with open(file_path, "w", encoding="utf-8", newline="") as file:
        writer_file = csv.writer(file, delimiter="|", quotechar='"')
        export = Export(writer_file)
        export.start()
        export.close()