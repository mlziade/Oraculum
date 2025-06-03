from django.db import models

class Picture(models.Model):
    id = models.BigAutoField(primary_key=True, help_text="Primary key for the picture")
    title = models.CharField(max_length=255, help_text="Title of the picture")
    image = models.ImageField(upload_to='pictures/', help_text="Image file of the picture")
    description = models.TextField(blank=True, null=True, help_text="Description of the picture")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time when the picture was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time when the picture was last updated")
    miniature = models.ImageField(upload_to='miniatures/', blank=True, null=True, help_text="Miniature version of this picture (optional)")
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
    classification = models.CharField(max_length=50, blank=True, null=True, help_text="Classification of the tag (optional)")

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
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