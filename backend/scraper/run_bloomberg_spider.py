#!/usr/bin/env python3
"""
Production runner for Bloomberg deals spider.

This script provides a production-ready way to run the Bloomberg spider
with proper error handling, logging, and monitoring.
"""

import os
import sys
import logging
import signal
import time
from datetime import datetime
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor, defer
from multiprocessing import Process

# Add the scraper directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


class BloombergSpiderRunner:
    """Production runner for Bloomberg spider with monitoring and safety features"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.start_time = None
        self.stats = {
            'items_scraped': 0,
            'errors': 0,
            'requests': 0,
            'start_time': None,
            'end_time': None,
        }
    
    def setup_logging(self):
        """Configure comprehensive logging"""
        
        log_format = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
        log_level = self.config.get('log_level', 'INFO')
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level),
            format=log_format,
            handlers=[
                logging.FileHandler(f'bloomberg_spider_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def get_production_settings(self):
        """Get production-optimized settings"""
        
        settings = get_project_settings()
        
        # Production overrides
        production_settings = {
            # Conservative rate limiting for production
            'DOWNLOAD_DELAY': self.config.get('download_delay', 8),
            'RANDOMIZE_DOWNLOAD_DELAY': self.config.get('randomize_delay', 3),
            'CONCURRENT_REQUESTS': 1,
            'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
            
            # Timeout settings
            'DOWNLOAD_TIMEOUT': 60,
            'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 90000,
            
            # Memory and performance
            'MEMUSAGE_ENABLED': True,
            'MEMUSAGE_LIMIT_MB': 2048,
            'MEMUSAGE_WARNING_MB': 1536,
            
            # Enhanced logging
            'LOG_LEVEL': self.config.get('log_level', 'INFO'),
            'LOG_FILE': f'bloomberg_production_{datetime.now().strftime("%Y%m%d")}.log',
            
            # Safety limits
            'CLOSESPIDER_ITEMCOUNT': self.config.get('max_items', 100),
            'CLOSESPIDER_TIMEOUT': self.config.get('max_runtime', 7200),  # 2 hours max
            'CLOSESPIDER_ERRORCOUNT': self.config.get('max_errors', 50),
            
            # Export results
            'FEEDS': {
                f'bloomberg_deals_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json': {
                    'format': 'json',
                    'overwrite': True,
                    'indent': 2,
                }
            },
            
            # Database settings (if enabled)
            'DATABASE_URL': os.getenv('DATABASE_URL'),
            'REDIS_URL': os.getenv('REDIS_URL'),
            
            # Playwright production settings
            'PLAYWRIGHT_LAUNCH_OPTIONS': {
                'headless': True,
                'args': [
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-features=VizDisplayCompositor',
                    '--memory-pressure-off',
                ]
            },
            
            # Pipeline configuration
            'ITEM_PIPELINES': {
                'scraper.pipelines.ValidationPipeline': 300,
                'scraper.pipelines.DuplicatesPipeline': 400,
                'scraper.pipelines.DataEnrichmentPipeline': 450,
                'scraper.pipelines.DatabasePipeline': 500,
            },
            
            # Middleware configuration
            'DOWNLOADER_MIDDLEWARES': {
                'scraper.middlewares.RotateUserAgentMiddleware': 400,
                'scraper.middlewares.BloombergAntiDetectionMiddleware': 405,
                'scraper.middlewares.RateLimitMiddleware': 500,
                'scrapy_playwright.middleware.ScrapyPlaywrightMiddleware': 585,
            },
            
            # HTTP caching
            'HTTPCACHE_ENABLED': True,
            'HTTPCACHE_EXPIRATION_SECS': 3600,
            'HTTPCACHE_DIR': 'httpcache',
            'HTTPCACHE_IGNORE_HTTP_CODES': [403, 429, 500, 502, 503, 504],
        }
        
        settings.update(production_settings)
        return settings
    
    def run_spider_sync(self):
        """Run spider synchronously (blocking)"""
        
        self.logger.info("Starting Bloomberg spider in synchronous mode")
        self.stats['start_time'] = datetime.now()
        
        try:
            settings = self.get_production_settings()
            process = CrawlerProcess(settings)
            process.crawl('bloomberg_deals')
            process.start()  # Blocks until finished
            
        except KeyboardInterrupt:
            self.logger.info("Spider interrupted by user")
        except Exception as e:
            self.logger.error(f"Spider failed with error: {e}")
            raise
        finally:
            self.stats['end_time'] = datetime.now()
            self.log_final_stats()
    
    @defer.inlineCallbacks
    def run_spider_async(self):
        """Run spider asynchronously (non-blocking)"""
        
        self.logger.info("Starting Bloomberg spider in asynchronous mode")
        self.stats['start_time'] = datetime.now()
        
        try:
            settings = self.get_production_settings()
            runner = CrawlerRunner(settings)
            yield runner.crawl('bloomberg_deals')
            
        except Exception as e:
            self.logger.error(f"Spider failed with error: {e}")
            raise
        finally:
            self.stats['end_time'] = datetime.now()
            self.log_final_stats()
            reactor.stop()
    
    def run_spider_process(self):
        """Run spider in separate process"""
        
        def spider_process():
            self.run_spider_sync()
        
        self.logger.info("Starting Bloomberg spider in separate process")
        
        process = Process(target=spider_process)
        process.start()
        
        # Monitor the process
        try:
            while process.is_alive():
                time.sleep(10)  # Check every 10 seconds
                self.logger.debug("Spider process is running...")
            
            process.join()
            
            if process.exitcode == 0:
                self.logger.info("Spider process completed successfully")
            else:
                self.logger.error(f"Spider process failed with exit code: {process.exitcode}")
                
        except KeyboardInterrupt:
            self.logger.info("Terminating spider process...")
            process.terminate()
            process.join(timeout=30)
            if process.is_alive():
                process.kill()
    
    def log_final_stats(self):
        """Log final statistics"""
        
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            self.logger.info(f"Spider completed in {duration}")
        
        self.logger.info("Final Statistics:")
        self.logger.info(f"- Items scraped: {self.stats['items_scraped']}")
        self.logger.info(f"- Errors encountered: {self.stats['errors']}")
        self.logger.info(f"- Total requests: {self.stats['requests']}")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, shutting down gracefully...")
            if reactor.running:
                reactor.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Main function with CLI interface"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Bloomberg deals spider')
    parser.add_argument('--mode', choices=['sync', 'async', 'process'], 
                       default='sync', help='Spider execution mode')
    parser.add_argument('--download-delay', type=int, default=8,
                       help='Download delay in seconds (default: 8)')
    parser.add_argument('--max-items', type=int, default=100,
                       help='Maximum items to scrape (default: 100)')
    parser.add_argument('--max-runtime', type=int, default=7200,
                       help='Maximum runtime in seconds (default: 7200)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level (default: INFO)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Validate configuration without running spider')
    
    args = parser.parse_args()
    
    # Configuration from command line arguments
    config = {
        'download_delay': args.download_delay,
        'max_items': args.max_items,
        'max_runtime': args.max_runtime,
        'log_level': args.log_level,
    }
    
    # Create runner
    runner = BloombergSpiderRunner(config)
    
    if args.dry_run:
        print("Configuration validation:")
        print(f"- Mode: {args.mode}")
        print(f"- Download delay: {config['download_delay']} seconds")
        print(f"- Max items: {config['max_items']}")
        print(f"- Max runtime: {config['max_runtime']} seconds") 
        print(f"- Log level: {config['log_level']}")
        print("Configuration is valid. Use without --dry-run to execute.")
        return
    
    # Setup signal handlers
    runner.setup_signal_handlers()
    
    # Run based on mode
    try:
        if args.mode == 'sync':
            runner.run_spider_sync()
        elif args.mode == 'async':
            from twisted.internet import reactor
            reactor.callWhenRunning(runner.run_spider_async)
            reactor.run()
        elif args.mode == 'process':
            runner.run_spider_process()
            
    except Exception as e:
        print(f"Failed to run spider: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()