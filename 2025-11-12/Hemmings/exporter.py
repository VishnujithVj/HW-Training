import csv
import logging
import re
from mongoengine import connect
from settings import MONGO_DB, MONGO_COLLECTION_DATA, FILE_HEADERS, FILE_NAME


class Exporter:
    """Export parsed data (like Hemmings cars) from MongoDB to CSV"""

    def __init__(self, writer):
        self.writer = writer
        self.mongo = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        self.db = self.mongo.get_database(MONGO_DB)
        logging.info("MongoDB connected")

    def start(self):
        """Export MongoDB documents to CSV file"""
        self.writer.writerow(FILE_HEADERS)
        count = 0

        collection = self.db[MONGO_COLLECTION_DATA]
        logging.info(f"Exporting data from collection: {MONGO_COLLECTION_DATA}")

        for item in collection.find(no_cursor_timeout=True):
            row = self.clean_item(item)
            self.writer.writerow([row.get(field, "") for field in FILE_HEADERS])
            count += 1

        logging.info(f"Export completed → {FILE_NAME} ({count} records)")

    def clean_item(self, item):
        """Clean up data fields for CSV export"""
        cleaned = {}
        for field in FILE_HEADERS:
            value = item.get(field, "")
            if isinstance(value, list):
                value = ", ".join(str(v).strip() for v in value if v)
            elif value is None:
                value = ""
            elif field.lower() == "description":
                value = self.clean_description(value)
            cleaned[field] = str(value).strip()
        return cleaned

    def clean_description(self, text):
        """Clean description text by removing HTML, extra spaces, and newlines"""
        if not text:
            return ""
        """Remove HTML tags"""
        text = re.sub(r"<[^>]+>", "", text)

        """Replace newlines, tabs, multiple spaces with single space"""
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def close(self):
        self.mongo.close()
        logging.info("MongoDB connection closed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")
    with open(FILE_NAME, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
        exporter = Exporter(writer)
        exporter.start()
        exporter.close()
