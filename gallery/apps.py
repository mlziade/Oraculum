from django.apps import AppConfig


class GalleryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gallery'
    verbose_name = 'Gallery'
    
    def ready(self):
        """
        Perform initialization tasks when the app is ready.
        This method is called when Django starts up.
        """
        pass