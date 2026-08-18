"""
WebSocket URL routing for the chat app.

URL pattern:
    ws/chat/<int:user_id>/

Where <user_id> is the ID of the target user to chat with.
The authenticated sender is derived from the JWT token in
the query string.
"""
from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path("ws/chat/<int:user_id>/", consumers.ChatConsumer.as_asgi()),
]
