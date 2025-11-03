import csv
import logging
from pymongo import MongoClient
from settings import MONGO_DB, MONGO_COLLECTION_DATA, FILE_NAME, FILE_HEADERS


class Export:
    """Post-Processing for REWE Product Data"""

    def __init__(self, writer):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client[MONGO_DB]
        self.collection = self.db[MONGO_COLLECTION_DATA]
        self.writer = writer
        logging.info("MongoDB connected for export")

    def start(self):
        """Export product data as CSV file"""
        self.writer.writerow(FILE_HEADERS)
        logging.info(f"Exporting data with headers: {len(FILE_HEADERS)} columns")

        cursor = self.collection.find({}, no_cursor_timeout=True)
        product_count = 0

        try:
            for item in cursor:
                row_data = []
                for header in FILE_HEADERS:
                    value = item.get(header, "")

                    """ Clean strings """
                    if isinstance(value, str):
                        value = value.strip()

                        """ Convert booleans """
                    elif isinstance(value, bool):
                        value = str(value).lower()

                        """ Default to string"""
                    else:
                        value = str(value) if value is not None else ""

                    row_data.append(value)

                self.writer.writerow(row_data)
                product_count += 1

                if product_count % 100 == 0:
                    logging.info(f"Exported {product_count} products...")

        finally:
            cursor.close()

        logging.info(f"Export completed successfully. Total products exported: {product_count}")

    def close(self):
        """Close MongoDB connection"""
        self.client.close()
        logging.info("MongoDB connection closed")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s:%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    with open(FILE_NAME, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        export = Export(writer)
        export.start()
        export.close()

    logging.info(f"CSV file '{FILE_NAME}' created successfully")
