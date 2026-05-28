"""
Tests for ingredients API
"""


from app_models.models import Ingredient
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import IngredientSerializer
from rest_framework import status
from rest_framework.test import APIClient

INGREDIENTS_URL = reverse("recipe:ingredient-list")


def detail_url(ingredient_id):
    """Create and retunr the ingredient URL"""
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


def create_user(email="user@example.com", password="testpass123"):
    """Create and retrun user"""

    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Cehcke the auth required"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTest(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_list_ingredients(self):
        """Test list ingredients"""
        Ingredient.objects.create(user=self.user, name="Oregano")
        Ingredient.objects.create(user=self.user, name="Platano")

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test List is only belonging to logger user"""

        user_2 = create_user(email="another@example.com", password="testpass123")

        Ingredient.objects.create(user=self.user, name="Platano")
        Ingredient.objects.create(user=user_2, name="Cacao")

        ingredients = Ingredient.objects.filter(user=self.user)

        serializer = IngredientSerializer(ingredients, many=True)

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(len(res.data), 1)

        self.assertEqual(res.data[0]["id"], serializer.data[0]["id"])

    def test_update_ingredients(self):

        ingredient = Ingredient.objects.create(user=self.user, name="Cilantro")

        payload = {"name": "Coriander"}
        url = detail_url(ingredient.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredient.refresh_from_db()

        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredients(self):

        ingredient = Ingredient.objects.create(user=self.user, name="Lettuce")

        url = detail_url(ingredient.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        ingredients = Ingredient.objects.filter(user=self.user)
     
        self.assertFalse(ingredients.exists())

