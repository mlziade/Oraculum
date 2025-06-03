from django.apps import AppConfig


class GalleryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gallery'

    def ready(self):
        """
        Initialize the APScheduler when Django starts
        """
        # Import here to avoid AppRegistryNotReady exception
        from gallery import scheduler
        
        # Don't run scheduler in test environment or when running commands
        import sys
        if not ('test' in sys.argv or 'collectstatic' in sys.argv or 
                'makemigrations' in sys.argv or 'migrate' in sys.argv):
            scheduler.start()