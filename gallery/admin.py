from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Picture, Tag, ProcessingQueue, TagClassification, FaceExtraction

@admin.register(Picture)
class PictureAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'tags')
    search_fields = ('title', 'description')
    filter_horizontal = ('tags',)
    readonly_fields = ('id', 'created_at', 'updated_at')

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

@admin.register(ProcessingQueue)
class ProcessingQueueAdmin(admin.ModelAdmin):
    list_display = ('id', 'picture_link', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('picture__title',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def picture_link(self, obj):
        """Create a clickable link to the Picture admin page"""
        if obj.picture:
            url = reverse('admin:gallery_picture_change', args=[obj.picture.pk])
            return format_html('<a href="{}">{}</a>', url, obj.picture.title)
        return '-'
    
    picture_link.short_description = 'Picture'
    picture_link.admin_order_field = 'picture__title'

@admin.register(FaceExtraction)
class FaceExtractionAdmin(admin.ModelAdmin):
    list_display = ('id', 'picture_link', 'bbox_info', 'confidence', 'created_at')
    list_filter = ('confidence', 'created_at', 'updated_at')
    search_fields = ('picture__title',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def picture_link(self, obj):
        """Create a clickable link to the Picture admin page"""
        if obj.picture:
            url = reverse('admin:gallery_picture_change', args=[obj.picture.pk])
            return format_html('<a href="{}">{}</a>', url, obj.picture.title)
        return '-'
    
    def bbox_info(self, obj):
        """Display bounding box information in a readable format"""
        return f"({obj.bbox_x}, {obj.bbox_y}) {obj.bbox_width}×{obj.bbox_height}"
    
    picture_link.short_description = 'Picture'
    picture_link.admin_order_field = 'picture__title'
    bbox_info.short_description = 'Bounding Box (x,y) w×h'
