"""
Models for the chat app.
"""
from django.conf import settings
from django.db import models


class Message(models.Model):
    """
    Represents a direct message between two users.
    """

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_messages",
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            models.Index(
                fields=["sender", "receiver", "timestamp"],
                name="idx_msg_sender_receiver_ts",
            ),
        ]

    def __str__(self):
        return (
            f"{self.sender.username} → {self.receiver.username}: "
            f"{self.content[:50]}"
        )
