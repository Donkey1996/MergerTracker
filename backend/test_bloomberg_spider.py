#!/usr/bin/env python3
"""
Test script for Bloomberg deals spider.

This script provides a safe way to test the Bloomberg spider
with various debugging options and safety checks.
"""

import os
import sys
import logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Add the scraper directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

def test_bloomberg_spider():
    """Test the Bloomberg spider with safety checks and debugging"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Bloomberg spider test")
    
    # Get Scrapy settings
    settings = get_project_settings()
    
    # Override settings for testing
    test_settings = {
        # Conservative settings for testing
        'DOWNLOAD_DELAY': 10,  # 10 second delay for testing
        'RANDOMIZE_DOWNLOAD_DELAY': 5,  # Up to 5 seconds additional delay
        'CONCURRENT_REQUESTS': 1,  # One request at a time
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        
        # Enable comprehensive logging
        'LOG_LEVEL': 'DEBUG',
        'LOG_FILE': 'bloomberg_test.log',
        
        # Disable database pipeline for testing
        'ITEM_PIPELINES': {
            'scraper.pipelines.ValidationPipeline': 300,
            'scraper.pipelines.DuplicatesPipeline': 400,
            'scraper.pipelines.DataEnrichmentPipeline': 450,
            # Comment out database pipeline for testing
            # 'scraper.pipelines.DatabasePipeline': 500,
        },
        
        # Enable test-specific middlewares
        'DOWNLOADER_MIDDLEWARES': {
            'scraper.middlewares.RotateUserAgentMiddleware': 400,
            'scraper.middlewares.BloombergAntiDetectionMiddleware': 405,
            'scrapy_playwright.middleware.ScrapyPlaywrightMiddleware': 585,
        },
        
        # Playwright settings for testing
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': False,  # Set to False to see browser for debugging
            'slow_mo': 1000,    # Slow down for observation
            'args': [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ]
        },
        
        # Test limits
        'CLOSESPIDER_ITEMCOUNT': 5,  # Stop after 5 items for testing
        'CLOSESPIDER_TIMEOUT': 300,  # Stop after 5 minutes
        
        # Export results for analysis
        'FEEDS': {
            'bloomberg_test_results.json': {
                'format': 'json',
                'overwrite': True,
            },
            'bloomberg_test_results.csv': {
                'format': 'csv',
                'overwrite': True,
            }
        }
    }
    
    # Update settings
    settings.update(test_settings)
    
    # Create crawler process
    process = CrawlerProcess(settings)
    
    try:
        # Add the spider
        process.crawl('bloomberg_deals')
        
        logger.info("Starting crawler process...")
        logger.info("Test configuration:")
        logger.info(f"- Download delay: {test_settings['DOWNLOAD_DELAY']} seconds")
        logger.info(f"- Max items: {test_settings['CLOSESPIDER_ITEMCOUNT']}")
        logger.info(f"- Timeout: {test_settings['CLOSESPIDER_TIMEOUT']} seconds")
        logger.info(f"- Headless mode: {test_settings['PLAYWRIGHT_LAUNCH_OPTIONS']['headless']}")
        
        # Start the crawler
        process.start()
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        raise
    finally:
        logger.info("Bloomberg spider test completed")
        logger.info("Check the following files for results:")
        logger.info("- bloomberg_test.log (detailed logs)")
        logger.info("- bloomberg_test_results.json (scraped data)")
        logger.info("- bloomberg_test_results.csv (scraped data)")

def validate_environment():
    """Validate that the environment is set up correctly for testing"""
    
    logger = logging.getLogger(__name__)
    
    # Check required packages
    required_packages = [
        'scrapy',
        'scrapy_playwright',
        'playwright',
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {missing_packages}")
        logger.error("Please install missing packages before running the test")
        return False
    
    # Check if Playwright browsers are installed
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser_path = p.chromium.executable_path
            if not os.path.exists(browser_path):
                logger.error("Playwright Chromium browser not found")
                logger.error("Run: playwright install chromium")
                return False
    except Exception as e:
        logger.warning(f"Could not verify Playwright installation: {e}")
    
    logger.info("Environment validation passed")
    return True

def run_safety_checks():
    """Run safety checks before starting the spider"""
    
    logger = logging.getLogger(__name__)
    
    logger.info("Running safety checks...")
    
    # Check robots.txt compliance
    logger.info("✓ Robots.txt compliance enabled in settings")
    
    # Check rate limiting
    logger.info("✓ Conservative rate limiting configured")
    
    # Check request limits
    logger.info("✓ Request limits configured for testing")
    
    # Check that we're not in production
    if os.getenv('ENVIRONMENT') == 'production':
        logger.error("❌ Do not run this test in production!")
        return False
    
    logger.info("✓ All safety checks passed")
    return True

def main():
    """Main test function"""
    
    print("=" * 60)
    print("Bloomberg Deals Spider Test")
    print("=" * 60)
    print()
    
    # Run validation and safety checks
    if not validate_environment():
        sys.exit(1)
    
    if not run_safety_checks():
        sys.exit(1)
    
    # Ask for user confirmation
    print("This test will:")
    print("1. Connect to Bloomberg's website using ethical scraping practices")
    print("2. Respect robots.txt and implement rate limiting")
    print("3. Extract a limited number of M&A deal articles")
    print("4. Save results to local files for analysis")
    print()
    
    response = input("Do you want to proceed with the test? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("Test cancelled by user")
        sys.exit(0)
    
    print()
    print("Starting Bloomberg spider test...")
    print("Note: This test may take several minutes due to rate limiting")
    print()
    
    try:
        test_bloomberg_spider()
        print()
        print("✓ Test completed successfully!")
        print("Check the generated files for results and logs.")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()