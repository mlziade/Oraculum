from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import QueueJob


@admin.register(QueueJob)
class QueueJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'picture_link', 'job_type', 'status', 'created_at', 'updated_at')
    list_filter = ('job_type', 'status', 'created_at', 'updated_at')
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
