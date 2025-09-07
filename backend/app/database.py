"""
Database connection and session management for Real-Time Climate Dashboard
Enterprise-grade async PostgreSQL setup with connection pooling
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData, event
from sqlalchemy.pool import NullPool
import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from .config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create database engine with connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in development
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections every hour
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)

# Create base class for all models
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

Base = declarative_base(metadata=metadata)

# Database session dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session for FastAPI endpoints
    Ensures proper session cleanup and error handling
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions outside of FastAPI
    Used by background tasks and data processing services
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

async def create_tables():
    """
    Create all database tables
    Used during application startup
    """
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from .models import buoy, reading, alert, user
            
            logger.info("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created successfully")
            
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise

async def drop_tables():
    """
    Drop all database tables (for testing/reset)
    """
    try:
        async with engine.begin() as conn:
            logger.warning("⚠️ Dropping all database tables...")
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("✅ Database tables dropped")
            
    except Exception as e:
        logger.error(f"❌ Failed to drop database tables: {e}")
        raise

async def check_db_connection():
    """
    Health check for database connection
    Returns True if connection is healthy
    """
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

# Event listeners for connection debugging (development only)
if settings.DEBUG:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Set PostgreSQL connection parameters for development"""
        pass  # Add any connection-specific settings here

    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Log SQL queries in debug mode"""
        if settings.LOG_LEVEL == "DEBUG":
            logger.debug(f"SQL: {statement}")
            if parameters:
                logger.debug(f"Parameters: {parameters}")

# Connection pool monitoring
class DatabaseMetrics:
    """Track database connection pool metrics for monitoring"""
    
    @staticmethod
    def get_pool_status():
        """Get current connection pool status"""
        pool = engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),  
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }
    
    @staticmethod
    async def get_active_connections():
        """Get count of active database connections"""
        try:
            async with engine.begin() as conn:
                result = await conn.execute(
                    "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
                )
                return result.scalar()
        except Exception as e:
            logger.error(f"Failed to get active connections: {e}")
            return None

# Export commonly used items
__all__ = [
    "engine",
    "AsyncSessionLocal", 
    "Base",
    "get_db",
    "get_db_session",
    "create_tables",
    "drop_tables",
    "check_db_connection",
    "DatabaseMetrics"
]