import json
import pandas as pd
import pymongo
import os
from datetime import datetime

data_folder = "data"
os.makedirs(data_folder, exist_ok=True)  

# MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["marksandspencer"]
products_detail_col = db["products_detail"]

docs = list(products_detail_col.find({}, {"_id": 0}))  

def convert_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()  # e.g. "2025-09-11T18:00:00"
    raise TypeError("Type not serializable")

# JSON ARRAY
json_array_path = os.path.join(data_folder, "products_array.json")
with open(json_array_path, "w", encoding="utf-8") as f:
    json.dump(docs, f, ensure_ascii=False, indent=4, default=convert_datetime)    

# JSON LINES
json_lines_path = os.path.join(data_folder, "products_lines.jsonl")
with open(json_lines_path, "w", encoding="utf-8") as f:
    for doc in docs:
        f.write(json.dumps(doc, ensure_ascii=False, default=convert_datetime) + "\n")

# CSV 
df = pd.DataFrame(docs)
csv_path = os.path.join(data_folder, "products.csv")
df.to_csv(csv_path, index=False, encoding="utf-8")

# Pipe-Separated CSV
pipe_csv_path = os.path.join(data_folder, "products_pipe.csv")
df.to_csv(pipe_csv_path, index=False, sep="|", encoding="utf-8")

print("Export completed: JSON array, JSON lines, CSV, and Pipe CSV saved in 'data/' folder.")

# Conversions
converted_csv_path = os.path.join(data_folder, "converted_from_json.csv")
df = pd.read_json(json_array_path)
df.to_csv(converted_csv_path, index=False)

print("Conversions completed: All formats transformed successfully in 'data/' folder.")
