import hashlib
import logging
from datetime import datetime
from scrapy.exceptions import DropItem
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import redis
import json

logger = logging.getLogger(__name__)


class ValidationPipeline:
    """Pipeline to validate scraped items"""
    
    def process_item(self, item, spider):
        # Validate required fields based on item type
        if hasattr(item, 'url') and not item.get('url'):
            raise DropItem(f"Missing URL in {item}")
        
        if hasattr(item, 'title') and not item.get('title'):
            raise DropItem(f"Missing title in {item}")
        
        # Add scraped timestamp
        if hasattr(item, 'scraped_date'):
            item['scraped_date'] = datetime.utcnow().isoformat()
        
        # Validate deal values
        if hasattr(item, 'deal_value') and item.get('deal_value'):
            try:
                deal_value = float(item['deal_value'])
                if deal_value <= 0:
                    item['deal_value'] = None
            except (ValueError, TypeError):
                item['deal_value'] = None
        
        return item


class DuplicatesPipeline:
    """Pipeline to filter out duplicate items"""
    
    def __init__(self):
        self.seen_urls = set()
        self.seen_deals = set()
    
    def process_item(self, item, spider):
        # For news articles, check URL duplicates
        if hasattr(item, 'url') and item.get('url'):
            if item['url'] in self.seen_urls:
                raise DropItem(f"Duplicate article found: {item['url']}")
            self.seen_urls.add(item['url'])
        
        # For deals, create a hash of key fields
        if hasattr(item, 'target_company') and hasattr(item, 'acquirer_company'):
            deal_hash = self._create_deal_hash(item)
            if deal_hash in self.seen_deals:
                raise DropItem(f"Duplicate deal found: {item.get('target_company')} - {item.get('acquirer_company')}")
            self.seen_deals.add(deal_hash)
        
        return item
    
    def _create_deal_hash(self, item):
        """Create unique hash for deal identification"""
        key_fields = [
            str(item.get('target_company', '')),
            str(item.get('acquirer_company', '')),
            str(item.get('deal_value', '')),
            str(item.get('announcement_date', ''))
        ]
        hash_string = '|'.join(key_fields).lower()
        return hashlib.md5(hash_string.encode()).hexdigest()


class DatabasePipeline:
    """Pipeline to store items in database"""
    
    def __init__(self, database_url, redis_url=None):
        self.database_url = database_url
        self.redis_url = redis_url
        self.engine = None
        self.Session = None
        self.redis_client = None
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            database_url=crawler.settings.get('DATABASE_URL'),
            redis_url=crawler.settings.get('REDIS_URL')
        )
    
    def open_spider(self, spider):
        self.engine = create_engine(self.database_url)
        self.Session = sessionmaker(bind=self.engine)
        
        if self.redis_url:
            self.redis_client = redis.from_url(self.redis_url)
        
        logger.info(f"Database pipeline opened for spider: {spider.name}")
    
    def close_spider(self, spider):
        if self.engine:
            self.engine.dispose()
        logger.info(f"Database pipeline closed for spider: {spider.name}")
    
    def process_item(self, item, spider):
        try:
            if hasattr(item, 'url'):  # News article
                self._save_news_article(item, spider)
            elif hasattr(item, 'target_company'):  # Deal
                self._save_deal(item, spider)
            elif hasattr(item, 'company_name'):  # Company
                self._save_company(item, spider)
            else:
                logger.warning(f"Unknown item type: {type(item)}")
            
            # Cache in Redis if available
            if self.redis_client:
                self._cache_item(item, spider)
            
            return item
            
        except Exception as e:
            logger.error(f"Error saving item to database: {e}")
            raise DropItem(f"Error saving item: {e}")
    
    def _save_news_article(self, item, spider):
        """Save news article to database"""
        session = self.Session()
        try:
            # Convert item to dict
            article_data = dict(item)
            
            # Insert into news_articles table
            insert_query = text("""
                INSERT INTO news_articles 
                (url, title, content, summary, source, author, published_date, 
                 scraped_date, category, word_count, reading_time)
                VALUES 
                (:url, :title, :content, :summary, :source, :author, 
                 :published_date, :scraped_date, :category, :word_count, :reading_time)
                ON CONFLICT (url) DO UPDATE SET
                    content = EXCLUDED.content,
                    summary = EXCLUDED.summary,
                    scraped_date = EXCLUDED.scraped_date
            """)
            
            session.execute(insert_query, article_data)
            session.commit()
            logger.debug(f"Saved news article: {item.get('title')}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving news article: {e}")
            raise
        finally:
            session.close()
    
    def _save_deal(self, item, spider):
        """Save M&A deal to database"""
        session = self.Session()
        try:
            deal_data = dict(item)
            
            insert_query = text("""
                INSERT INTO deals
                (deal_id, deal_type, deal_status, target_company, acquirer_company,
                 deal_value, deal_value_currency, enterprise_value, industry_sector,
                 geographic_region, deal_structure, announcement_date, 
                 expected_completion_date, source_url, confidence_score, 
                 extraction_method, created_date)
                VALUES
                (:deal_id, :deal_type, :deal_status, :target_company, :acquirer_company,
                 :deal_value, :deal_value_currency, :enterprise_value, :industry_sector,
                 :geographic_region, :deal_structure, :announcement_date,
                 :expected_completion_date, :source_url, :confidence_score,
                 :extraction_method, :created_date)
                ON CONFLICT (deal_id) DO UPDATE SET
                    deal_status = EXCLUDED.deal_status,
                    deal_value = EXCLUDED.deal_value,
                    last_updated = NOW()
            """)
            
            session.execute(insert_query, deal_data)
            session.commit()
            logger.debug(f"Saved deal: {item.get('target_company')} - {item.get('acquirer_company')}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving deal: {e}")
            raise
        finally:
            session.close()
    
    def _save_company(self, item, spider):
        """Save company information to database"""
        session = self.Session()
        try:
            company_data = dict(item)
            
            insert_query = text("""
                INSERT INTO companies
                (company_id, company_name, ticker_symbol, exchange, industry,
                 sector, market_cap, headquarters, revenue, employees,
                 founded_year, data_source, last_updated)
                VALUES
                (:company_id, :company_name, :ticker_symbol, :exchange, :industry,
                 :sector, :market_cap, :headquarters, :revenue, :employees,
                 :founded_year, :data_source, :last_updated)
                ON CONFLICT (company_id) DO UPDATE SET
                    market_cap = EXCLUDED.market_cap,
                    revenue = EXCLUDED.revenue,
                    employees = EXCLUDED.employees,
                    last_updated = EXCLUDED.last_updated
            """)
            
            session.execute(insert_query, company_data)
            session.commit()
            logger.debug(f"Saved company: {item.get('company_name')}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving company: {e}")
            raise
        finally:
            session.close()
    
    def _cache_item(self, item, spider):
        """Cache item in Redis for fast access"""
        try:
            cache_key = f"scraper:{spider.name}:{item.get('url', item.get('deal_id', 'unknown'))}"
            cache_data = json.dumps(dict(item), default=str)
            self.redis_client.setex(cache_key, 86400, cache_data)  # Cache for 24 hours
        except Exception as e:
            logger.warning(f"Error caching item in Redis: {e}")


class DataEnrichmentPipeline:
    """Pipeline to enrich scraped data with additional information"""
    
    def __init__(self):
        self.industry_keywords = {
            'technology': ['software', 'tech', 'ai', 'artificial intelligence', 'cloud', 'saas'],
            'healthcare': ['pharmaceutical', 'biotech', 'medical', 'healthcare', 'drug'],
            'finance': ['bank', 'financial', 'fintech', 'insurance', 'payment'],
            'energy': ['oil', 'gas', 'renewable', 'solar', 'wind', 'energy'],
            'retail': ['retail', 'consumer', 'e-commerce', 'shopping'],
            'manufacturing': ['manufacturing', 'industrial', 'automotive', 'aerospace']
        }
    
    def process_item(self, item, spider):
        # Enrich industry classification
        if hasattr(item, 'industry_sector') and not item.get('industry_sector'):
            item['industry_sector'] = self._classify_industry(item)
        
        # Calculate confidence score for deals
        if hasattr(item, 'confidence_score') and not item.get('confidence_score'):
            item['confidence_score'] = self._calculate_confidence_score(item)
        
        # Generate deal ID if missing
        if hasattr(item, 'deal_id') and not item.get('deal_id'):
            item['deal_id'] = self._generate_deal_id(item)
        
        return item
    
    def _classify_industry(self, item):
        """Classify industry based on company names and content"""
        content = ' '.join([
            str(item.get('target_company', '')),
            str(item.get('acquirer_company', '')),
            str(item.get('title', '')),
            str(item.get('content', ''))
        ]).lower()
        
        for industry, keywords in self.industry_keywords.items():
            if any(keyword in content for keyword in keywords):
                return industry
        
        return 'other'
    
    def _calculate_confidence_score(self, item):
        """Calculate confidence score based on available data"""
        score = 0.0
        max_score = 1.0
        
        # Check for required fields
        if item.get('target_company'):
            score += 0.3
        if item.get('acquirer_company'):
            score += 0.3
        if item.get('deal_value'):
            score += 0.2
        if item.get('announcement_date'):
            score += 0.1
        if item.get('source_url'):
            score += 0.1
        
        return min(score, max_score)
    
    def _generate_deal_id(self, item):
        """Generate unique deal ID"""
        import uuid
        key_data = f"{item.get('target_company', '')}-{item.get('acquirer_company', '')}-{item.get('announcement_date', '')}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, key_data))