"""Database configuration and session management."""

import logging
from typing import AsyncGenerator

# Temporarily disabled SQLAlchemy for Cosmos DB migration
# from sqlalchemy.ext.asyncio import (
#     AsyncSession,
#     async_sessionmaker,
#     create_async_engine,
# )
# from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = logging.getLogger(__name__)

# Placeholder for Cosmos DB
class AsyncSession:
    """Placeholder for async session"""
    pass

# Create async engine - placeholder
# engine = create_async_engine(
#     settings.database_url,
#     echo=settings.db_echo,
#     future=True,
#     pool_pre_ping=True,
#     pool_size=10,
#     max_overflow=20,
# )

# Create async session factory - placeholder
# AsyncSessionLocal = async_sessionmaker(
#     engine,
#     class_=AsyncSession,
#     expire_on_commit=False,
#     autocommit=False,
#     autoflush=False,
# )


class Base:
    """Base class for all database models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    # For now, return a dummy session
    yield AsyncSession()


async def create_db_and_tables():
    """Create database tables."""
    # Cosmos DB doesn't need table creation
    logger.info("Using Cosmos DB - no tables to create")


async def drop_db_and_tables():
    """Drop all database tables."""
    # Cosmos DB doesn't need table dropping
    logger.info("Using Cosmos DB - no tables to drop")