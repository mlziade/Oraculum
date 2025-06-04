from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import FaceExtraction

@admin.register(FaceExtraction)
class FaceExtractionAdmin(admin.ModelAdmin):
    list_display = ('id', 'picture_link', 'bbox_x', 'bbox_y', 'bbox_width', 'bbox_height', 'confidence', 'created_at', 'updated_at')
    list_filter = ('created_at', 'confidence', 'picture')
    search_fields = ('picture__title',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('picture', ('bbox_x', 'bbox_y'), ('bbox_width', 'bbox_height'), 'confidence')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def picture_link(self, obj):
        if obj.picture:
            link = reverse("admin:gallery_picture_change", args=[obj.picture.id])
            return format_html('<a href="{}">{}</a>', link, obj.picture.title)
        return "No picture"
    picture_link.short_description = 'Picture'
    picture_link.admin_order_field = 'picture'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('picture')

