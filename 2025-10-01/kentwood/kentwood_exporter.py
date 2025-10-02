import json
from pathlib import Path
from pymongo import MongoClient


DB_NAME = "kentwood_db"
COLLECTION_NAME = "agents_details"
EXPORT_DIR = Path("data")
EXPORT_DIR.mkdir(exist_ok=True)


client = MongoClient("mongodb://localhost:27017/")
db = client[DB_NAME]
collection = db[COLLECTION_NAME]


def export_jsonl(records, filepath):
    """Export as JSON Lines"""
    with open(filepath, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def export_json_array(records, filepath):
    """Export as JSON Array"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

# Main
def main():
    print("Fetching data from MongoDB...")
    records = list(collection.find({}, {"_id": 0}))  
    
    if not records:
        print("No records found in MongoDB.")
        return
    

    jsonl_file = EXPORT_DIR / "agents_details.jsonl"
    json_file = EXPORT_DIR / "agents_details.json"
    

    print("Exporting JSON Lines...")
    export_jsonl(records, jsonl_file)
    
    print("Exporting JSON Array...")
    export_json_array(records, json_file)
    
    print(f"\n✅ Export completed! Files saved in '{EXPORT_DIR}/'")

if __name__ == "__main__":
    main()
