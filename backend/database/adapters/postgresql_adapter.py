import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, select, insert, update, delete, func, and_, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .base import DatabaseAdapter, DatabaseError, ConnectionError, ValidationError, NotFoundError, DuplicateError

logger = logging.getLogger(__name__)


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL/TimescaleDB adapter for MergerTracker"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        super().__init__(connection_config)
        self.engine = None
        self.session_factory = None
        
        # Build connection URL
        self.connection_url = self._build_connection_url(connection_config)
    
    def _build_connection_url(self, config: Dict[str, Any]) -> str:
        """Build PostgreSQL connection URL from config"""
        host = config.get('host', 'localhost')
        port = config.get('port', 5432)
        database = config.get('database', 'mergertracker')
        username = config.get('username', 'postgres')
        password = config.get('password', '')
        
        # Use asyncpg driver for async operations
        return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
    
    async def connect(self) -> bool:
        """Establish connection to PostgreSQL"""
        try:
            self.engine = create_async_engine(
                self.connection_url,
                pool_size=self.connection_config.get('pool_size', 10),
                max_overflow=self.connection_config.get('max_overflow', 20),
                pool_timeout=self.connection_config.get('pool_timeout', 30),
                pool_recycle=self.connection_config.get('pool_recycle', 3600),
                echo=self.connection_config.get('echo', False)
            )
            
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            logger.info("Successfully connected to PostgreSQL database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise ConnectionError(f"Database connection failed: {e}")
    
    async def disconnect(self) -> bool:
        """Close database connection"""
        try:
            if self.engine:
                await self.engine.dispose()
                self.engine = None
                self.session_factory = None
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from database: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.session_factory() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    # Deal operations
    async def create_deal(self, deal_data: Dict[str, Any]) -> str:
        """Create a new M&A deal record"""
        try:
            async with self.session_factory() as session:
                # Use upsert to handle duplicates
                stmt = pg_insert(text("deals")).values(deal_data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['deal_id'],
                    set_=dict(
                        deal_status=stmt.excluded.deal_status,
                        deal_value=stmt.excluded.deal_value,
                        last_updated=func.now()
                    )
                )
                
                result = await session.execute(stmt)
                await session.commit()
                
                return deal_data.get('deal_id')
                
        except IntegrityError as e:
            raise DuplicateError(f"Deal already exists: {e}")
        except Exception as e:
            logger.error(f"Error creating deal: {e}")
            raise DatabaseError(f"Failed to create deal: {e}")
    
    async def get_deal(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """Get a deal by ID"""
        try:
            async with self.session_factory() as session:
                query = text("""
                    SELECT d.*, 
                           t.company_name as target_name,
                           a.company_name as acquirer_name
                    FROM deals d
                    LEFT JOIN companies t ON d.target_company = t.company_id
                    LEFT JOIN companies a ON d.acquirer_company = a.company_id
                    WHERE d.deal_id = :deal_id
                """)
                
                result = await session.execute(query, {'deal_id': deal_id})
                row = result.fetchone()
                
                if row:
                    return dict(row._mapping)
                return None
                
        except Exception as e:
            logger.error(f"Error getting deal {deal_id}: {e}")
            raise DatabaseError(f"Failed to get deal: {e}")
    
    async def update_deal(self, deal_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing deal"""
        try:
            async with self.session_factory() as session:
                update_data['last_updated'] = datetime.utcnow()
                
                query = text("""
                    UPDATE deals 
                    SET deal_status = COALESCE(:deal_status, deal_status),
                        deal_value = COALESCE(:deal_value, deal_value),
                        deal_value_currency = COALESCE(:deal_value_currency, deal_value_currency),
                        expected_completion_date = COALESCE(:expected_completion_date, expected_completion_date),
                        actual_completion_date = COALESCE(:actual_completion_date, actual_completion_date),
                        last_updated = :last_updated
                    WHERE deal_id = :deal_id
                """)
                
                update_data['deal_id'] = deal_id
                result = await session.execute(query, update_data)
                await session.commit()
                
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating deal {deal_id}: {e}")
            raise DatabaseError(f"Failed to update deal: {e}")
    
    async def delete_deal(self, deal_id: str) -> bool:
        """Delete a deal"""
        try:
            async with self.session_factory() as session:
                query = text("DELETE FROM deals WHERE deal_id = :deal_id")
                result = await session.execute(query, {'deal_id': deal_id})
                await session.commit()
                
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error deleting deal {deal_id}: {e}")
            raise DatabaseError(f"Failed to delete deal: {e}")
    
    async def list_deals(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_date",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """List deals with filtering and pagination"""
        try:
            async with self.session_factory() as session:
                # Build dynamic query
                where_clauses = []
                params = {'limit': limit, 'offset': offset}
                
                if filters:
                    if filters.get('deal_type'):
                        where_clauses.append("deal_type = :deal_type")
                        params['deal_type'] = filters['deal_type']
                    
                    if filters.get('industry_sector'):
                        where_clauses.append("industry_sector = :industry_sector")
                        params['industry_sector'] = filters['industry_sector']
                    
                    if filters.get('deal_value_min'):
                        where_clauses.append("deal_value >= :deal_value_min")
                        params['deal_value_min'] = filters['deal_value_min']
                    
                    if filters.get('deal_value_max'):
                        where_clauses.append("deal_value <= :deal_value_max")
                        params['deal_value_max'] = filters['deal_value_max']
                    
                    if filters.get('date_from'):
                        where_clauses.append("announcement_date >= :date_from")
                        params['date_from'] = filters['date_from']
                    
                    if filters.get('date_to'):
                        where_clauses.append("announcement_date <= :date_to")
                        params['date_to'] = filters['date_to']
                
                where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
                order_clause = f"ORDER BY {sort_by} {sort_order.upper()}"
                
                query = text(f"""
                    SELECT d.*, 
                           t.company_name as target_name,
                           a.company_name as acquirer_name
                    FROM deals d
                    LEFT JOIN companies t ON d.target_company = t.company_id
                    LEFT JOIN companies a ON d.acquirer_company = a.company_id
                    WHERE {where_clause}
                    {order_clause}
                    LIMIT :limit OFFSET :offset
                """)
                
                result = await session.execute(query, params)
                rows = result.fetchall()
                
                return [dict(row._mapping) for row in rows]
                
        except Exception as e:
            logger.error(f"Error listing deals: {e}")
            raise DatabaseError(f"Failed to list deals: {e}")
    
    # Company operations
    async def create_company(self, company_data: Dict[str, Any]) -> str:
        """Create a new company record"""
        try:
            async with self.session_factory() as session:
                stmt = pg_insert(text("companies")).values(company_data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['company_id'],
                    set_=dict(
                        market_cap=stmt.excluded.market_cap,
                        revenue=stmt.excluded.revenue,
                        employees=stmt.excluded.employees,
                        last_updated=func.now()
                    )
                )
                
                await session.execute(stmt)
                await session.commit()
                
                return company_data.get('company_id')
                
        except Exception as e:
            logger.error(f"Error creating company: {e}")
            raise DatabaseError(f"Failed to create company: {e}")
    
    async def get_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get a company by ID"""
        try:
            async with self.session_factory() as session:
                query = text("SELECT * FROM companies WHERE company_id = :company_id")
                result = await session.execute(query, {'company_id': company_id})
                row = result.fetchone()
                
                if row:
                    return dict(row._mapping)
                return None
                
        except Exception as e:
            logger.error(f"Error getting company {company_id}: {e}")
            raise DatabaseError(f"Failed to get company: {e}")
    
    async def update_company(self, company_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing company"""
        try:
            async with self.session_factory() as session:
                update_data['last_updated'] = datetime.utcnow()
                update_data['company_id'] = company_id
                
                # Build dynamic update query
                set_clauses = []
                for key in update_data.keys():
                    if key != 'company_id':
                        set_clauses.append(f"{key} = COALESCE(:{key}, {key})")
                
                set_clause = ", ".join(set_clauses)
                
                query = text(f"""
                    UPDATE companies 
                    SET {set_clause}
                    WHERE company_id = :company_id
                """)
                
                result = await session.execute(query, update_data)
                await session.commit()
                
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating company {company_id}: {e}")
            raise DatabaseError(f"Failed to update company: {e}")
    
    async def delete_company(self, company_id: str) -> bool:
        """Delete a company"""
        try:
            async with self.session_factory() as session:
                query = text("DELETE FROM companies WHERE company_id = :company_id")
                result = await session.execute(query, {'company_id': company_id})
                await session.commit()
                
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error deleting company {company_id}: {e}")
            raise DatabaseError(f"Failed to delete company: {e}")
    
    async def list_companies(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List companies with filtering and pagination"""
        try:
            async with self.session_factory() as session:
                where_clauses = []
                params = {'limit': limit, 'offset': offset}
                
                if filters:
                    if filters.get('industry'):
                        where_clauses.append("industry ILIKE :industry")
                        params['industry'] = f"%{filters['industry']}%"
                    
                    if filters.get('sector'):
                        where_clauses.append("sector ILIKE :sector")
                        params['sector'] = f"%{filters['sector']}%"
                    
                    if filters.get('exchange'):
                        where_clauses.append("exchange = :exchange")
                        params['exchange'] = filters['exchange']
                
                where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                query = text(f"""
                    SELECT * FROM companies 
                    WHERE {where_clause}
                    ORDER BY company_name 
                    LIMIT :limit OFFSET :offset
                """)
                
                result = await session.execute(query, params)
                rows = result.fetchall()
                
                return [dict(row._mapping) for row in rows]
                
        except Exception as e:
            logger.error(f"Error listing companies: {e}")
            raise DatabaseError(f"Failed to list companies: {e}")
    
    # News article operations
    async def create_article(self, article_data: Dict[str, Any]) -> str:
        """Create a new news article record"""
        try:
            async with self.session_factory() as session:
                stmt = pg_insert(text("news_articles")).values(article_data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['url'],
                    set_=dict(
                        content=stmt.excluded.content,
                        summary=stmt.excluded.summary,
                        scraped_date=func.now()
                    )
                )
                
                result = await session.execute(stmt)
                await session.commit()
                
                return article_data.get('url')
                
        except Exception as e:
            logger.error(f"Error creating article: {e}")
            raise DatabaseError(f"Failed to create article: {e}")
    
    async def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Get an article by ID"""
        try:
            async with self.session_factory() as session:
                query = text("SELECT * FROM news_articles WHERE url = :article_id OR id = :article_id")
                result = await session.execute(query, {'article_id': article_id})
                row = result.fetchone()
                
                if row:
                    return dict(row._mapping)
                return None
                
        except Exception as e:
            logger.error(f"Error getting article {article_id}: {e}")
            raise DatabaseError(f"Failed to get article: {e}")
    
    async def list_articles(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List articles with filtering and pagination"""
        try:
            async with self.session_factory() as session:
                where_clauses = []
                params = {'limit': limit, 'offset': offset}
                
                if filters:
                    if filters.get('source'):
                        where_clauses.append("source = :source")
                        params['source'] = filters['source']
                    
                    if filters.get('date_from'):
                        where_clauses.append("published_date >= :date_from")
                        params['date_from'] = filters['date_from']
                    
                    if filters.get('date_to'):
                        where_clauses.append("published_date <= :date_to")
                        params['date_to'] = filters['date_to']
                
                where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                query = text(f"""
                    SELECT * FROM news_articles 
                    WHERE {where_clause}
                    ORDER BY published_date DESC 
                    LIMIT :limit OFFSET :offset
                """)
                
                result = await session.execute(query, params)
                rows = result.fetchall()
                
                return [dict(row._mapping) for row in rows]
                
        except Exception as e:
            logger.error(f"Error listing articles: {e}")
            raise DatabaseError(f"Failed to list articles: {e}")
    
    # Search operations
    async def search_deals(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search deals using full-text search"""
        try:
            async with self.session_factory() as session:
                # Use PostgreSQL full-text search
                search_query = text("""
                    SELECT d.*, 
                           t.company_name as target_name,
                           a.company_name as acquirer_name,
                           ts_rank(to_tsvector('english', 
                               COALESCE(d.target_company, '') || ' ' || 
                               COALESCE(d.acquirer_company, '') || ' ' ||
                               COALESCE(d.industry_sector, '')
                           ), plainto_tsquery('english', :query)) as rank
                    FROM deals d
                    LEFT JOIN companies t ON d.target_company = t.company_id
                    LEFT JOIN companies a ON d.acquirer_company = a.company_id
                    WHERE to_tsvector('english', 
                        COALESCE(d.target_company, '') || ' ' || 
                        COALESCE(d.acquirer_company, '') || ' ' ||
                        COALESCE(d.industry_sector, '')
                    ) @@ plainto_tsquery('english', :query)
                    ORDER BY rank DESC
                    LIMIT :limit
                """)
                
                result = await session.execute(search_query, {'query': query, 'limit': limit})
                rows = result.fetchall()
                
                return [dict(row._mapping) for row in rows]
                
        except Exception as e:
            logger.error(f"Error searching deals: {e}")
            raise DatabaseError(f"Failed to search deals: {e}")
    
    async def search_companies(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search companies using full-text search"""
        try:
            async with self.session_factory() as session:
                search_query = text("""
                    SELECT *,
                           ts_rank(to_tsvector('english', 
                               COALESCE(company_name, '') || ' ' || 
                               COALESCE(industry, '') || ' ' ||
                               COALESCE(sector, '')
                           ), plainto_tsquery('english', :query)) as rank
                    FROM companies
                    WHERE to_tsvector('english', 
                        COALESCE(company_name, '') || ' ' || 
                        COALESCE(industry, '') || ' ' ||
                        COALESCE(sector, '')
                    ) @@ plainto_tsquery('english', :query)
                    ORDER BY rank DESC
                    LIMIT :limit
                """)
                
                result = await session.execute(search_query, {'query': query, 'limit': limit})
                rows = result.fetchall()
                
                return [dict(row._mapping) for row in rows]
                
        except Exception as e:
            logger.error(f"Error searching companies: {e}")
            raise DatabaseError(f"Failed to search companies: {e}")
    
    # Analytics operations
    async def get_deal_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        group_by: str = "month"
    ) -> Dict[str, Any]:
        """Get deal analytics and trends"""
        try:
            async with self.session_factory() as session:
                # Build date grouping based on parameter
                if group_by == "day":
                    date_trunc = "day"
                elif group_by == "week":
                    date_trunc = "week"
                elif group_by == "month":
                    date_trunc = "month"
                else:
                    date_trunc = "quarter"
                
                params = {}
                where_conditions = []
                
                if date_from:
                    where_conditions.append("announcement_date >= :date_from")
                    params['date_from'] = date_from
                
                if date_to:
                    where_conditions.append("announcement_date <= :date_to")
                    params['date_to'] = date_to
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                analytics_query = text(f"""
                    SELECT 
                        date_trunc('{date_trunc}', announcement_date) as period,
                        COUNT(*) as deal_count,
                        SUM(deal_value) as total_value,
                        AVG(deal_value) as avg_value,
                        MAX(deal_value) as max_value,
                        COUNT(DISTINCT industry_sector) as industry_count
                    FROM deals 
                    WHERE {where_clause} AND announcement_date IS NOT NULL
                    GROUP BY period
                    ORDER BY period DESC
                """)
                
                result = await session.execute(analytics_query, params)
                rows = result.fetchall()
                
                return {
                    'trends': [dict(row._mapping) for row in rows],
                    'summary': {
                        'total_deals': sum(row.deal_count for row in rows),
                        'total_value': sum(row.total_value or 0 for row in rows),
                        'avg_deal_size': sum(row.avg_value or 0 for row in rows) / len(rows) if rows else 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting deal analytics: {e}")
            raise DatabaseError(f"Failed to get analytics: {e}")
    
    async def get_industry_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get industry-wise deal analytics"""
        try:
            async with self.session_factory() as session:
                params = {}
                where_conditions = []
                
                if date_from:
                    where_conditions.append("announcement_date >= :date_from")
                    params['date_from'] = date_from
                
                if date_to:
                    where_conditions.append("announcement_date <= :date_to")
                    params['date_to'] = date_to
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                industry_query = text(f"""
                    SELECT 
                        COALESCE(industry_sector, 'Unknown') as industry,
                        COUNT(*) as deal_count,
                        SUM(deal_value) as total_value,
                        AVG(deal_value) as avg_value
                    FROM deals 
                    WHERE {where_clause}
                    GROUP BY industry_sector
                    ORDER BY deal_count DESC
                """)
                
                result = await session.execute(industry_query, params)
                rows = result.fetchall()
                
                return {
                    'industries': [dict(row._mapping) for row in rows]
                }
                
        except Exception as e:
            logger.error(f"Error getting industry analytics: {e}")
            raise DatabaseError(f"Failed to get industry analytics: {e}")
    
    # Migration and maintenance operations
    async def run_migrations(self, migration_files: List[str]) -> bool:
        """Run database migrations"""
        try:
            async with self.engine.begin() as conn:
                # Create migrations table if it doesn't exist
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version VARCHAR(255) PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                for migration_file in migration_files:
                    # Check if migration already applied
                    result = await conn.execute(
                        text("SELECT 1 FROM schema_migrations WHERE version = :version"),
                        {'version': migration_file}
                    )
                    
                    if not result.fetchone():
                        # Read and execute migration
                        with open(migration_file, 'r') as f:
                            migration_sql = f.read()
                        
                        await conn.execute(text(migration_sql))
                        
                        # Record migration
                        await conn.execute(
                            text("INSERT INTO schema_migrations (version) VALUES (:version)"),
                            {'version': migration_file}
                        )
                        
                        logger.info(f"Applied migration: {migration_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error running migrations: {e}")
            raise DatabaseError(f"Migration failed: {e}")
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        try:
            async with self.session_factory() as session:
                query = text("SELECT * FROM schema_migrations ORDER BY applied_at DESC")
                result = await session.execute(query)
                rows = result.fetchall()
                
                return {
                    'applied_migrations': [dict(row._mapping) for row in rows],
                    'migration_count': len(rows)
                }
                
        except Exception as e:
            logger.error(f"Error getting migration status: {e}")
            return {'applied_migrations': [], 'migration_count': 0}
    
    async def backup_data(self, backup_path: str) -> bool:
        """Create a backup using pg_dump"""
        import subprocess
        import os
        
        try:
            # Extract connection info for pg_dump
            config = self.connection_config
            
            env = os.environ.copy()
            env['PGPASSWORD'] = config.get('password', '')
            
            cmd = [
                'pg_dump',
                '-h', config.get('host', 'localhost'),
                '-p', str(config.get('port', 5432)),
                '-U', config.get('username', 'postgres'),
                '-d', config.get('database', 'mergertracker'),
                '-f', backup_path,
                '--verbose'
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Database backup created successfully: {backup_path}")
                return True
            else:
                logger.error(f"Backup failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            async with self.session_factory() as session:
                stats_query = text("""
                    SELECT 
                        'deals' as table_name,
                        COUNT(*) as row_count,
                        pg_size_pretty(pg_total_relation_size('deals')) as size
                    FROM deals
                    UNION ALL
                    SELECT 
                        'companies' as table_name,
                        COUNT(*) as row_count,
                        pg_size_pretty(pg_total_relation_size('companies')) as size
                    FROM companies
                    UNION ALL
                    SELECT 
                        'news_articles' as table_name,
                        COUNT(*) as row_count,
                        pg_size_pretty(pg_total_relation_size('news_articles')) as size
                    FROM news_articles
                """)
                
                result = await session.execute(stats_query)
                rows = result.fetchall()
                
                return {
                    'table_stats': [dict(row._mapping) for row in rows],
                    'connection_info': {
                        'adapter': 'postgresql',
                        'host': self.connection_config.get('host'),
                        'database': self.connection_config.get('database'),
                        'connected': await self.health_check()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            raise DatabaseError(f"Failed to get database stats: {e}")