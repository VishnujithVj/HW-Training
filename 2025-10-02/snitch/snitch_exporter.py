import json
from pathlib import Path
from pymongo import MongoClient

MONGODB_URI = "mongodb://localhost:27017"
DB_NAME = "snitch_db"
COLLECTION_NAME = "product_details"
EXPORT_DIR = Path("data")

EXPORT_DIR.mkdir(exist_ok=True)

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def export_jsonl(records, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Exported {len(records)} records to {filepath}")

def export_json_array(records, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(list(records), f, ensure_ascii=False, indent=2)
    print(f"Exported {len(records)} records to {filepath}")

def main():
    records = list(collection.find({}, {"_id": 0}))  

    jsonl_path = EXPORT_DIR / "products_details.jsonl"
    json_array_path = EXPORT_DIR / "products_details_arr.json"

    export_jsonl(records, jsonl_path)
    export_json_array(records, json_array_path)

if __name__ == "__main__":
    main()
