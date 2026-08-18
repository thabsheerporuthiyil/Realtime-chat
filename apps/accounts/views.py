"""
Views for the accounts app.

Provides user registration (public) and authenticated
user listing endpoints.
"""
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    Register a new user.

    POST /api/auth/register/

    Public endpoint — no authentication required.
    Returns the created user along with JWT access and refresh tokens
    so the client can immediately authenticate after registration.
    """

    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens for immediate authentication
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class UserListView(generics.ListAPIView):
    """
    List all registered users (excluding the requesting user).

    GET /api/auth/users/

    Requires JWT authentication.
    """

    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """Exclude the currently authenticated user from the list."""
        return User.objects.exclude(pk=self.request.user.pk).order_by("username")
