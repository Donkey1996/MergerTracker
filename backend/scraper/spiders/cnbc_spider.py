import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader
from scrapy_playwright.page import PageMethod
from datetime import datetime, timedelta
import feedparser
import json
from urllib.parse import urljoin, urlparse
from ..items import NewsArticleItem, RSSFeedItem, DealItem


class CNBCSpider(scrapy.Spider):
    """Spider for scraping CNBC M&A news"""
    
    name = 'cnbc'
    allowed_domains = ['cnbc.com']
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 30000,
    }
    
    def start_requests(self):
        # RSS feeds for M&A content
        rss_feeds = [
            'https://www.cnbc.com/id/100003114/device/rss/rss.html',  # Markets
            'https://www.cnbc.com/id/10000115/device/rss/rss.html',   # Business
        ]
        
        # Direct M&A section URLs
        ma_urls = [
            'https://www.cnbc.com/deals-and-ipos/',
            'https://www.cnbc.com/mergers/',
        ]
        
        # Start with RSS feeds
        for feed_url in rss_feeds:
            yield Request(
                url=feed_url,
                callback=self.parse_rss_feed,
                meta={
                    'feed_type': 'rss',
                    'source': 'cnbc'
                }
            )
        
        # Then scrape M&A sections directly
        for url in ma_urls:
            yield Request(
                url=url,
                callback=self.parse_ma_section,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', 'div[data-module="ArticleBody"]'),
                    ]
                }
            )
    
    def parse_rss_feed(self, response):
        """Parse RSS feed for M&A related articles"""
        feed = feedparser.parse(response.text)
        
        for entry in feed.entries:
            # Filter for M&A related content
            ma_keywords = ['merger', 'acquisition', 'buyout', 'takeover', 'deal', 'm&a', 'ipo']
            title_lower = entry.title.lower()
            
            if any(keyword in title_lower for keyword in ma_keywords):
                loader = ItemLoader(item=RSSFeedItem(), response=response)
                loader.add_value('title', entry.title)
                loader.add_value('link', entry.link)
                loader.add_value('description', getattr(entry, 'summary', ''))
                loader.add_value('published_date', getattr(entry, 'published', ''))
                loader.add_value('source', 'cnbc')
                loader.add_value('guid', getattr(entry, 'id', entry.link))
                loader.add_value('category', 'M&A')
                
                rss_item = loader.load_item()
                yield rss_item
                
                # Follow the link to get full article
                yield Request(
                    url=entry.link,
                    callback=self.parse_article,
                    meta={
                        'playwright': True,
                        'playwright_page_methods': [
                            PageMethod('wait_for_selector', 'div[data-module="ArticleBody"]'),
                        ],
                        'rss_data': dict(rss_item)
                    }
                )
    
    def parse_ma_section(self, response):
        """Parse M&A section pages for article links"""
        article_links = response.css('.Card-titleContainer a::attr(href)').getall()
        
        for link in article_links:
            full_url = urljoin(response.url, link)
            yield Request(
                url=full_url,
                callback=self.parse_article,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', 'div[data-module="ArticleBody"]'),
                    ]
                }
            )
        
        # Handle pagination
        next_page = response.css('.PageBuilder-pageNavigation a[aria-label="Next"]::attr(href)').get()
        if next_page:
            yield Request(
                url=urljoin(response.url, next_page),
                callback=self.parse_ma_section,
                meta=response.meta
            )
    
    def parse_article(self, response):
        """Parse individual article for detailed content and deal information"""
        loader = ItemLoader(item=NewsArticleItem(), response=response)
        
        # Basic article information
        loader.add_value('url', response.url)
        loader.add_css('title', 'h1.ArticleHeader-headline::text')
        loader.add_css('content', 'div[data-module="ArticleBody"] p::text')
        loader.add_css('author', '.Author-authorName::text')
        
        # Extract publication date
        pub_date_elem = response.css('time[data-module="ArticleHeader"]::attr(datetime)').get()
        if pub_date_elem:
            loader.add_value('published_date', pub_date_elem)
        
        # Article metadata
        loader.add_value('source', 'cnbc')
        loader.add_css('category', '.ArticleHeader-eyebrow::text')
        
        # Calculate word count and reading time
        content_text = ' '.join(response.css('div[data-module="ArticleBody"] p::text').getall())
        word_count = len(content_text.split()) if content_text else 0
        reading_time = max(1, word_count // 200)  # Assume 200 words per minute
        
        loader.add_value('word_count', word_count)
        loader.add_value('reading_time', reading_time)
        
        article_item = loader.load_item()
        yield article_item
        
        # Extract deal information using AI/NLP
        yield Request(
            url=response.url,
            callback=self.extract_deal_info,
            meta={
                'article_item': dict(article_item),
                'dont_filter': True
            }
        )
    
    def extract_deal_info(self, response):
        """Extract structured deal information from article content"""
        article_data = response.meta['article_item']
        content = article_data.get('content', '')
        title = article_data.get('title', '')
        
        # Simple rule-based extraction (can be enhanced with AI/NLP)
        deal_patterns = self._extract_deal_patterns(title + ' ' + content)
        
        if deal_patterns:
            loader = ItemLoader(item=DealItem(), response=response)
            
            # Basic deal information
            loader.add_value('deal_type', deal_patterns.get('deal_type', 'acquisition'))
            loader.add_value('target_company', deal_patterns.get('target_company'))
            loader.add_value('acquirer_company', deal_patterns.get('acquirer_company'))
            loader.add_value('deal_value', deal_patterns.get('deal_value'))
            loader.add_value('deal_value_currency', 'USD')
            
            # Source and metadata
            loader.add_value('source_url', response.url)
            loader.add_value('source_article_id', article_data.get('url'))
            loader.add_value('extraction_method', 'rule_based')
            loader.add_value('created_date', datetime.utcnow().isoformat())
            
            # Try to extract dates
            announcement_date = self._extract_date_from_content(content)
            if announcement_date:
                loader.add_value('announcement_date', announcement_date)
            
            deal_item = loader.load_item()
            yield deal_item
    
    def _extract_deal_patterns(self, text):
        """Extract deal information using regex patterns"""
        import re
        
        patterns = {}
        text_lower = text.lower()
        
        # Deal type patterns
        if any(word in text_lower for word in ['acquires', 'acquisition', 'buys', 'purchased']):
            patterns['deal_type'] = 'acquisition'
        elif any(word in text_lower for word in ['merger', 'merge', 'combining']):
            patterns['deal_type'] = 'merger'
        elif any(word in text_lower for word in ['ipo', 'public offering', 'goes public']):
            patterns['deal_type'] = 'ipo'
        
        # Company name extraction (basic patterns)
        company_patterns = [
            r'([A-Z][a-zA-Z\s&]+(?:Inc|Corp|LLC|Ltd|Co\.?))',
            r'([A-Z][a-zA-Z\s&]+) (?:acquires|buys|purchases)',
            r'(?:acquires|buys|purchases) ([A-Z][a-zA-Z\s&]+)',
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if 'acquirer_company' not in patterns:
                    patterns['acquirer_company'] = matches[0].strip()
                elif 'target_company' not in patterns:
                    patterns['target_company'] = matches[0].strip()
        
        # Deal value extraction
        value_pattern = r'\\$([0-9]+(?:\\.[0-9]+)?(?:\\s*(?:billion|million|b|m)))'
        value_match = re.search(value_pattern, text_lower)
        if value_match:
            patterns['deal_value'] = value_match.group(1)
        
        return patterns
    
    def _extract_date_from_content(self, content):
        """Extract announcement date from content"""
        import re
        from dateutil import parser
        
        # Common date patterns in news articles
        date_patterns = [
            r'announced (?:on )?([A-Za-z]+ \\d{1,2}, \\d{4})',
            r'said (?:on )?([A-Za-z]+ \\d{1,2}, \\d{4})',
            r'([A-Za-z]+ \\d{1,2}, \\d{4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content)
            if match:
                try:
                    date_str = match.group(1)
                    parsed_date = parser.parse(date_str)
                    return parsed_date.isoformat()
                except:
                    continue
        
        return None