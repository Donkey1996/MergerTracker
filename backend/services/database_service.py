"""
Database service layer for MergerTracker

This service provides a high-level interface to database operations
and handles the database adapter initialization and management.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from ..database.factory import DatabaseFactory, get_database_config_from_env
from ..database.adapters.base import DatabaseAdapter, DatabaseError

logger = logging.getLogger(__name__)


class DatabaseService:
    """High-level database service for MergerTracker"""
    
    def __init__(self, adapter: DatabaseAdapter):
        self.adapter = adapter
        self._connected = False
    
    async def initialize(self) -> bool:
        """Initialize the database service"""
        try:
            await self.adapter.connect()
            self._connected = True
            logger.info("Database service initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown the database service"""
        try:
            await self.adapter.disconnect()
            self._connected = False
            logger.info("Database service shutdown completed")
            return True
        except Exception as e:
            logger.error(f"Error during database service shutdown: {e}")
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if database service is connected"""
        return self._connected
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            is_healthy = await self.adapter.health_check()
            stats = await self.adapter.get_database_stats()
            
            return {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'connected': self._connected,
                'adapter_type': self.adapter.__class__.__name__,
                'stats': stats
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'error',
                'connected': False,
                'error': str(e)
            }
    
    # Deal management methods
    async def create_deal(self, deal_data: Dict[str, Any]) -> str:
        """Create a new M&A deal"""
        try:
            # Add metadata
            deal_data['created_date'] = datetime.utcnow()
            deal_data['last_updated'] = datetime.utcnow()
            
            return await self.adapter.create_deal(deal_data)
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error in create_deal service: {e}")
            raise DatabaseError(f"Failed to create deal: {e}")
    
    async def get_deal(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """Get a deal by ID"""
        return await self.adapter.get_deal(deal_id)
    
    async def update_deal(self, deal_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing deal"""
        return await self.adapter.update_deal(deal_id, update_data)
    
    async def delete_deal(self, deal_id: str) -> bool:
        """Delete a deal"""
        return await self.adapter.delete_deal(deal_id)
    
    async def list_deals(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "created_date",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """List deals with pagination"""
        offset = (page - 1) * page_size
        
        deals = await self.adapter.list_deals(
            filters=filters,
            limit=page_size,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return {
            'deals': deals,
            'page': page,
            'page_size': page_size,
            'has_more': len(deals) == page_size
        }
    
    async def search_deals(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search deals by text query"""
        return await self.adapter.search_deals(query, filters, limit)
    
    # Company management methods
    async def create_company(self, company_data: Dict[str, Any]) -> str:
        """Create a new company"""
        try:
            company_data['last_updated'] = datetime.utcnow()
            return await self.adapter.create_company(company_data)
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error in create_company service: {e}")
            raise DatabaseError(f"Failed to create company: {e}")
    
    async def get_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get a company by ID"""
        return await self.adapter.get_company(company_id)
    
    async def update_company(self, company_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing company"""
        return await self.adapter.update_company(company_id, update_data)
    
    async def delete_company(self, company_id: str) -> bool:
        """Delete a company"""
        return await self.adapter.delete_company(company_id)
    
    async def list_companies(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """List companies with pagination"""
        offset = (page - 1) * page_size
        
        companies = await self.adapter.list_companies(
            filters=filters,
            limit=page_size,
            offset=offset
        )
        
        return {
            'companies': companies,
            'page': page,
            'page_size': page_size,
            'has_more': len(companies) == page_size
        }
    
    async def search_companies(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search companies by text query"""
        return await self.adapter.search_companies(query, filters, limit)
    
    # News article methods
    async def create_article(self, article_data: Dict[str, Any]) -> str:
        """Create a new news article"""
        try:
            article_data['scraped_date'] = datetime.utcnow()
            return await self.adapter.create_article(article_data)
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error in create_article service: {e}")
            raise DatabaseError(f"Failed to create article: {e}")
    
    async def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Get an article by ID"""
        return await self.adapter.get_article(article_id)
    
    async def list_articles(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """List articles with pagination"""
        offset = (page - 1) * page_size
        
        articles = await self.adapter.list_articles(
            filters=filters,
            limit=page_size,
            offset=offset
        )
        
        return {
            'articles': articles,
            'page': page,
            'page_size': page_size,
            'has_more': len(articles) == page_size
        }
    
    # Analytics methods
    async def get_deal_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        group_by: str = "month"
    ) -> Dict[str, Any]:
        """Get deal analytics and trends"""
        return await self.adapter.get_deal_analytics(date_from, date_to, group_by)
    
    async def get_industry_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get industry-wise deal analytics"""
        return await self.adapter.get_industry_analytics(date_from, date_to)
    
    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary statistics"""
        try:
            # Get recent deals
            recent_deals = await self.list_deals(page_size=5, sort_by="created_date")
            
            # Get deal analytics for the last 6 months
            from datetime import datetime, timedelta
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            analytics = await self.get_deal_analytics(date_from=six_months_ago)
            
            # Get industry breakdown
            industry_stats = await self.get_industry_analytics(date_from=six_months_ago)
            
            return {
                'recent_deals': recent_deals['deals'],
                'analytics': analytics,
                'industry_stats': industry_stats,
                'summary': {
                    'total_deals': analytics['summary']['total_deals'],
                    'total_value': analytics['summary']['total_value'],
                    'avg_deal_size': analytics['summary']['avg_deal_size']
                }
            }
        except Exception as e:
            logger.error(f"Error getting dashboard summary: {e}")
            raise DatabaseError(f"Failed to get dashboard summary: {e}")
    
    # Maintenance methods
    async def run_migrations(self, migration_files: List[str]) -> bool:
        """Run database migrations"""
        return await self.adapter.run_migrations(migration_files)
    
    async def create_backup(self, backup_path: str) -> bool:
        """Create a database backup"""
        return await self.adapter.backup_data(backup_path)
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get migration status"""
        return await self.adapter.get_migration_status()


# Singleton database service instance
_database_service: Optional[DatabaseService] = None


async def get_database_service() -> DatabaseService:
    """Get the global database service instance"""
    global _database_service
    
    if _database_service is None:
        config = get_database_config_from_env()
        adapter = DatabaseFactory.create_adapter(config)
        _database_service = DatabaseService(adapter)
        await _database_service.initialize()
    
    return _database_service


@asynccontextmanager
async def database_session():
    """Context manager for database operations"""
    service = await get_database_service()
    try:
        yield service
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise


async def initialize_database_service() -> DatabaseService:
    """Initialize the database service (for application startup)"""
    return await get_database_service()


async def shutdown_database_service():
    """Shutdown the database service (for application shutdown)"""
    global _database_service
    
    if _database_service:
        await _database_service.shutdown()
        _database_service = None