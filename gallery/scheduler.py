from apscheduler.schedulers.background import BackgroundScheduler
from django.core import management
import logging

logger = logging.getLogger(__name__)

def start():
    """
    Start the APScheduler to run the process_pending_jobs command every 5 minutes.
    """
    scheduler = BackgroundScheduler()

    # Schedule job to run every 5 minutes
    scheduler.add_job(
        lambda: management.call_command('process_pending_jobs'),
        'interval',
        minutes=1,
        id='process_pending_jobs_5min',
        replace_existing=True
    )

    # Log when the next run will happen
    scheduler.start()

    for job in scheduler.get_jobs():
        logger.info(f"Job '{job.id}' scheduled to run next at: {job.next_run_time}")
