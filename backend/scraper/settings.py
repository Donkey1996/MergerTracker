# Scrapy settings for MergerTracker project

BOT_NAME = 'mergertracker'

SPIDER_MODULES = ['scraper.spiders']
NEWSPIDER_MODULE = 'scraper.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure delays for requests
RANDOMIZE_DOWNLOAD_DELAY = 0.5
DOWNLOAD_DELAY = 3
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 4

# AutoThrottle settings
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_RANDOM_DELAY = 0.2

# User-Agent settings
USER_AGENT = 'mergertracker (+http://www.mergertracker.com)'

# Configure pipelines
ITEM_PIPELINES = {
    'scraper.pipelines.ValidationPipeline': 300,
    'scraper.pipelines.DuplicatesPipeline': 400,
    'scraper.pipelines.DataEnrichmentPipeline': 450,
    'scraper.pipelines.DatabasePipeline': 500,
}

# Configure middlewares
DOWNLOADER_MIDDLEWARES = {
    'scraper.middlewares.RotateUserAgentMiddleware': 400,
    'scraper.middlewares.BloombergAntiDetectionMiddleware': 405,
    'scraper.middlewares.ProxyMiddleware': 410,
    'scraper.middlewares.RateLimitMiddleware': 500,
    'scrapy_playwright.middleware.ScrapyPlaywrightMiddleware': 585,
}

# Playwright settings
PLAYWRIGHT_BROWSER_TYPE = 'chromium'
PLAYWRIGHT_LAUNCH_OPTIONS = {
    'headless': True,
}

# Cache settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = 'httpcache'

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'scrapy.log'

# Database settings
DATABASE_URL = 'postgresql://user:password@localhost:5432/mergertracker'
REDIS_URL = 'redis://localhost:6379'

# Request fingerprinting
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
FEED_EXPORT_ENCODING = 'utf-8'