import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader
from scrapy_playwright.page import PageMethod
from datetime import datetime
import json
import yfinance as yf
from urllib.parse import urljoin, urlparse
from ..items import NewsArticleItem, DealItem, CompanyItem


class YahooFinanceSpider(scrapy.Spider):
    """Spider for scraping Yahoo Finance M&A news and company data"""
    
    name = 'yahoo_finance'
    allowed_domains = ['finance.yahoo.com']
    custom_settings = {
        'DOWNLOAD_DELAY': 3,  # More conservative due to ToS restrictions
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 30000,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
    }
    
    def start_requests(self):
        # M&A specific URLs
        urls = [
            'https://finance.yahoo.com/topic/mergers-ipos/',
            'https://finance.yahoo.com/news/category/mergers-acquisitions',
        ]
        
        for url in urls:
            yield Request(
                url=url,
                callback=self.parse_ma_section,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', '[data-testid="news-stream"]'),
                    ]
                }
            )
    
    def parse_ma_section(self, response):
        """Parse M&A section for article links"""
        # Yahoo Finance uses different selectors for news items
        article_selectors = [
            '[data-testid="news-stream"] h3 a',
            '.Ov(h) .Fw(b) a',
            '.js-stream-content h3 a',
        ]
        
        article_links = []
        for selector in article_selectors:
            links = response.css(f'{selector}::attr(href)').getall()
            article_links.extend(links)
        
        for link in article_links:
            # Handle both relative and absolute URLs
            if link.startswith('/'):
                full_url = urljoin('https://finance.yahoo.com', link)
            elif link.startswith('http'):
                full_url = link
            else:
                full_url = urljoin(response.url, link)
            
            # Filter for M&A related content
            if self._is_ma_related_url(full_url):
                yield Request(
                    url=full_url,
                    callback=self.parse_article,
                    meta={
                        'playwright': True,
                        'playwright_page_methods': [
                            PageMethod('wait_for_selector', '[data-testid="caas-body"]'),
                        ]
                    }
                )
        
        # Handle "Load More" or pagination
        load_more = response.css('[data-testid="load-more-news"]::attr(href)').get()
        if load_more:
            yield Request(
                url=urljoin(response.url, load_more),
                callback=self.parse_ma_section,
                meta=response.meta
            )
    
    def parse_article(self, response):
        """Parse individual Yahoo Finance article"""
        loader = ItemLoader(item=NewsArticleItem(), response=response)
        
        # Article metadata
        loader.add_value('url', response.url)
        loader.add_css('title', 'h1[data-testid="headline"]::text')
        
        # Content extraction - Yahoo uses different structures
        content_selectors = [
            '[data-testid="caas-body"] p::text',
            '.caas-body p::text',
            '.article-body p::text',
        ]
        
        content_found = False
        for selector in content_selectors:
            content = response.css(selector).getall()
            if content:
                loader.add_value('content', content)
                content_found = True
                break
        
        if not content_found:
            # Fallback to general paragraph extraction
            loader.add_css('content', 'div p::text')
        
        # Author and publication date
        loader.add_css('author', '[data-testid="author-name"]::text')
        
        # Try multiple date selectors
        date_selectors = [
            'time::attr(datetime)',
            '[data-testid="published-date"]::attr(datetime)',
            '.caas-attr-time-style::attr(datetime)',
        ]
        
        for selector in date_selectors:
            pub_date = response.css(selector).get()
            if pub_date:
                loader.add_value('published_date', pub_date)
                break
        
        # Article properties
        loader.add_value('source', 'yahoo_finance')
        
        # Calculate metrics
        content_text = ' '.join(response.css('[data-testid="caas-body"] p::text').getall())
        if content_text:
            word_count = len(content_text.split())
            loader.add_value('word_count', word_count)
            loader.add_value('reading_time', max(1, word_count // 200))
        
        article_item = loader.load_item()
        yield article_item
        
        # Extract deal information
        yield Request(
            url=response.url,
            callback=self.extract_deal_info,
            meta={
                'article_item': dict(article_item),
                'dont_filter': True
            }
        )
    
    def extract_deal_info(self, response):
        """Extract deal information from Yahoo Finance articles"""
        article_data = response.meta['article_item']
        content = article_data.get('content', '')
        title = article_data.get('title', '')
        full_text = title + ' ' + content
        
        # Enhanced deal extraction for Yahoo Finance
        deal_info = self._extract_yahoo_deal_patterns(full_text, response)
        
        if deal_info and deal_info.get('target_company') and deal_info.get('acquirer_company'):
            loader = ItemLoader(item=DealItem(), response=response)
            
            # Deal details
            for key, value in deal_info.items():
                if value:
                    loader.add_value(key, value)
            
            # Source metadata
            loader.add_value('source_url', response.url)
            loader.add_value('source_article_id', article_data.get('url'))
            loader.add_value('extraction_method', 'yahoo_finance_rules')
            loader.add_value('created_date', datetime.utcnow().isoformat())
            
            deal_item = loader.load_item()
            yield deal_item
            
            # Also try to get company information using yfinance
            for company in [deal_info.get('target_company'), deal_info.get('acquirer_company')]:
                if company:
                    yield Request(
                        url=f'https://finance.yahoo.com/quote/{self._get_ticker_symbol(company)}',
                        callback=self.extract_company_info,
                        meta={'company_name': company},
                        dont_filter=True
                    )
    
    def extract_company_info(self, response):
        """Extract company information using yfinance API and web scraping"""
        company_name = response.meta['company_name']
        
        # Try to find ticker symbol from the page
        ticker_symbol = self._extract_ticker_from_page(response)
        
        if ticker_symbol:
            try:
                # Use yfinance to get company data
                ticker = yf.Ticker(ticker_symbol)
                info = ticker.info
                
                loader = ItemLoader(item=CompanyItem(), response=response)
                
                # Basic company information
                loader.add_value('company_name', company_name)
                loader.add_value('ticker_symbol', ticker_symbol)
                loader.add_value('exchange', info.get('exchange'))
                
                # Financial metrics
                loader.add_value('market_cap', info.get('marketCap'))
                loader.add_value('revenue', info.get('totalRevenue'))
                loader.add_value('employees', info.get('fullTimeEmployees'))
                
                # Company details
                loader.add_value('industry', info.get('industry'))
                loader.add_value('sector', info.get('sector'))
                loader.add_value('headquarters', f"{info.get('city', '')}, {info.get('country', '')}")
                
                # Metadata
                loader.add_value('data_source', 'yahoo_finance')
                loader.add_value('last_updated', datetime.utcnow().isoformat())
                
                # Generate company ID
                company_id = f"yf_{ticker_symbol.lower()}"
                loader.add_value('company_id', company_id)
                
                company_item = loader.load_item()
                yield company_item
                
            except Exception as e:
                self.logger.warning(f"Could not fetch company data for {ticker_symbol}: {e}")
    
    def _is_ma_related_url(self, url):
        """Check if URL is related to M&A content"""
        ma_keywords = [
            'merger', 'acquisition', 'buyout', 'takeover', 'deal', 'm-a', 
            'ipo', 'spac', 'private-equity', 'leveraged-buyout'
        ]
        url_lower = url.lower()
        return any(keyword in url_lower for keyword in ma_keywords)
    
    def _extract_yahoo_deal_patterns(self, text, response):
        """Extract deal patterns specific to Yahoo Finance content"""
        import re
        
        patterns = {}
        text_lower = text.lower()
        
        # Enhanced deal type detection
        deal_type_patterns = {
            'acquisition': [
                r'(\\w+(?:\\s+\\w+)*?)\\s+(?:acquires|acquired|buying|bought|purchases|purchased)\\s+(\\w+(?:\\s+\\w+)*?)',
                r'(\\w+(?:\\s+\\w+)*?)\\s+to\\s+(?:acquire|buy|purchase)\\s+(\\w+(?:\\s+\\w+)*?)',
                r'acquisition\\s+of\\s+(\\w+(?:\\s+\\w+)*?)\\s+by\\s+(\\w+(?:\\s+\\w+)*?)'
            ],
            'merger': [
                r'(\\w+(?:\\s+\\w+)*?)\\s+(?:merges?|merging)\\s+with\\s+(\\w+(?:\\s+\\w+)*?)',
                r'merger\\s+between\\s+(\\w+(?:\\s+\\w+)*?)\\s+and\\s+(\\w+(?:\\s+\\w+)*?)'
            ],
            'ipo': [
                r'(\\w+(?:\\s+\\w+)*?)\\s+(?:goes?\\s+public|ipo|initial\\s+public\\s+offering)'
            ]
        }
        
        # Try to match deal patterns
        for deal_type, type_patterns in deal_type_patterns.items():
            for pattern in type_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    patterns['deal_type'] = deal_type
                    if deal_type == 'acquisition':
                        patterns['acquirer_company'] = match.group(1).strip().title()
                        if match.lastindex >= 2:
                            patterns['target_company'] = match.group(2).strip().title()
                    elif deal_type == 'merger':
                        patterns['target_company'] = match.group(1).strip().title()
                        if match.lastindex >= 2:
                            patterns['acquirer_company'] = match.group(2).strip().title()
                    elif deal_type == 'ipo':
                        patterns['target_company'] = match.group(1).strip().title()
                    break
            if patterns:
                break
        
        # Enhanced deal value extraction
        value_patterns = [
            r'\\$([0-9,]+(?:\\.[0-9]+)?)\\s*(billion|million|b|m)\\b',
            r'worth\\s+\\$([0-9,]+(?:\\.[0-9]+)?)\\s*(billion|million|b|m)?',
            r'valued\\s+at\\s+\\$([0-9,]+(?:\\.[0-9]+)?)\\s*(billion|million|b|m)?',
            r'deal\\s+worth\\s+\\$([0-9,]+(?:\\.[0-9]+)?)\\s*(billion|million|b|m)?'
        ]
        
        for pattern in value_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = match.group(1).replace(',', '')
                unit = match.group(2) if match.lastindex >= 2 else ''
                
                # Convert to standard format
                numeric_value = float(value)
                if unit and unit.lower() in ['billion', 'b']:
                    numeric_value *= 1000000000
                elif unit and unit.lower() in ['million', 'm']:
                    numeric_value *= 1000000
                
                patterns['deal_value'] = numeric_value
                patterns['deal_value_currency'] = 'USD'
                break
        
        return patterns
    
    def _get_ticker_symbol(self, company_name):
        """Attempt to derive ticker symbol from company name"""
        # This is a simplified approach - in production, you'd want a more robust lookup
        ticker_hints = {
            'apple': 'AAPL',
            'microsoft': 'MSFT',
            'google': 'GOOGL',
            'alphabet': 'GOOGL',
            'amazon': 'AMZN',
            'tesla': 'TSLA',
            'meta': 'META',
            'facebook': 'META',
        }
        
        company_lower = company_name.lower()
        for hint, ticker in ticker_hints.items():
            if hint in company_lower:
                return ticker
        
        # Default approach: use first 3-4 letters
        clean_name = ''.join(c for c in company_name if c.isalpha())
        return clean_name[:4].upper()
    
    def _extract_ticker_from_page(self, response):
        """Extract ticker symbol from Yahoo Finance page"""
        # Try various selectors for ticker symbols
        ticker_selectors = [
            '[data-testid="quote-header-info"] h1::text',
            '.D\\(ib\\).Fz\\(18px\\)::text',
            '[data-reactid*="symbol"]::text',
        ]
        
        for selector in ticker_selectors:
            ticker_text = response.css(selector).get()
            if ticker_text and '(' in ticker_text and ')' in ticker_text:
                # Extract text between parentheses
                import re
                match = re.search(r'\\(([A-Z]+)\\)', ticker_text)
                if match:
                    return match.group(1)
        
        return None