"""
Serializers for the chat app.
"""
from rest_framework import serializers

from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for the Message model.

    Presents sender and receiver as usernames for readability,
    while also exposing their IDs for programmatic use.
    """

    sender = serializers.CharField(source="sender.username", read_only=True)
    sender_id = serializers.IntegerField(source="sender.id", read_only=True)
    receiver = serializers.CharField(source="receiver.username", read_only=True)
    receiver_id = serializers.IntegerField(source="receiver.id", read_only=True)

    class Meta:
        model = Message
        fields = (
            "id",
            "sender",
            "sender_id",
            "receiver",
            "receiver_id",
            "content",
            "timestamp",
            "is_read",
        )
        read_only_fields = fields
