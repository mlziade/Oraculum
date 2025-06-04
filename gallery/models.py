import os
import uuid
from django.db import models
from .service import hash_upload_path, miniature_upload_path

class Picture(models.Model):
    id = models.BigAutoField(primary_key=True, help_text="Primary key for the picture")
    title = models.CharField(max_length=255, help_text="Title of the picture")
    image = models.ImageField(upload_to=hash_upload_path, help_text="Image file of the picture")
    description = models.TextField(blank=True, null=True, help_text="Description of the picture")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time when the picture was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time when the picture was last updated")
    miniature = models.ImageField(upload_to=miniature_upload_path, blank=True, null=True, help_text="Miniature version of this picture (optional)")
    tags = models.ManyToManyField('tagging.Tag', blank=True, related_name='pictures', help_text="Tags associated with this picture")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Picture"
        verbose_name_plural = "Pictures"
        ordering = ['title']