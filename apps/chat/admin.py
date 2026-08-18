"""
Admin configuration for the chat app.
"""
from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin view for the Message model."""

    list_display = ("id", "sender", "receiver", "content_preview", "timestamp", "is_read")
    list_filter = ("is_read", "timestamp")
    search_fields = ("sender__username", "receiver__username", "content")
    readonly_fields = ("timestamp",)
    ordering = ("-timestamp",)

    @admin.display(description="Content")
    def content_preview(self, obj):
        """Show a truncated version of the message content."""
        return obj.content[:75] + "..." if len(obj.content) > 75 else obj.content
