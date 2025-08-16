#!/usr/bin/env python3
"""
Parallel Scraper for MergerTracker
Scrapes Bloomberg and Ion Analytics simultaneously and stores in Supabase
"""

import asyncio
import sys
import os
import logging
import signal
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import asynccontextmanager

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parallel_scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ParallelScraper:
    """Orchestrates parallel scraping of multiple news sources"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.scraper_dir = Path(__file__).parent / 'scraper'
        self.results = {}
        self.start_time = None
        self.shutdown_requested = False
        
    def setup_environment(self):
        """Setup environment variables for scrapers"""
        os.environ['SUPABASE_URL'] = self.supabase_url
        os.environ['SUPABASE_SERVICE_KEY'] = self.supabase_key
        os.environ['DATABASE_ADAPTER'] = 'supabase'
        os.environ['SCRAPY_SETTINGS_MODULE'] = 'scraper.settings'
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
    
    def run_spider(self, spider_name: str, max_items: int = 50, download_delay: int = 5) -> Dict[str, Any]:
        """Run a single spider in a subprocess"""
        try:
            logger.info(f"Starting {spider_name} spider...")
            
            cmd = [
                'scrapy', 'crawl', spider_name,
                '-s', f'DOWNLOAD_DELAY={download_delay}',
                '-s', f'CLOSESPIDER_ITEMCOUNT={max_items}',
                '-s', 'LOG_LEVEL=INFO',
                '-s', 'FEEDS={items.json:json}',
                '--logfile', f'{spider_name}_spider.log'
            ]
            
            process = subprocess.run(
                cmd,
                cwd=self.scraper_dir,
                capture_output=True,
                text=True,
                timeout=7200  # 2 hour timeout
            )
            
            # Parse results
            items_file = self.scraper_dir / 'items.json'
            items_count = 0
            
            if items_file.exists():
                try:
                    with open(items_file, 'r') as f:
                        items = json.load(f)
                        items_count = len(items) if isinstance(items, list) else 1
                    items_file.unlink()  # Clean up
                except Exception as e:
                    logger.warning(f"Could not parse items file for {spider_name}: {e}")
            
            result = {
                'spider': spider_name,
                'success': process.returncode == 0,
                'items_scraped': items_count,
                'stdout': process.stdout,
                'stderr': process.stderr,
                'return_code': process.returncode,
                'duration': 0  # Will be calculated by caller
            }
            
            if result['success']:
                logger.info(f"✅ {spider_name} completed successfully: {items_count} items")
            else:
                logger.error(f"❌ {spider_name} failed: {process.stderr}")
            
            return result
            
        except subprocess.TimeoutExpired:
            logger.error(f"❌ {spider_name} timed out after 2 hours")
            return {
                'spider': spider_name,
                'success': False,
                'items_scraped': 0,
                'error': 'Timeout after 2 hours',
                'duration': 7200
            }
        except Exception as e:
            logger.error(f"❌ {spider_name} failed with exception: {e}")
            return {
                'spider': spider_name,
                'success': False,
                'items_scraped': 0,
                'error': str(e),
                'duration': 0
            }
    
    def run_parallel_scraping(self, max_items_per_spider: int = 25) -> Dict[str, Any]:
        """Run Bloomberg and Ion Analytics scrapers in parallel"""
        self.start_time = time.time()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Setup environment
        self.setup_environment()
        
        # Define spider configurations
        spiders = [
            {
                'name': 'bloomberg_deals',
                'max_items': max_items_per_spider,
                'download_delay': 8  # Conservative delay for Bloomberg
            },
            {
                'name': 'ion_analytics',
                'max_items': max_items_per_spider,
                'download_delay': 5  # Moderate delay for Ion Analytics
            }
        ]
        
        logger.info(f"🚀 Starting parallel scraping of {len(spiders)} sources...")
        logger.info(f"📊 Max items per spider: {max_items_per_spider}")
        logger.info(f"🗄️ Database: Supabase")
        
        # Run spiders in parallel using ThreadPoolExecutor
        results = {}
        with ThreadPoolExecutor(max_workers=len(spiders), thread_name_prefix='spider') as executor:
            # Submit all spider jobs
            future_to_spider = {
                executor.submit(
                    self.run_spider, 
                    spider['name'], 
                    spider['max_items'], 
                    spider['download_delay']
                ): spider['name'] 
                for spider in spiders
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_spider):
                spider_name = future_to_spider[future]
                
                if self.shutdown_requested:
                    logger.info("Shutdown requested, cancelling remaining spiders...")
                    break
                
                try:
                    spider_start = time.time()
                    result = future.result()
                    result['duration'] = time.time() - spider_start
                    results[spider_name] = result
                    
                except Exception as e:
                    logger.error(f"Spider {spider_name} raised an exception: {e}")
                    results[spider_name] = {
                        'spider': spider_name,
                        'success': False,
                        'items_scraped': 0,
                        'error': str(e),
                        'duration': 0
                    }
        
        # Calculate summary statistics
        total_duration = time.time() - self.start_time
        total_items = sum(r.get('items_scraped', 0) for r in results.values())
        successful_spiders = sum(1 for r in results.values() if r.get('success', False))
        
        summary = {
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'total_duration': round(total_duration, 2),
            'total_items_scraped': total_items,
            'successful_spiders': successful_spiders,
            'total_spiders': len(spiders),
            'success_rate': round(successful_spiders / len(spiders) * 100, 1),
            'items_per_minute': round(total_items / (total_duration / 60), 2) if total_duration > 0 else 0,
            'spider_results': results
        }
        
        self.results = summary
        return summary
    
    async def verify_supabase_connection(self) -> bool:
        """Verify Supabase connection before starting"""
        try:
            from database.adapters.supabase_adapter import SupabaseAdapter
            
            adapter = SupabaseAdapter({
                'url': self.supabase_url,
                'key': self.supabase_key
            })
            
            await adapter.connect()
            health = await adapter.health_check()
            await adapter.disconnect()
            
            if health:
                logger.info("✅ Supabase connection verified")
                return True
            else:
                logger.error("❌ Supabase health check failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Supabase connection failed: {e}")
            return False
    
    def print_summary(self):
        """Print detailed summary of scraping results"""
        if not self.results:
            logger.warning("No results to display")
            return
        
        print("\n" + "="*80)
        print("🎯 PARALLEL SCRAPING SUMMARY")
        print("="*80)
        
        summary = self.results
        print(f"📅 Started: {summary['start_time']}")
        print(f"⏱️  Duration: {summary['total_duration']:.1f} seconds")
        print(f"📊 Items Scraped: {summary['total_items_scraped']}")
        print(f"✅ Success Rate: {summary['success_rate']:.1f}% ({summary['successful_spiders']}/{summary['total_spiders']})")
        print(f"🚀 Speed: {summary['items_per_minute']:.1f} items/minute")
        
        print("\n📈 INDIVIDUAL SPIDER RESULTS:")
        print("-" * 80)
        
        for spider_name, result in summary['spider_results'].items():
            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            duration = result.get('duration', 0)
            items = result.get('items_scraped', 0)
            
            print(f"{spider_name:<20} | {status:<10} | {items:>3} items | {duration:>6.1f}s")
            
            if not result['success'] and 'error' in result:
                print(f"{'':>20} | Error: {result['error']}")
        
        print("="*80)
    
    def save_results(self, filename: str = None):
        """Save results to JSON file"""
        if not self.results:
            return
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'scraping_results_{timestamp}.json'
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            logger.info(f"📄 Results saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run parallel M&A news scraping',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python parallel_scraper.py --url "https://xxx.supabase.co" --key "your_key"
  python parallel_scraper.py --url "https://xxx.supabase.co" --key "your_key" --max-items 10
        """
    )
    
    parser.add_argument('--url', required=True, help='Supabase project URL')
    parser.add_argument('--key', required=True, help='Supabase service role key')
    parser.add_argument('--max-items', type=int, default=25, help='Max items per spider (default: 25)')
    parser.add_argument('--verify-only', action='store_true', help='Only verify Supabase connection')
    parser.add_argument('--save-results', help='Save results to specific file')
    
    args = parser.parse_args()
    
    # Create scraper instance
    scraper = ParallelScraper(args.url, args.key)
    
    try:
        # Verify Supabase connection
        logger.info("🔍 Verifying Supabase connection...")
        connection_ok = await scraper.verify_supabase_connection()
        
        if not connection_ok:
            logger.error("❌ Cannot proceed without valid Supabase connection")
            return 1
        
        if args.verify_only:
            logger.info("✅ Connection verification completed successfully")
            return 0
        
        # Run parallel scraping
        logger.info("🚀 Starting parallel scraping process...")
        results = scraper.run_parallel_scraping(args.max_items)
        
        # Display and save results
        scraper.print_summary()
        
        if args.save_results:
            scraper.save_results(args.save_results)
        else:
            scraper.save_results()
        
        # Return appropriate exit code
        success_rate = results.get('success_rate', 0)
        return 0 if success_rate >= 50 else 1
        
    except KeyboardInterrupt:
        logger.info("❌ Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)