import os
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Replace this with your actual MongoDB Atlas connection string in the .env file
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/research_engine")

client = AsyncIOMotorClient(
    MONGODB_URL,
    tlsCAFile=certifi.where()
)
db = client.get_database("research_engine")

def get_db():
    return db
