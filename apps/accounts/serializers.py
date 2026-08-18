"""
Serializers for the accounts app.

Handles user registration with validation and
read-only user representation for the user list.
"""
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers

from apps.chat.models import Message

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Accepts username, email, password, and password_confirm.
    Validates that passwords match and creates a user with
    a properly hashed password.
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "password_confirm")
        extra_kwargs = {
            "email": {"required": True},
        }

    def validate_email(self, value):
        """Ensure the email address is unique."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value.lower()

    def validate(self, attrs):
        """Ensure password and password_confirm match."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        """Create a new user with a hashed password."""
        validated_data.pop("password_confirm")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for listing registered users.
    Includes unread message count and latest message timestamp.
    """

    unread_count = serializers.SerializerMethodField()
    last_message_time = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "date_joined",
            "unread_count",
            "last_message_time",
        )
        read_only_fields = fields

    def get_unread_count(self, obj):
        """Count unread messages sent by this user to the authenticated requesting user."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Message.objects.filter(
                sender=obj, receiver=request.user, is_read=False
            ).count()
        return 0

    def get_last_message_time(self, obj):
        """Return the timestamp of the latest message exchanged between the users."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            last_msg = Message.objects.filter(
                Q(sender=obj, receiver=request.user)
                | Q(sender=request.user, receiver=obj)
            ).order_by("-timestamp").first()
            if last_msg:
                return last_msg.timestamp.isoformat()
        return None
