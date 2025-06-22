"""Cosmos DB configuration and connection management."""

import os
from typing import Optional
from azure.cosmos.aio import CosmosClient
from azure.cosmos import exceptions, PartitionKey
from motor.motor_asyncio import AsyncIOMotorClient
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class CosmosDBManager:
    """Manages Cosmos DB connections and operations."""
    
    def __init__(self):
        self.cosmos_endpoint = settings.cosmos_endpoint
        self.cosmos_key = settings.cosmos_key
        self.database_name = settings.cosmos_database_name
        self.client: Optional[CosmosClient] = None
        self.database = None
        
        # Containers
        self.users_container = None
        self.agents_container = None
        self.messages_container = None
        
    async def initialize(self):
        """Initialize Cosmos DB client and create database/containers if needed."""
        try:
            # Initialize Cosmos Client
            self.client = CosmosClient(
                url=self.cosmos_endpoint,
                credential=self.cosmos_key,
            )
            
            # Create database if it doesn't exist
            try:
                self.database = await self.client.create_database_if_not_exists(
                    id=self.database_name
                )
            except exceptions.CosmosResourceExistsError:
                self.database = self.client.get_database_client(self.database_name)
            
            # Create containers
            await self._create_containers()
            
            logger.info("Cosmos DB initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            raise
    
    async def _create_containers(self):
        """Create required containers with appropriate partition keys."""
        
        # Users container - partitioned by user_id
        try:
            self.users_container = await self.database.create_container_if_not_exists(
                id="users",
                partition_key=PartitionKey(path="/id"),
                default_ttl=-1,  # No TTL
            )
        except exceptions.CosmosResourceExistsError:
            self.users_container = self.database.get_container_client("users")
        
        # Agents container - partitioned by user_id for query efficiency
        try:
            self.agents_container = await self.database.create_container_if_not_exists(
                id="agents",
                partition_key=PartitionKey(path="/user_id"),
                default_ttl=-1,
            )
        except exceptions.CosmosResourceExistsError:
            self.agents_container = self.database.get_container_client("agents")
        
        # Messages container - partitioned by conversation_id
        try:
            self.messages_container = await self.database.create_container_if_not_exists(
                id="messages",
                partition_key=PartitionKey(path="/conversation_id"),
                default_ttl=2592000,  # 30 days TTL
            )
        except exceptions.CosmosResourceExistsError:
            self.messages_container = self.database.get_container_client("system_inbox")
    
    async def close(self):
        """Close the Cosmos DB connection."""
        if self.client:
            await self.client.close()


# Global instance
cosmos_manager = CosmosDBManager()


# MongoDB API Alternative (if using Cosmos DB MongoDB API)
class MongoDBManager:
    """Manages MongoDB connections for Cosmos DB MongoDB API."""
    
    def __init__(self):
        self.connection_string = settings.cosmos_mongodb_connection_string
        self.database_name = settings.cosmos_database_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
    
    async def initialize(self):
        """Initialize MongoDB client."""
        try:
            self.client = AsyncIOMotorClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,
            )
            
            # Verify connection
            await self.client.admin.command('ping')
            
            self.database = self.client[self.database_name]
            
            # Create indexes
            await self._create_indexes()
            
            logger.info("MongoDB (Cosmos DB) initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB: {e}")
            raise
    
    async def _create_indexes(self):
        """Create required indexes for better query performance."""
        # Users collection
        users = self.database.users
        await users.create_index("email", unique=True)
        await users.create_index("username", unique=True)
        
        # Agents collection
        agents = self.database.agents
        await agents.create_index("user_id")
        await agents.create_index([("user_id", 1), ("created_at", -1)])
        
        # Messages collection
        messages = self.database.messages
        await messages.create_index("conversation_id")
        await messages.create_index([("conversation_id", 1), ("created_at", -1)])
        await messages.create_index("user_id")
    
    async def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()


# Choose which API to use based on configuration
if settings.use_cosmos_mongodb_api:
    db_manager = MongoDBManager()
else:
    db_manager = cosmos_manager