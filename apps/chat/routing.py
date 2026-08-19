"""
WebSocket URL routing for the chat app.

URL patterns:
    ws/chat/<int:user_id>/   — Direct messaging with a target user
    ws/notifications/        — Sidebar notification stream (auto-connects on page load)

The authenticated sender is derived from the JWT token in
the query string.
"""
from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path("ws/chat/<int:user_id>/", consumers.ChatConsumer.as_asgi()),
    path("ws/notifications/", consumers.NotificationConsumer.as_asgi()),
]
