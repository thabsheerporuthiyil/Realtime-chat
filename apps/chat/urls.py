"""
URL configuration for the chat app.

Endpoints:
    GET /api/chat/messages/<user_id>/  — Message history with a specific user
"""
from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path(
        "messages/<int:user_id>/",
        views.MessageHistoryView.as_view(),
        name="message-history",
    ),
]
