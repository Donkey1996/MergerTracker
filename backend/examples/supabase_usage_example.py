"""
Supabase Database Adapter Usage Examples

This file demonstrates how to use the SupabaseAdapter for MergerTracker,
including basic operations, bulk operations, search, analytics, and real-time features.

Prerequisites:
1. Set up a Supabase project at https://supabase.com
2. Run the schema from /database/scripts/supabase_schema.sql in your Supabase SQL editor
3. Set the required environment variables:
   - SUPABASE_URL
   - SUPABASE_SERVICE_KEY
   - SUPABASE_ANON_KEY (optional)
"""

import asyncio
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the database components
from database.factory import create_database_adapter
from config.supabase_config import create_supabase_config_from_env, log_supabase_config


async def setup_supabase_adapter():
    """Set up the Supabase adapter with configuration"""
    try:
        # Create configuration from environment variables
        config = create_supabase_config_from_env()
        log_supabase_config(config)
        
        # Create the adapter
        adapter = create_database_adapter(
            adapter_type='supabase',
            connection_params=config.get_connection_params()
        )
        
        # Connect to the database
        await adapter.connect()
        
        # Verify connection health
        is_healthy = await adapter.health_check()
        if not is_healthy:
            raise Exception("Database health check failed")
        
        logger.info("Supabase adapter setup successful!")
        return adapter
        
    except Exception as e:
        logger.error(f"Failed to setup Supabase adapter: {e}")
        raise


async def basic_crud_operations_example(adapter):
    """Demonstrate basic CRUD operations"""
    logger.info("=== Basic CRUD Operations Example ===")
    
    try:
        # Create a sample company
        company_data = {
            'name': 'Example Corp',
            'legal_name': 'Example Corporation Inc.',
            'ticker_symbol': 'EXPL',
            'exchange': 'NASDAQ',
            'country': 'US',
            'industry_classification_id': None,
            'market_cap': 1000000000.00,  # $1B
            'annual_revenue': 500000000.00,  # $500M
            'employee_count': 5000,
            'is_public': True,
            'website': 'https://example-corp.com',
            'description': 'A sample technology company for demonstration'
        }
        
        company_id = await adapter.create_company(company_data)
        logger.info(f"Created company with ID: {company_id}")
        
        # Retrieve the company
        retrieved_company = await adapter.get_company(company_id)
        logger.info(f"Retrieved company: {retrieved_company['name']}")
        
        # Update the company
        update_data = {
            'market_cap': 1200000000.00,  # Updated to $1.2B
            'employee_count': 5500
        }
        
        updated = await adapter.update_company(company_id, update_data)
        logger.info(f"Company updated: {updated}")
        
        # Create a sample deal
        deal_data = {
            'deal_name': f'Acquisition of {company_data["name"]}',
            'deal_type': 'acquisition',
            'deal_status': 'announced',
            'announcement_date': datetime.now().date(),
            'transaction_value': 1500000000.00,  # $1.5B
            'currency': 'USD',
            'target_geography': 'US',
            'acquirer_geography': 'US',
            'primary_industry_sic': '7372',
            'deal_description': 'Strategic acquisition to expand market presence'
        }
        
        deal_id = await adapter.create_deal(deal_data)
        logger.info(f"Created deal with ID: {deal_id}")
        
        # Retrieve the deal
        retrieved_deal = await adapter.get_deal(deal_id)
        logger.info(f"Retrieved deal: {retrieved_deal['deal_name']}")
        
        # Create a sample news article
        article_data = {
            'title': f'Breaking: {deal_data["deal_name"]} Announced',
            'url': f'https://example-news.com/articles/{deal_id}',
            'content': f'In a major development, {deal_data["deal_name"]} has been announced...',
            'summary': 'Major acquisition announcement in the technology sector',
            'source_name': 'Example News',
            'source_domain': 'example-news.com',
            'publish_date': datetime.now(timezone.utc),
            'ma_relevance_score': 0.95,
            'contains_deal_info': True,
            'deal_id': int(retrieved_deal['id']),
            'mentioned_companies': [company_data['name']],
            'mentioned_tickers': [company_data['ticker_symbol']]
        }
        
        article_id = await adapter.create_article(article_data)
        logger.info(f"Created article with ID: {article_id}")
        
        return {
            'company_id': company_id,
            'deal_id': deal_id,
            'article_id': article_id
        }
        
    except Exception as e:
        logger.error(f"Error in CRUD operations: {e}")
        raise


async def bulk_operations_example(adapter):
    """Demonstrate bulk operations for performance"""
    logger.info("=== Bulk Operations Example ===")
    
    try:
        # Bulk insert companies
        companies_data = [
            {
                'name': f'Tech Company {i}',
                'ticker_symbol': f'TECH{i:02d}',
                'exchange': 'NASDAQ',
                'country': 'US',
                'market_cap': 100000000 * i,  # Variable market cap
                'is_public': True
            }
            for i in range(1, 6)  # Create 5 companies
        ]
        
        company_ids = await adapter.bulk_insert_companies(companies_data)
        logger.info(f"Bulk inserted {len(company_ids)} companies")
        
        # Bulk insert deals
        deals_data = [
            {
                'deal_name': f'Deal Number {i}',
                'deal_type': 'acquisition',
                'deal_status': 'announced',
                'announcement_date': datetime.now().date(),
                'transaction_value': 50000000 * i,  # Variable deal size
                'currency': 'USD',
                'primary_geography': 'US'
            }
            for i in range(1, 11)  # Create 10 deals
        ]
        
        deal_ids = await adapter.bulk_insert_deals(deals_data)
        logger.info(f"Bulk inserted {len(deal_ids)} deals")
        
        # Bulk insert news articles
        articles_data = [
            {
                'title': f'News Article {i}: M&A Update',
                'url': f'https://example-news.com/article-{i}',
                'content': f'This is sample content for article {i} about M&A activity...',
                'source_name': 'Example Financial News',
                'source_domain': 'example-financial.com',
                'publish_date': datetime.now(timezone.utc),
                'ma_relevance_score': 0.8 + (i * 0.01),  # Variable relevance
                'contains_deal_info': True
            }
            for i in range(1, 21)  # Create 20 articles
        ]
        
        article_ids = await adapter.bulk_insert_articles(articles_data)
        logger.info(f"Bulk inserted {len(article_ids)} articles")
        
        return {
            'bulk_company_ids': company_ids,
            'bulk_deal_ids': deal_ids,
            'bulk_article_ids': article_ids
        }
        
    except Exception as e:
        logger.error(f"Error in bulk operations: {e}")
        raise


async def search_operations_example(adapter):
    """Demonstrate search capabilities"""
    logger.info("=== Search Operations Example ===")
    
    try:
        # Search for deals
        deal_results = await adapter.search_deals(
            query='acquisition technology',
            limit=10
        )
        logger.info(f"Found {len(deal_results)} deals matching 'acquisition technology'")
        
        # Search for companies
        company_results = await adapter.search_companies(
            query='Tech Company',
            limit=5
        )
        logger.info(f"Found {len(company_results)} companies matching 'Tech Company'")
        
        # Search for articles
        article_results = await adapter.search_articles(
            query='M&A',
            filters={'ma_relevance_min': 0.8},
            limit=10
        )
        logger.info(f"Found {len(article_results)} articles matching 'M&A' with high relevance")
        
        # Advanced search across all tables
        advanced_results = await adapter.advanced_search({
            'query': 'technology acquisition',
            'filters': {
                'date_from': datetime(2024, 1, 1).date()
            },
            'limit_per_table': 5
        })
        
        logger.info("Advanced search results:")
        logger.info(f"  Deals: {len(advanced_results['deals'])}")
        logger.info(f"  Companies: {len(advanced_results['companies'])}")
        logger.info(f"  Articles: {len(advanced_results['articles'])}")
        
        return {
            'deal_search_count': len(deal_results),
            'company_search_count': len(company_results),
            'article_search_count': len(article_results),
            'advanced_search_results': advanced_results
        }
        
    except Exception as e:
        logger.error(f"Error in search operations: {e}")
        raise


async def analytics_example(adapter):
    """Demonstrate analytics capabilities"""
    logger.info("=== Analytics Example ===")
    
    try:
        # Get deal analytics by month
        deal_analytics = await adapter.get_deal_analytics(
            date_from=datetime(2024, 1, 1),
            date_to=datetime.now(),
            group_by='month'
        )
        
        logger.info("Deal Analytics (by month):")
        logger.info(f"  Total deals: {deal_analytics['summary']['total_deals']}")
        logger.info(f"  Total value: ${deal_analytics['summary']['total_value']:,.2f}")
        logger.info(f"  Average deal size: ${deal_analytics['summary']['avg_deal_size']:,.2f}")
        logger.info(f"  Number of periods: {len(deal_analytics['trends'])}")
        
        # Get industry analytics
        industry_analytics = await adapter.get_industry_analytics(
            date_from=datetime(2024, 1, 1)
        )
        
        logger.info(f"Industry Analytics: {len(industry_analytics['industries'])} industries analyzed")
        
        # Get database statistics
        db_stats = await adapter.get_database_stats()
        
        logger.info("Database Statistics:")
        for table_stat in db_stats['table_stats']:
            logger.info(f"  {table_stat['table_name']}: {table_stat['row_count']} rows")
        
        return {
            'deal_analytics': deal_analytics,
            'industry_analytics': industry_analytics,
            'database_stats': db_stats
        }
        
    except Exception as e:
        logger.error(f"Error in analytics: {e}")
        raise


async def realtime_subscriptions_example(adapter):
    """Demonstrate real-time subscription capabilities"""
    logger.info("=== Real-time Subscriptions Example ===")
    
    try:
        # Define callback functions for different tables
        def deal_callback(event_data):
            logger.info(f"Deal event: {event_data['event_type']} - {event_data['record'].get('deal_name', 'Unknown')}")
        
        def company_callback(event_data):
            logger.info(f"Company event: {event_data['event_type']} - {event_data['record'].get('name', 'Unknown')}")
        
        def article_callback(event_data):
            logger.info(f"Article event: {event_data['event_type']} - {event_data['record'].get('title', 'Unknown')}")
        
        # Subscribe to real-time updates
        deals_subscription = await adapter.subscribe_to_deals(deal_callback)
        companies_subscription = await adapter.subscribe_to_companies(company_callback)
        articles_subscription = await adapter.subscribe_to_articles(article_callback)
        
        logger.info(f"Created subscriptions:")
        logger.info(f"  Deals: {deals_subscription}")
        logger.info(f"  Companies: {companies_subscription}")
        logger.info(f"  Articles: {articles_subscription}")
        
        # Subscribe with filters
        filtered_subscription = await adapter.subscribe_with_filters(
            table_name='deals',
            callback=lambda event: logger.info(f"Filtered deal event: {event['record'].get('deal_name')}"),
            filters={'deal_status': 'announced'},
            events=['INSERT', 'UPDATE']
        )
        
        logger.info(f"Created filtered subscription: {filtered_subscription}")
        
        # List active subscriptions
        active_subscriptions = await adapter.list_active_subscriptions()
        logger.info(f"Active subscriptions: {len(active_subscriptions)}")
        
        # Simulate some time for subscriptions to be active
        await asyncio.sleep(1)
        
        # Clean up subscriptions
        await adapter._unsubscribe(deals_subscription)
        await adapter._unsubscribe(companies_subscription)
        await adapter._unsubscribe(articles_subscription)
        await adapter._unsubscribe(filtered_subscription)
        
        logger.info("Cleaned up all subscriptions")
        
        return {
            'subscriptions_created': 4,
            'subscriptions_cleaned': 4
        }
        
    except Exception as e:
        logger.error(f"Error in real-time subscriptions: {e}")
        raise


async def listing_and_filtering_example(adapter):
    """Demonstrate listing and filtering capabilities"""
    logger.info("=== Listing and Filtering Example ===")
    
    try:
        # List deals with filters
        recent_deals = await adapter.list_deals(
            filters={
                'deal_status': 'announced',
                'date_from': datetime(2024, 1, 1).date()
            },
            limit=10,
            sort_by='transaction_value',
            sort_order='desc'
        )
        
        logger.info(f"Found {len(recent_deals)} recent announced deals")
        
        # List companies with filters
        public_companies = await adapter.list_companies(
            filters={
                'is_public': True,
                'country': 'US'
            },
            limit=20
        )
        
        logger.info(f"Found {len(public_companies)} US public companies")
        
        # List articles with filters
        relevant_articles = await adapter.list_articles(
            filters={
                'contains_deal_info': True,
                'ma_relevance_min': 0.7,
                'date_from': datetime(2024, 1, 1)
            },
            limit=15
        )
        
        logger.info(f"Found {len(relevant_articles)} highly relevant M&A articles")
        
        return {
            'recent_deals_count': len(recent_deals),
            'public_companies_count': len(public_companies),
            'relevant_articles_count': len(relevant_articles)
        }
        
    except Exception as e:
        logger.error(f"Error in listing and filtering: {e}")
        raise


async def main():
    """Main function to run all examples"""
    try:
        # Setup the adapter
        adapter = await setup_supabase_adapter()
        
        # Run all examples
        examples_results = {}
        
        # Basic CRUD operations
        examples_results['crud'] = await basic_crud_operations_example(adapter)
        
        # Bulk operations
        examples_results['bulk'] = await bulk_operations_example(adapter)
        
        # Search operations
        examples_results['search'] = await search_operations_example(adapter)
        
        # Listing and filtering
        examples_results['listing'] = await listing_and_filtering_example(adapter)
        
        # Analytics
        examples_results['analytics'] = await analytics_example(adapter)
        
        # Real-time subscriptions
        examples_results['realtime'] = await realtime_subscriptions_example(adapter)
        
        # Summary
        logger.info("=== Examples Summary ===")
        logger.info(f"All examples completed successfully!")
        logger.info(f"Results summary: {examples_results}")
        
    except Exception as e:
        logger.error(f"Error running examples: {e}")
        raise
    
    finally:
        # Clean up
        if 'adapter' in locals():
            await adapter.disconnect()
            logger.info("Disconnected from Supabase")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())