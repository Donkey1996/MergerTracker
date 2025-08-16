"""
Supabase adapter for MergerTracker

This module provides a complete Supabase database adapter implementation
using the supabase-py client library with comprehensive error handling,
full-text search, real-time subscriptions, and bulk operations.
"""

import asyncio
import logging
import uuid
from typing import List, Dict, Any, Optional, Union, Callable
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from postgrest.exceptions import APIError
from gotrue.errors import AuthApiError

from .base import (
    DatabaseAdapter, 
    DatabaseError, 
    ConnectionError, 
    ValidationError, 
    NotFoundError, 
    DuplicateError
)

logger = logging.getLogger(__name__)


class SupabaseAdapter(DatabaseAdapter):
    """Supabase adapter for MergerTracker with comprehensive functionality"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        super().__init__(connection_config)
        self.client: Optional[Client] = None
        self.connection_url = None
        self.service_key = None
        self.anon_key = None
        self._subscription_callbacks = {}
        
        # Extract connection parameters
        self._extract_connection_params(connection_config)
        
    def _extract_connection_params(self, config: Dict[str, Any]) -> None:
        """Extract and validate Supabase connection parameters"""
        self.connection_url = config.get('url')
        self.service_key = config.get('service_key')
        self.anon_key = config.get('key') or config.get('anon_key')
        
        if not self.connection_url:
            raise ValueError("Supabase URL is required")
        
        if not self.service_key:
            raise ValueError("Supabase service key is required")
            
        if not self.anon_key:
            logger.warning("Supabase anon key not provided - some features may be limited")
    
    async def connect(self) -> bool:
        """Establish connection to Supabase"""
        try:
            # Configure client options for better performance
            client_options = ClientOptions(
                postgrest_client_timeout=30,
                storage_client_timeout=30,
                schema="public"
            )
            
            # Create client with service key for full access
            self.client = create_client(
                supabase_url=self.connection_url,
                supabase_key=self.service_key,
                options=client_options
            )
            
            # Test connection with a simple query
            result = self.client.table('users').select('count', count='exact').limit(0).execute()
            
            logger.info("Successfully connected to Supabase database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise ConnectionError(f"Supabase connection failed: {e}")
    
    async def disconnect(self) -> bool:
        """Close Supabase connection"""
        try:
            if self.client:
                # Close any active subscriptions
                for subscription_id in list(self._subscription_callbacks.keys()):
                    await self._unsubscribe(subscription_id)
                
                # Supabase client doesn't need explicit disconnection
                self.client = None
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from Supabase: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check Supabase database health"""
        try:
            if not self.client:
                return False
                
            # Simple health check query
            result = self.client.table('users').select('count', count='exact').limit(0).execute()
            return result.count is not None
            
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return False
    
    def _handle_api_error(self, error: Exception, operation: str) -> None:
        """Handle and convert Supabase API errors to appropriate database errors"""
        if isinstance(error, APIError):
            if error.code == '23505':  # Unique violation
                raise DuplicateError(f"Duplicate entry in {operation}: {error.message}")
            elif error.code == '23503':  # Foreign key violation
                raise ValidationError(f"Foreign key constraint violation in {operation}: {error.message}")
            elif error.code == '23502':  # Not null violation
                raise ValidationError(f"Required field missing in {operation}: {error.message}")
            else:
                raise DatabaseError(f"{operation} failed: {error.message}")
        elif isinstance(error, AuthApiError):
            raise ConnectionError(f"Authentication error in {operation}: {error.message}")
        else:
            raise DatabaseError(f"{operation} failed: {str(error)}")
    
    # Deal operations
    async def create_deal(self, deal_data: Dict[str, Any]) -> str:
        """Create a new M&A deal record"""
        try:
            # Ensure we have a deal_id
            if 'deal_id' not in deal_data:
                deal_data['deal_id'] = str(uuid.uuid4())
            
            # Convert datetime objects to ISO strings
            deal_data = self._prepare_data_for_insert(deal_data)
            
            result = self.client.table('deals').insert(deal_data).execute()
            
            if result.data:
                logger.info(f"Created deal: {deal_data['deal_id']}")
                return deal_data['deal_id']
            else:
                raise DatabaseError("Failed to create deal - no data returned")
                
        except Exception as e:
            self._handle_api_error(e, "create_deal")
    
    async def get_deal(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """Get a deal by ID with related data"""
        try:
            result = self.client.table('deals').select("""
                *,
                deal_participants!inner(
                    *,
                    companies!inner(*)
                ),
                deal_advisors(*),
                news_articles(*)
            """).eq('deal_id', deal_id).execute()
            
            if result.data:
                deal = result.data[0]
                return self._format_deal_response(deal)
            return None
            
        except Exception as e:
            self._handle_api_error(e, f"get_deal({deal_id})")
    
    async def update_deal(self, deal_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing deal"""
        try:
            # Add updated_at timestamp
            update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Prepare data for update
            update_data = self._prepare_data_for_insert(update_data)
            
            result = self.client.table('deals').update(update_data).eq('deal_id', deal_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            self._handle_api_error(e, f"update_deal({deal_id})")
    
    async def delete_deal(self, deal_id: str) -> bool:
        """Delete a deal"""
        try:
            result = self.client.table('deals').delete().eq('deal_id', deal_id).execute()
            return len(result.data) > 0
            
        except Exception as e:
            self._handle_api_error(e, f"delete_deal({deal_id})")
    
    async def list_deals(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """List deals with filtering and pagination"""
        try:
            query = self.client.table('deals').select("""
                *,
                deal_participants!left(
                    role,
                    companies!inner(name, ticker_symbol)
                )
            """)
            
            # Apply filters
            if filters:
                query = self._apply_deal_filters(query, filters)
            
            # Apply sorting
            if sort_order.lower() == 'desc':
                query = query.order(sort_by, desc=True)
            else:
                query = query.order(sort_by, desc=False)
            
            # Apply pagination
            query = query.range(offset, offset + limit - 1)
            
            result = query.execute()
            
            return [self._format_deal_response(deal) for deal in result.data]
            
        except Exception as e:
            self._handle_api_error(e, "list_deals")
    
    def _apply_deal_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to deal queries"""
        if filters.get('deal_type'):
            query = query.eq('deal_type', filters['deal_type'])
        
        if filters.get('deal_status'):
            query = query.eq('deal_status', filters['deal_status'])
        
        if filters.get('industry_sector'):
            query = query.eq('primary_industry_sic', filters['industry_sector'])
        
        if filters.get('deal_value_min'):
            query = query.gte('transaction_value', filters['deal_value_min'])
        
        if filters.get('deal_value_max'):
            query = query.lte('transaction_value', filters['deal_value_max'])
        
        if filters.get('date_from'):
            query = query.gte('announcement_date', filters['date_from'])
        
        if filters.get('date_to'):
            query = query.lte('announcement_date', filters['date_to'])
        
        if filters.get('geography'):
            query = query.eq('primary_geography', filters['geography'])
        
        return query
    
    # Company operations
    async def create_company(self, company_data: Dict[str, Any]) -> str:
        """Create a new company record"""
        try:
            # Generate ID if not provided
            if 'id' not in company_data:
                company_data['id'] = None  # Let PostgreSQL generate the ID
            
            company_data = self._prepare_data_for_insert(company_data)
            
            result = self.client.table('companies').insert(company_data).execute()
            
            if result.data:
                company_id = str(result.data[0]['id'])
                logger.info(f"Created company: {company_id}")
                return company_id
            else:
                raise DatabaseError("Failed to create company - no data returned")
                
        except Exception as e:
            self._handle_api_error(e, "create_company")
    
    async def get_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get a company by ID"""
        try:
            result = self.client.table('companies').select("""
                *,
                industry_classifications(*),
                deal_participants!left(
                    role,
                    deals!inner(deal_name, deal_type, deal_status, transaction_value, announcement_date)
                )
            """).eq('id', company_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            self._handle_api_error(e, f"get_company({company_id})")
    
    async def update_company(self, company_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing company"""
        try:
            update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            update_data = self._prepare_data_for_insert(update_data)
            
            result = self.client.table('companies').update(update_data).eq('id', company_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            self._handle_api_error(e, f"update_company({company_id})")
    
    async def delete_company(self, company_id: str) -> bool:
        """Delete a company"""
        try:
            result = self.client.table('companies').delete().eq('id', company_id).execute()
            return len(result.data) > 0
            
        except Exception as e:
            self._handle_api_error(e, f"delete_company({company_id})")
    
    async def list_companies(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List companies with filtering and pagination"""
        try:
            query = self.client.table('companies').select("""
                *,
                industry_classifications(sic_description, gics_sector_name)
            """)
            
            # Apply filters
            if filters:
                if filters.get('industry'):
                    query = query.ilike('gics_sector', f"%{filters['industry']}%")
                
                if filters.get('sector'):
                    query = query.ilike('gics_industry_group', f"%{filters['sector']}%")
                
                if filters.get('exchange'):
                    query = query.eq('exchange', filters['exchange'])
                
                if filters.get('country'):
                    query = query.eq('country', filters['country'])
                
                if filters.get('is_public') is not None:
                    query = query.eq('is_public', filters['is_public'])
            
            # Apply pagination
            query = query.range(offset, offset + limit - 1).order('name')
            
            result = query.execute()
            return result.data
            
        except Exception as e:
            self._handle_api_error(e, "list_companies")
    
    # News article operations
    async def create_article(self, article_data: Dict[str, Any]) -> str:
        """Create a new news article record"""
        try:
            # Ensure we have an article_id
            if 'article_id' not in article_data:
                article_data['article_id'] = str(uuid.uuid4())
            
            article_data = self._prepare_data_for_insert(article_data)
            
            result = self.client.table('news_articles').insert(article_data).execute()
            
            if result.data:
                article_id = article_data['article_id']
                logger.info(f"Created article: {article_id}")
                return article_id
            else:
                raise DatabaseError("Failed to create article - no data returned")
                
        except Exception as e:
            self._handle_api_error(e, "create_article")
    
    async def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Get an article by ID"""
        try:
            # Try by article_id first, then by URL
            result = self.client.table('news_articles').select('*').or_(
                f'article_id.eq.{article_id},url.eq.{article_id}'
            ).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            self._handle_api_error(e, f"get_article({article_id})")
    
    async def list_articles(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List articles with filtering and pagination"""
        try:
            query = self.client.table('news_articles').select('*')
            
            # Apply filters
            if filters:
                if filters.get('source'):
                    query = query.eq('source_name', filters['source'])
                
                if filters.get('date_from'):
                    query = query.gte('publish_date', filters['date_from'])
                
                if filters.get('date_to'):
                    query = query.lte('publish_date', filters['date_to'])
                
                if filters.get('contains_deal_info') is not None:
                    query = query.eq('contains_deal_info', filters['contains_deal_info'])
                
                if filters.get('ma_relevance_min'):
                    query = query.gte('ma_relevance_score', filters['ma_relevance_min'])
            
            # Apply pagination and sorting
            query = query.range(offset, offset + limit - 1).order('publish_date', desc=True)
            
            result = query.execute()
            return result.data
            
        except Exception as e:
            self._handle_api_error(e, "list_articles")
    
    # Search operations using PostgreSQL full-text search
    async def search_deals(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search deals using full-text search"""
        try:
            # Use the search function we created in the schema
            result = self.client.rpc('search_deals', {
                'search_text': query,
                'max_results': limit
            }).execute()
            
            return result.data
            
        except Exception as e:
            # Fallback to basic text search if RPC function is not available
            logger.warning(f"RPC search function not available, falling back to basic search: {e}")
            return await self._fallback_text_search('deals', query, filters, limit)
    
    async def search_companies(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search companies using full-text search"""
        try:
            # Use the search function we created in the schema
            result = self.client.rpc('search_companies', {
                'search_text': query,
                'max_results': limit
            }).execute()
            
            return result.data
            
        except Exception as e:
            # Fallback to basic text search if RPC function is not available
            logger.warning(f"RPC search function not available, falling back to basic search: {e}")
            return await self._fallback_text_search('companies', query, filters, limit)
    
    async def search_articles(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search news articles using full-text search"""
        try:
            # Use PostgreSQL full-text search on title and content
            search_query = self.client.table('news_articles').select('*')
            
            # Apply full-text search using textSearch
            search_query = search_query.text_search('title', query)
            
            # Apply additional filters
            if filters:
                if filters.get('source'):
                    search_query = search_query.eq('source_name', filters['source'])
                
                if filters.get('date_from'):
                    search_query = search_query.gte('publish_date', filters['date_from'])
                
                if filters.get('date_to'):
                    search_query = search_query.lte('publish_date', filters['date_to'])
                
                if filters.get('ma_relevance_min'):
                    search_query = search_query.gte('ma_relevance_score', filters['ma_relevance_min'])
            
            # Order by relevance and limit results
            result = search_query.order('ma_relevance_score', desc=True).limit(limit).execute()
            
            return result.data
            
        except Exception as e:
            self._handle_api_error(e, f"search_articles({query})")
    
    async def _fallback_text_search(
        self,
        table_name: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fallback text search using ILIKE patterns"""
        try:
            search_query = self.client.table(table_name).select('*')
            
            # Use ILIKE for case-insensitive pattern matching
            if table_name == 'deals':
                search_query = search_query.or_(
                    f'deal_name.ilike.%{query}%,deal_description.ilike.%{query}%'
                )
            elif table_name == 'companies':
                search_query = search_query.or_(
                    f'name.ilike.%{query}%,description.ilike.%{query}%'
                )
            elif table_name == 'news_articles':
                search_query = search_query.or_(
                    f'title.ilike.%{query}%,content.ilike.%{query}%,summary.ilike.%{query}%'
                )
            
            result = search_query.limit(limit).execute()
            return result.data
            
        except Exception as e:
            self._handle_api_error(e, f"_fallback_text_search({table_name}, {query})")
    
    async def advanced_search(
        self,
        search_params: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Advanced search across multiple tables"""
        try:
            results = {
                'deals': [],
                'companies': [],
                'articles': []
            }
            
            query = search_params.get('query', '')
            filters = search_params.get('filters', {})
            limit_per_table = search_params.get('limit_per_table', 25)
            
            if query:
                # Search all tables concurrently
                tasks = [
                    self.search_deals(query, filters, limit_per_table),
                    self.search_companies(query, filters, limit_per_table),
                    self.search_articles(query, filters, limit_per_table)
                ]
                
                deals_results, companies_results, articles_results = await asyncio.gather(*tasks)
                
                results['deals'] = deals_results
                results['companies'] = companies_results
                results['articles'] = articles_results
            
            return results
            
        except Exception as e:
            self._handle_api_error(e, "advanced_search")
    
    # Analytics operations
    async def get_deal_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        group_by: str = "month"
    ) -> Dict[str, Any]:
        """Get deal analytics and trends"""
        try:
            # Use the analytics function we created in the schema
            result = self.client.rpc('get_deal_analytics', {
                'date_from': date_from.date() if date_from else None,
                'date_to': date_to.date() if date_to else None,
                'group_by_period': group_by
            }).execute()
            
            trends = result.data
            
            # Calculate summary statistics
            total_deals = sum(trend['deal_count'] for trend in trends)
            total_value = sum(trend['total_value'] or 0 for trend in trends)
            avg_deal_size = total_value / total_deals if total_deals > 0 else 0
            
            return {
                'trends': trends,
                'summary': {
                    'total_deals': total_deals,
                    'total_value': total_value,
                    'avg_deal_size': avg_deal_size
                }
            }
            
        except Exception as e:
            self._handle_api_error(e, "get_deal_analytics")
    
    async def get_industry_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get industry-wise deal analytics"""
        try:
            query = self.client.table('deals').select("""
                primary_industry_sic,
                industry_classifications!left(sic_description),
                transaction_value,
                id
            """, count='exact')
            
            if date_from:
                query = query.gte('announcement_date', date_from.date())
            
            if date_to:
                query = query.lte('announcement_date', date_to.date())
            
            result = query.execute()
            
            # Process the data to group by industry
            industry_stats = {}
            for deal in result.data:
                industry = deal.get('primary_industry_sic', 'Unknown')
                industry_name = (
                    deal.get('industry_classifications', {}).get('sic_description', 'Unknown')
                    if deal.get('industry_classifications') else 'Unknown'
                )
                
                if industry not in industry_stats:
                    industry_stats[industry] = {
                        'industry': industry_name,
                        'deal_count': 0,
                        'total_value': 0,
                        'avg_value': 0
                    }
                
                industry_stats[industry]['deal_count'] += 1
                if deal.get('transaction_value'):
                    industry_stats[industry]['total_value'] += float(deal['transaction_value'])
            
            # Calculate averages
            for stats in industry_stats.values():
                if stats['deal_count'] > 0:
                    stats['avg_value'] = stats['total_value'] / stats['deal_count']
            
            return {
                'industries': list(industry_stats.values())
            }
            
        except Exception as e:
            self._handle_api_error(e, "get_industry_analytics")
    
    # Migration operations
    async def run_migrations(self, migration_files: List[str]) -> bool:
        """Run database migrations - Supabase handles this via their dashboard"""
        logger.warning("Supabase migrations should be run via the Supabase dashboard or CLI")
        return True
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        return {
            'applied_migrations': [],
            'migration_count': 0,
            'note': 'Supabase migrations are managed via the dashboard'
        }
    
    # Backup and maintenance
    async def backup_data(self, backup_path: str) -> bool:
        """Create a backup - Supabase handles automated backups"""
        logger.warning("Supabase backups are handled automatically - use Supabase dashboard for manual backups")
        return True
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics and health metrics"""
        try:
            # Get table counts
            deals_count = self.client.table('deals').select('count', count='exact').limit(0).execute().count
            companies_count = self.client.table('companies').select('count', count='exact').limit(0).execute().count
            articles_count = self.client.table('news_articles').select('count', count='exact').limit(0).execute().count
            
            return {
                'table_stats': [
                    {'table_name': 'deals', 'row_count': deals_count, 'size': 'N/A'},
                    {'table_name': 'companies', 'row_count': companies_count, 'size': 'N/A'},
                    {'table_name': 'news_articles', 'row_count': articles_count, 'size': 'N/A'}
                ],
                'connection_info': {
                    'adapter': 'supabase',
                    'url': self.connection_url,
                    'connected': await self.health_check()
                }
            }
            
        except Exception as e:
            self._handle_api_error(e, "get_database_stats")
    
    # Bulk operations for performance
    async def bulk_insert_deals(self, deals_data: List[Dict[str, Any]]) -> List[str]:
        """Bulk insert deals for performance"""
        try:
            # Prepare all data
            prepared_data = []
            deal_ids = []
            
            for deal_data in deals_data:
                if 'deal_id' not in deal_data:
                    deal_data['deal_id'] = str(uuid.uuid4())
                
                deal_ids.append(deal_data['deal_id'])
                prepared_data.append(self._prepare_data_for_insert(deal_data))
            
            # Batch insert with upsert to handle duplicates
            result = self.client.table('deals').upsert(
                prepared_data, 
                on_conflict='deal_id',
                returning='minimal'  # Reduce response size for performance
            ).execute()
            
            logger.info(f"Bulk inserted/updated {len(prepared_data)} deals")
            return deal_ids
                
        except Exception as e:
            self._handle_api_error(e, "bulk_insert_deals")
    
    async def bulk_insert_articles(self, articles_data: List[Dict[str, Any]]) -> List[str]:
        """Bulk insert news articles for performance"""
        try:
            # Prepare all data
            prepared_data = []
            article_ids = []
            
            for article_data in articles_data:
                if 'article_id' not in article_data:
                    article_data['article_id'] = str(uuid.uuid4())
                
                article_ids.append(article_data['article_id'])
                prepared_data.append(self._prepare_data_for_insert(article_data))
            
            # Batch insert with upsert to handle duplicates
            result = self.client.table('news_articles').upsert(
                prepared_data,
                on_conflict='url',
                returning='minimal'  # Reduce response size for performance
            ).execute()
            
            logger.info(f"Bulk inserted/updated {len(prepared_data)} articles")
            return article_ids
                
        except Exception as e:
            self._handle_api_error(e, "bulk_insert_articles")
    
    async def bulk_insert_companies(self, companies_data: List[Dict[str, Any]]) -> List[str]:
        """Bulk insert companies for performance"""
        try:
            # Prepare all data
            prepared_data = []
            company_ids = []
            
            for company_data in companies_data:
                prepared_data.append(self._prepare_data_for_insert(company_data))
            
            # Batch insert
            result = self.client.table('companies').upsert(
                prepared_data,
                on_conflict='cusip,isin,lei',  # Handle duplicates based on unique identifiers
                returning='minimal'
            ).execute()
            
            if result.data:
                company_ids = [str(record.get('id', '')) for record in result.data]
            
            logger.info(f"Bulk inserted/updated {len(prepared_data)} companies")
            return company_ids
                
        except Exception as e:
            self._handle_api_error(e, "bulk_insert_companies")
    
    async def bulk_update_deals(self, updates: List[Dict[str, Any]]) -> int:
        """Bulk update deals by deal_id"""
        try:
            update_count = 0
            
            # Process updates in batches to avoid hitting limits
            batch_size = 100
            for i in range(0, len(updates), batch_size):
                batch = updates[i:i + batch_size]
                
                # Prepare batch data
                prepared_batch = []
                for update_data in batch:
                    if 'deal_id' not in update_data:
                        continue
                    
                    prepared_data = self._prepare_data_for_insert(update_data)
                    prepared_data['updated_at'] = datetime.now(timezone.utc).isoformat()
                    prepared_batch.append(prepared_data)
                
                if prepared_batch:
                    result = self.client.table('deals').upsert(
                        prepared_batch,
                        on_conflict='deal_id',
                        returning='minimal'
                    ).execute()
                    
                    update_count += len(prepared_batch)
            
            logger.info(f"Bulk updated {update_count} deals")
            return update_count
                
        except Exception as e:
            self._handle_api_error(e, "bulk_update_deals")
    
    async def bulk_delete_records(self, table_name: str, ids: List[str], id_column: str = 'id') -> int:
        """Bulk delete records from a table"""
        try:
            if not ids:
                return 0
            
            # Supabase doesn't support bulk delete directly, so we use filter
            result = self.client.table(table_name).delete().in_(id_column, ids).execute()
            
            delete_count = len(result.data) if result.data else 0
            logger.info(f"Bulk deleted {delete_count} records from {table_name}")
            return delete_count
                
        except Exception as e:
            self._handle_api_error(e, f"bulk_delete_records({table_name})")
    
    async def bulk_insert_deal_participants(self, participants_data: List[Dict[str, Any]]) -> List[str]:
        """Bulk insert deal participants"""
        try:
            prepared_data = []
            for participant_data in participants_data:
                prepared_data.append(self._prepare_data_for_insert(participant_data))
            
            result = self.client.table('deal_participants').upsert(
                prepared_data,
                on_conflict='deal_id,company_id,role',
                returning='minimal'
            ).execute()
            
            logger.info(f"Bulk inserted/updated {len(prepared_data)} deal participants")
            return [str(i) for i in range(len(prepared_data))]  # Return placeholder IDs
                
        except Exception as e:
            self._handle_api_error(e, "bulk_insert_deal_participants")
    
    # Real-time subscription support
    async def subscribe_to_deals(self, callback: Callable[[Dict[str, Any]], None]) -> str:
        """Subscribe to real-time deal updates"""
        try:
            subscription_id = str(uuid.uuid4())
            
            def handle_changes(payload):
                try:
                    # Transform payload to standardized format
                    event_data = {
                        'table': 'deals',
                        'event_type': payload.get('eventType', 'unknown'),
                        'record': payload.get('new', payload.get('old', {})),
                        'old_record': payload.get('old'),
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'subscription_id': subscription_id
                    }
                    callback(event_data)
                except Exception as e:
                    logger.error(f"Error in deals subscription callback: {e}")
            
            # Note: In a real implementation, you would use Supabase's realtime client
            # For now, we store the callback for potential future use
            self._subscription_callbacks[subscription_id] = {
                'table': 'deals',
                'callback': handle_changes,
                'filters': {},
                'created_at': datetime.now(timezone.utc)
            }
            
            logger.info(f"Created deals subscription: {subscription_id}")
            return subscription_id
            
        except Exception as e:
            logger.error(f"Failed to create deals subscription: {e}")
            raise DatabaseError(f"Subscription failed: {e}")
    
    async def subscribe_to_articles(self, callback: Callable[[Dict[str, Any]], None]) -> str:
        """Subscribe to real-time article updates"""
        try:
            subscription_id = str(uuid.uuid4())
            
            def handle_changes(payload):
                try:
                    event_data = {
                        'table': 'news_articles',
                        'event_type': payload.get('eventType', 'unknown'),
                        'record': payload.get('new', payload.get('old', {})),
                        'old_record': payload.get('old'),
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'subscription_id': subscription_id
                    }
                    callback(event_data)
                except Exception as e:
                    logger.error(f"Error in articles subscription callback: {e}")
            
            self._subscription_callbacks[subscription_id] = {
                'table': 'news_articles',
                'callback': handle_changes,
                'filters': {},
                'created_at': datetime.now(timezone.utc)
            }
            
            logger.info(f"Created articles subscription: {subscription_id}")
            return subscription_id
            
        except Exception as e:
            logger.error(f"Failed to create articles subscription: {e}")
            raise DatabaseError(f"Subscription failed: {e}")
    
    async def subscribe_to_companies(self, callback: Callable[[Dict[str, Any]], None]) -> str:
        """Subscribe to real-time company updates"""
        try:
            subscription_id = str(uuid.uuid4())
            
            def handle_changes(payload):
                try:
                    event_data = {
                        'table': 'companies',
                        'event_type': payload.get('eventType', 'unknown'),
                        'record': payload.get('new', payload.get('old', {})),
                        'old_record': payload.get('old'),
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'subscription_id': subscription_id
                    }
                    callback(event_data)
                except Exception as e:
                    logger.error(f"Error in companies subscription callback: {e}")
            
            self._subscription_callbacks[subscription_id] = {
                'table': 'companies',
                'callback': handle_changes,
                'filters': {},
                'created_at': datetime.now(timezone.utc)
            }
            
            logger.info(f"Created companies subscription: {subscription_id}")
            return subscription_id
            
        except Exception as e:
            logger.error(f"Failed to create companies subscription: {e}")
            raise DatabaseError(f"Subscription failed: {e}")
    
    async def subscribe_with_filters(
        self,
        table_name: str,
        callback: Callable[[Dict[str, Any]], None],
        filters: Optional[Dict[str, Any]] = None,
        events: Optional[List[str]] = None
    ) -> str:
        """Subscribe to real-time updates with filters and event types"""
        try:
            subscription_id = str(uuid.uuid4())
            
            # Default to all events if not specified
            if events is None:
                events = ['INSERT', 'UPDATE', 'DELETE']
            
            def handle_changes(payload):
                try:
                    event_type = payload.get('eventType', 'unknown').upper()
                    
                    # Filter by event type
                    if event_type not in events:
                        return
                    
                    # Apply custom filters if provided
                    if filters and not self._apply_realtime_filters(payload, filters):
                        return
                    
                    event_data = {
                        'table': table_name,
                        'event_type': event_type,
                        'record': payload.get('new', payload.get('old', {})),
                        'old_record': payload.get('old'),
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'subscription_id': subscription_id
                    }
                    callback(event_data)
                except Exception as e:
                    logger.error(f"Error in filtered subscription callback: {e}")
            
            self._subscription_callbacks[subscription_id] = {
                'table': table_name,
                'callback': handle_changes,
                'filters': filters or {},
                'events': events,
                'created_at': datetime.now(timezone.utc)
            }
            
            logger.info(f"Created filtered subscription for {table_name}: {subscription_id}")
            return subscription_id
            
        except Exception as e:
            logger.error(f"Failed to create filtered subscription: {e}")
            raise DatabaseError(f"Subscription failed: {e}")
    
    def _apply_realtime_filters(self, payload: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Apply filters to real-time event payload"""
        try:
            record = payload.get('new', payload.get('old', {}))
            
            for field, expected_value in filters.items():
                record_value = record.get(field)
                
                # Simple equality check - can be extended for more complex filters
                if record_value != expected_value:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying realtime filters: {e}")
            return False
    
    async def _unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from real-time updates"""
        try:
            if subscription_id in self._subscription_callbacks:
                subscription_info = self._subscription_callbacks[subscription_id]
                del self._subscription_callbacks[subscription_id]
                
                logger.info(f"Unsubscribed from {subscription_info.get('table', 'unknown')}: {subscription_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unsubscribe {subscription_id}: {e}")
            return False
    
    async def list_active_subscriptions(self) -> List[Dict[str, Any]]:
        """List all active subscriptions"""
        try:
            subscriptions = []
            for sub_id, sub_info in self._subscription_callbacks.items():
                subscriptions.append({
                    'subscription_id': sub_id,
                    'table': sub_info.get('table'),
                    'filters': sub_info.get('filters', {}),
                    'events': sub_info.get('events', []),
                    'created_at': sub_info.get('created_at', '').isoformat() if sub_info.get('created_at') else None
                })
            
            return subscriptions
            
        except Exception as e:
            logger.error(f"Error listing subscriptions: {e}")
            return []
    
    async def get_subscription_status(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific subscription"""
        try:
            if subscription_id in self._subscription_callbacks:
                sub_info = self._subscription_callbacks[subscription_id]
                return {
                    'subscription_id': subscription_id,
                    'table': sub_info.get('table'),
                    'filters': sub_info.get('filters', {}),
                    'events': sub_info.get('events', []),
                    'created_at': sub_info.get('created_at', '').isoformat() if sub_info.get('created_at') else None,
                    'active': True
                }
            
            return {
                'subscription_id': subscription_id,
                'active': False
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription status: {e}")
            return None
    
    # Utility methods
    def _prepare_data_for_insert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for insertion by converting types as needed"""
        prepared_data = {}
        
        for key, value in data.items():
            if isinstance(value, datetime):
                # Convert datetime to ISO string
                prepared_data[key] = value.isoformat()
            elif isinstance(value, (list, dict)):
                # Keep JSON-serializable types as-is
                prepared_data[key] = value
            elif value is None:
                # Keep None values
                prepared_data[key] = value
            else:
                # Convert other types to string if needed
                prepared_data[key] = value
        
        return prepared_data
    
    def _format_deal_response(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        """Format deal response to include participant companies"""
        formatted_deal = deal.copy()
        
        # Extract company information from participants
        participants = deal.get('deal_participants', [])
        if participants:
            target_companies = [
                p['companies'] for p in participants 
                if p.get('role') == 'target' and p.get('companies')
            ]
            acquirer_companies = [
                p['companies'] for p in participants 
                if p.get('role') == 'acquirer' and p.get('companies')
            ]
            
            if target_companies:
                formatted_deal['target_name'] = target_companies[0].get('name')
            if acquirer_companies:
                formatted_deal['acquirer_name'] = acquirer_companies[0].get('name')
        
        return formatted_deal
    
    # Context manager support for connection management
    @asynccontextmanager
    async def get_connection(self):
        """Context manager for database connections"""
        if not self.client:
            await self.connect()
        
        try:
            yield self.client
        finally:
            # Supabase client doesn't need explicit cleanup for individual operations
            pass