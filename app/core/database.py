"""Database configuration and utilities for PostgreSQL integration."""

import os
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from urllib.parse import urlparse
import asyncpg
import structlog
from app.core.aws_config import get_aws_parameter_store

logger = structlog.get_logger()


class DatabaseManager:
    """Manages PostgreSQL database connections for the Exercise Service."""
    
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._connection_url: Optional[str] = None
        
    async def initialize(self) -> None:
        """Initialize the database connection pool."""
        try:
            # Get database URL from Parameter Store in production
            if os.getenv("ENVIRONMENT") == "production":
                aws_params = get_aws_parameter_store()
                self._connection_url = aws_params.get_parameter("/spool/postgres-url")
                
                if not self._connection_url:
                    raise ValueError("Database URL not found in Parameter Store")
                    
                logger.info("Loaded database URL from AWS Parameter Store")
            else:
                # For development/testing
                self._connection_url = os.getenv("DATABASE_URL", "postgresql://localhost/spool_exercise_dev")
                logger.info("Using development database URL")
                
            # Create connection pool
            self._pool = await asyncpg.create_pool(
                self._connection_url,
                min_size=2,
                max_size=10,
                command_timeout=60,
                server_settings={
                    'jit': 'off',  # Disable JIT for faster connection times
                    'application_name': 'spool-exercise-service'
                }
            )
            
            logger.info("Database connection pool created successfully")
            
        except Exception as e:
            logger.error("Failed to initialize database connection", error=str(e))
            raise
            
    async def close(self) -> None:
        """Close the database connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("Database connection pool closed")
            
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool."""
        if not self._pool:
            raise RuntimeError("Database not initialized")
            
        async with self._pool.acquire() as connection:
            yield connection
            
    async def health_check(self) -> bool:
        """Check if the database is healthy."""
        try:
            async with self.get_connection() as conn:
                await conn.fetchval("SELECT 1")
                return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False
            
    async def execute_query(self, query: str, *args) -> Any:
        """Execute a database query."""
        try:
            async with self.get_connection() as conn:
                return await conn.fetchval(query, *args)
        except Exception as e:
            logger.error("Database query failed", query=query, error=str(e))
            raise
            
    async def fetch_all(self, query: str, *args) -> list:
        """Fetch all results from a query."""
        try:
            async with self.get_connection() as conn:
                return await conn.fetch(query, *args)
        except Exception as e:
            logger.error("Database fetch failed", query=query, error=str(e))
            raise
            
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch one result from a query."""
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchrow(query, *args)
                return dict(result) if result else None
        except Exception as e:
            logger.error("Database fetch one failed", query=query, error=str(e))
            raise


# Global database manager instance
db_manager = DatabaseManager()


async def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    return db_manager


async def init_database():
    """Initialize the database connection."""
    await db_manager.initialize()


async def close_database():
    """Close the database connection."""
    await db_manager.close()