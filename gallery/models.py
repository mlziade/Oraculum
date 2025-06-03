from django.db import models

class Picture(models.Model):
    title = models.CharField(max_length=255, help_text="Title of the picture")
    image = models.ImageField(upload_to='pictures/', help_text="Image file of the picture")
    description = models.TextField(blank=True, null=True, help_text="Description of the picture")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time when the picture was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time when the picture was last updated")
    is_miniature = models.BooleanField(default=False, help_text="Indicates if the picture is a miniature")
    miniature = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='original', help_text="Miniature version of this picture (optional)")    

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Picture"
        verbose_name_plural = "Pictures"
        ordering = ['title']