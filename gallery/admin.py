from django.contrib import admin
from .models import Picture, Tag, ProcessingQueue

@admin.register(Picture)
class PictureAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'tags')
    search_fields = ('title', 'description')
    filter_horizontal = ('tags',)
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'classification', 'description')
    list_filter = ('classification',)
    search_fields = ('name', 'description')
    readonly_fields = ('id',)

@admin.register(ProcessingQueue)
class ProcessingQueueAdmin(admin.ModelAdmin):
    list_display = ('id', 'picture', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('picture__title',)
    readonly_fields = ('id', 'created_at', 'updated_at')
