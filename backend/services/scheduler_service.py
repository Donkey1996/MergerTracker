"""
Scheduler service for MergerTracker

This service manages the scheduling and execution of scraping jobs
using APScheduler for automated data collection.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
import subprocess
import os

from .database_service import get_database_service

logger = logging.getLogger(__name__)


class ScraperSchedulerService:
    """Service for scheduling and managing scraping jobs"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.scheduler = None
        self.scraper_jobs = {}
        self._running = False
    
    async def initialize(self) -> bool:
        """Initialize the scheduler service"""
        try:
            # Configure job stores and executors
            jobstores = {
                'default': RedisJobStore(
                    host='localhost', 
                    port=6379, 
                    db=1,
                    decode_responses=True
                )
            }
            
            executors = {
                'default': AsyncIOExecutor(),
            }
            
            job_defaults = {
                'coalesce': False,
                'max_instances': 3,
                'misfire_grace_time': 300,  # 5 minutes
            }
            
            self.scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone='UTC'
            )
            
            # Add default scraping jobs
            await self._setup_default_jobs()
            
            logger.info("Scheduler service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize scheduler service: {e}")
            return False
    
    async def start(self) -> bool:
        """Start the scheduler"""
        try:
            if not self.scheduler:
                await self.initialize()
            
            self.scheduler.start()
            self._running = True
            logger.info("Scheduler service started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown the scheduler"""
        try:
            if self.scheduler and self._running:
                self.scheduler.shutdown(wait=True)
                self._running = False
                logger.info("Scheduler service shutdown completed")
            return True
            
        except Exception as e:
            logger.error(f"Error during scheduler shutdown: {e}")
            return False
    
    async def _setup_default_jobs(self):
        """Setup default scraping jobs"""
        
        # CNBC scraping - every 4 hours
        self.scheduler.add_job(
            func=self._run_cnbc_scraper,
            trigger=IntervalTrigger(hours=4),
            id='cnbc_scraper',
            name='CNBC M&A News Scraper',
            replace_existing=True
        )
        
        # Yahoo Finance scraping - every 6 hours
        self.scheduler.add_job(
            func=self._run_yahoo_finance_scraper,
            trigger=IntervalTrigger(hours=6),
            id='yahoo_finance_scraper',
            name='Yahoo Finance M&A Scraper',
            replace_existing=True
        )
        
        # MarketWatch scraping - every 8 hours
        self.scheduler.add_job(
            func=self._run_marketwatch_scraper,
            trigger=IntervalTrigger(hours=8),
            id='marketwatch_scraper',
            name='MarketWatch M&A Scraper',
            replace_existing=True
        )
        
        # Daily analytics update - at 2 AM UTC
        self.scheduler.add_job(
            func=self._update_analytics,
            trigger=CronTrigger(hour=2, minute=0),
            id='daily_analytics_update',
            name='Daily Analytics Update',
            replace_existing=True
        )
        
        # Weekly backup - Sundays at 3 AM UTC
        self.scheduler.add_job(
            func=self._create_backup,
            trigger=CronTrigger(day_of_week=6, hour=3, minute=0),
            id='weekly_backup',
            name='Weekly Database Backup',
            replace_existing=True
        )
        
        logger.info("Default scraping jobs configured")
    
    async def _run_cnbc_scraper(self):
        """Run CNBC scraper"""
        try:
            logger.info("Starting CNBC scraper job")
            
            # Run scrapy spider
            result = await self._run_scrapy_spider('cnbc')
            
            if result['success']:
                logger.info(f"CNBC scraper completed successfully. Items scraped: {result['items_count']}")
                await self._log_scraper_run('cnbc', True, result['items_count'])
            else:
                logger.error(f"CNBC scraper failed: {result['error']}")
                await self._log_scraper_run('cnbc', False, 0, result['error'])
                
        except Exception as e:
            logger.error(f"Error in CNBC scraper job: {e}")
            await self._log_scraper_run('cnbc', False, 0, str(e))
    
    async def _run_yahoo_finance_scraper(self):
        """Run Yahoo Finance scraper"""
        try:
            logger.info("Starting Yahoo Finance scraper job")
            
            result = await self._run_scrapy_spider('yahoo_finance')
            
            if result['success']:
                logger.info(f"Yahoo Finance scraper completed successfully. Items scraped: {result['items_count']}")
                await self._log_scraper_run('yahoo_finance', True, result['items_count'])
            else:
                logger.error(f"Yahoo Finance scraper failed: {result['error']}")
                await self._log_scraper_run('yahoo_finance', False, 0, result['error'])
                
        except Exception as e:
            logger.error(f"Error in Yahoo Finance scraper job: {e}")
            await self._log_scraper_run('yahoo_finance', False, 0, str(e))
    
    async def _run_marketwatch_scraper(self):
        """Run MarketWatch scraper"""
        try:
            logger.info("Starting MarketWatch scraper job")
            
            result = await self._run_scrapy_spider('marketwatch')
            
            if result['success']:
                logger.info(f"MarketWatch scraper completed successfully. Items scraped: {result['items_count']}")
                await self._log_scraper_run('marketwatch', True, result['items_count'])
            else:
                logger.error(f"MarketWatch scraper failed: {result['error']}")
                await self._log_scraper_run('marketwatch', False, 0, result['error'])
                
        except Exception as e:
            logger.error(f"Error in MarketWatch scraper job: {e}")
            await self._log_scraper_run('marketwatch', False, 0, str(e))
    
    async def _run_scrapy_spider(self, spider_name: str) -> Dict[str, Any]:
        """Run a Scrapy spider and return results"""
        try:
            # Change to scraper directory
            scraper_dir = os.path.join(os.path.dirname(__file__), '..', 'scraper')
            
            # Run scrapy command
            cmd = [
                'scrapy', 'crawl', spider_name,
                '-s', 'LOG_LEVEL=INFO',
                '-s', 'FEEDS={items.json:json}',
                '--nolog'  # Disable scrapy logging to stdout
            ]
            
            # Run the process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=scraper_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Try to count items from output file
                items_count = 0
                items_file = os.path.join(scraper_dir, 'items.json')
                if os.path.exists(items_file):
                    import json
                    try:
                        with open(items_file, 'r') as f:
                            items = json.load(f)
                            items_count = len(items) if isinstance(items, list) else 1
                        os.remove(items_file)  # Clean up
                    except:
                        pass
                
                return {
                    'success': True,
                    'items_count': items_count,
                    'stdout': stdout.decode() if stdout else '',
                    'stderr': stderr.decode() if stderr else ''
                }
            else:
                return {
                    'success': False,
                    'error': stderr.decode() if stderr else 'Unknown error',
                    'items_count': 0
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'items_count': 0
            }
    
    async def _log_scraper_run(self, spider_name: str, success: bool, items_count: int, error: str = None):
        """Log scraper run to database"""
        try:
            db_service = await get_database_service()
            
            # Create a scraper run log entry
            log_data = {
                'spider_name': spider_name,
                'run_date': datetime.utcnow(),
                'success': success,
                'items_scraped': items_count,
                'error_message': error,
                'run_duration': 0  # Could be calculated if needed
            }
            
            # In a real implementation, you'd want to store this in a dedicated table
            # For now, we'll just log it
            logger.info(f"Scraper run logged: {log_data}")
            
        except Exception as e:
            logger.error(f"Error logging scraper run: {e}")
    
    async def _update_analytics(self):
        """Update analytics data"""
        try:
            logger.info("Starting daily analytics update")
            
            db_service = await get_database_service()
            
            # Update various analytics
            # This could include calculating trends, aggregating data, etc.
            yesterday = datetime.utcnow() - timedelta(days=1)
            analytics = await db_service.get_deal_analytics(
                date_from=yesterday,
                date_to=datetime.utcnow()
            )
            
            logger.info(f"Analytics updated: {analytics['summary']}")
            
        except Exception as e:
            logger.error(f"Error updating analytics: {e}")
    
    async def _create_backup(self):
        """Create database backup"""
        try:
            logger.info("Starting weekly database backup")
            
            db_service = await get_database_service()
            
            # Generate backup filename with timestamp
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_path = f"/tmp/mergertracker_backup_{timestamp}.sql"
            
            success = await db_service.create_backup(backup_path)
            
            if success:
                logger.info(f"Database backup created successfully: {backup_path}")
            else:
                logger.error("Database backup failed")
                
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
    
    # Job management methods
    async def add_custom_job(
        self,
        func,
        trigger,
        job_id: str,
        name: str = None,
        **kwargs
    ) -> bool:
        """Add a custom scheduled job"""
        try:
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                name=name or job_id,
                replace_existing=True,
                **kwargs
            )
            logger.info(f"Custom job added: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding custom job {job_id}: {e}")
            return False
    
    async def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Job removed: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")
            return False
    
    async def pause_job(self, job_id: str) -> bool:
        """Pause a scheduled job"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Job paused: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")
            return False
    
    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Job resumed: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")
            return False
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a specific job"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                return {
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger),
                    'pending': job.pending
                }
            else:
                return {'error': 'Job not found'}
                
        except Exception as e:
            logger.error(f"Error getting job status {job_id}: {e}")
            return {'error': str(e)}
    
    async def list_jobs(self) -> List[Dict[str, Any]]:
        """List all scheduled jobs"""
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger),
                    'pending': job.pending
                })
            return jobs
            
        except Exception as e:
            logger.error(f"Error listing jobs: {e}")
            return []
    
    async def run_job_now(self, job_id: str) -> bool:
        """Manually trigger a job to run now"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                self.scheduler.modify_job(job_id, next_run_time=datetime.utcnow())
                logger.info(f"Job {job_id} scheduled to run immediately")
                return True
            else:
                logger.error(f"Job {job_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Error running job {job_id}: {e}")
            return False


# Global scheduler service instance
_scheduler_service: Optional[ScraperSchedulerService] = None


async def get_scheduler_service() -> ScraperSchedulerService:
    """Get the global scheduler service instance"""
    global _scheduler_service
    
    if _scheduler_service is None:
        _scheduler_service = ScraperSchedulerService()
        await _scheduler_service.initialize()
        await _scheduler_service.start()
    
    return _scheduler_service


async def initialize_scheduler_service() -> ScraperSchedulerService:
    """Initialize the scheduler service (for application startup)"""
    return await get_scheduler_service()


async def shutdown_scheduler_service():
    """Shutdown the scheduler service (for application shutdown)"""
    global _scheduler_service
    
    if _scheduler_service:
        await _scheduler_service.shutdown()
        _scheduler_service = None