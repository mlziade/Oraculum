from django.contrib import admin
from .models import Picture

@admin.register(Picture)
class PictureAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'tags')
    search_fields = ('title', 'description')
    filter_horizontal = ('tags',)
    readonly_fields = ('id', 'created_at', 'updated_at')
