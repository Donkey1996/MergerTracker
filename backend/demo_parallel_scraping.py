#!/usr/bin/env python3
"""
Demo script to show parallel scraping capabilities
Uses mock data when Supabase is not available
"""

import asyncio
import sys
import os
import logging
import time
import json
from datetime import datetime
from typing import Dict, Any

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockScraper:
    """Mock scraper to simulate real scraping behavior"""
    
    def __init__(self, name: str, items_count: int, duration: int, success_rate: float = 0.9):
        self.name = name
        self.items_count = items_count
        self.duration = duration
        self.success_rate = success_rate
    
    async def scrape(self) -> Dict[str, Any]:
        """Simulate scraping process"""
        logger.info(f"🕷️  Starting {self.name} scraper...")
        
        # Simulate scraping time
        await asyncio.sleep(self.duration)
        
        # Simulate success/failure
        import random
        success = random.random() < self.success_rate
        
        if success:
            items_scraped = random.randint(int(self.items_count * 0.7), self.items_count)
            logger.info(f"✅ {self.name} completed: {items_scraped} items scraped")
            
            return {
                'spider': self.name,
                'success': True,
                'items_scraped': items_scraped,
                'duration': self.duration,
                'sample_data': self._generate_sample_data(items_scraped)
            }
        else:
            logger.error(f"❌ {self.name} failed")
            return {
                'spider': self.name,
                'success': False,
                'items_scraped': 0,
                'duration': self.duration,
                'error': 'Simulated failure'
            }
    
    def _generate_sample_data(self, count: int) -> list:
        """Generate sample M&A data"""
        sample_deals = [
            {
                'title': f'Major Tech Acquisition Deal #{i+1}',
                'target_company': f'TechTarget{i+1} Inc',
                'acquirer_company': f'BigCorp{i+1} Ltd',
                'deal_value': round(random.uniform(500, 5000) * 1000000, 2),
                'industry': random.choice(['Technology', 'Healthcare', 'Finance', 'Energy']),
                'source': self.name,
                'scraped_at': datetime.utcnow().isoformat()
            }
            for i in range(min(count, 5))  # Only show first 5 for demo
        ]
        return sample_deals


async def demo_parallel_scraping():
    """Demonstrate parallel scraping capabilities"""
    
    print("🚀 MergerTracker Parallel Scraping Demo")
    print("="*60)
    print("This demo simulates scraping Bloomberg and Ion Analytics")
    print("in parallel and storing results in Supabase.")
    print()
    
    # Create mock scrapers
    scrapers = [
        MockScraper("bloomberg_deals", items_count=25, duration=3, success_rate=0.8),
        MockScraper("ion_analytics", items_count=30, duration=4, success_rate=0.9),
    ]
    
    # Start parallel scraping
    start_time = time.time()
    logger.info("Starting parallel scraping simulation...")
    
    # Run scrapers concurrently
    tasks = [scraper.scrape() for scraper in scrapers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Calculate summary
    total_duration = time.time() - start_time
    total_items = sum(r.get('items_scraped', 0) for r in results if isinstance(r, dict))
    successful_scrapers = sum(1 for r in results if isinstance(r, dict) and r.get('success', False))
    
    # Display results
    print("\n📊 SCRAPING RESULTS")
    print("-" * 60)
    
    for result in results:
        if isinstance(result, dict):
            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            items = result.get('items_scraped', 0)
            duration = result.get('duration', 0)
            
            print(f"{result['spider']:<20} | {status:<10} | {items:>3} items | {duration:>4.1f}s")
            
            # Show sample data for successful scrapers
            if result['success'] and 'sample_data' in result:
                print(f"Sample data from {result['spider']}:")
                for item in result['sample_data'][:2]:  # Show first 2 items
                    print(f"  📄 {item['title']}")
                    print(f"     Target: {item['target_company']} | Acquirer: {item['acquirer_company']}")
                    print(f"     Value: ${item['deal_value']:,.0f} | Industry: {item['industry']}")
                print()
    
    # Summary statistics
    print("-" * 60)
    print(f"⏱️  Total Duration: {total_duration:.1f} seconds")
    print(f"📈 Total Items: {total_items}")
    print(f"✅ Success Rate: {successful_scrapers}/{len(scrapers)} ({successful_scrapers/len(scrapers)*100:.1f}%)")
    print(f"🚀 Throughput: {total_items/total_duration:.1f} items/second")
    
    # Simulate database storage
    print("\n💾 SIMULATING DATABASE STORAGE")
    print("-" * 60)
    
    # Combine all scraped data
    all_data = []
    for result in results:
        if isinstance(result, dict) and result.get('success') and 'sample_data' in result:
            all_data.extend(result['sample_data'])
    
    if all_data:
        print("📊 Data that would be stored in Supabase:")
        print(f"   • {len(all_data)} M&A deals")
        print(f"   • Industries: {', '.join(set(item['industry'] for item in all_data))}")
        print(f"   • Total value: ${sum(item['deal_value'] for item in all_data):,.0f}")
        
        # Show database operations that would happen
        print("\n🗄️  Database operations (simulated):")
        print("   ✅ Connected to Supabase")
        print(f"   ✅ Inserted {len(all_data)} deals into 'deals' table")
        print(f"   ✅ Updated {len(set(item['target_company'] for item in all_data))} companies")
        print(f"   ✅ Created {len(all_data)} news article entries")
        print("   ✅ Updated analytics tables")
        
        # Save to file for inspection
        output_file = f"demo_scraped_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_duration': total_duration,
                    'total_items': total_items,
                    'successful_scrapers': successful_scrapers,
                    'scraped_at': datetime.utcnow().isoformat()
                },
                'scraped_data': all_data
            }, f, indent=2)
        
        print(f"   💾 Demo data saved to: {output_file}")
    
    print("\n" + "="*60)
    print("✅ Demo completed successfully!")
    print("\nTo run with real Supabase:")
    print("1. Set up your Supabase project")
    print("2. Get your project URL and service role key") 
    print("3. Run: python parallel_scraper.py --url 'your_url' --key 'your_key'")
    
    return True


async def main():
    """Main function"""
    try:
        success = await demo_parallel_scraping()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n❌ Demo interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)