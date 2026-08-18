"""
WebSocket consumer for real-time chat messaging.

Handles the full lifecycle of a WebSocket chat connection:
  1. Authentication validation on connect
  2. Joining a deterministic channel group for the conversation
  3. Joining a user-specific group for real-time cross-chat notifications
  4. Receiving messages, persisting to DB, and broadcasting to both groups
  5. Leaving groups on disconnect
"""
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model

from .models import Message

User = get_user_model()


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    Async WebSocket consumer for direct messaging and real-time notifications.

    URL pattern: ws/chat/<int:user_id>/?token=<jwt>
    Where <user_id> is the target user to chat with.
    """

    async def connect(self):
        """
        Handle WebSocket connection.

        Validates authentication, joins conversation room group and
        user-specific notification group.
        """
        self.user = self.scope.get("user")

        # Reject unauthenticated connections
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # Extract and validate the target user
        self.target_user_id = self.scope["url_route"]["kwargs"]["user_id"]

        # Prevent chatting with yourself
        if self.target_user_id == self.user.id:
            await self.close(code=4003)
            return

        target_exists = await self._user_exists(self.target_user_id)
        if not target_exists:
            await self.close(code=4004)
            return

        # Deterministic room name for conversation pair
        self.room_name = self._get_room_name(self.user.id, self.target_user_id)
        # User-specific group name for instant notifications from any sender
        self.user_group = f"user_{self.user.id}"

        # Join both the conversation room group and personal notification group
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.channel_layer.group_add(self.user_group, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        """Leave channel groups on disconnect."""
        if hasattr(self, "room_name"):
            await self.channel_layer.group_discard(
                self.room_name, self.channel_name
            )
        if hasattr(self, "user_group"):
            await self.channel_layer.group_discard(
                self.user_group, self.channel_name
            )

    async def receive_json(self, content, **kwargs):
        """
        Handle incoming messages from the WebSocket client.

        Validates content, persists to database, and broadcasts to both
        the conversation room group and recipient's personal notification group.
        """
        message_text = content.get("message", "").strip()

        if not message_text:
            await self.send_json(
                {"type": "error", "detail": "Message content cannot be empty."}
            )
            return

        # Persist the message to the database
        message = await self._save_message(
            sender_id=self.user.id,
            receiver_id=self.target_user_id,
            content=message_text,
        )

        payload = {
            "type": "chat.message",
            "message": {
                "id": message["id"],
                "sender": message["sender"],
                "sender_id": message["sender_id"],
                "receiver_id": self.target_user_id,
                "content": message["content"],
                "timestamp": message["timestamp"],
            },
        }

        # Broadcast to conversation group (for users currently in this chat window)
        await self.channel_layer.group_send(self.room_name, payload)

        # Broadcast to target recipient's personal group (for instant notifications across all tabs/chats)
        target_user_group = f"user_{self.target_user_id}"
        await self.channel_layer.group_send(target_user_group, payload)

    async def chat_message(self, event):
        """
        Handle messages received from channel groups.
        Sends message data to the WebSocket client.
        """
        await self.send_json(
            {
                "type": "chat_message",
                "message": event["message"],
            }
        )

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    @staticmethod
    def _get_room_name(user_id_1, user_id_2):
        """Compute a deterministic room name for two users."""
        ids = sorted([user_id_1, user_id_2])
        return f"chat_{ids[0]}_{ids[1]}"

    @database_sync_to_async
    def _save_message(self, sender_id, receiver_id, content):
        """Save a message to the database and return a serializable dict."""
        message = Message.objects.create(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
        )
        return {
            "id": message.id,
            "sender": message.sender.username,
            "sender_id": message.sender_id,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
        }

    @database_sync_to_async
    def _user_exists(self, user_id):
        """Check if a user with the given ID exists."""
        return User.objects.filter(pk=user_id).exists()
