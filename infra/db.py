# infra/db.py
# -------------------------------
# MongoDB Connection Module
# -------------------------------

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

# Load config.env
load_dotenv("config.env")

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI not found in config.env")
if not DATABASE_NAME:
    raise ValueError("❌ DATABASE_NAME not found in config.env")

# MongoClient (shared globally)
client = MongoClient(MONGO_URI, server_api=ServerApi("1"))

def get_db():
    """
    Returns a database instance for all Mongo operations.
    """
    return client[DATABASE_NAME]

# Test connection on startup
try:
    client.admin.command("ping")
    print("[MongoDB] Connected to MongoDB Atlas successfully.")
except Exception as e:
    print("[MongoDB] Connection error:", e)
