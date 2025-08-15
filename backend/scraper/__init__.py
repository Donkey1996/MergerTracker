"""
MergerTracker Scraping System

A comprehensive web scraping framework for M&A news collection using
Scrapy + Playwright with ethical scraping practices.
"""

__version__ = "1.0.0"

# Core scraping configuration
SCRAPER_NAME = "mergertracker-scraper"
SCRAPER_VERSION = __version__

# Default user agents for rotation
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0"
]

# Supported news sources
SUPPORTED_SOURCES = [
    "reuters",
    "bloomberg", 
    "financial_times",
    "wall_street_journal",
    "cnbc",
    "yahoo_finance",
    "sec_edgar",
    "pr_newswire",
    "business_wire",
    "marketwatch"
]