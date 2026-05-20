import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_database: str = os.getenv("MONGODB_DATABASE", "learning_analytics")
    mongodb_collection: str = os.getenv("MONGODB_COLLECTION", "student_interactions")


settings = Settings()
