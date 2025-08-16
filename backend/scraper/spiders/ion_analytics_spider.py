import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader
from datetime import datetime, timedelta
import json
import re
from urllib.parse import urljoin, urlparse, parse_qs
from ..items import NewsArticleItem, DealItem

# Try to import Playwright components, fallback gracefully
try:
    from scrapy_playwright.page import PageMethod
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    # Define a dummy PageMethod for compatibility
    class PageMethod:
        def __init__(self, *args, **kwargs):
            pass


class IonAnalyticsSpider(scrapy.Spider):
    """Spider for scraping Ion Analytics merger market news and intelligence"""
    
    name = 'ion_analytics'
    allowed_domains = ['ionanalytics.com']
    custom_settings = {
        'DOWNLOAD_DELAY': 4,  # Respect rate limiting (3-5 seconds)
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 45000,
        'PLAYWRIGHT_PAGE_CLOSE_TIMEOUT': 30000,
    }
    
    def start_requests(self):
        """Initialize scraping with the main news intelligence page"""
        base_url = (
            'https://ionanalytics.com/insights/tag/news-intelligence/'
            '?postcat=mergermarket&posttag=news-intelligence&vertCat=&reg=&ind='
        )
        
        # Use Playwright if available, otherwise fallback to standard scraping
        meta = {
            'page_number': 1,
            'total_posts': None
        }
        
        if PLAYWRIGHT_AVAILABLE:
            meta.update({
                'playwright': True,
                'playwright_page_methods': [
                    PageMethod('wait_for_selector', '.masonry-item', timeout=30000),
                    PageMethod('wait_for_load_state', 'networkidle'),
                ],
            })
        
        yield Request(
            url=base_url,
            callback=self.parse_news_listing,
            meta=meta
        )
    
    def parse_news_listing(self, response):
        """Parse the news listing page and extract article links"""
        # Extract article cards from the masonry layout
        article_cards = response.css('.masonry-item')
        
        for card in article_cards:
            article_url = card.css('a::attr(href)').get()
            title = card.css('.insight-card-title::text').get()
            category = card.css('.insight-card-category::text').get()
            date_text = card.css('.insight-card-date::text').get()
            
            if article_url:
                # Follow article link to get full content
                article_meta = {
                    'preview_data': {
                        'title': title,
                        'category': category,
                        'date_text': date_text,
                    }
                }
                
                if PLAYWRIGHT_AVAILABLE:
                    article_meta.update({
                        'playwright': True,
                        'playwright_page_methods': [
                            PageMethod('wait_for_selector', '.post-content, .entry-content', timeout=30000),
                        ],
                    })
                
                yield Request(
                    url=urljoin(response.url, article_url),
                    callback=self.parse_article,
                    meta=article_meta
                )
        
        # Handle pagination via AJAX load more
        yield from self._handle_ajax_pagination(response)
    
    def _handle_ajax_pagination(self, response):
        """Handle AJAX-based pagination with load more functionality"""
        page_number = response.meta.get('page_number', 1)
        total_posts = response.meta.get('total_posts')
        
        # Extract total posts from page if not already known
        if total_posts is None:
            # Look for total posts indicator
            posts_text = response.css('.posts-found::text').get() or ''
            total_match = re.search(r'(\d+)\s*posts?', posts_text)
            if total_match:
                total_posts = int(total_match.group(1))
            else:
                total_posts = 918  # Fallback based on initial analysis
        
        # Calculate if more pages exist (6 posts per page based on analysis)
        posts_per_page = 6
        current_post_count = page_number * posts_per_page
        
        if current_post_count < total_posts:
            # Make AJAX request for next page
            ajax_url = 'https://ionanalytics.com/wp-admin/admin-ajax.php'
            
            ajax_data = {
                'action': 'load_more_posts',
                'page': page_number + 1,
                'postcat': 'mergermarket',
                'posttag': 'news-intelligence',
                'vertCat': '',
                'reg': '',
                'ind': '',
            }
            
            yield Request(
                url=ajax_url,
                method='POST',
                body=self._build_ajax_body(ajax_data),
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': response.url,
                },
                callback=self.parse_ajax_response,
                meta={
                    'page_number': page_number + 1,
                    'total_posts': total_posts,
                }
            )
    
    def _build_ajax_body(self, data):
        """Build AJAX request body from data dictionary"""
        from urllib.parse import urlencode
        return urlencode(data)
    
    def parse_ajax_response(self, response):
        """Parse AJAX response containing more articles"""
        try:
            # The AJAX response likely contains HTML fragments
            # Parse the returned content for article cards
            article_cards = response.css('.masonry-item')
            
            for card in article_cards:
                article_url = card.css('a::attr(href)').get()
                title = card.css('.insight-card-title::text').get()
                category = card.css('.insight-card-category::text').get()
                date_text = card.css('.insight-card-date::text').get()
                
                if article_url:
                    ajax_article_meta = {
                        'preview_data': {
                            'title': title,
                            'category': category,
                            'date_text': date_text,
                        }
                    }
                    
                    if PLAYWRIGHT_AVAILABLE:
                        ajax_article_meta.update({
                            'playwright': True,
                            'playwright_page_methods': [
                                PageMethod('wait_for_selector', '.post-content, .entry-content', timeout=30000),
                            ],
                        })
                    
                    yield Request(
                        url=urljoin('https://ionanalytics.com', article_url),
                        callback=self.parse_article,
                        meta=ajax_article_meta
                    )
            
            # Continue pagination if more content exists
            yield from self._handle_ajax_pagination(response)
            
        except Exception as e:
            self.logger.error(f"Error parsing AJAX response: {e}")
    
    def parse_article(self, response):
        """Parse individual article for detailed content and deal information"""
        loader = ItemLoader(item=NewsArticleItem(), response=response)
        preview_data = response.meta.get('preview_data', {})
        
        # Basic article information
        loader.add_value('url', response.url)
        
        # Try multiple selectors for title
        title = (
            response.css('h1.post-title::text').get() or
            response.css('h1.entry-title::text').get() or
            response.css('.post-header h1::text').get() or
            preview_data.get('title', '')
        )
        loader.add_value('title', title)
        
        # Extract main content
        content_selectors = [
            '.post-content p::text',
            '.entry-content p::text',
            '.article-body p::text',
            '.content p::text'
        ]
        
        content_paragraphs = []
        for selector in content_selectors:
            paragraphs = response.css(selector).getall()
            if paragraphs:
                content_paragraphs = paragraphs
                break
        
        if content_paragraphs:
            loader.add_value('content', content_paragraphs)
        
        # Extract author information
        author_selectors = [
            '.post-author::text',
            '.author-name::text',
            '.byline::text',
            '.post-meta .author::text'
        ]
        
        for selector in author_selectors:
            author = response.css(selector).get()
            if author:
                loader.add_value('author', author.strip())
                break
        
        # Extract publication date
        pub_date = self._extract_publication_date(response, preview_data)
        if pub_date:
            loader.add_value('published_date', pub_date)
        
        # Article metadata
        loader.add_value('source', 'ion_analytics')
        loader.add_value('category', preview_data.get('category', 'News Intelligence'))
        loader.add_value('scraped_date', datetime.utcnow().isoformat())
        
        # Extract tags if available
        tags = response.css('.post-tags a::text, .entry-tags a::text').getall()
        if tags:
            loader.add_value('tags', [tag.strip() for tag in tags])
        
        # Calculate content metrics
        content_text = ' '.join(content_paragraphs) if content_paragraphs else ''
        word_count = len(content_text.split()) if content_text else 0
        reading_time = max(1, word_count // 200)  # 200 words per minute
        
        loader.add_value('word_count', word_count)
        loader.add_value('reading_time', reading_time)
        
        article_item = loader.load_item()
        yield article_item
        
        # Extract deal information if article contains M&A content
        if self._is_ma_content(title, content_text):
            yield Request(
                url=response.url,
                callback=self.extract_deal_info,
                meta={
                    'article_item': dict(article_item),
                    'dont_filter': True
                }
            )
    
    def _extract_publication_date(self, response, preview_data):
        """Extract publication date from various possible locations"""
        # Try structured data first
        date_selectors = [
            'time::attr(datetime)',
            '.post-date::attr(datetime)',
            '.entry-date::attr(datetime)',
            '.publish-date::attr(datetime)'
        ]
        
        for selector in date_selectors:
            date_val = response.css(selector).get()
            if date_val:
                return self._normalize_date(date_val)
        
        # Try text-based date extraction
        text_date_selectors = [
            '.post-date::text',
            '.entry-date::text',
            '.publish-date::text',
            '.post-meta .date::text'
        ]
        
        for selector in text_date_selectors:
            date_text = response.css(selector).get()
            if date_text:
                normalized = self._normalize_date(date_text.strip())
                if normalized:
                    return normalized
        
        # Use preview data as fallback
        preview_date = preview_data.get('date_text', '')
        if preview_date:
            return self._normalize_date(preview_date)
        
        return None
    
    def _normalize_date(self, date_string):
        """Normalize various date formats to ISO format"""
        if not date_string:
            return None
        
        try:
            from dateutil import parser
            parsed_date = parser.parse(date_string)
            return parsed_date.isoformat()
        except:
            # Try manual parsing for common formats
            date_patterns = [
                r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
                r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
                r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})',  # Month DD, YYYY
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, date_string)
                if match:
                    try:
                        if pattern == date_patterns[0]:  # MM/DD/YYYY
                            month, day, year = match.groups()
                            date_obj = datetime(int(year), int(month), int(day))
                        elif pattern == date_patterns[1]:  # YYYY-MM-DD
                            year, month, day = match.groups()
                            date_obj = datetime(int(year), int(month), int(day))
                        elif pattern == date_patterns[2]:  # Month DD, YYYY
                            from dateutil import parser
                            date_obj = parser.parse(match.group(0))
                        
                        return date_obj.isoformat()
                    except:
                        continue
        
        return None
    
    def _is_ma_content(self, title, content):
        """Check if content is M&A related"""
        ma_keywords = [
            'merger', 'acquisition', 'acquires', 'acquired', 'buyout', 'takeover',
            'deal', 'm&a', 'mergers', 'acquisitions', 'purchased', 'buys',
            'combine', 'consolidation', 'divestiture', 'spin-off', 'ipo',
            'leveraged buyout', 'lbo', 'strategic acquisition', 'hostile takeover'
        ]
        
        text_to_check = (title + ' ' + content).lower()
        return any(keyword in text_to_check for keyword in ma_keywords)
    
    def extract_deal_info(self, response):
        """Extract structured deal information from article content"""
        article_data = response.meta['article_item']
        content = article_data.get('content', '')
        title = article_data.get('title', '')
        
        # Advanced deal pattern extraction
        deal_patterns = self._extract_advanced_deal_patterns(title + ' ' + content)
        
        if deal_patterns and deal_patterns.get('confidence', 0) > 0.3:
            loader = ItemLoader(item=DealItem(), response=response)
            
            # Basic deal information
            loader.add_value('deal_type', deal_patterns.get('deal_type', 'acquisition'))
            loader.add_value('deal_status', deal_patterns.get('deal_status', 'announced'))
            
            # Companies involved
            if deal_patterns.get('target_company'):
                loader.add_value('target_company', deal_patterns['target_company'])
            if deal_patterns.get('acquirer_company'):
                loader.add_value('acquirer_company', deal_patterns['acquirer_company'])
            
            # Financial details
            if deal_patterns.get('deal_value'):
                loader.add_value('deal_value', deal_patterns['deal_value'])
                loader.add_value('deal_value_currency', 'USD')  # Default assumption
            
            # Industry and geographic information
            if deal_patterns.get('industry_sector'):
                loader.add_value('industry_sector', deal_patterns['industry_sector'])
            if deal_patterns.get('geographic_region'):
                loader.add_value('geographic_region', deal_patterns['geographic_region'])
            
            # Advisors
            if deal_patterns.get('financial_advisors'):
                loader.add_value('financial_advisors', deal_patterns['financial_advisors'])
            if deal_patterns.get('legal_advisors'):
                loader.add_value('legal_advisors', deal_patterns['legal_advisors'])
            
            # Timeline
            if deal_patterns.get('announcement_date'):
                loader.add_value('announcement_date', deal_patterns['announcement_date'])
            if deal_patterns.get('expected_completion_date'):
                loader.add_value('expected_completion_date', deal_patterns['expected_completion_date'])
            
            # Source and metadata
            loader.add_value('source_url', response.url)
            loader.add_value('source_article_id', article_data.get('url'))
            loader.add_value('confidence_score', deal_patterns.get('confidence', 0.5))
            loader.add_value('extraction_method', 'rule_based_advanced')
            loader.add_value('created_date', datetime.utcnow().isoformat())
            
            deal_item = loader.load_item()
            yield deal_item
    
    def _extract_advanced_deal_patterns(self, text):
        """Advanced deal information extraction with confidence scoring"""
        patterns = {}
        confidence_score = 0.0
        text_lower = text.lower()
        
        # Deal type patterns with confidence weighting
        deal_type_patterns = {
            'acquisition': [
                (r'\b(?:acquires|acquired|acquisition|purchases|bought|buys)\b', 0.9),
                (r'\b(?:takes over|takeover)\b', 0.8),
                (r'\b(?:agrees to (?:buy|purchase))\b', 0.8),
            ],
            'merger': [
                (r'\b(?:merger|merge|merging|combined|combining)\b', 0.9),
                (r'\b(?:all-stock|stock-for-stock)\b', 0.7),
            ],
            'ipo': [
                (r'\b(?:ipo|initial public offering|goes public|public offering)\b', 0.9),
                (r'\b(?:lists on|stock exchange listing)\b', 0.7),
            ],
            'divestiture': [
                (r'\b(?:divests|divestiture|sells|disposal)\b', 0.8),
                (r'\b(?:spin-off|spins off|carve-out)\b', 0.8),
            ]
        }
        
        for deal_type, type_patterns in deal_type_patterns.items():
            for pattern, weight in type_patterns:
                if re.search(pattern, text_lower):
                    patterns['deal_type'] = deal_type
                    confidence_score += weight * 0.2
                    break
        
        # Company name extraction with improved patterns
        company_patterns = [
            # Pattern: "Company A acquires Company B"
            (r'\b([A-Z][a-zA-Z\s&.-]+(?:Inc|Corp|LLC|Ltd|Co\.?|Group|Holdings|International|Technologies|Solutions|Systems|Services))\s+(?:acquires|buys|purchases|acquired)\s+([A-Z][a-zA-Z\s&.-]+(?:Inc|Corp|LLC|Ltd|Co\.?|Group|Holdings|International|Technologies|Solutions|Systems|Services))', 0.9),
            # Pattern: "Acquisition of Company B by Company A"
            (r'acquisition\s+of\s+([A-Z][a-zA-Z\s&.-]+(?:Inc|Corp|LLC|Ltd|Co\.?|Group|Holdings|International|Technologies|Solutions|Systems|Services))\s+by\s+([A-Z][a-zA-Z\s&.-]+(?:Inc|Corp|LLC|Ltd|Co\.?|Group|Holdings|International|Technologies|Solutions|Systems|Services))', 0.8),
            # Pattern: Stock ticker symbols
            (r'\(([A-Z]{2,5})\)', 0.6),
        ]
        
        for pattern, weight in company_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if pattern == company_patterns[0][0]:  # Acquirer-target pattern
                    patterns['acquirer_company'] = matches[0][0].strip()
                    patterns['target_company'] = matches[0][1].strip()
                elif pattern == company_patterns[1][0]:  # Target-acquirer pattern
                    patterns['target_company'] = matches[0][0].strip()
                    patterns['acquirer_company'] = matches[0][1].strip()
                confidence_score += weight * 0.25
                break
        
        # Deal value extraction with enhanced patterns
        value_patterns = [
            (r'\$([0-9]+(?:\.[0-9]+)?)\s*billion', lambda m: float(m.group(1)) * 1000000000, 0.9),
            (r'\$([0-9]+(?:\.[0-9]+)?)\s*million', lambda m: float(m.group(1)) * 1000000, 0.9),
            (r'\$([0-9,]+(?:\.[0-9]+)?)\s*(?:bn|b)', lambda m: float(m.group(1).replace(',', '')) * 1000000000, 0.8),
            (r'\$([0-9,]+(?:\.[0-9]+)?)\s*(?:mn|m)', lambda m: float(m.group(1).replace(',', '')) * 1000000, 0.8),
            (r'valued?\s+at\s+\$([0-9,]+(?:\.[0-9]+)?)\s*(?:billion|bn|b)', lambda m: float(m.group(1).replace(',', '')) * 1000000000, 0.8),
        ]
        
        for pattern, converter, weight in value_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    patterns['deal_value'] = converter(match)
                    confidence_score += weight * 0.2
                    break
                except:
                    continue
        
        # Industry sector detection
        industry_keywords = {
            'technology': ['technology', 'tech', 'software', 'saas', 'ai', 'artificial intelligence', 'cloud', 'digital'],
            'healthcare': ['healthcare', 'pharma', 'pharmaceutical', 'biotech', 'medical', 'health'],
            'financial_services': ['financial', 'banking', 'insurance', 'fintech', 'payments', 'credit'],
            'energy': ['energy', 'oil', 'gas', 'renewable', 'solar', 'wind', 'utilities'],
            'real_estate': ['real estate', 'property', 'reit', 'construction', 'development'],
            'retail': ['retail', 'consumer', 'e-commerce', 'fashion', 'apparel'],
            'telecommunications': ['telecom', 'telecommunications', 'wireless', 'broadband', 'network'],
        }
        
        for sector, keywords in industry_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                patterns['industry_sector'] = sector
                confidence_score += 0.1
                break
        
        # Geographic region detection
        geographic_keywords = {
            'north_america': ['united states', 'usa', 'canada', 'north america', 'american'],
            'europe': ['europe', 'european', 'uk', 'germany', 'france', 'britain', 'england'],
            'asia_pacific': ['asia', 'china', 'japan', 'singapore', 'australia', 'korea', 'india'],
            'global': ['global', 'worldwide', 'international', 'multinational'],
        }
        
        for region, keywords in geographic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                patterns['geographic_region'] = region
                confidence_score += 0.05
                break
        
        # Advisor extraction
        advisor_patterns = [
            (r'advised by ([A-Z][a-zA-Z\s&]+)', 'financial_advisors'),
            (r'([A-Z][a-zA-Z\s&]+) advised', 'financial_advisors'),
            (r'legal counsel[:\s]+([A-Z][a-zA-Z\s&]+)', 'legal_advisors'),
            (r'represented by ([A-Z][a-zA-Z\s&]+)', 'legal_advisors'),
        ]
        
        for pattern, advisor_type in advisor_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if advisor_type not in patterns:
                    patterns[advisor_type] = []
                patterns[advisor_type].extend([match.strip() for match in matches])
                confidence_score += 0.05
        
        # Date extraction for deal timeline
        date_patterns = [
            (r'announced\s+(?:on\s+)?([A-Za-z]+\s+\d{1,2},\s+\d{4})', 'announcement_date'),
            (r'expected\s+to\s+(?:close|complete)\s+(?:by\s+)?([A-Za-z]+\s+\d{4})', 'expected_completion_date'),
            (r'completion\s+(?:by\s+)?([A-Za-z]+\s+\d{4})', 'expected_completion_date'),
        ]
        
        for pattern, date_type in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    from dateutil import parser
                    parsed_date = parser.parse(match.group(1))
                    patterns[date_type] = parsed_date.isoformat()
                    confidence_score += 0.1
                except:
                    continue
        
        # Deal status detection
        status_patterns = [
            (r'\b(?:announced|announces)\b', 'announced', 0.8),
            (r'\b(?:completed|closed|finalized)\b', 'completed', 0.9),
            (r'\b(?:pending|awaiting|subject to)\b', 'pending', 0.7),
            (r'\b(?:terminated|cancelled|abandoned)\b', 'canceled', 0.9),
        ]
        
        for pattern, status, weight in status_patterns:
            if re.search(pattern, text_lower):
                patterns['deal_status'] = status
                confidence_score += weight * 0.1
                break
        
        patterns['confidence'] = min(confidence_score, 1.0)
        return patterns