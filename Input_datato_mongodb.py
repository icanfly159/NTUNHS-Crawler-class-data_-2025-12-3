import json
import os
from pathlib import Path

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# === 1. MongoDB connection ===
# Use your real URI here. (Better: move to env var later.)
uri = "mongodb+srv://ntunhs:Aa22512188@ntunhsdatabase.to42hoq.mongodb.net/?appName=NTUNHSdatabase"



client = MongoClient(uri, server_api=ServerApi("1"))

# All collections will go into this database
db = client["NTUNHS_CLASS_DATA"]

# === 2. Folder that contains your JSON files ===
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

if not DATA_DIR.exists():
    raise SystemExit(f"Data folder not found: {DATA_DIR}")

# === 3. Loop over all JSON files ===
for json_path in sorted(DATA_DIR.glob("*.json")):
    collection_name = json_path.stem          # e.g. "courses_1051"
    collection = db[collection_name]

    print(f"\nProcessing {json_path.name} -> collection '{collection_name}'")

    # Optional: drop existing data so you don't get duplicates while testing
    # collection.drop()

    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Decide how to insert depending on JSON structure
    if isinstance(data, list):
        if not data:
            print("  File is an empty list, skipping.")
            continue
        result = collection.insert_many(data)
        print(f"  Inserted {len(result.inserted_ids)} documents.")
    elif isinstance(data, dict):
        result = collection.insert_one(data)
        print("  Inserted 1 document.")
    else:
        print(f"  Unsupported JSON type in {json_path.name}: {type(data)}")
        continue

print("\n✅ Import finished.")
