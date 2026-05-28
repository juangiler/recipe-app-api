"""
Test for app_models.
"""
from decimal import Decimal
from unittest.mock import patch

from app_models import models
# Get the user model default from Django
from django.contrib.auth import get_user_model
from django.test import TestCase


def create_user(email="test@example.com", password="testpass123"):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email=email, password=password)


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email is successful."""
        email = "test@example.com"
        password = "testpass123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized."""
        sample_emails = [
            ["test1@EXAMPLE.COM", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.COM", "TEST3@example.com"],
            ["test4@EXAMPLE.COM", "test4@example.com"],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(
                email=email, password="sample123"
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test creating a user without an email raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "test123")

    def test_create_superuser(self):
        """Test creating a new superuser."""
        user = get_user_model().objects.create_superuser(
            email="test_superuser@example.com", password="test123"
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test creating a new recipe is successful."""
        user = get_user_model().objects.create_user(
            email="test@example.com", password="testpass123"
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title="Sample recipe name",
            time_minutes=5,
            price=Decimal("5.50"),
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """Test creating a new tag"""
        user = create_user()

        tag = models.Tag.objects.create(user=user, name="Tag")
        self.assertEqual(str(tag), tag.name)



    def test_create_ingredient(self):
        """Test creating an ingredient is successful"""
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user = user,
            name = "Ingredient1"
            
            
        )
        self.assertEqual(str(ingredient), ingredient.name)
        
    @patch("app_models.models.uuid.uuid4")
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test that image is saved in the correct location."""
        uuid = "test-uuid"
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, "myimage.jpg")

        exp_path = f"uploads/recipe/{uuid}.jpg"
        self.assertEqual(file_path, exp_path)
