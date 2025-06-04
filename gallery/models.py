import os
import uuid
from django.db import models

def hash_upload_path(instance, filename):
    """Generate a random hash filename while preserving the extension."""
    ext = os.path.splitext(filename)[1]  # Get the file extension
    random_filename = f"{uuid.uuid4().hex}{ext}"
    return os.path.join('pictures/', random_filename)

def miniature_upload_path(instance, filename):
    """Generate a random hash filename for miniatures while preserving the extension."""
    ext = os.path.splitext(filename)[1]  # Get the file extension
    random_filename = f"{uuid.uuid4().hex}{ext}"
    return os.path.join('miniatures/', random_filename)

class Picture(models.Model):
    id = models.BigAutoField(primary_key=True, help_text="Primary key for the picture")
    title = models.CharField(max_length=255, help_text="Title of the picture")
    image = models.ImageField(upload_to=hash_upload_path, help_text="Image file of the picture")
    description = models.TextField(blank=True, null=True, help_text="Description of the picture")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time when the picture was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time when the picture was last updated")
    miniature = models.ImageField(upload_to=miniature_upload_path, blank=True, null=True, help_text="Miniature version of this picture (optional)")
    tags = models.ManyToManyField('Tag', blank=True, related_name='pictures', help_text="Tags associated with this picture")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Picture"
        verbose_name_plural = "Pictures"
        ordering = ['title']

class Tag(models.Model):
    id = models.BigAutoField(primary_key=True, help_text="Primary key for the tag")
    name = models.CharField(max_length=50, unique=True, help_text="Name of the tag")
    description = models.TextField(blank=True, null=True, help_text="Description of the tag")
    classification = models.ForeignKey('TagClassification', on_delete=models.CASCADE, related_name='tags', blank=True, null=True, help_text="Classification of the tag")

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['name']

class TagClassification(models.Model):
    id = models.BigAutoField(primary_key=True, help_text="Primary key for the tag classification")
    name = models.CharField(max_length=50, unique=True, help_text="Name of the tag classification")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tag Classification"
        verbose_name_plural = "Tag Classifications"
        ordering = ['name']

class ProcessingQueue(models.Model):

    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.BigAutoField(primary_key=True, help_text="Primary key for the processing queue")
    picture = models.ForeignKey(Picture, on_delete=models.CASCADE, related_name='processing_queue', help_text="Picture to be processed")
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING, help_text="Current status of the processing")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time when the processing was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time when the processing was last updated")

    def __str__(self):
        return f"{self.picture.title} - {self.status}"

    class Meta:
        verbose_name = "Processing Queue"
        verbose_name_plural = "Processing Queues"
        ordering = ['created_at']

class FaceExtraction(models.Model):
    id = models.BigAutoField(primary_key=True, help_text="Primary key for the face extraction")
    picture = models.ForeignKey(Picture, on_delete=models.CASCADE, related_name='face_extractions', help_text="Picture from which faces are extracted")
    face_image = models.ImageField(upload_to=hash_upload_path, help_text="Extracted face image")
    bbox_x = models.IntegerField(help_text="X coordinate of the bounding box top-left corner")
    bbox_y = models.IntegerField(help_text="Y coordinate of the bounding box top-left corner")
    bbox_width = models.IntegerField(help_text="Width of the bounding box")
    bbox_height = models.IntegerField(help_text="Height of the bounding box")
    confidence = models.FloatField(help_text="Confidence score of the face detection")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time when the face extraction was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time when the face extraction was last updated")

    def __str__(self):
        return f"Face Extraction from {self.picture.title}"

    class Meta:
        verbose_name = "Face Extraction"
        verbose_name_plural = "Face Extractions"
        ordering = ['created_at']