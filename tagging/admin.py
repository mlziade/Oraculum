from django.contrib import admin
from .models import Tag, TagClassification


@admin.register(TagClassification)
class TagClassificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    readonly_fields = ('id',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'classification')
    list_filter = ('classification',)
    search_fields = ('name',)
    readonly_fields = ('id',)
