#!/usr/bin/env python3
"""
Command-line script to run MergerTracker scrapers manually

Usage:
    python run_scraper.py cnbc
    python run_scraper.py yahoo_finance
    python run_scraper.py marketwatch
    python run_scraper.py --all
    python run_scraper.py --list-spiders
"""

import sys
import os
import asyncio
import argparse
import logging
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.database_service import initialize_database_service, shutdown_database_service
from services.scheduler_service import ScraperSchedulerService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ManualScraperRunner:
    """Manual scraper runner for testing and development"""
    
    def __init__(self):
        self.scheduler_service = None
        self.db_service = None
    
    async def initialize(self):
        """Initialize services"""
        try:
            # Initialize database service
            self.db_service = await initialize_database_service()
            logger.info("Database service initialized")
            
            # Initialize scheduler service (without starting the scheduler)
            self.scheduler_service = ScraperSchedulerService()
            await self.scheduler_service.initialize()
            logger.info("Scheduler service initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown services"""
        try:
            if self.scheduler_service:
                await self.scheduler_service.shutdown()
            
            await shutdown_database_service()
            logger.info("Services shut down successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def run_spider(self, spider_name: str):
        """Run a specific spider"""
        try:
            logger.info(f"Starting {spider_name} spider...")
            start_time = datetime.utcnow()
            
            if spider_name == 'cnbc':
                await self.scheduler_service._run_cnbc_scraper()
            elif spider_name == 'yahoo_finance':
                await self.scheduler_service._run_yahoo_finance_scraper()
            elif spider_name == 'marketwatch':
                await self.scheduler_service._run_marketwatch_scraper()
            else:
                logger.error(f"Unknown spider: {spider_name}")
                return False
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Spider {spider_name} completed in {duration:.2f} seconds")
            
            return True
            
        except Exception as e:
            logger.error(f"Error running spider {spider_name}: {e}")
            return False
    
    async def run_all_spiders(self):
        """Run all available spiders"""
        spiders = ['cnbc', 'yahoo_finance', 'marketwatch']
        results = {}
        
        for spider in spiders:
            logger.info(f"Running spider: {spider}")
            success = await self.run_spider(spider)
            results[spider] = success
            
            if not success:
                logger.error(f"Spider {spider} failed")
            
            # Wait between spiders to be respectful
            await asyncio.sleep(5)
        
        # Summary
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        logger.info(f"Completed {successful}/{total} spiders successfully")
        
        for spider, success in results.items():
            status = "✓" if success else "✗"
            logger.info(f"  {status} {spider}")
        
        return results
    
    def list_spiders(self):
        """List available spiders"""
        spiders = [
            ('cnbc', 'CNBC M&A News Scraper'),
            ('yahoo_finance', 'Yahoo Finance M&A Scraper'),
            ('marketwatch', 'MarketWatch M&A Scraper'),
        ]
        
        print("Available spiders:")
        for spider_id, description in spiders:
            print(f"  {spider_id:<15} - {description}")
    
    async def test_database(self):
        """Test database connection and basic operations"""
        try:
            logger.info("Testing database connection...")
            
            health = await self.db_service.health_check()
            logger.info(f"Database health: {health}")
            
            # Test creating a sample deal
            sample_deal = {
                'deal_id': f'test_deal_{int(datetime.utcnow().timestamp())}',
                'deal_type': 'acquisition',
                'target_company': 'Test Target Corp',
                'acquirer_company': 'Test Acquirer Inc',
                'deal_value': 1000000000,  # $1B
                'deal_value_currency': 'USD',
                'industry_sector': 'technology',
                'deal_status': 'announced',
                'source_url': 'https://example.com/test-deal',
                'extraction_method': 'manual_test',
                'confidence_score': 1.0
            }
            
            deal_id = await self.db_service.create_deal(sample_deal)
            logger.info(f"Created test deal: {deal_id}")
            
            # Retrieve the deal
            retrieved_deal = await self.db_service.get_deal(deal_id)
            if retrieved_deal:
                logger.info("Successfully retrieved test deal")
                
                # Clean up - delete the test deal
                await self.db_service.delete_deal(deal_id)
                logger.info("Test deal cleaned up")
            
            logger.info("Database test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database test failed: {e}")
            return False


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='MergerTracker Scraper Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_scraper.py cnbc              # Run CNBC spider
  python run_scraper.py yahoo_finance     # Run Yahoo Finance spider  
  python run_scraper.py --all             # Run all spiders
  python run_scraper.py --list-spiders    # List available spiders
  python run_scraper.py --test-db         # Test database connection
        """
    )
    
    parser.add_argument('spider', nargs='?', help='Spider name to run')
    parser.add_argument('--all', action='store_true', help='Run all spiders')
    parser.add_argument('--list-spiders', action='store_true', help='List available spiders')
    parser.add_argument('--test-db', action='store_true', help='Test database connection')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle list spiders command (doesn't need services)
    if args.list_spiders:
        runner = ManualScraperRunner()
        runner.list_spiders()
        return
    
    # Initialize runner
    runner = ManualScraperRunner()
    
    try:
        if not await runner.initialize():
            logger.error("Failed to initialize services")
            return 1
        
        if args.test_db:
            success = await runner.test_database()
            return 0 if success else 1
        
        elif args.all:
            results = await runner.run_all_spiders()
            failed_spiders = [spider for spider, success in results.items() if not success]
            return 0 if not failed_spiders else 1
        
        elif args.spider:
            if args.spider not in ['cnbc', 'yahoo_finance', 'marketwatch']:
                logger.error(f"Unknown spider: {args.spider}")
                print("\nUse --list-spiders to see available spiders")
                return 1
            
            success = await runner.run_spider(args.spider)
            return 0 if success else 1
        
        else:
            parser.print_help()
            return 1
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 1
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    
    finally:
        await runner.shutdown()


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)