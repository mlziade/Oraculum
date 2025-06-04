from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'

    def ready(self):
        """
        Initialize the scheduler when Django starts
        """
        # Import here to avoid AppRegistryNotReady exception
        try:
            from jobs import scheduler
            scheduler.start()
            logger.info("Job scheduler initialized successfully")
        except ImportError as e:
            logger.error(f"Failed to import scheduler: {e}")
        except Exception as e:
            logger.error(f"Failed to start job scheduler: {e}")
