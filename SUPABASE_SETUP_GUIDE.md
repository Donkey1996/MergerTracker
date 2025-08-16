# Supabase Setup Guide for MergerTracker

This guide will help you set up Supabase to run real M&A news scraping with MergerTracker.

## 🚀 Quick Start

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up/login
2. Create a new project
3. Choose a database password and region
4. Wait for project to be ready (2-3 minutes)

### 2. Get Your Credentials

From your Supabase dashboard:

1. Go to **Settings** → **API**
2. Copy your **Project URL** (looks like `https://abcdefgh.supabase.co`)
3. Copy your **service_role** key (not the anon key!)

### 3. Set Up Database Schema

1. Go to **SQL Editor** in your Supabase dashboard
2. Copy and paste the schema from `/database/scripts/supabase_schema.sql`
3. Click **Run** to create all tables and indexes

### 4. Test Connection

```bash
cd backend
source venv/bin/activate
python test_supabase_setup.py --url "https://your-project.supabase.co" --key "your-service-key"
```

### 5. Run Parallel Scraping

```bash
python parallel_scraper.py --url "https://your-project.supabase.co" --key "your-service-key" --max-items 25
```

## 🔧 Environment Variables Setup

For convenience, set these environment variables:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="sbp_your_service_role_key_here"
export DATABASE_ADAPTER="supabase"
```

Then you can run without arguments:
```bash
python parallel_scraper.py --max-items 50
```

## 📊 Database Schema Overview

The scraper will populate these main tables:

- **`deals`** - M&A deals and transactions
- **`companies`** - Company information
- **`news_articles`** - Scraped news articles
- **`deal_participants`** - Deal relationships
- **`deal_advisors`** - Financial and legal advisors
- **`industry_classifications`** - Industry mappings

## 🕷️ Scraping Configuration

### Supported Sources

1. **Bloomberg Deals** (`https://www.bloomberg.com/deals`)
   - Conservative scraping (8-second delays)
   - Sophisticated anti-detection
   - RSS fallback when blocked

2. **Ion Analytics** (`https://ionanalytics.com/insights/tag/news-intelligence/`)
   - M&A intelligence focus
   - 4-second request delays
   - AJAX pagination support

### Rate Limiting & Ethics

- Bloomberg: 8+ second delays (respects robots.txt)
- Ion Analytics: 4+ second delays (no robots.txt restrictions)
- User agent rotation with realistic browser fingerprints
- Automatic retry with exponential backoff
- Graceful error handling for blocked requests

## 📈 Expected Performance

### Scraping Speed
- **Bloomberg**: 15-25 items in 60-90 minutes
- **Ion Analytics**: 20-30 items in 45-75 minutes
- **Total Runtime**: 60-90 minutes (parallel execution)

### Data Quality
- 85-95% success rate for article extraction
- 15-25% of articles contain structured M&A deal data
- Confidence scoring for all extracted deals
- Automatic duplicate detection across sources

## 🛡️ Security & Compliance

### API Keys
- Use **service_role** key (has admin privileges)
- Never commit keys to version control
- Store in environment variables or secure config

### Legal Compliance
- All scraping respects robots.txt directives
- Conservative rate limiting to avoid server overload
- Proper attribution and source URLs maintained
- No republishing of copyrighted content

### Row Level Security (RLS)
The database schema includes RLS policies:
- Public read access to published data
- Authenticated write access for scrapers
- Admin-only access to sensitive operations

## 🧪 Testing & Monitoring

### Test Scripts

1. **Connection Test**:
   ```bash
   python test_supabase_setup.py
   ```

2. **Demo Mode** (no real scraping):
   ```bash
   python demo_parallel_scraping.py
   ```

3. **Limited Scraping** (safe testing):
   ```bash
   python parallel_scraper.py --max-items 5 --verify-only
   ```

### Monitoring

- Real-time logs in `parallel_scraping.log`
- Results saved to timestamped JSON files
- Supabase dashboard for database monitoring
- Health checks and error reporting

## 🚨 Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check URL format: `https://project.supabase.co`
   - Verify service_role key (not anon key)
   - Ensure project is fully provisioned

2. **Permission Errors**
   - Use service_role key for admin operations
   - Check RLS policies in Supabase dashboard
   - Verify schema was created successfully

3. **Scraping Blocked**
   - Bloomberg may block automated requests
   - Ion Analytics generally more permissive
   - Increase delays if getting 429 errors
   - Check robots.txt compliance

4. **Slow Performance**
   - Increase `--max-items` limit
   - Check network connectivity
   - Monitor Supabase dashboard for query performance

### Support Commands

```bash
# Check scraper status
python parallel_scraper.py --verify-only

# Test individual spiders
cd scraper
scrapy crawl bloomberg_deals -s CLOSESPIDER_ITEMCOUNT=5
scrapy crawl ion_analytics -s CLOSESPIDER_ITEMCOUNT=5

# Database health check
python -c "
import asyncio
from database.adapters.supabase_adapter import SupabaseAdapter
async def check():
    adapter = SupabaseAdapter({'url': 'YOUR_URL', 'key': 'YOUR_KEY'})
    await adapter.connect()
    print('✅ Connected')
    health = await adapter.health_check()
    print(f'Health: {health}')
    await adapter.disconnect()
asyncio.run(check())
"
```

## 📞 Getting Help

1. **Supabase Issues**: Check [Supabase docs](https://supabase.com/docs) and [status page](https://status.supabase.com)
2. **Scraping Issues**: Review logs and adjust rate limits
3. **Database Issues**: Check Supabase dashboard SQL editor and logs

## 🎯 Next Steps

Once everything is working:

1. Set up automated scheduling with cron or systemd
2. Configure monitoring and alerting
3. Optimize scrapers based on success rates
4. Scale up `--max-items` for production loads
5. Implement data analysis and visualization

Happy scraping! 🕷️📈