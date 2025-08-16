# Supabase Database Adapter for MergerTracker

This document provides comprehensive documentation for the Supabase database adapter implementation in the MergerTracker project.

## Overview

The SupabaseAdapter provides a complete database abstraction layer for Supabase, offering:

- Full CRUD operations for all MergerTracker entities
- Bulk operations for high-performance data ingestion
- Advanced full-text search capabilities
- Real-time subscriptions for live data updates
- Analytics and reporting functions
- Comprehensive error handling and logging
- Row Level Security (RLS) support
- Connection pooling and optimization

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MergerTracker Application                    │
├─────────────────────────────────────────────────────────────────┤
│                    DatabaseAdapter Interface                   │
├─────────────────────────────────────────────────────────────────┤
│                      SupabaseAdapter                          │
├─────────────────────────────────────────────────────────────────┤
│                     supabase-py Client                        │
├─────────────────────────────────────────────────────────────────┤
│                      Supabase Cloud                           │
│           (PostgreSQL + Real-time + Auth + Storage)            │
└─────────────────────────────────────────────────────────────────┘
```

## Setup and Configuration

### 1. Environment Variables

Set the following environment variables:

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=sbp_your_service_role_key_here

# Optional
SUPABASE_ANON_KEY=eyJ...your_anon_key_here
SUPABASE_JWT_SECRET=your-jwt-secret

# Connection Settings
SUPABASE_TIMEOUT=30
SUPABASE_RETRY_COUNT=3

# Feature Toggles
SUPABASE_ENABLE_REALTIME=true
SUPABASE_ENABLE_AUTH=true
SUPABASE_ENABLE_STORAGE=false

# Schema Settings
SUPABASE_SCHEMA=public
SUPABASE_AUTO_REFRESH_TOKEN=true

# Database Adapter Selection
DATABASE_ADAPTER=supabase
```

### 2. Database Schema Setup

1. Create a new Supabase project at [https://supabase.com](https://supabase.com)
2. Copy the SQL schema from `/database/scripts/supabase_schema.sql`
3. Run the schema in your Supabase SQL editor or via CLI:
   ```bash
   supabase db push
   ```

### 3. Dependencies

The adapter requires the following Python package:

```bash
pip install supabase==2.3.4
```

## Usage Examples

### Basic Setup

```python
from database.factory import create_database_adapter
from config.supabase_config import create_supabase_config_from_env

# Create configuration
config = create_supabase_config_from_env()

# Create adapter
adapter = create_database_adapter(
    adapter_type='supabase',
    connection_params=config.get_connection_params()
)

# Connect
await adapter.connect()

# Verify health
is_healthy = await adapter.health_check()
```

### CRUD Operations

#### Create Operations

```python
# Create a company
company_data = {
    'name': 'Example Corp',
    'ticker_symbol': 'EXPL',
    'market_cap': 1000000000.00,
    'is_public': True
}
company_id = await adapter.create_company(company_data)

# Create a deal
deal_data = {
    'deal_name': 'Acquisition of Example Corp',
    'deal_type': 'acquisition',
    'deal_status': 'announced',
    'transaction_value': 1500000000.00
}
deal_id = await adapter.create_deal(deal_data)

# Create a news article
article_data = {
    'title': 'Major Acquisition Announced',
    'url': 'https://news.example.com/article-1',
    'content': 'Article content...',
    'source_name': 'Financial Times'
}
article_id = await adapter.create_article(article_data)
```

#### Read Operations

```python
# Get records by ID
company = await adapter.get_company(company_id)
deal = await adapter.get_deal(deal_id)
article = await adapter.get_article(article_id)

# List records with filtering
deals = await adapter.list_deals(
    filters={'deal_status': 'announced'},
    limit=50,
    sort_by='transaction_value',
    sort_order='desc'
)

companies = await adapter.list_companies(
    filters={'country': 'US', 'is_public': True},
    limit=100
)

articles = await adapter.list_articles(
    filters={'ma_relevance_min': 0.8},
    limit=25
)
```

#### Update Operations

```python
# Update company
await adapter.update_company(company_id, {
    'market_cap': 1200000000.00,
    'employee_count': 5500
})

# Update deal
await adapter.update_deal(deal_id, {
    'deal_status': 'completed',
    'actual_completion_date': datetime.now().date()
})
```

#### Delete Operations

```python
# Delete records
await adapter.delete_company(company_id)
await adapter.delete_deal(deal_id)
```

### Bulk Operations

```python
# Bulk insert companies
companies_data = [
    {'name': f'Company {i}', 'ticker_symbol': f'COMP{i}'}
    for i in range(100)
]
company_ids = await adapter.bulk_insert_companies(companies_data)

# Bulk insert deals
deals_data = [
    {'deal_name': f'Deal {i}', 'deal_type': 'acquisition'}
    for i in range(50)
]
deal_ids = await adapter.bulk_insert_deals(deals_data)

# Bulk insert articles
articles_data = [
    {'title': f'Article {i}', 'url': f'https://news.com/{i}'}
    for i in range(200)
]
article_ids = await adapter.bulk_insert_articles(articles_data)

# Bulk update deals
updates = [
    {'deal_id': deal_id, 'deal_status': 'pending'}
    for deal_id in deal_ids[:10]
]
update_count = await adapter.bulk_update_deals(updates)

# Bulk delete
delete_count = await adapter.bulk_delete_records(
    table_name='companies',
    ids=company_ids[:5],
    id_column='id'
)
```

### Search Operations

```python
# Search deals
deal_results = await adapter.search_deals(
    query='technology acquisition',
    limit=25
)

# Search companies
company_results = await adapter.search_companies(
    query='biotech startup',
    limit=15
)

# Search articles
article_results = await adapter.search_articles(
    query='merger announcement',
    filters={'ma_relevance_min': 0.7},
    limit=30
)

# Advanced search across all tables
advanced_results = await adapter.advanced_search({
    'query': 'artificial intelligence',
    'filters': {'date_from': datetime(2024, 1, 1).date()},
    'limit_per_table': 10
})
```

### Analytics Operations

```python
# Deal analytics
analytics = await adapter.get_deal_analytics(
    date_from=datetime(2024, 1, 1),
    date_to=datetime.now(),
    group_by='month'
)

print(f"Total deals: {analytics['summary']['total_deals']}")
print(f"Total value: ${analytics['summary']['total_value']:,.2f}")

# Industry analytics
industry_stats = await adapter.get_industry_analytics(
    date_from=datetime(2024, 1, 1)
)

for industry in industry_stats['industries']:
    print(f"{industry['industry']}: {industry['deal_count']} deals")

# Database statistics
db_stats = await adapter.get_database_stats()
for table in db_stats['table_stats']:
    print(f"{table['table_name']}: {table['row_count']} rows")
```

### Real-time Subscriptions

```python
# Subscribe to deal updates
def deal_callback(event_data):
    print(f"Deal {event_data['event_type']}: {event_data['record']['deal_name']}")

deals_subscription = await adapter.subscribe_to_deals(deal_callback)

# Subscribe to company updates
def company_callback(event_data):
    print(f"Company {event_data['event_type']}: {event_data['record']['name']}")

companies_subscription = await adapter.subscribe_to_companies(company_callback)

# Subscribe with filters
filtered_subscription = await adapter.subscribe_with_filters(
    table_name='deals',
    callback=lambda event: print(f"High-value deal: {event['record']['deal_name']}"),
    filters={'transaction_value': {'gt': 1000000000}},
    events=['INSERT', 'UPDATE']
)

# List active subscriptions
subscriptions = await adapter.list_active_subscriptions()
print(f"Active subscriptions: {len(subscriptions)}")

# Clean up
await adapter._unsubscribe(deals_subscription)
await adapter._unsubscribe(companies_subscription)
await adapter._unsubscribe(filtered_subscription)
```

## Database Schema

The Supabase schema includes the following main tables:

### Core Tables

- **users**: User authentication and profile data
- **companies**: Company information and financials
- **deals**: M&A deal records with comprehensive metadata
- **deal_participants**: Relationship between deals and companies
- **deal_advisors**: Financial and legal advisors for deals
- **news_articles**: News articles and media coverage
- **industry_classifications**: SIC/NAICS/GICS industry codes

### Key Features

- **UUID Primary Keys**: For globally unique identifiers
- **JSONB Columns**: For flexible AI-extracted data storage
- **Array Columns**: For multi-value fields (tags, keywords, etc.)
- **Full-text Search Indexes**: For efficient text search
- **GIN Indexes**: For array and JSONB columns
- **Composite Indexes**: For common query patterns
- **Row Level Security**: For data access control
- **Real-time Subscriptions**: For live data updates

### Performance Optimizations

- **Trigram Indexes**: For fuzzy text matching
- **Partial Indexes**: For filtered queries
- **Composite Indexes**: For multi-column queries
- **JSONB Indexes**: For AI data queries
- **Updated At Triggers**: Automatic timestamp updates

## Error Handling

The adapter includes comprehensive error handling:

```python
from database.adapters.base import (
    DatabaseError,
    ConnectionError,
    ValidationError,
    NotFoundError,
    DuplicateError
)

try:
    await adapter.create_deal(deal_data)
except DuplicateError:
    print("Deal already exists")
except ValidationError as e:
    print(f"Invalid data: {e}")
except ConnectionError as e:
    print(f"Connection failed: {e}")
except DatabaseError as e:
    print(f"Database error: {e}")
```

## Performance Considerations

### Best Practices

1. **Use Bulk Operations**: For inserting multiple records
2. **Enable Connection Pooling**: Configure appropriate pool sizes
3. **Use Prepared Statements**: Automatic with supabase-py
4. **Optimize Queries**: Use appropriate filters and limits
5. **Monitor RLS Policies**: Ensure efficient policy execution

### Configuration Tuning

```python
# Optimal configuration for high-throughput scenarios
config = SupabaseConfig(
    url=supabase_url,
    service_key=service_key,
    timeout=60,  # Longer timeout for bulk operations
    retry_count=5,  # More retries for reliability
    enable_realtime=False  # Disable if not needed
)
```

## Security Features

### Row Level Security (RLS)

The schema includes RLS policies that:

- Allow authenticated users to read all data
- Restrict write operations to service role
- Protect user profile data
- Support API key authentication

### Authentication

```python
# API key authentication
user_id = await adapter.client.rpc('authenticate_api_key', {
    'api_key': user_api_key
})
```

## Monitoring and Debugging

### Logging

The adapter provides comprehensive logging:

```python
import logging

# Enable debug logging
logging.getLogger('database.adapters.supabase_adapter').setLevel(logging.DEBUG)

# View connection info
from config.supabase_config import log_supabase_config
log_supabase_config(config)
```

### Health Checks

```python
# Regular health checks
is_healthy = await adapter.health_check()
if not is_healthy:
    logger.error("Database health check failed")
    
# Connection validation
validation_result = validate_supabase_connection(config)
if not validation_result['valid']:
    logger.error(f"Configuration errors: {validation_result['errors']}")
```

## Migration and Maintenance

### Schema Updates

1. Create migration files in `/database/scripts/`
2. Run migrations via Supabase Dashboard or CLI
3. Update adapter code if needed
4. Test thoroughly in staging environment

### Backup and Recovery

Supabase provides automatic backups. For additional backup:

```python
# Export data for backup
backup_data = {
    'deals': await adapter.list_deals(limit=10000),
    'companies': await adapter.list_companies(limit=10000),
    'articles': await adapter.list_articles(limit=10000)
}
```

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify SUPABASE_URL and keys
   - Check network connectivity
   - Ensure Supabase project is active

2. **Permission Errors**
   - Verify RLS policies
   - Check API key permissions
   - Ensure service key is used for writes

3. **Performance Issues**
   - Check query complexity
   - Verify indexes are being used
   - Monitor connection pool usage

4. **Real-time Issues**
   - Verify real-time is enabled in Supabase
   - Check subscription filters
   - Monitor callback errors

### Support Resources

- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [MergerTracker Issues](https://github.com/your-repo/issues)

## Contributing

When contributing to the Supabase adapter:

1. Follow the existing code patterns
2. Add comprehensive tests
3. Update documentation
4. Ensure error handling is robust
5. Test with real Supabase instance

## License

This adapter is part of the MergerTracker project and follows the same license terms.