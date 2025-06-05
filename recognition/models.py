from django.db import models
from gallery.models import Picture

class FaceExtraction(models.Model):

    class AlgorithmChoices(models.TextChoices):
        HAAR = 'haar', 'Haar Cascade'
        DNN = 'dnn', 'DNN Enhanced'

    id = models.BigAutoField(primary_key=True, help_text="Primary key for the face extraction")
    picture = models.ForeignKey(Picture, on_delete=models.CASCADE, related_name='face_extractions', help_text="Picture from which faces are extracted")
    bbox_x = models.IntegerField(help_text="X coordinate of the bounding box top-left corner")
    bbox_y = models.IntegerField(help_text="Y coordinate of the bounding box top-left corner")
    bbox_width = models.IntegerField(help_text="Width of the bounding box")
    bbox_height = models.IntegerField(help_text="Height of the bounding box")
    confidence = models.FloatField(help_text="Confidence score of the face detection")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time when the face extraction was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time when the face extraction was last updated")
    algorithm = models.CharField(max_length=10, choices=AlgorithmChoices.choices, default=AlgorithmChoices.HAAR, help_text="Algorithm used for face extraction")

    def __str__(self):
        return f"Face Extraction from {self.picture.title}"

    class Meta:
        verbose_name = "Face Extraction"
        verbose_name_plural = "Face Extractions"
        ordering = ['created_at']