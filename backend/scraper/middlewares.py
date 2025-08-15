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