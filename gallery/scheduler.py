from apscheduler.schedulers.background import BackgroundScheduler
from django.core import management
import logging

logger = logging.getLogger(__name__)

def process_single_job():
    """
    Wrapper function to call the process_pending_jobs command with max_jobs=1
    """
    try:
        management.call_command('process_pending_jobs', max_jobs=1)
    except Exception as e:
        logger.error(f"Error processing job: {e}")

def start():
    """
    Start the APScheduler to run the process_pending_jobs command every 5 minutes.
    Only one job will be processed at a time with no overlapping executions.
    """
    scheduler = BackgroundScheduler()

    # Schedule job to run every 5 minutes with no overlapping executions
    scheduler.add_job(
        process_single_job,
        'interval',
        minutes=5,
        id='process_pending_jobs_5min',
        replace_existing=True,
        max_instances=1  # Prevent overlapping executions
    )

    # Log when the next run will happen
    scheduler.start()

    for job in scheduler.get_jobs():
        logger.info(f"Job '{job.id}' scheduled to run next at: {job.next_run_time}")
