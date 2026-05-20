from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

client = AsyncIOMotorClient(
    settings.mongodb_uri,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=60000,
)
database = client[settings.mongodb_database]
collection = database[settings.mongodb_collection]


def get_collection(name: str):
    return database[name]
