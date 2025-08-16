import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader
from scrapy_playwright.page import PageMethod
from datetime import datetime, timedelta
import json
import re
import random
import time
from urllib.parse import urljoin, urlparse, parse_qs
from ..items import NewsArticleItem, DealItem, CompanyItem


class BloombergDealsSpider(scrapy.Spider):
    """
    Specialized spider for scraping M&A deals from Bloomberg.
    
    This spider handles Bloomberg's anti-bot measures through:
    - Playwright browser automation for dynamic content
    - Sophisticated user agent rotation
    - Rate limiting with random delays
    - Respectful crawling following robots.txt
    - Graceful error handling and fallback mechanisms
    """
    
    name = 'bloomberg_deals'
    allowed_domains = ['bloomberg.com']
    
    # Conservative settings for ethical scraping
    custom_settings = {
        'DOWNLOAD_DELAY': 5,  # 5 second delay between requests
        'RANDOMIZE_DOWNLOAD_DELAY': 2,  # Random 0-4 second additional delay
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # One request at a time
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 60000,  # 60 second timeout
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'args': [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-features=VizDisplayCompositor'
            ]
        },
        'USER_AGENT_LIST': [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        ]
    }
    
    def start_requests(self):
        """Initialize crawling with Bloomberg M&A section"""
        
        # Bloomberg M&A and deals URLs
        start_urls = [
            'https://www.bloomberg.com/deals',
            'https://www.bloomberg.com/markets/deals',
            'https://www.bloomberg.com/news/industries/deals'
        ]
        
        for url in start_urls:
            yield Request(
                url=url,
                callback=self.parse_deals_section,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_timeout', 3000),  # Wait 3 seconds for page load
                        PageMethod('wait_for_load_state', 'networkidle'),  # Wait for network to be idle
                        PageMethod('evaluate', '''() => {
                            // Remove automation indicators
                            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                            delete window.chrome.runtime.onConnect;
                        }'''),
                        PageMethod('set_extra_http_headers', {
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.5',
                            'Accept-Encoding': 'gzip, deflate',
                            'Upgrade-Insecure-Requests': '1',
                            'Sec-Fetch-Dest': 'document',
                            'Sec-Fetch-Mode': 'navigate',
                            'Sec-Fetch-Site': 'none',
                            'Cache-Control': 'max-age=0',
                        }),
                    ],
                    'dont_filter': True,
                },
                headers={
                    'Referer': 'https://www.bloomberg.com/',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                errback=self.handle_error
            )
    
    def parse_deals_section(self, response):
        """Parse Bloomberg deals section for article links and deal information"""
        
        self.logger.info(f"Parsing Bloomberg deals section: {response.url}")
        
        # Check if page loaded successfully
        if response.status == 403:
            self.logger.warning(f"Access denied for {response.url}. Implementing fallback strategy.")
            yield from self._handle_access_denied(response)
            return
        
        # Multiple selectors for Bloomberg's different page layouts
        article_selectors = [
            # Main deal articles
            'article[data-module="Story"] a[href*="/news/articles/"]::attr(href)',
            '.story-package-module__story a::attr(href)',
            
            # Deal listings and summaries
            '[data-module="DealsModule"] a::attr(href)',
            '.deals-module a::attr(href)',
            
            # News articles in general layout
            '.story-list-story a::attr(href)',
            '[data-module="FeatureStory"] a::attr(href)',
            
            # Alternative selectors for different layouts
            'h3 a[href*="/news/articles/"]::attr(href)',
            '.headline a::attr(href)',
            '.story-item a::attr(href)',
        ]
        
        found_links = set()
        
        for selector in article_selectors:
            links = response.css(selector).getall()
            for link in links:
                if link and self._is_deal_related_url(link):
                    full_url = urljoin(response.url, link)
                    found_links.add(full_url)
        
        self.logger.info(f"Found {len(found_links)} potential deal-related articles")
        
        # Process each article with random delays
        for i, link in enumerate(found_links):
            # Add randomized delay between article requests
            delay = random.uniform(3, 8)  # 3-8 second random delay
            
            yield Request(
                url=link,
                callback=self.parse_article,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_timeout', 2000),
                        PageMethod('wait_for_load_state', 'domcontentloaded'),
                        PageMethod('evaluate', '''() => {
                            // Scroll to load dynamic content
                            window.scrollTo(0, document.body.scrollHeight / 2);
                        }'''),
                        PageMethod('wait_for_timeout', 1000),
                    ],
                    'download_delay': delay,
                    'priority': 10 - min(i, 9),  # Higher priority for first articles
                },
                headers=self._get_random_headers(),
                errback=self.handle_error
            )
        
        # Look for "Load More" or pagination
        load_more_selectors = [
            '.load-more-button::attr(href)',
            '[data-module="LoadMore"] a::attr(href)',
            '.pagination-next::attr(href)',
            'a[aria-label="Next page"]::attr(href)',
        ]
        
        for selector in load_more_selectors:
            next_page = response.css(selector).get()
            if next_page:
                yield Request(
                    url=urljoin(response.url, next_page),
                    callback=self.parse_deals_section,
                    meta=response.meta,
                    headers=self._get_random_headers(),
                    dont_filter=True
                )
                break  # Only follow one pagination link
    
    def parse_article(self, response):
        """Parse individual Bloomberg article for news and deal information"""
        
        self.logger.info(f"Parsing article: {response.url}")
        
        # Check for paywall or access issues
        if self._is_paywalled(response):
            self.logger.warning(f"Article appears to be paywalled: {response.url}")
            return
        
        # Extract news article information
        article_item = self._extract_article_data(response)
        if article_item:
            yield article_item
            
            # Extract deal information from the article
            deal_items = self._extract_deal_data(response, article_item)
            for deal_item in deal_items:
                yield deal_item
    
    def _extract_article_data(self, response):
        """Extract news article data from Bloomberg article page"""
        
        loader = ItemLoader(item=NewsArticleItem(), response=response)
        
        # Article metadata
        loader.add_value('url', response.url)
        loader.add_value('source', 'bloomberg')
        loader.add_value('scraped_date', datetime.utcnow().isoformat())
        
        # Title extraction - Bloomberg uses multiple possible selectors
        title_selectors = [
            'h1[data-module="ArticleHeader"]::text',
            '.headline__text::text',
            'h1.lede-text-v2__hed::text',
            'h1::text',
        ]
        
        for selector in title_selectors:
            title = response.css(selector).get()
            if title:
                loader.add_value('title', title.strip())
                break
        
        # Content extraction
        content_selectors = [
            '[data-module="ArticleBody"] p::text',
            '.article-body p::text',
            '.fence-body p::text',
            'div[data-module="Body"] p::text',
        ]
        
        content_found = False
        for selector in content_selectors:
            content_paragraphs = response.css(selector).getall()
            if content_paragraphs:
                loader.add_value('content', content_paragraphs)
                content_found = True
                break
        
        if not content_found:
            # Fallback to any paragraph text
            loader.add_css('content', 'p::text')
        
        # Author extraction
        author_selectors = [
            '[data-module="ArticleHeader"] .author::text',
            '.byline-names a::text',
            '.author-name::text',
        ]
        
        for selector in author_selectors:
            author = response.css(selector).get()
            if author:
                loader.add_value('author', author.strip())
                break
        
        # Publication date
        date_selectors = [
            'time[data-module="ArticleHeader"]::attr(datetime)',
            '.timestamp::attr(datetime)',
            'time::attr(datetime)',
        ]
        
        for selector in date_selectors:
            pub_date = response.css(selector).get()
            if pub_date:
                loader.add_value('published_date', pub_date)
                break
        
        # Calculate reading metrics
        all_text = ' '.join(response.css('p::text').getall())
        if all_text:
            word_count = len(all_text.split())
            loader.add_value('word_count', word_count)
            loader.add_value('reading_time', max(1, word_count // 200))
        
        # Category based on URL and content
        if any(keyword in response.url.lower() for keyword in ['deals', 'merger', 'acquisition']):
            loader.add_value('category', 'mergers_acquisitions')
        
        try:
            return loader.load_item()
        except Exception as e:
            self.logger.error(f"Error loading article item from {response.url}: {e}")
            return None
    
    def _extract_deal_data(self, response, article_item):
        """Extract M&A deal information from Bloomberg article"""
        
        if not article_item:
            return []
        
        title = article_item.get('title', '')
        content = ' '.join(article_item.get('content', []))
        full_text = f"{title} {content}"
        
        deals = self._parse_bloomberg_deal_patterns(full_text, response)
        
        deal_items = []
        for deal_info in deals:
            if deal_info.get('target_company') or deal_info.get('acquirer_company'):
                loader = ItemLoader(item=DealItem(), response=response)
                
                # Basic deal information
                for key, value in deal_info.items():
                    if value:
                        loader.add_value(key, value)
                
                # Source and metadata
                loader.add_value('source_url', response.url)
                loader.add_value('source_article_id', article_item.get('url'))
                loader.add_value('extraction_method', 'bloomberg_nlp_rules')
                loader.add_value('created_date', datetime.utcnow().isoformat())
                
                # Generate deal ID
                if deal_info.get('target_company') and deal_info.get('acquirer_company'):
                    deal_id = self._generate_deal_id(deal_info)
                    loader.add_value('deal_id', deal_id)
                
                try:
                    deal_item = loader.load_item()
                    deal_items.append(deal_item)
                except Exception as e:
                    self.logger.error(f"Error loading deal item: {e}")
        
        return deal_items
    
    def _parse_bloomberg_deal_patterns(self, text, response):
        """Parse Bloomberg-specific deal patterns from text"""
        
        deals = []
        text_lower = text.lower()
        
        # Bloomberg deal patterns
        deal_patterns = [
            # Acquisition patterns
            {
                'type': 'acquisition',
                'patterns': [
                    r'(\w+(?:\s+\w+)*?)\s+(?:agrees to acquire|will acquire|is acquiring|agreed to buy|will buy|is buying)\s+(\w+(?:\s+\w+)*?)(?:\s+for|\s+in a deal)',
                    r'(\w+(?:\s+\w+)*?)\s+to\s+(?:acquire|buy|purchase)\s+(\w+(?:\s+\w+)*?)(?:\s+for|\s+in)',
                    r'acquisition\s+of\s+(\w+(?:\s+\w+)*?)\s+by\s+(\w+(?:\s+\w+)*?)',
                    r'(\w+(?:\s+\w+)*?)\s+(?:acquires|bought|purchased)\s+(\w+(?:\s+\w+)*?)',
                ]
            },
            # Merger patterns
            {
                'type': 'merger',
                'patterns': [
                    r'(\w+(?:\s+\w+)*?)\s+(?:merges with|to merge with|merging with)\s+(\w+(?:\s+\w+)*?)',
                    r'merger\s+(?:between|of)\s+(\w+(?:\s+\w+)*?)\s+and\s+(\w+(?:\s+\w+)*?)',
                    r'(\w+(?:\s+\w+)*?)\s+and\s+(\w+(?:\s+\w+)*?)\s+(?:to merge|will merge|are merging)',
                ]
            },
            # IPO patterns
            {
                'type': 'ipo',
                'patterns': [
                    r'(\w+(?:\s+\w+)*?)\s+(?:files for|plans|prepares for)\s+(?:ipo|initial public offering)',
                    r'(\w+(?:\s+\w+)*?)\s+(?:goes public|going public)',
                ]
            }
        ]
        
        for deal_type_info in deal_patterns:
            deal_type = deal_type_info['type']
            
            for pattern in deal_type_info['patterns']:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                
                for match in matches:
                    deal_info = {'deal_type': deal_type}
                    
                    if deal_type == 'acquisition':
                        deal_info['acquirer_company'] = self._clean_company_name(match.group(1))
                        if match.lastindex >= 2:
                            deal_info['target_company'] = self._clean_company_name(match.group(2))
                    
                    elif deal_type == 'merger':
                        deal_info['target_company'] = self._clean_company_name(match.group(1))
                        if match.lastindex >= 2:
                            deal_info['acquirer_company'] = self._clean_company_name(match.group(2))
                    
                    elif deal_type == 'ipo':
                        deal_info['target_company'] = self._clean_company_name(match.group(1))
                        deal_info['deal_type'] = 'ipo'
                    
                    # Extract deal value
                    deal_value_info = self._extract_deal_value(text, match.start(), match.end())
                    deal_info.update(deal_value_info)
                    
                    # Extract date information
                    date_info = self._extract_deal_dates(text, match.start(), match.end())
                    deal_info.update(date_info)
                    
                    # Extract industry/sector
                    sector_info = self._extract_sector_info(text, deal_info)
                    deal_info.update(sector_info)
                    
                    deals.append(deal_info)
        
        return deals
    
    def _extract_deal_value(self, text, match_start, match_end):
        """Extract deal value from surrounding text"""
        
        # Look around the match for value information
        context_start = max(0, match_start - 200)
        context_end = min(len(text), match_end + 200)
        context = text[context_start:context_end].lower()
        
        value_patterns = [
            r'\$([0-9,]+(?:\.[0-9]+)?)\s*(billion|million|b|m)(?:\s|$)',
            r'worth\s+\$([0-9,]+(?:\.[0-9]+)?)\s*(billion|million|b|m)?',
            r'valued\s+at\s+\$([0-9,]+(?:\.[0-9]+)?)\s*(billion|million|b|m)?',
            r'deal\s+worth\s+\$([0-9,]+(?:\.[0-9]+)?)\s*(billion|million|b|m)?',
            r'for\s+\$([0-9,]+(?:\.[0-9]+)?)\s*(billion|million|b|m)?',
        ]
        
        for pattern in value_patterns:
            match = re.search(pattern, context)
            if match:
                value_str = match.group(1).replace(',', '')
                try:
                    value = float(value_str)
                    unit = match.group(2) if match.lastindex >= 2 and match.group(2) else ''
                    
                    # Convert to standard format (dollars)
                    if unit.lower() in ['billion', 'b']:
                        value *= 1000000000
                    elif unit.lower() in ['million', 'm']:
                        value *= 1000000
                    
                    return {
                        'deal_value': value,
                        'deal_value_currency': 'USD'
                    }
                except ValueError:
                    continue
        
        return {}
    
    def _extract_deal_dates(self, text, match_start, match_end):
        """Extract relevant dates from deal text"""
        
        context_start = max(0, match_start - 100)
        context_end = min(len(text), match_end + 100)
        context = text[context_start:context_end]
        
        date_info = {}
        
        # Look for announcement dates
        date_patterns = [
            r'announced\s+(?:on\s+)?([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'said\s+(?:on\s+)?([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'on\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(1)
                    # Parse date (simplified - in production use proper date parsing)
                    date_info['announcement_date'] = date_str
                    break
                except:
                    continue
        
        return date_info
    
    def _extract_sector_info(self, text, deal_info):
        """Extract industry sector information"""
        
        sector_keywords = {
            'technology': ['tech', 'software', 'ai', 'artificial intelligence', 'cloud', 'saas', 'digital'],
            'healthcare': ['pharma', 'pharmaceutical', 'biotech', 'medical', 'healthcare', 'drug', 'medicine'],
            'finance': ['bank', 'financial', 'fintech', 'insurance', 'payment', 'credit', 'investment'],
            'energy': ['oil', 'gas', 'renewable', 'solar', 'wind', 'energy', 'petroleum', 'power'],
            'retail': ['retail', 'consumer', 'e-commerce', 'shopping', 'store', 'brand'],
            'manufacturing': ['manufacturing', 'industrial', 'automotive', 'aerospace', 'factory'],
            'real_estate': ['real estate', 'property', 'reit', 'construction', 'development'],
            'telecommunications': ['telecom', 'wireless', 'mobile', 'network', 'communications'],
        }
        
        text_lower = text.lower()
        company_text = f"{deal_info.get('target_company', '')} {deal_info.get('acquirer_company', '')}".lower()
        
        for sector, keywords in sector_keywords.items():
            if any(keyword in text_lower or keyword in company_text for keyword in keywords):
                return {'industry_sector': sector}
        
        return {'industry_sector': 'other'}
    
    def _clean_company_name(self, name):
        """Clean and normalize company names"""
        if not name:
            return None
        
        # Remove common noise words
        noise_words = ['inc', 'corp', 'ltd', 'llc', 'co', 'company', 'the', 'a', 'an']
        
        # Clean name
        cleaned = name.strip().title()
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned
    
    def _generate_deal_id(self, deal_info):
        """Generate unique deal ID"""
        import hashlib
        
        key_components = [
            deal_info.get('target_company', ''),
            deal_info.get('acquirer_company', ''),
            deal_info.get('deal_type', ''),
            str(deal_info.get('deal_value', '')),
        ]
        
        key_string = '|'.join(key_components).lower()
        return hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    def _is_deal_related_url(self, url):
        """Check if URL is related to M&A deals"""
        
        deal_keywords = [
            'deal', 'merger', 'acquisition', 'buyout', 'takeover',
            'm-a', 'ipo', 'spac', 'private-equity', 'leveraged-buyout',
            'consolidation', 'joint-venture', 'partnership'
        ]
        
        url_lower = url.lower()
        return any(keyword in url_lower for keyword in deal_keywords)
    
    def _is_paywalled(self, response):
        """Check if the article is behind a paywall"""
        
        paywall_indicators = [
            'paywall',
            'subscription required',
            'subscribe to continue',
            'premium content',
            'subscriber exclusive'
        ]
        
        page_text = response.text.lower()
        return any(indicator in page_text for indicator in paywall_indicators)
    
    def _get_random_headers(self):
        """Get randomized headers for requests"""
        
        user_agents = self.custom_settings['USER_AGENT_LIST']
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.bloomberg.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _handle_access_denied(self, response):
        """Handle access denied scenarios with fallback strategies"""
        
        self.logger.warning("Implementing fallback strategy for Bloomberg access restrictions")
        
        # Try alternative Bloomberg RSS feeds or structured endpoints
        fallback_urls = [
            'https://feeds.bloomberg.com/markets/deals.rss',
            'https://www.bloomberg.com/markets/deals?rss=true',
        ]
        
        for url in fallback_urls:
            yield Request(
                url=url,
                callback=self.parse_rss_feed,
                headers=self._get_random_headers(),
                dont_filter=True
            )
    
    def parse_rss_feed(self, response):
        """Parse RSS feed as fallback method"""
        
        try:
            import feedparser
            
            feed = feedparser.parse(response.text)
            
            for entry in feed.entries:
                if hasattr(entry, 'link') and self._is_deal_related_url(entry.link):
                    yield Request(
                        url=entry.link,
                        callback=self.parse_article,
                        meta={'playwright': True},
                        headers=self._get_random_headers()
                    )
        
        except Exception as e:
            self.logger.error(f"Error parsing RSS feed: {e}")
    
    def handle_error(self, failure):
        """Handle spider errors gracefully"""
        
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}")
        
        # Log error details for monitoring
        if hasattr(failure.value, 'response'):
            response = failure.value.response
            self.logger.error(f"Response status: {response.status}")
            
            # If blocked, implement exponential backoff
            if response.status in [403, 429, 503]:
                self.logger.warning("Implementing exponential backoff due to rate limiting")
                # The spider will naturally slow down due to the download delay settings
        
        return None