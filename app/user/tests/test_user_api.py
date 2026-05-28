"""
Tests for the user API.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")

def create_user(**params):
    """Helper function to create new users."""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the users API (public)."""

    def setUp(self):
        self.client = APIClient()

        # crewate a constant payload to use in the tests
        self.payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test Name",
        }

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful."""
        res = self.client.post(CREATE_USER_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=self.payload["email"])
        self.assertTrue(user.check_password(self.payload["password"]))
        self.assertNotIn("password", res.data)

    def test_user_exists(self):
        """Test creating a user that already exists fails."""
        create_user(**self.payload)
        res = self.client.post(CREATE_USER_URL, self.payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that the password must be more than 5 characters."""
        payload = {"email": "test@example.com", "password": "123"}
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(email=payload["email"]).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generates token for valid credentials."""
        user_detail = {
            'name': 'Test Name',
            'email': "test@example.com",
            'password': "test-user-password123"
        }
        create_user(**user_detail)
        payload = {
            'email': user_detail['email'],
            'password': user_detail['password']
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertIn("token", res.data)
        

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
    def test_create_token_blank_password(self):
        """Test that token is not created if password is blank."""
        payload = {
            'email': "test@example.com",
            'password': ""
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn("token",res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_create_token_bad_passwrod(self):
        """Test that token is not created when password is incorrect."""
        create_user(email="test@example.com", password="goodpass")
        payload = {
            'email': "test@example.com",
            'password': "badpass"
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn("token",res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_retrieve_user_unauthorized(self):
        """Test that authentication is required for users."""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        
        
class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):
        self.user = create_user(
            email="test@example.com",
            password="testpass123",
            name="Test Name",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user."""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual({'name': res.data["name"] , "email":res.data["email"]}, {
            'name': self.user.name,
            'email': self.user.email
        })
    def test_post_me_not_allowed(self):
        """Test that POST is not allowed on the me URL."""
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
    def test_update_user_profile(self):
        """Test updating the user profile for authenticated user."""
        payload = {
            'name': "Updated Name",
            'password': "newpassword123"
        }
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)