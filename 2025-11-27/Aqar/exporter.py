import json
import logging
from pymongo import MongoClient
from settings import MONGO_DB, FILE_NAME, FILE_HEADERS, MONGO_COLLECTION_DATA

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")


def clean_value(val):
    if val is None:
        return ""

    try:
        s = str(val).strip()
        return s if s else ""
    except:
        return ""


class Export:
    """Export ProductItem collection to NDJSON (one JSON object per line)"""

    def __init__(self, file_handle):
        self.file_handle = file_handle
        self.client = MongoClient("localhost", 27017)
        self.db = self.client[MONGO_DB]

    def start(self):
        logging.info("Starting export...")

        max_records = 200
        count = 0

        cursor = self.db[MONGO_COLLECTION_DATA].find(no_cursor_timeout=True).limit(max_records)

        for item in cursor:

            data = {}
            for header in FILE_HEADERS:
                raw_value = item.get(header, "")
                data[header] = clean_value(raw_value)

            # Write NDJSON (newline separated)
            self.file_handle.write(json.dumps(data, ensure_ascii=False) + "\n")

            count += 1
            logging.info(f"Exported ({count}/{max_records}): {item.get('title', '')}")

        logging.info(f"Export completed. Total records: {count}")


if __name__ == "__main__":
    # Ensure output file is .json
    json_file_name = (
        FILE_NAME.replace(".csv", ".json")
        if ".csv" in FILE_NAME.lower()
        else FILE_NAME + ".json"
    )

    with open(json_file_name, "w", encoding="utf-8") as file:
        export = Export(file)
        export.start()

    logging.info(f"Data exported to {json_file_name}")
