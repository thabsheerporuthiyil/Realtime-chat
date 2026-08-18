"""
Tests for the chat app.

Covers:
    - Message model creation and string representation
    - Message history endpoint (authentication, filtering, permissions)
    - Deterministic room name generation
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .consumers import ChatConsumer
from .models import Message

User = get_user_model()


class MessageModelTests(TestCase):
    """Tests for the Message model."""

    def setUp(self):
        self.alice = User.objects.create_user(
            username="alice", email="alice@example.com", password="pass12345"
        )
        self.bob = User.objects.create_user(
            username="bob", email="bob@example.com", password="pass12345"
        )

    def test_create_message(self):
        """A message can be created with sender, receiver, and content."""
        msg = Message.objects.create(
            sender=self.alice,
            receiver=self.bob,
            content="Hello Bob!",
        )
        self.assertEqual(msg.sender, self.alice)
        self.assertEqual(msg.receiver, self.bob)
        self.assertEqual(msg.content, "Hello Bob!")
        self.assertFalse(msg.is_read)
        self.assertIsNotNone(msg.timestamp)

    def test_message_str(self):
        """String representation includes sender, receiver, and truncated content."""
        msg = Message.objects.create(
            sender=self.alice,
            receiver=self.bob,
            content="Hello Bob!",
        )
        self.assertIn("alice", str(msg))
        self.assertIn("bob", str(msg))
        self.assertIn("Hello Bob!", str(msg))

    def test_message_ordering(self):
        """Messages are ordered by timestamp ascending."""
        msg1 = Message.objects.create(
            sender=self.alice, receiver=self.bob, content="First"
        )
        msg2 = Message.objects.create(
            sender=self.bob, receiver=self.alice, content="Second"
        )
        messages = list(Message.objects.all())
        self.assertEqual(messages[0], msg1)
        self.assertEqual(messages[1], msg2)


class MessageHistoryViewTests(TestCase):
    """Tests for GET /api/chat/messages/<user_id>/"""

    def setUp(self):
        self.client = APIClient()
        self.alice = User.objects.create_user(
            username="alice", email="alice@example.com", password="pass12345"
        )
        self.bob = User.objects.create_user(
            username="bob", email="bob@example.com", password="pass12345"
        )
        self.charlie = User.objects.create_user(
            username="charlie", email="charlie@example.com", password="pass12345"
        )

        # Create messages between alice and bob
        Message.objects.create(
            sender=self.alice, receiver=self.bob, content="Hi Bob!"
        )
        Message.objects.create(
            sender=self.bob, receiver=self.alice, content="Hi Alice!"
        )
        # Create a message between bob and charlie (alice should NOT see)
        Message.objects.create(
            sender=self.bob, receiver=self.charlie, content="Hi Charlie!"
        )

    def test_history_authenticated(self):
        """Authenticated user can retrieve message history."""
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(f"/api/chat/messages/{self.bob.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        messages = response.data["results"]
        self.assertEqual(len(messages), 2)

    def test_history_unauthenticated(self):
        """Unauthenticated request returns 401."""
        response = self.client.get(f"/api/chat/messages/{self.bob.id}/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_history_only_shows_conversation(self):
        """History only includes messages between the two specified users."""
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(f"/api/chat/messages/{self.bob.id}/")

        messages = response.data["results"]
        for msg in messages:
            participants = {msg["sender"], msg["receiver"]}
            self.assertTrue(
                {"alice", "bob"} == participants,
                f"Unexpected participants: {participants}",
            )

    def test_history_excludes_other_conversations(self):
        """Alice cannot see messages between Bob and Charlie."""
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(f"/api/chat/messages/{self.charlie.id}/")

        messages = response.data["results"]
        self.assertEqual(len(messages), 0)

    def test_history_nonexistent_user(self):
        """Requesting history with a nonexistent user returns 404."""
        self.client.force_authenticate(user=self.alice)
        response = self.client.get("/api/chat/messages/9999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_history_bidirectional(self):
        """Both users see the same messages in a conversation."""
        self.client.force_authenticate(user=self.alice)
        response_alice = self.client.get(f"/api/chat/messages/{self.bob.id}/")

        self.client.force_authenticate(user=self.bob)
        response_bob = self.client.get(f"/api/chat/messages/{self.alice.id}/")

        self.assertEqual(
            len(response_alice.data["results"]),
            len(response_bob.data["results"]),
        )

    def test_history_marks_unread_messages_as_read(self):
        """Fetching message history marks unread incoming messages as read."""
        unread_msg = Message.objects.create(
            sender=self.bob, receiver=self.alice, content="Unread message", is_read=False
        )
        self.assertFalse(unread_msg.is_read)

        self.client.force_authenticate(user=self.alice)
        self.client.get(f"/api/chat/messages/{self.bob.id}/")

        unread_msg.refresh_from_db()
        self.assertTrue(unread_msg.is_read)


class DeterministicRoomNameTests(TestCase):
    """Tests for the deterministic room name logic."""

    def test_room_name_is_deterministic(self):
        """Room name is the same regardless of argument order."""
        name_a = ChatConsumer._get_room_name(1, 2)
        name_b = ChatConsumer._get_room_name(2, 1)
        self.assertEqual(name_a, name_b)

    def test_room_name_format(self):
        """Room name follows the expected format."""
        name = ChatConsumer._get_room_name(5, 3)
        self.assertEqual(name, "chat_3_5")
