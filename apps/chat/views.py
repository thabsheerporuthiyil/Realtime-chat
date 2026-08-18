"""
Views for the chat app.

Provides paginated message history between the authenticated
user and a specified target user.
"""
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound

from .models import Message
from .serializers import MessageSerializer

User = get_user_model()


class MessageHistoryView(generics.ListAPIView):
    """
    Retrieve the chat history between the authenticated user
    and a target user identified by `user_id` in the URL.

    GET /api/chat/messages/<user_id>/

    Results are paginated (default: 50 per page) and ordered
    by timestamp ascending. Automatically marks unread incoming messages as read.
    """

    serializer_class = MessageSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        target_user_id = self.kwargs["user_id"]
        current_user = self.request.user

        # Validate target user exists
        if not User.objects.filter(pk=target_user_id).exists():
            raise NotFound(detail="User not found.")

        # Mark unread incoming messages from the target user as read
        Message.objects.filter(
            sender_id=target_user_id, receiver=current_user, is_read=False
        ).update(is_read=True)

        # Fetch messages in both directions between the two users
        return Message.objects.filter(
            Q(sender=current_user, receiver_id=target_user_id)
            | Q(sender_id=target_user_id, receiver=current_user)
        ).select_related("sender", "receiver")
