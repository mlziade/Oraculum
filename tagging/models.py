from django.db import models

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