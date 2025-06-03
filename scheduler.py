import os
import sys
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from django.core import management
from django.conf import settings
import time
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class JobScheduler:
    """Scheduler for processing pending jobs using Django management commands with APScheduler"""
    
    def __init__(self):
        self.scheduler = None
        self.is_running = False
        self.max_jobs_per_run = 10
        self.ollama_model = None
    
    def configure(self, max_jobs_per_run=10, ollama_model=None):
        """Configure scheduler parameters"""
        self.max_jobs_per_run = max_jobs_per_run
        self.ollama_model = ollama_model
        logger.info(f"Scheduler configured: max_jobs={max_jobs_per_run}, model={ollama_model}")
    
    def process_pending_jobs(self):
        """Execute the process_pending_jobs Django management command"""
        try:
            logger.info("Starting to process pending jobs...")
            
            # Build command arguments
            cmd_args = ['process_pending_jobs', f'--max-jobs={self.max_jobs_per_run}']
            
            if self.ollama_model:
                cmd_args.append(f'--model={self.ollama_model}')
            
            # Execute the Django management command
            management.call_command(*cmd_args)
            
            logger.info("Job processing completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing pending jobs: {str(e)}")
    
    def start_scheduler(self, interval_minutes=5):
        """Start the job scheduler with APScheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.scheduler = BackgroundScheduler()
        self.is_running = True
        
        logger.info("Starting job scheduler with APScheduler...")
        
        # Schedule job to run every 5 minutes (or custom interval)
        self.scheduler.add_job(
            self.process_pending_jobs,
            'interval',
            minutes=interval_minutes,
            id='process_pending_jobs_scheduler',
            replace_existing=True
        )
        
        # Start the scheduler
        self.scheduler.start()
        
        # Log when the next run will happen
        for job in self.scheduler.get_jobs():
            logger.info(f"Job '{job.id}' scheduled to run next at: {job.next_run_time}")
        
        logger.info(f"Scheduler started. Jobs will be processed every {interval_minutes} minutes.")
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Keep the main thread alive
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        finally:
            self.stop_scheduler()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down scheduler...")
        self.stop_scheduler()
    
    def stop_scheduler(self):
        """Stop the job scheduler"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("APScheduler shutdown completed")
        
        self.is_running = False
        logger.info("Scheduler stopped")
    
    def run_once(self):
        """Run job processing once (useful for testing)"""
        logger.info("Running job processing once...")
        self.process_pending_jobs()
    
    def list_jobs(self):
        """List all scheduled jobs"""
        if self.scheduler:
            jobs = self.scheduler.get_jobs()
            for job in jobs:
                logger.info(f"Job ID: {job.id}, Next run: {job.next_run_time}")
            return jobs
        return []


def start(interval_minutes=5, max_jobs=10, model=None):
    """
    Start the APScheduler to run the process_pending_jobs command every 5 minutes.
    This function matches your original pattern.
    """
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oraculum.settings')
    
    import django
    django.setup()
    
    scheduler = JobScheduler()
    scheduler.configure(max_jobs_per_run=max_jobs, ollama_model=model)
    
    # Create APScheduler instance
    background_scheduler = BackgroundScheduler()
    
    # Schedule job to run every interval_minutes
    background_scheduler.add_job(
        scheduler.process_pending_jobs,
        'interval',
        minutes=interval_minutes,
        id='process_pending_jobs_scheduler',
        replace_existing=True
    )
    
    # Start the scheduler
    background_scheduler.start()
    
    # Log when the next run will happen
    for job in background_scheduler.get_jobs():
        logger.info(f"Job '{job.id}' scheduled to run next at: {job.next_run_time}")
    
    logger.info(f"Background scheduler started. Jobs will be processed every {interval_minutes} minutes.")
    
    return background_scheduler


def main():
    """Main function to run the scheduler"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Django Job Scheduler with APScheduler')
    parser.add_argument(
        '--max-jobs',
        type=int,
        default=10,
        help='Maximum number of jobs to process per run (default: 10)'
    )
    parser.add_argument(
        '--model',
        type=str,
        help='Ollama model to use for processing (must be vision-capable)'
    )
    parser.add_argument(
        '--run-once',
        action='store_true',
        help='Run job processing once and exit'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Interval in minutes between job runs (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oraculum.settings')
    
    import django
    django.setup()
    
    # Create and configure scheduler
    scheduler = JobScheduler()
    scheduler.configure(
        max_jobs_per_run=args.max_jobs,
        ollama_model=args.model
    )
    
    if args.run_once:
        # Run once and exit
        scheduler.run_once()
    else:
        # Start continuous scheduler with specified interval
        scheduler.start_scheduler(interval_minutes=args.interval)


if __name__ == '__main__':
    main()
