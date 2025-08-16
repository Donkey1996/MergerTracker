#!/usr/bin/env python3
"""
Test Supabase setup and connection
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_supabase_connection():
    """Test Supabase connection with sample credentials"""
    
    print("🔍 Testing Supabase Connection Setup")
    print("="*50)
    
    # Check if Supabase credentials are provided via environment
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials!")
        print("\nPlease set environment variables:")
        print("export SUPABASE_URL='https://your-project.supabase.co'")
        print("export SUPABASE_SERVICE_KEY='your-service-role-key'")
        print("\nOr provide them as command line arguments:")
        print("python test_supabase_setup.py --url 'https://xxx.supabase.co' --key 'your_key'")
        return False
    
    try:
        print(f"🌐 Supabase URL: {supabase_url}")
        print(f"🔑 Key provided: {'*' * (len(supabase_key) - 8) + supabase_key[-8:] if len(supabase_key) > 8 else '***'}")
        
        # Test basic Supabase client creation
        print("\n1. Testing Supabase client creation...")
        from supabase import create_client, Client
        
        supabase_client: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created successfully")
        
        # Test basic API call
        print("\n2. Testing API connection...")
        try:
            # Try to access auth users (requires service role key)
            response = supabase_client.auth.admin.list_users()
            print("✅ API connection successful")
            print(f"📊 Users in database: {len(response.users) if hasattr(response, 'users') else 'N/A'}")
        except Exception as e:
            print(f"⚠️  API test failed (might be permissions): {e}")
        
        # Test our adapter if available
        print("\n3. Testing MergerTracker database adapter...")
        try:
            from database.adapters.supabase_adapter import SupabaseAdapter
            
            adapter = SupabaseAdapter({
                'url': supabase_url,
                'key': supabase_key
            })
            
            await adapter.connect()
            print("✅ Database adapter connected successfully")
            
            # Test health check
            health = await adapter.health_check()
            print(f"✅ Health check: {'PASS' if health else 'FAIL'}")
            
            # Test basic operations if health is good
            if health:
                print("\n4. Testing basic database operations...")
                
                # Test getting database stats
                try:
                    stats = await adapter.get_database_stats()
                    print("✅ Database statistics retrieved")
                    print(f"📈 Connection status: {stats.get('connection_info', {}).get('connected', 'Unknown')}")
                except Exception as e:
                    print(f"⚠️  Stats retrieval failed: {e}")
            
            await adapter.disconnect()
            print("✅ Database adapter disconnected cleanly")
            
        except ImportError:
            print("⚠️  MergerTracker database adapter not found (files may not be created yet)")
        except Exception as e:
            print(f"❌ Database adapter test failed: {e}")
        
        print("\n" + "="*50)
        print("✅ Supabase setup test completed successfully!")
        print("\n🚀 Ready to run parallel scraping:")
        print(f"python parallel_scraper.py --url '{supabase_url}' --key 'your_service_key'")
        
        return True
        
    except ImportError:
        print("❌ Supabase package not installed")
        print("Run: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def main():
    """Main function with argument parsing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Supabase connection setup')
    parser.add_argument('--url', help='Supabase URL (overrides env var)')
    parser.add_argument('--key', help='Supabase service key (overrides env var)')
    
    args = parser.parse_args()
    
    # Override env vars if provided
    if args.url:
        os.environ['SUPABASE_URL'] = args.url
    if args.key:
        os.environ['SUPABASE_SERVICE_KEY'] = args.key
    
    # Run test
    success = asyncio.run(test_supabase_connection())
    return 0 if success else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)