import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader
from scrapy_playwright.page import PageMethod
from datetime import datetime
import re
from urllib.parse import urljoin
from ..items import NewsArticleItem, DealItem


class MarketWatchSpider(scrapy.Spider):
    """Spider for scraping MarketWatch M&A news"""
    
    name = 'marketwatch'
    allowed_domains = ['marketwatch.com']
    custom_settings = {
        'DOWNLOAD_DELAY': 4,  # Conservative approach
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 30000,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
    }
    
    def start_requests(self):
        # MarketWatch M&A and corporate news sections
        urls = [
            'https://www.marketwatch.com/markets/deals',
            'https://www.marketwatch.com/news/corporate',
            'https://www.marketwatch.com/search?q=merger+acquisition&m=Keyword&rpp=25&mp=2007&bd=false&rs=true',
        ]
        
        for url in urls:
            yield Request(
                url=url,
                callback=self.parse_section,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', '.article__content, .collection__elements'),
                    ]
                }
            )
    
    def parse_section(self, response):
        """Parse MarketWatch sections for M&A articles"""
        # MarketWatch uses different layouts - try multiple selectors
        article_selectors = [
            '.collection__elements .article__content h3 a',
            '.element--article h3 a',
            '.article-summary h3 a',
            '.headlines .article__content h3 a',
        ]
        
        article_links = []
        for selector in article_selectors:
            links = response.css(f'{selector}::attr(href)').getall()
            article_links.extend(links)
        
        # Filter and process article links
        for link in article_links:
            full_url = urljoin(response.url, link)
            
            # Check if article is M&A related
            if self._is_ma_related_link(link, response):
                yield Request(
                    url=full_url,
                    callback=self.parse_article,
                    meta={
                        'playwright': True,
                        'playwright_page_methods': [
                            PageMethod('wait_for_selector', '.article__body, .articleWrap'),
                        ]
                    }
                )
        
        # Handle pagination
        next_page_selectors = [
            '.pagination .next-page::attr(href)',
            '.btn-more-content::attr(href)',
            '.load-more::attr(data-url)',
        ]
        
        for selector in next_page_selectors:
            next_page = response.css(selector).get()
            if next_page:
                yield Request(
                    url=urljoin(response.url, next_page),
                    callback=self.parse_section,
                    meta=response.meta
                )
                break
    
    def parse_article(self, response):
        """Parse individual MarketWatch article"""
        loader = ItemLoader(item=NewsArticleItem(), response=response)
        
        # Article identification
        loader.add_value('url', response.url)
        
        # Title extraction - try multiple selectors
        title_selectors = [
            'h1.article__headline::text',
            '.articleWrap h1::text',
            '.headline h1::text',
        ]
        
        for selector in title_selectors:
            title = response.css(selector).get()
            if title:
                loader.add_value('title', title)
                break
        
        # Content extraction
        content_selectors = [
            '.article__body p::text',
            '.articleWrap .paywall p::text',
            '.articleWrap > p::text',
            '.story p::text',
        ]
        
        content_found = False
        for selector in content_selectors:
            content = response.css(selector).getall()
            if content:
                loader.add_value('content', content)
                content_found = True
                break
        
        # Author information
        author_selectors = [
            '.author-name::text',
            '.article__author .author::text',
            '.byline .author::text',
        ]
        
        for selector in author_selectors:
            author = response.css(selector).get()
            if author:
                loader.add_value('author', author)
                break
        
        # Publication date
        date_selectors = [
            '.timestamp::attr(data-est)',
            '.article__timestamp time::attr(datetime)',
            '.date-published::attr(datetime)',
        ]
        
        for selector in date_selectors:
            pub_date = response.css(selector).get()
            if pub_date:
                loader.add_value('published_date', pub_date)
                break
        
        # Article metadata
        loader.add_value('source', 'marketwatch')
        loader.add_css('category', '.article__sector::text')
        
        # Calculate word count and reading time
        content_text = ' '.join(response.css('.article__body p::text').getall())
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
        """Extract deal information from MarketWatch articles"""
        article_data = response.meta['article_item']
        content = article_data.get('content', '')
        title = article_data.get('title', '')
        full_text = title + ' ' + content
        
        # MarketWatch-specific deal extraction
        deal_info = self._extract_marketwatch_deals(full_text, response.url)
        
        if deal_info and (deal_info.get('target_company') or deal_info.get('acquirer_company')):
            loader = ItemLoader(item=DealItem(), response=response)
            
            # Basic deal information
            for key, value in deal_info.items():
                if value:
                    loader.add_value(key, value)
            
            # Default currency for MarketWatch (primarily US focused)
            if deal_info.get('deal_value'):
                loader.add_value('deal_value_currency', 'USD')
            
            # Source metadata
            loader.add_value('source_url', response.url)
            loader.add_value('source_article_id', article_data.get('url'))
            loader.add_value('extraction_method', 'marketwatch_rules')
            loader.add_value('created_date', datetime.utcnow().isoformat())
            
            deal_item = loader.load_item()
            yield deal_item
    
    def _is_ma_related_link(self, link, response):
        """Check if a link is related to M&A content"""
        ma_keywords = [
            'merger', 'acquisition', 'buyout', 'takeover', 'deal', 
            'acquire', 'merge', 'buy', 'purchase', 'ipo', 'spac'
        ]
        
        # Check the link URL itself
        link_lower = link.lower()
        if any(keyword in link_lower for keyword in ma_keywords):
            return True
        
        # Check the article headline/title near the link
        link_element = response.css(f'a[href="{link}"]')
        if link_element:
            link_text = link_element.css('::text').get() or ''
            title_text = link_element.xpath('./ancestor::*//text()').getall()
            combined_text = (link_text + ' ' + ' '.join(title_text)).lower()
            
            if any(keyword in combined_text for keyword in ma_keywords):
                return True
        
        return False
    
    def _extract_marketwatch_deals(self, text, source_url):
        """Extract deal information using MarketWatch-specific patterns"""
        patterns = {}
        text_lower = text.lower()
        
        # MarketWatch often uses specific language patterns
        deal_patterns = {
            'acquisition': [
                r'([\\w\\s&]+)\\s+(?:said|announced)\\s+it\\s+(?:would\\s+)?(?:acquire|buy|purchase)\\s+([\\w\\s&]+)',
                r'([\\w\\s&]+)\\s+to\\s+(?:acquire|buy|purchase)\\s+([\\w\\s&]+)',
                r'([\\w\\s&]+)\\s+acquires\\s+([\\w\\s&]+)',
                r'acquisition\\s+of\\s+([\\w\\s&]+)\\s+by\\s+([\\w\\s&]+)',
            ],
            'merger': [
                r'([\\w\\s&]+)\\s+(?:and|&)\\s+([\\w\\s&]+)\\s+(?:to\\s+)?merge',
                r'merger\\s+(?:of|between)\\s+([\\w\\s&]+)\\s+(?:and|&)\\s+([\\w\\s&]+)',
                r'([\\w\\s&]+)\\s+merges\\s+with\\s+([\\w\\s&]+)',
            ],
            'ipo': [
                r'([\\w\\s&]+)\\s+(?:files\\s+for\\s+)?ipo',
                r'([\\w\\s&]+)\\s+goes\\s+public',
                r'initial\\s+public\\s+offering.*?(?:of|by)\\s+([\\w\\s&]+)',
            ]
        }
        
        # Try to match deal patterns
        for deal_type, type_patterns in deal_patterns.items():
            for pattern in type_patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    patterns['deal_type'] = deal_type
                    
                    if deal_type == 'acquisition':
                        patterns['acquirer_company'] = self._clean_company_name(match.group(1))
                        if match.lastindex >= 2:
                            patterns['target_company'] = self._clean_company_name(match.group(2))
                    elif deal_type == 'merger':
                        patterns['target_company'] = self._clean_company_name(match.group(1))
                        if match.lastindex >= 2:
                            patterns['acquirer_company'] = self._clean_company_name(match.group(2))
                    elif deal_type == 'ipo':
                        patterns['target_company'] = self._clean_company_name(match.group(1))
                    
                    break
            if patterns:
                break
        
        # Deal value extraction with MarketWatch-specific patterns
        value_patterns = [
            r'(?:deal\\s+(?:worth|valued)\\s+at\\s+)?\\$([0-9,]+(?:\\.[0-9]+)?)\\s*(billion|million|b|m)\\b',
            r'(?:transaction\\s+of\\s+)?\\$([0-9,]+(?:\\.[0-9]+)?)\\s*(billion|million|b|m)?',
            r'([0-9,]+(?:\\.[0-9]+)?)\\s*(?:\\$)?\\s*(billion|million)\\s+(?:deal|transaction)',
            r'valued\\s+at\\s+about\\s+\\$([0-9,]+(?:\\.[0-9]+)?)\\s*(billion|million)?',
        ]
        
        for pattern in value_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value_str = match.group(1).replace(',', '')
                unit = match.group(2) if match.lastindex >= 2 else ''
                
                try:
                    numeric_value = float(value_str)
                    if unit and unit.lower() in ['billion', 'b']:
                        numeric_value *= 1000000000
                    elif unit and unit.lower() in ['million', 'm']:
                        numeric_value *= 1000000
                    
                    patterns['deal_value'] = numeric_value
                    break
                except ValueError:
                    continue
        
        # Industry classification based on MarketWatch categories
        industry_patterns = {
            'technology': [
                'tech', 'software', 'cloud', 'ai', 'artificial intelligence',
                'semiconductor', 'chip', 'internet', 'digital'
            ],
            'healthcare': [
                'pharmaceutical', 'biotech', 'medical', 'healthcare', 
                'drug', 'hospital', 'clinical'
            ],
            'finance': [
                'bank', 'financial', 'fintech', 'insurance', 'investment',
                'credit', 'payment', 'lending'
            ],
            'energy': [
                'oil', 'gas', 'energy', 'renewable', 'solar', 'wind',
                'petroleum', 'drilling'
            ],
            'manufacturing': [
                'manufacturing', 'industrial', 'automotive', 'aerospace',
                'defense', 'machinery'
            ]
        }
        
        for industry, keywords in industry_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                patterns['industry_sector'] = industry
                break
        
        # Extract announcement date
        date_patterns = [
            r'announced\\s+(?:on\\s+)?([a-z]+\\s+\\d{1,2},?\\s+\\d{4})',
            r'said\\s+(?:on\\s+)?([a-z]+\\s+\\d{1,2},?\\s+\\d{4})',
            r'([a-z]+\\s+\\d{1,2},?\\s+\\d{4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    from dateutil import parser
                    date_str = match.group(1)
                    parsed_date = parser.parse(date_str)
                    patterns['announcement_date'] = parsed_date.isoformat()
                    break
                except:
                    continue
        
        return patterns
    
    def _clean_company_name(self, company_name):
        """Clean and normalize company name"""
        if not company_name:
            return None
        
        # Remove common words and clean up
        company_name = company_name.strip()
        
        # Remove common stop words at the beginning
        stop_words = ['the', 'a', 'an', 'said', 'announced', 'will', 'would']
        words = company_name.lower().split()
        
        # Filter out stop words
        cleaned_words = []
        for word in words:
            if word not in stop_words and len(word) > 2:
                cleaned_words.append(word)
        
        if cleaned_words:
            # Capitalize each word
            return ' '.join(word.capitalize() for word in cleaned_words)
        
        return company_name.title()