from django.contrib import admin
from .models import Tag, TagClassification


@admin.register(TagClassification)
class TagClassificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    readonly_fields = ('id',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'classification', 'description')
    list_filter = ('classification',)
    search_fields = ('name', 'description')
    readonly_fields = ('id',)
