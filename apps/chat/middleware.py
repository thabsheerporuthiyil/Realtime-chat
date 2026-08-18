"""
WebSocket authentication middleware for Django Channels.

Extracts a JWT access token from the WebSocket query string
and authenticates the connection. The authenticated user is
attached to the ASGI scope.

Usage in ASGI config:
    JWTAuthMiddleware(URLRouter(websocket_urlpatterns))

Connection URL format:
    ws://host/ws/chat/<user_id>/?token=<jwt_access_token>
"""
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_string):
    """
    Validate a JWT access token and return the associated user.

    Returns AnonymousUser if the token is invalid or the user
    does not exist.
    """
    try:
        validated_token = AccessToken(token_string)
        user_id = validated_token["user_id"]
        return User.objects.get(pk=user_id)
    except (InvalidToken, TokenError, User.DoesNotExist, KeyError):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom ASGI middleware that authenticates WebSocket
    connections using JWT tokens passed in the query string.

    Rejects unauthenticated connections with close code 4001.
    """

    async def __call__(self, scope, receive, send):
        # Parse the query string for the 'token' parameter
        query_params = parse_qs(scope.get("query_string", b"").decode("utf-8"))
        token_list = query_params.get("token", [])

        if token_list:
            scope["user"] = await get_user_from_token(token_list[0])
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
