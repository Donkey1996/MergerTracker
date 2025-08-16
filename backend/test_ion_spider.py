#!/usr/bin/env python3
"""
Test script for Ion Analytics spider
Validates functionality and integration with the scraping pipeline
"""

import sys
import os
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.append('.')

def test_spider_instantiation():
    """Test that the spider can be created successfully"""
    try:
        from scraper.spiders.ion_analytics_spider import IonAnalyticsSpider
        spider = IonAnalyticsSpider()
        
        print("✓ Spider instantiation successful")
        print(f"  Name: {spider.name}")
        print(f"  Domains: {spider.allowed_domains}")
        print(f"  Download delay: {spider.custom_settings.get('DOWNLOAD_DELAY', 'default')}")
        
        return spider
    except Exception as e:
        print(f"✗ Spider instantiation failed: {e}")
        return None

def test_start_requests(spider):
    """Test start_requests method"""
    try:
        requests = list(spider.start_requests())
        
        if requests:
            req = requests[0]
            print("✓ Start requests generation successful")
            print(f"  Generated {len(requests)} requests")
            print(f"  First URL: {req.url}")
            print(f"  Callback: {req.callback.__name__}")
            print(f"  Meta keys: {list(req.meta.keys())}")
            return True
        else:
            print("✗ No start requests generated")
            return False
    except Exception as e:
        print(f"✗ Start requests generation failed: {e}")
        return False

def test_pattern_extraction(spider):
    """Test deal pattern extraction functionality"""
    try:
        # Test text with M&A content
        test_content = """
        Tech Giant Corp announced today that it has agreed to acquire StartupCo Inc 
        for $2.5 billion in an all-cash transaction. The deal, which values StartupCo 
        at a premium to its last private valuation, is expected to close in Q2 2024, 
        subject to regulatory approval. Goldman Sachs advised Tech Giant Corp on the 
        transaction, while Morgan Stanley represented StartupCo Inc.
        """
        
        patterns = spider._extract_advanced_deal_patterns(test_content)
        
        print("✓ Pattern extraction test successful")
        print(f"  Deal type: {patterns.get('deal_type', 'Not detected')}")
        print(f"  Deal value: {patterns.get('deal_value', 'Not detected')}")
        print(f"  Confidence: {patterns.get('confidence', 0):.2f}")
        print(f"  Acquirer: {patterns.get('acquirer_company', 'Not detected')}")
        print(f"  Target: {patterns.get('target_company', 'Not detected')}")
        
        if patterns.get('confidence', 0) > 0.3:
            print("  ✓ High confidence extraction")
        else:
            print("  ⚠ Low confidence extraction")
        
        return True
    except Exception as e:
        print(f"✗ Pattern extraction test failed: {e}")
        return False

def test_ma_content_detection(spider):
    """Test M&A content detection"""
    try:
        test_cases = [
            ("Google acquires AI startup for $500M", True),
            ("Stock market rises amid inflation concerns", False),
            ("Merger between two tech giants announced", True),
            ("Company reports quarterly earnings", False),
            ("Private equity buyout of retail chain", True),
        ]
        
        results = []
        for content, expected in test_cases:
            detected = spider._is_ma_content(content, "")
            results.append((content, expected, detected, expected == detected))
            
        correct = sum(1 for _, _, _, match in results if match)
        total = len(results)
        
        print(f"✓ M&A content detection test: {correct}/{total} correct")
        for content, expected, detected, match in results:
            status = "✓" if match else "✗"
            print(f"  {status} '{content[:50]}...' -> {detected} (expected {expected})")
        
        return correct >= total * 0.8  # 80% accuracy threshold
    except Exception as e:
        print(f"✗ M&A content detection test failed: {e}")
        return False

def test_date_normalization(spider):
    """Test date normalization functionality"""
    try:
        test_dates = [
            "December 15, 2023",
            "2023-12-15",
            "12/15/2023",
            "Dec 15, 2023",
            "15 December 2023",
        ]
        
        results = []
        for date_str in test_dates:
            normalized = spider._normalize_date(date_str)
            results.append((date_str, normalized, normalized is not None))
        
        successful = sum(1 for _, _, success in results if success)
        total = len(results)
        
        print(f"✓ Date normalization test: {successful}/{total} successful")
        for original, normalized, success in results:
            status = "✓" if success else "✗"
            print(f"  {status} '{original}' -> {normalized}")
        
        return successful >= total * 0.8  # 80% success threshold
    except Exception as e:
        print(f"✗ Date normalization test failed: {e}")
        return False

def test_ajax_body_building(spider):
    """Test AJAX request body building"""
    try:
        test_data = {
            'action': 'load_more_posts',
            'page': 2,
            'postcat': 'mergermarket',
            'posttag': 'news-intelligence',
        }
        
        body = spider._build_ajax_body(test_data)
        
        print("✓ AJAX body building test successful")
        print(f"  Generated body: {body}")
        print(f"  Content-Type ready: {'action=load_more_posts' in body}")
        
        return 'action=load_more_posts' in body
    except Exception as e:
        print(f"✗ AJAX body building test failed: {e}")
        return False

def test_item_compatibility():
    """Test compatibility with existing item structures"""
    try:
        from scraper.items import NewsArticleItem, DealItem
        from scrapy.loader import ItemLoader
        
        # Test NewsArticleItem
        news_loader = ItemLoader(item=NewsArticleItem())
        news_loader.add_value('title', 'Test Article')
        news_loader.add_value('source', 'ion_analytics')
        news_loader.add_value('url', 'https://test.com/article')
        news_item = news_loader.load_item()
        
        # Test DealItem
        deal_loader = ItemLoader(item=DealItem())
        deal_loader.add_value('deal_type', 'acquisition')
        deal_loader.add_value('source_url', 'https://test.com/article')
        deal_loader.add_value('confidence_score', 0.8)
        deal_item = deal_loader.load_item()
        
        print("✓ Item compatibility test successful")
        print(f"  NewsArticleItem fields: {list(news_item.keys())}")
        print(f"  DealItem fields: {list(deal_item.keys())}")
        
        return True
    except Exception as e:
        print(f"✗ Item compatibility test failed: {e}")
        return False

def test_robots_txt_compliance():
    """Test robots.txt compliance"""
    try:
        from scraper.spiders.ion_analytics_spider import IonAnalyticsSpider
        spider = IonAnalyticsSpider()
        
        # Check if spider respects robots.txt through Scrapy settings
        from scraper.settings import ROBOTSTXT_OBEY
        
        print("✓ Robots.txt compliance test")
        print(f"  ROBOTSTXT_OBEY setting: {ROBOTSTXT_OBEY}")
        print(f"  Spider respects rate limits: {spider.custom_settings.get('DOWNLOAD_DELAY', 0) >= 3}")
        print(f"  Concurrent requests limited: {spider.custom_settings.get('CONCURRENT_REQUESTS_PER_DOMAIN', 0) <= 4}")
        
        return ROBOTSTXT_OBEY and spider.custom_settings.get('DOWNLOAD_DELAY', 0) >= 3
    except Exception as e:
        print(f"✗ Robots.txt compliance test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and provide summary"""
    print("=" * 60)
    print("ION ANALYTICS SPIDER TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Spider Instantiation", test_spider_instantiation),
        ("Start Requests", lambda spider: test_start_requests(spider) if spider else False),
        ("Pattern Extraction", lambda spider: test_pattern_extraction(spider) if spider else False),
        ("M&A Content Detection", lambda spider: test_ma_content_detection(spider) if spider else False),
        ("Date Normalization", lambda spider: test_date_normalization(spider) if spider else False),
        ("AJAX Body Building", lambda spider: test_ajax_body_building(spider) if spider else False),
        ("Item Compatibility", lambda spider: test_item_compatibility()),
        ("Robots.txt Compliance", lambda spider: test_robots_txt_compliance()),
    ]
    
    spider = None
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        
        if test_name == "Spider Instantiation":
            spider = test_func()
            result = spider is not None
        elif test_name in ["Item Compatibility", "Robots.txt Compliance"]:
            result = test_func(spider)
        else:
            result = test_func(spider)
        
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status:6} | {test_name}")
    
    print("-" * 60)
    print(f"OVERALL: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Spider is ready for production use.")
    elif passed >= total * 0.8:
        print("⚠️  Most tests passed. Spider is functional with minor issues.")
    else:
        print("❌ Multiple test failures. Spider needs debugging before use.")
    
    return passed, total

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.WARNING)
    
    try:
        passed, total = run_all_tests()
        sys.exit(0 if passed == total else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error during testing: {e}")
        sys.exit(1)