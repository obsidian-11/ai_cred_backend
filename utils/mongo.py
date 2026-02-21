from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["ai_cred_db"]

def get_collection(name="sources"):
    return db[name]