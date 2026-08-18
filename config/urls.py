"""
Root URL configuration for the Real-Time Chat API project.
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    # API endpoints
    path("api/auth/", include("apps.accounts.urls")),
    path("api/chat/", include("apps.chat.urls")),
    # Web Application Pages
    path("", TemplateView.as_view(template_name="chat/index.html"), name="chat-dashboard"),
    path("login/", TemplateView.as_view(template_name="auth/login.html"), name="login-page"),
    path("register/", TemplateView.as_view(template_name="auth/register.html"), name="register-page"),
]
