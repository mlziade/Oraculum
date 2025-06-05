from django.db import models
from gallery.models import Picture

class QueueJob(models.Model):

    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
    
    class JobTypeChoices(models.TextChoices):
        FACE_EXTRACTION_DNN = 'face_extraction_dnn', 'Face Extraction (DNN)'
        FACE_EXTRACTION_HAAR = 'face_extraction_haar', 'Face Extraction (Haar Cascade)'
        TAGS = 'tags', 'Tags'

    id = models.BigAutoField(primary_key=True, help_text="Primary key for the queue job")
    picture = models.ForeignKey(Picture, on_delete=models.CASCADE, related_name='queue_jobs', help_text="Picture to be processed")
    job_type = models.CharField(max_length=20, choices=JobTypeChoices.choices, help_text="Type of job to be processed")
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING, help_text="Current status of the processing")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time when the job was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time when the job was last updated")

    def __str__(self):
        return f"{self.picture.title} - {self.status}"

    class Meta:
        verbose_name = "Queue Job"
        verbose_name_plural = "Queue Jobs"
        ordering = ['created_at']