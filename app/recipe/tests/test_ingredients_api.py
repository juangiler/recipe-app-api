"""
Tests for ingredients API
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from app_models.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

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

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test listing recipes based on ingredients only on assigned status"""
        
        in1 = Ingredient.objects.create(user=self.user, name="Yuca")
        in2 = Ingredient.objects.create(user=self.user, name="Cilantro")
        
        recipe = Recipe.objects.create(
            title = "Encebollado",
            time_minutes = 5,
            price = Decimal('4.20'),  # noqa: F821
            user = self.user
        )
        
        recipe.ingredients.add(in1)
        
        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})
        
        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)
        
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)
        
        
    def test_filter_ingredients_unique(self):
        """Test filetered ingridients returns a unique list"""
        ing = Ingredient.objects.create(user=self.user, name= "Eggs")
        Ingredient.objects.create(user=self.user, name="Lentils")

        recipe1 = Recipe.objects.create(
            title = 'Eggs Benedict',
            time_minutes = 60,
            price = Decimal('7.00'),
            user = self.user
        )
        
        recipe2  = Recipe.objects.create(
            title= "herb Egss",
            time_minutes = 54,
            price= Decimal('4.00'),
            user=self.user
            
        )
        recipe1.ingredients.add(ing)
        recipe2.ingredients.add(ing)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only':1})
        
        self.assertEqual(len(res.data),1)