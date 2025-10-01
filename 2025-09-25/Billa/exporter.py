import csv
import os
from datetime import datetime
from pathlib import Path
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "billa_site_db"
COLLECTION_NAME = "product_details"

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def export_to_csv():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    cursor = collection.find({})

    docs = list(cursor)
    if not docs:
        print("No documents found in MongoDB collection.")
        return

    fieldnames = sorted({key for doc in docs for key in doc.keys() if key != "_id"})

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = DATA_DIR / f"Datahut_Billa_{timestamp}.csv"

    # piped-delimited CSV
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="|")
        writer.writeheader()
        for doc in docs:
            doc.pop("_id", None)
            writer.writerow(doc)

    print(f"Exported {len(docs)} records to {output_file}")

if __name__ == "__main__":
    export_to_csv()
