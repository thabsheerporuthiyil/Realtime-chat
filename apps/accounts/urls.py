"""
URL configuration for the accounts app.

Endpoints:
    POST /api/auth/register/       — Register a new user
    POST /api/auth/login/          — Obtain JWT token pair
    POST /api/auth/token/refresh/  — Refresh an access token
    GET  /api/auth/users/          — List all registered users
"""
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("users/", views.UserListView.as_view(), name="user-list"),
]
