from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        self.connection_config = connection_config
        self.connection = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the database"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Close database connection"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if database connection is healthy"""
        pass
    
    # Deal operations
    @abstractmethod
    async def create_deal(self, deal_data: Dict[str, Any]) -> str:
        """Create a new M&A deal record"""
        pass
    
    @abstractmethod
    async def get_deal(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """Get a deal by ID"""
        pass
    
    @abstractmethod
    async def update_deal(self, deal_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing deal"""
        pass
    
    @abstractmethod
    async def delete_deal(self, deal_id: str) -> bool:
        """Delete a deal"""
        pass
    
    @abstractmethod
    async def list_deals(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_date",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """List deals with filtering and pagination"""
        pass
    
    # Company operations
    @abstractmethod
    async def create_company(self, company_data: Dict[str, Any]) -> str:
        """Create a new company record"""
        pass
    
    @abstractmethod
    async def get_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get a company by ID"""
        pass
    
    @abstractmethod
    async def update_company(self, company_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing company"""
        pass
    
    @abstractmethod
    async def delete_company(self, company_id: str) -> bool:
        """Delete a company"""
        pass
    
    @abstractmethod
    async def list_companies(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List companies with filtering and pagination"""
        pass
    
    # News article operations
    @abstractmethod
    async def create_article(self, article_data: Dict[str, Any]) -> str:
        """Create a new news article record"""
        pass
    
    @abstractmethod
    async def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Get an article by ID"""
        pass
    
    @abstractmethod
    async def list_articles(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List articles with filtering and pagination"""
        pass
    
    # Search operations
    @abstractmethod
    async def search_deals(
        self, 
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search deals by text query"""
        pass
    
    @abstractmethod
    async def search_companies(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search companies by text query"""
        pass
    
    # Analytics operations
    @abstractmethod
    async def get_deal_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        group_by: str = "month"
    ) -> Dict[str, Any]:
        """Get deal analytics and trends"""
        pass
    
    @abstractmethod
    async def get_industry_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get industry-wise deal analytics"""
        pass
    
    # Migration operations
    @abstractmethod
    async def run_migrations(self, migration_files: List[str]) -> bool:
        """Run database migrations"""
        pass
    
    @abstractmethod
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        pass
    
    # Backup and maintenance
    @abstractmethod
    async def backup_data(self, backup_path: str) -> bool:
        """Create a backup of the database"""
        pass
    
    @abstractmethod
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics and health metrics"""
        pass


class DatabaseConfig(BaseModel):
    """Configuration model for database connections"""
    
    adapter_type: str  # 'postgresql', 'supabase', 'firebase'
    connection_params: Dict[str, Any]
    pool_size: Optional[int] = 10
    max_overflow: Optional[int] = 20
    pool_timeout: Optional[int] = 30
    pool_recycle: Optional[int] = 3600
    echo: Optional[bool] = False
    
    class Config:
        extra = "allow"


class DatabaseError(Exception):
    """Base exception for database operations"""
    pass


class ConnectionError(DatabaseError):
    """Exception raised when database connection fails"""
    pass


class ValidationError(DatabaseError):
    """Exception raised when data validation fails"""
    pass


class NotFoundError(DatabaseError):
    """Exception raised when requested resource is not found"""
    pass


class DuplicateError(DatabaseError):
    """Exception raised when trying to create duplicate resource"""
    pass