from django.apps import AppConfig


class RecognitionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recognition'
    verbose_name = 'Face Recognition'
    
    def ready(self):
        """
        Perform initialization tasks when the app is ready.
        This method is called when Django starts up.
        """
        pass