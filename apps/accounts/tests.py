"""
Tests for the accounts app.

Covers:
    - User registration (success, validation errors)
    - User login (JWT token generation)
    - User list endpoint (authentication, exclusion of self)
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class RegisterViewTests(TestCase):
    """Tests for POST /api/auth/register/"""

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/auth/register/"

    def test_register_success(self):
        """Successful registration returns 201 with user data and tokens."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])
        self.assertEqual(response.data["user"]["username"], "testuser")
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_register_password_mismatch(self):
        """Mismatched passwords return 400."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepass123",
            "password_confirm": "differentpass",
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)

    def test_register_duplicate_username(self):
        """Duplicate username returns 400."""
        User.objects.create_user(
            username="existing", email="existing@example.com", password="pass123"
        )
        data = {
            "username": "existing",
            "email": "new@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        """Duplicate email returns 400."""
        User.objects.create_user(
            username="existing", email="test@example.com", password="pass123"
        )
        data = {
            "username": "newuser",
            "email": "test@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password(self):
        """Password shorter than 8 characters returns 400."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "short",
            "password_confirm": "short",
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTests(TestCase):
    """Tests for POST /api/auth/login/"""

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/auth/login/"
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="securepass123"
        )

    def test_login_success(self):
        """Valid credentials return JWT access and refresh tokens."""
        data = {"username": "testuser", "password": "securepass123"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_credentials(self):
        """Invalid credentials return 401."""
        data = {"username": "testuser", "password": "wrongpassword"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserListViewTests(TestCase):
    """Tests for GET /api/auth/users/"""

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/auth/users/"
        self.user = User.objects.create_user(
            username="me", email="me@example.com", password="securepass123"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@example.com", password="securepass123"
        )

    def test_user_list_authenticated(self):
        """Authenticated user can list other users."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = [u["username"] for u in response.data["results"]]
        self.assertIn("other", usernames)
        self.assertNotIn("me", usernames)

    def test_user_list_unauthenticated(self):
        """Unauthenticated request returns 401."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list_excludes_self(self):
        """The requesting user is excluded from the results."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        user_ids = [u["id"] for u in response.data["results"]]
        self.assertNotIn(self.user.id, user_ids)
