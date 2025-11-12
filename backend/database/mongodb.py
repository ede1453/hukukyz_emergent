"""MongoDB client and connection management"""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB client manager"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.mongo_url)
            self.db = self.client[settings.db_name]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.db_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def get_collection(self, collection_name: str):
        """Get a collection"""
        if not self.db:
            raise RuntimeError("Database not connected")
        return self.db[collection_name]


# Global MongoDB client instance
mongodb_client = MongoDBClient()


# Collection helpers
def get_users_collection():
    return mongodb_client.get_collection("users")


def get_conversations_collection():
    return mongodb_client.get_collection("conversations")


def get_documents_collection():
    return mongodb_client.get_collection("documents")


def get_upload_logs_collection():
    return mongodb_client.get_collection("upload_logs")


def get_document_versions_collection():
    return mongodb_client.get_collection("document_versions")
