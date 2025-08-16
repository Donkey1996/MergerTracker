# Bloomberg Deals Spider Guide

## Overview

The Bloomberg Deals Spider is a specialized Scrapy spider designed to ethically scrape M&A deal information from Bloomberg's financial news platform. It implements sophisticated anti-detection measures while respecting Bloomberg's robots.txt and maintaining ethical scraping practices.

## Features

### 🛡️ Anti-Detection & Ethics
- **Robots.txt Compliance**: Automatically checks and respects robots.txt rules
- **Intelligent Rate Limiting**: Progressive delays (5-15 seconds) based on request volume
- **Browser Fingerprint Rotation**: Realistic user agents with matching headers
- **Session Management**: Maintains cookies and session state like a real browser
- **Graceful Error Handling**: Exponential backoff for rate limits and server errors

### 🎯 Data Extraction
- **Deal Information**: Target/acquirer companies, deal values, types, sectors
- **Article Metadata**: Titles, authors, publication dates, content
- **Company Data**: Industry classifications, geographic regions
- **Deal Timeline**: Announcement dates, expected completion dates

### 🔧 Technical Capabilities
- **Dynamic Content**: Uses Playwright for JavaScript-heavy pages
- **Multiple Selectors**: Robust CSS selector strategies for different page layouts
- **Fallback Mechanisms**: RSS feeds and alternative endpoints when blocked
- **Data Enrichment**: Automatic industry classification and confidence scoring

## Architecture

### Spider Components

1. **BloombergDealsSpider**: Main spider class
2. **BloombergAntiDetectionMiddleware**: Advanced anti-detection middleware
3. **Enhanced Pipelines**: Validation, deduplication, and enrichment
4. **Playwright Integration**: Browser automation for dynamic content

### Data Flow

```
Start URLs → Parse Deals Section → Extract Article Links → Parse Articles → Extract Deal Data → Save to Database
```

## Configuration

### Spider Settings

```python
custom_settings = {
    'DOWNLOAD_DELAY': 5,  # 5 second base delay
    'RANDOMIZE_DOWNLOAD_DELAY': 2,  # Up to 2 seconds additional
    'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # Sequential requests
    'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 60000,  # 60 second timeout
}
```

### Middleware Configuration

The Bloomberg spider uses specialized middleware:

```python
DOWNLOADER_MIDDLEWARES = {
    'scraper.middlewares.RotateUserAgentMiddleware': 400,
    'scraper.middlewares.BloombergAntiDetectionMiddleware': 405,
    'scraper.middlewares.RateLimitMiddleware': 500,
    'scrapy_playwright.middleware.ScrapyPlaywrightMiddleware': 585,
}
```

## Usage

### Basic Usage

```bash
# Navigate to backend directory
cd backend

# Run the Bloomberg spider
scrapy crawl bloomberg_deals

# Run with custom settings
scrapy crawl bloomberg_deals -s DOWNLOAD_DELAY=10 -s CLOSESPIDER_ITEMCOUNT=20
```

### Testing

```bash
# Run the test script
python test_bloomberg_spider.py

# Run with debugging (non-headless browser)
python test_bloomberg_spider.py  # Will prompt for confirmation
```

### Integration with Scheduler

```python
from scraper.spiders.bloomberg_deals_spider import BloombergDealsSpider
from scrapy.crawler import CrawlerRunner

# In your scheduler service
crawler = CrawlerRunner()
crawler.crawl(BloombergDealsSpider)
```

## Data Output

### News Articles

```json
{
    "url": "https://bloomberg.com/news/articles/...",
    "title": "Company A Agrees to Acquire Company B for $5 Billion",
    "content": "Article content...",
    "author": "Reporter Name",
    "published_date": "2024-01-15T10:30:00Z",
    "source": "bloomberg",
    "word_count": 847,
    "reading_time": 4
}
```

### M&A Deals

```json
{
    "deal_id": "abc123def456",
    "deal_type": "acquisition",
    "deal_status": "announced",
    "target_company": "Company B",
    "acquirer_company": "Company A", 
    "deal_value": 5000000000,
    "deal_value_currency": "USD",
    "industry_sector": "technology",
    "announcement_date": "January 15, 2024",
    "source_url": "https://bloomberg.com/news/articles/...",
    "confidence_score": 0.9,
    "extraction_method": "bloomberg_nlp_rules"
}
```

## Error Handling & Monitoring

### Common Issues

1. **403 Forbidden**: Implement retry with different user agents
2. **429 Rate Limited**: Exponential backoff (30, 60 seconds)
3. **Paywall Content**: Skip paywalled articles gracefully
4. **Dynamic Content**: Use Playwright for JavaScript-heavy pages

### Monitoring Metrics

- **Success Rate**: Percentage of successful requests
- **Deal Extraction Rate**: Deals found per article
- **Average Response Time**: Request latency tracking
- **Error Distribution**: Types and frequency of errors

### Logging

```python
# Enable debug logging
LOG_LEVEL = 'DEBUG'
LOG_FILE = 'bloomberg_spider.log'

# Custom log formatting with context
LOGGING = {
    'formatters': {
        'detailed': {
            'format': '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
        }
    }
}
```

## Compliance & Ethics

### Legal Considerations

- ✅ Respects robots.txt directives
- ✅ Implements reasonable rate limiting
- ✅ Uses public content only
- ✅ Provides proper attribution
- ✅ Follows Bloomberg's Terms of Service

### Best Practices

1. **Rate Limiting**: Never exceed 1 request per 5 seconds minimum
2. **Request Volume**: Limit daily requests to reasonable numbers
3. **User Agent**: Always identify as legitimate research crawler
4. **Content Usage**: Use data for analysis, not republication
5. **Monitoring**: Track and respond to error rates

### Risk Mitigation

- **Progressive Delays**: Increase delays if errors occur
- **Circuit Breaker**: Stop crawling if error rate is too high
- **Graceful Degradation**: Fall back to RSS feeds if blocked
- **Monitoring Alerts**: Notify on unusual error patterns

## Performance Optimization

### Caching Strategy

```python
# Enable HTTP caching
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600  # 1 hour cache
HTTPCACHE_DIR = 'httpcache'
```

### Memory Management

```python
# Limit memory usage
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 2048  # 2GB limit
MEMUSAGE_WARNING_MB = 1536  # Warning at 1.5GB
```

### Concurrent Processing

```python
# Balance speed vs politeness
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 1  # Sequential for Bloomberg
REACTOR_THREADPOOL_MAXSIZE = 20
```

## Troubleshooting

### Common Problems

**Problem**: Spider gets 403 errors consistently
**Solution**: 
- Check if user agents are being rotated properly
- Increase delays between requests
- Verify robots.txt compliance
- Consider using different IP address

**Problem**: No deal data extracted from articles
**Solution**:
- Check CSS selectors are current
- Verify article content is loading completely
- Test regex patterns with sample text
- Enable debug logging to see extraction attempts

**Problem**: Playwright timeouts
**Solution**:
- Increase PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT
- Check network connectivity
- Verify Playwright browser installation
- Use wait_for_load_state in page methods

### Debug Commands

```bash
# Test specific URL
scrapy shell "https://www.bloomberg.com/deals"

# Check robots.txt
scrapy shell "https://www.bloomberg.com/robots.txt"

# Run with verbose logging
scrapy crawl bloomberg_deals -L DEBUG

# Test with limited items
scrapy crawl bloomberg_deals -s CLOSESPIDER_ITEMCOUNT=5
```

## Maintenance

### Regular Updates

1. **Selector Updates**: Bloomberg may change their HTML structure
2. **User Agent Rotation**: Keep browser versions current
3. **Rate Limit Tuning**: Adjust based on success rates
4. **Pattern Updates**: Update deal extraction patterns

### Monitoring Schedule

- **Daily**: Check error rates and success metrics
- **Weekly**: Review extracted data quality
- **Monthly**: Update selectors and patterns if needed
- **Quarterly**: Review compliance and ethics practices

## Integration Examples

### With APScheduler

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scrapy.crawler import CrawlerRunner

scheduler = AsyncIOScheduler()
crawler = CrawlerRunner()

@scheduler.scheduled_job('cron', hour=9, minute=0)  # Daily at 9 AM
async def run_bloomberg_spider():
    await crawler.crawl(BloombergDealsSpider)

scheduler.start()
```

### With Database

```python
# Configure database pipeline
ITEM_PIPELINES = {
    'scraper.pipelines.ValidationPipeline': 300,
    'scraper.pipelines.DuplicatesPipeline': 400,
    'scraper.pipelines.DataEnrichmentPipeline': 450,
    'scraper.pipelines.DatabasePipeline': 500,
}

# Database connection
DATABASE_URL = 'postgresql://user:password@localhost:5432/mergertracker'
```

## Support

For issues and questions:

1. Check the logs in `bloomberg_spider.log`
2. Review the troubleshooting section
3. Test with the included test script
4. Monitor Bloomberg's robots.txt for changes
5. Verify compliance with current terms of service

Remember: Always prioritize ethical scraping practices and respect for Bloomberg's resources and policies.