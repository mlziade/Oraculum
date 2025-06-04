from apscheduler.schedulers.background import BackgroundScheduler
from django.core import management
import logging
import sys
import atexit

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

def start():
    """
    Start the APScheduler to run management commands on schedule.
    """
    global scheduler
    
    # Don't start scheduler during tests, migrations, or other administrative commands
    if any(cmd in sys.argv for cmd in ['test', 'collectstatic', 'makemigrations', 'migrate', 'shell']):
        logger.info("Scheduler not started - running administrative command")
        return

    # Don't start if already running
    if scheduler is not None and scheduler.running:
        logger.info("Scheduler already running")
        return

    scheduler = BackgroundScheduler()    
    scheduler.add_job(
        lambda: management.call_command('process_face_extraction_jobs', max_jobs=5, run_once=True),
        'interval',
        seconds=30, # Schedule face extraction jobs to run every 30 seconds
        id='face_extraction_job',
        replace_existing=True,
        max_instances=1  # Prevent overlapping executions
    )

    scheduler.add_job(
        lambda: management.call_command('process_tagging_jobs', max_jobs=3, run_once=True),
        'interval',
        minutes=2, # Schedule tagging jobs to run every 2 minutes
        id='tagging_job',
        replace_existing=True,
        max_instances=1  # Prevent overlapping executions
    )

    # Start the scheduler
    try:
        scheduler.start()
        logger.info("APScheduler started successfully")
        
        # Register cleanup function
        atexit.register(stop)
        
        # Log scheduled jobs
        for job in scheduler.get_jobs():
            next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'Not scheduled'
            logger.info(f"Job '{job.id}' scheduled to run next at: {next_run}")
            
    except Exception as e:
        logger.error(f"Failed to start APScheduler: {e}")

def stop():
    """
    Stop the APScheduler gracefully.
    """
    global scheduler
    
    try:
        if scheduler is not None and scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("APScheduler stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping APScheduler: {e}")

def get_scheduler():
    """
    Get the global scheduler instance.
    """
    return scheduler

def is_running():
    """
    Check if the scheduler is running.
    """
    return scheduler is not None and scheduler.running
