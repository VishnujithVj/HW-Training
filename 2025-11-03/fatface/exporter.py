import csv
import logging
from mongoengine import connect
from items import ProductItem
from settings import MONGO_DB, FILE_NAME, FILE_HEADERS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

class Export:
    """Post-Processing Exporter"""

    def __init__(self, writer):
        self.mongo = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        logging.info("MongoDB connected")
        self.writer = writer

    def start(self):
        """Export as CSV file"""
        self.writer.writerow(FILE_HEADERS)
        logging.info("CSV headers written")

        products = ProductItem.objects.all()
        logging.info(f"Found {len(products)} products to export")
        
        for product in products:
            data = []
            for header in FILE_HEADERS:
                value = getattr(product, header, "")
                if value is None:
                    data.append("")
                elif isinstance(value, bool):
                    data.append(str(value).lower())
                elif isinstance(value, (int, float)):
                    data.append(str(value))
                else:
                    data.append(str(value) if value else "")
            
            self.writer.writerow(data)
            
        logging.info(f"Successfully exported {len(products)} products to CSV")

    def close(self):
        pass

if __name__ == "__main__":
    with open(f"{FILE_NAME}.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="|", quotechar='"', quoting=csv.QUOTE_ALL)
        export = Export(writer)
        export.start()
        export.close()