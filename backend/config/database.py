from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
import structlog

from .settings import settings

logger = structlog.get_logger(__name__)

# Create async engine for PostgreSQL with TimescaleDB
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=30,
    echo=settings.ENVIRONMENT == "development",
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database and create tables"""
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they are registered
            from models import deals, companies, news, users  # noqa
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
            # Enable TimescaleDB extension and create hypertables
            await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
            
            # Create hypertables for time-series data
            try:
                await conn.execute(
                    "SELECT create_hypertable('deals', 'announcement_date', if_not_exists => TRUE);"
                )
                await conn.execute(
                    "SELECT create_hypertable('news_articles', 'publish_date', if_not_exists => TRUE);"
                )
            except Exception as e:
                logger.warning("Failed to create hypertables", error=str(e))
                
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")