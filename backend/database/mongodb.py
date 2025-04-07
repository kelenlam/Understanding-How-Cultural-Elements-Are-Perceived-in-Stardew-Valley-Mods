# backend/database/mongodb.py
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict
from ..config import Config
import datetime

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        try:
            self.client = AsyncIOMotorClient(Config.MONGO_URI) 
            self.db = self.client[Config.MONGO_DB]
            print("Connected to MongoDB")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            self.redis = None

    async def close(self):
        if self.client:
            self.client.close()

    async def store_analysis(self, analysis_result: Dict):
        collection = self.db.analysis_results
        await collection.insert_one({
            **analysis_result,
            "timestamp": datetime.datetime.utcnow()
        })

    async def get_analysis_history(self, query: str):
        collection = self.db.analysis_results
        return await collection.find_one(  # Returns the most recent analysis result for the query
        {"original_query": query},
        sort=[("timestamp", -1)]
        )