"""Django admin configuration for the capsules app.

This module configures the Django admin interface for managing TimeCapsule and
CapsuleContent models. It includes custom admin views, inline content management,
and specialized display and filtering options.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import TimeCapsule, CapsuleContent

# Register your models here.

class CapsuleContentInline(admin.TabularInline):
    """Inline admin interface for CapsuleContent.
    
    Allows managing capsule content directly from the TimeCapsule admin page.
    """
    model = CapsuleContent
    extra = 1

@admin.register(CapsuleContent)
class CapsuleContentAdmin(admin.ModelAdmin):
    """Admin interface for CapsuleContent model.
    
    Provides standalone management of capsule content with:
    - List display configuration
    - Search and filter options
    """
    list_display = ('title', 'capsule', 'content_type', 'uploaded_at', 'view_file')
    list_filter = ('content_type', 'uploaded_at')
    search_fields = ('title', 'capsule__title')
    readonly_fields = ('uploaded_at',)
    
    def view_file(self, obj):
        """Displays a link to view the uploaded file.
        
        If a file is associated with the CapsuleContent instance, returns an HTML
        link to view the file. Otherwise, returns a message indicating no file.
        """
        if obj.file:
            return format_html('<a href="{}" target="_blank">View File</a>', obj.file.url)
        return "No file"
    view_file.short_description = 'File'

@admin.register(TimeCapsule)
class TimeCapsuleAdmin(admin.ModelAdmin):
    """Admin interface for TimeCapsule model.
    
    Customizes the admin interface with:
    - List display configuration
    - Search functionality
    - Filtering options
    - Inline content management
    """
    list_display = ('title', 'creator', 'unlock_date', 'status', 'created_at', 'content_count')
    list_filter = ('status', 'created_at', 'unlock_date')
    search_fields = ('title', 'creator__username', 'description')
    readonly_fields = ('created_at',)
    date_hierarchy = 'unlock_date'
    inlines = [CapsuleContentInline]
    
    def content_count(self, obj):
        """Displays the number of items in the time capsule.
        
        Returns the count of CapsuleContent instances associated with the
        TimeCapsule instance.
        """
        return obj.contents.count()
    content_count.short_description = 'Number of Items'

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'creator')
        }),
        ('Time Settings', {
            'fields': ('unlock_date', 'status', 'is_public')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    class Media:
        """Media class for admin interface customization.
        
        Includes custom CSS for admin styling.
        """
        css = {
            'all': ('css/admin.css',)
        }
