"""
Base database adapter interface and abstract classes
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
from datetime import datetime
from uuid import UUID
import asyncio
from contextlib import asynccontextmanager

from pydantic import BaseModel


class DatabaseSession(ABC):
    """Abstract database session for transaction management"""
    
    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction"""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the session"""
        pass


class QueryFilter(BaseModel):
    """Standard query filter for cross-database compatibility"""
    field: str
    operator: str  # eq, ne, gt, gte, lt, lte, in, not_in, contains, icontains
    value: Any


class QueryOptions(BaseModel):
    """Standard query options for cross-database compatibility"""
    filters: List[QueryFilter] = []
    order_by: Optional[List[str]] = None
    limit: Optional[int] = None
    offset: Optional[int] = 0
    include_relations: List[str] = []


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._connection = None
    
    @abstractmethod
    async def connect(self) -> None:
        """Initialize database connection"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check database connectivity and health"""
        pass
    
    @abstractmethod
    async def migrate(self) -> None:
        """Run database migrations"""
        pass
    
    @abstractmethod
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[DatabaseSession, None]:
        """Get database session with transaction management"""
        pass
    
    # CRUD Operations
    @abstractmethod
    async def create(
        self,
        session: DatabaseSession,
        table: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new record"""
        pass
    
    @abstractmethod
    async def get_by_id(
        self,
        session: DatabaseSession,
        table: str,
        record_id: Union[str, UUID, int],
        include_relations: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get record by ID"""
        pass
    
    @abstractmethod
    async def query(
        self,
        session: DatabaseSession,
        table: str,
        options: QueryOptions
    ) -> List[Dict[str, Any]]:
        """Query records with filters and options"""
        pass
    
    @abstractmethod
    async def update(
        self,
        session: DatabaseSession,
        table: str,
        record_id: Union[str, UUID, int],
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a record"""
        pass
    
    @abstractmethod
    async def delete(
        self,
        session: DatabaseSession,
        table: str,
        record_id: Union[str, UUID, int]
    ) -> bool:
        """Delete a record"""
        pass
    
    @abstractmethod
    async def count(
        self,
        session: DatabaseSession,
        table: str,
        filters: List[QueryFilter] = None
    ) -> int:
        """Count records matching filters"""
        pass
    
    # Bulk Operations
    @abstractmethod
    async def bulk_create(
        self,
        session: DatabaseSession,
        table: str,
        data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create multiple records"""
        pass
    
    @abstractmethod
    async def bulk_update(
        self,
        session: DatabaseSession,
        table: str,
        updates: List[Dict[str, Any]]  # Each dict should include ID and update data
    ) -> List[Dict[str, Any]]:
        """Update multiple records"""
        pass
    
    # Time-series specific operations (for TimescaleDB and similar)
    @abstractmethod
    async def time_bucket_query(
        self,
        session: DatabaseSession,
        table: str,
        time_column: str,
        bucket_size: str,  # '1 hour', '1 day', etc.
        aggregations: Dict[str, str],  # column: function (count, avg, sum, etc.)
        filters: List[QueryFilter] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Time-bucketed aggregation query for time-series data"""
        pass
    
    # Search operations
    @abstractmethod
    async def full_text_search(
        self,
        session: DatabaseSession,
        table: str,
        search_fields: List[str],
        query: str,
        options: QueryOptions = None
    ) -> List[Dict[str, Any]]:
        """Full-text search across specified fields"""
        pass


class DatabaseFactory:
    """Factory for creating database adapters"""
    
    _adapters = {}
    
    @classmethod
    def register_adapter(cls, name: str, adapter_class: type):
        """Register a database adapter"""
        cls._adapters[name] = adapter_class
    
    @classmethod
    def create_adapter(cls, name: str, config: Dict[str, Any]) -> DatabaseAdapter:
        """Create a database adapter instance"""
        if name not in cls._adapters:
            raise ValueError(f"Unknown database adapter: {name}")
        
        return cls._adapters[name](config)
    
    @classmethod
    def list_adapters(cls) -> List[str]:
        """List available database adapters"""
        return list(cls._adapters.keys())