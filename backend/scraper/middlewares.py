import random
import logging
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware
from scrapy.exceptions import NotConfigured

logger = logging.getLogger(__name__)


class RotateUserAgentMiddleware(UserAgentMiddleware):
    """Middleware to rotate user agents for ethical scraping"""
    
    def __init__(self):
        self.user_agent_list = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
        ]
    
    def process_request(self, request, spider):
        ua = random.choice(self.user_agent_list)
        request.headers['User-Agent'] = ua
        return None


class ProxyMiddleware(HttpProxyMiddleware):
    """Middleware for proxy rotation (optional)"""
    
    def __init__(self):
        self.proxies = []
        # Add proxy list if needed for production
        # self.proxies = ['http://proxy1:port', 'http://proxy2:port']
    
    def process_request(self, request, spider):
        if self.proxies:
            proxy = random.choice(self.proxies)
            request.meta['proxy'] = proxy
        return None


class RateLimitMiddleware:
    """Custom rate limiting middleware"""
    
    def __init__(self, delay=3.0):
        self.delay = delay
        self.last_request_time = {}
    
    @classmethod
    def from_crawler(cls, crawler):
        delay = crawler.settings.getfloat('DOWNLOAD_DELAY', 3.0)
        return cls(delay=delay)
    
    def process_request(self, request, spider):
        import time
        domain = request.url.split('/')[2]
        current_time = time.time()
        
        if domain in self.last_request_time:
            time_since_last = current_time - self.last_request_time[domain]
            if time_since_last < self.delay:
                time.sleep(self.delay - time_since_last)
        
        self.last_request_time[domain] = time.time()
        return None


class RetryMiddleware:
    """Enhanced retry middleware with exponential backoff"""
    
    def __init__(self, max_retry_times=3, retry_http_codes=None):
        self.max_retry_times = max_retry_times
        self.retry_http_codes = retry_http_codes or [500, 502, 503, 504, 408, 429]
        self.priority_adjust = -1
    
    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        return cls(
            max_retry_times=settings.getint('RETRY_TIMES'),
            retry_http_codes=settings.getlist('RETRY_HTTP_CODES')
        )
    
    def process_response(self, request, response, spider):
        if response.status in self.retry_http_codes:
            reason = f'Received {response.status} response'
            return self._retry(request, reason, spider) or response
        return response
    
    def process_exception(self, request, exception, spider):
        if isinstance(exception, (ConnectionError, TimeoutError)):
            return self._retry(request, str(exception), spider)
        return None
    
    def _retry(self, request, reason, spider):
        retries = request.meta.get('retry_times', 0) + 1
        
        if retries <= self.max_retry_times:
            logger.debug(f"Retrying {request.url} (failed {retries} times): {reason}")
            
            # Exponential backoff
            retry_delay = 2 ** retries
            request.meta['retry_times'] = retries
            request.priority = request.priority + self.priority_adjust
            
            import time
            time.sleep(retry_delay)
            
            return request.copy()
        else:
            logger.error(f"Gave up retrying {request.url} (failed {retries} times): {reason}")
            return None


class RobotsTxtMiddleware:
    """Enhanced robots.txt compliance middleware"""
    
    def __init__(self):
        self.robots_cache = {}
    
    def process_request(self, request, spider):
        import urllib.robotparser
        from urllib.parse import urlparse
        
        parsed_url = urlparse(request.url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        if base_url not in self.robots_cache:
            robots_url = f"{base_url}/robots.txt"
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            try:
                rp.read()
                self.robots_cache[base_url] = rp
            except Exception as e:
                logger.warning(f"Could not fetch robots.txt for {base_url}: {e}")
                return None
        
        rp = self.robots_cache[base_url]
        user_agent = request.headers.get('User-Agent', '').decode('utf-8')
        
        if not rp.can_fetch(user_agent, request.url):
            logger.warning(f"Robots.txt disallows fetching {request.url}")
            # Return a 403 response instead of fetching
            from scrapy.http import Response
            return Response(
                url=request.url,
                status=403,
                body=b"Blocked by robots.txt"
            )
        
        # Check crawl delay
        crawl_delay = rp.crawl_delay(user_agent)
        if crawl_delay:
            request.meta['download_delay'] = crawl_delay
        
        return None


class BloombergAntiDetectionMiddleware:
    """
    Specialized middleware for Bloomberg scraping with advanced anti-detection.
    
    This middleware implements multiple strategies to avoid detection:
    - Advanced user agent rotation with realistic browser fingerprints
    - Dynamic request header generation
    - Session management and cookie handling
    - Intelligent retry logic with exponential backoff
    - Request timing randomization
    """
    
    def __init__(self):
        self.session_cookies = {}
        self.request_counts = {}
        self.last_request_times = {}
        
        # Realistic user agent pool with corresponding headers
        self.browser_profiles = [
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'sec_ch_ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec_ch_ua_platform': '"Windows"',
                'sec_ch_ua_mobile': '?0',
            },
            {
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'sec_ch_ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec_ch_ua_platform': '"macOS"',
                'sec_ch_ua_mobile': '?0',
            },
            {
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
                'sec_ch_ua': None,  # Safari doesn't send these headers
                'sec_ch_ua_platform': None,
                'sec_ch_ua_mobile': None,
            },
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                'sec_ch_ua': None,  # Firefox doesn't send these headers
                'sec_ch_ua_platform': None,
                'sec_ch_ua_mobile': None,
            }
        ]
    
    def process_request(self, request, spider):
        # Only apply to Bloomberg requests
        if 'bloomberg.com' not in request.url:
            return None
        
        # Select random browser profile
        profile = random.choice(self.browser_profiles)
        
        # Set user agent
        request.headers['User-Agent'] = profile['user_agent']
        
        # Add Chrome-specific headers if applicable
        if profile['sec_ch_ua']:
            request.headers['Sec-CH-UA'] = profile['sec_ch_ua']
            request.headers['Sec-CH-UA-Platform'] = profile['sec_ch_ua_platform']
            request.headers['Sec-CH-UA-Mobile'] = profile['sec_ch_ua_mobile']
        
        # Add realistic browser headers
        request.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })
        
        # Add referer for internal navigation
        if request.meta.get('is_internal_navigation'):
            request.headers['Referer'] = 'https://www.bloomberg.com/'
        
        # Implement request throttling per domain
        self._throttle_request(request, spider)
        
        return None
    
    def process_response(self, request, response, spider):
        # Only process Bloomberg responses
        if 'bloomberg.com' not in request.url:
            return response
        
        # Store session cookies for future requests
        if 'Set-Cookie' in response.headers:
            domain = self._extract_domain(request.url)
            if domain not in self.session_cookies:
                self.session_cookies[domain] = {}
            
            # Simple cookie parsing (in production, use proper cookie jar)
            cookies = response.headers.getlist('Set-Cookie')
            for cookie in cookies:
                cookie_str = cookie.decode('utf-8')
                if '=' in cookie_str:
                    name, value = cookie_str.split('=', 1)[0], cookie_str.split('=', 1)[1].split(';')[0]
                    self.session_cookies[domain][name] = value
        
        # Handle different response scenarios
        if response.status == 403:
            logger.warning(f"Access denied for {request.url}. Implementing retry strategy.")
            return self._handle_access_denied(request, response, spider)
        
        elif response.status == 429:
            logger.warning(f"Rate limited for {request.url}. Implementing backoff.")
            return self._handle_rate_limit(request, response, spider)
        
        elif response.status in [500, 502, 503, 504]:
            logger.warning(f"Server error {response.status} for {request.url}")
            return self._handle_server_error(request, response, spider)
        
        return response
    
    def _throttle_request(self, request, spider):
        """Implement intelligent request throttling"""
        import time
        
        domain = self._extract_domain(request.url)
        current_time = time.time()
        
        # Track request counts per domain
        if domain not in self.request_counts:
            self.request_counts[domain] = 0
        
        self.request_counts[domain] += 1
        
        # Implement progressive delays based on request count
        if self.request_counts[domain] > 20:
            # After 20 requests, increase delay significantly
            base_delay = 10
        elif self.request_counts[domain] > 10:
            # After 10 requests, moderate delay
            base_delay = 7
        else:
            # First 10 requests, normal delay
            base_delay = 5
        
        # Add randomization
        delay = base_delay + random.uniform(1, 3)
        
        # Check if we need to wait based on last request
        if domain in self.last_request_times:
            time_since_last = current_time - self.last_request_times[domain]
            if time_since_last < delay:
                sleep_time = delay - time_since_last
                logger.info(f"Throttling request to {domain}, sleeping {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        self.last_request_times[domain] = time.time()
    
    def _handle_access_denied(self, request, response, spider):
        """Handle 403 Access Denied responses"""
        retry_times = request.meta.get('bloomberg_retry_times', 0)
        
        if retry_times < 3:
            # Retry with different strategy
            retry_request = request.copy()
            retry_request.meta['bloomberg_retry_times'] = retry_times + 1
            retry_request.meta['dont_filter'] = True
            
            # Wait longer before retry
            delay = (2 ** retry_times) * 5  # Exponential backoff: 5, 10, 20 seconds
            retry_request.meta['download_delay'] = delay
            
            logger.info(f"Retrying request to {request.url} in {delay} seconds (attempt {retry_times + 1})")
            
            # Change strategy for retry
            if retry_times == 0:
                # First retry: change user agent
                profile = random.choice(self.browser_profiles)
                retry_request.headers['User-Agent'] = profile['user_agent']
            elif retry_times == 1:
                # Second retry: try as mobile browser
                retry_request.headers['User-Agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1'
                retry_request.headers['Sec-CH-UA-Mobile'] = '?1'
            
            return retry_request
        
        logger.error(f"Giving up on {request.url} after {retry_times} retries")
        return response
    
    def _handle_rate_limit(self, request, response, spider):
        """Handle 429 Rate Limited responses"""
        retry_times = request.meta.get('bloomberg_rate_limit_retries', 0)
        
        if retry_times < 2:
            retry_request = request.copy()
            retry_request.meta['bloomberg_rate_limit_retries'] = retry_times + 1
            retry_request.meta['dont_filter'] = True
            
            # Longer delay for rate limiting
            delay = 30 + (retry_times * 30)  # 30, 60 seconds
            retry_request.meta['download_delay'] = delay
            
            logger.warning(f"Rate limited. Retrying {request.url} in {delay} seconds")
            return retry_request
        
        return response
    
    def _handle_server_error(self, request, response, spider):
        """Handle server errors with exponential backoff"""
        retry_times = request.meta.get('bloomberg_server_error_retries', 0)
        
        if retry_times < 2:
            retry_request = request.copy()
            retry_request.meta['bloomberg_server_error_retries'] = retry_times + 1
            retry_request.meta['dont_filter'] = True
            
            delay = (2 ** retry_times) * 3  # 3, 6 seconds
            retry_request.meta['download_delay'] = delay
            
            logger.warning(f"Server error {response.status}. Retrying {request.url} in {delay} seconds")
            return retry_request
        
        return response
    
    def _extract_domain(self, url):
        """Extract domain from URL"""
        from urllib.parse import urlparse
        return urlparse(url).netloc