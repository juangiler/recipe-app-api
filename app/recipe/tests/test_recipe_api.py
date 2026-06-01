"""
Test for recipe APIs.
"""

import os
import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from app_models.models import Ingredient, Recipe, Tag
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer

RECIPE_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and returns a recipe detail URL"""

    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id):
    """Create and return an image upload URL."""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def create_recipe(user, **params):
    """Helper function to create and return a sample recipe."""
    defaults = {
        "title": "Sample recipe",
        "time_minutes": 10,
        "price": Decimal("5.25"),
        "link": "http://example.com/recipe.pdf",
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    """Helper function to create and return a user."""
    return get_user_model().objects.create_user(**params)


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated recipe API access."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required."""
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated recipe API access."""

    def setUp(self):

        self.user = create_user(email='test@example.com', password='testpass123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test that recipes returned are for the authenticated user."""
        other_user = create_user(email='other@example.com', password='password123')
        create_recipe(user=other_user, title='Other user\'s recipe')
        create_recipe(user=self.user, title='My recipe')
        res = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(len(res.data), 1)
        self.assertNotEqual(res.data, "Other user's recipe")

    def test_get_recipe_detail(self):
        """Test get recipe detail (retrieve) """

        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe."""
        payload = {
            "title": "Chocolate cheesecake",
            "time_minutes": 30,
            "price": Decimal("5.00"),
            "description": "A delicious chocolate cheesecake recipe.",
            "link": "http://example.com/chocolate_cheesecake.pdf",
        }
        # make a POST request to the API with the payload
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # extract the recipe from the database using the ID returned in the response
        recipe = Recipe.objects.get(id=res.data["id"])

        # check that the recipe's attributes match the payload
        for key in payload.keys():
            self.assertEqual(getattr(recipe, key), payload[key])

        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        """Test partial update of a recipe"""
        original_link = "https://example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user,
            title='Sample Recipe Title',
            link=original_link,
        )

        payload = {'title': 'New Recipe title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update_recipe(self):
        """Test full update of a recipe"""
        recipe = create_recipe(
            user=self.user,
            title='Sample Recipe Title',
            link='https://example.com/recipe.pdf',
        )

        payload = {
            'title': 'New Recipe title',
            'link': 'https://example.com/new-recipe.pdf',
            'time_minutes': 25,
            'price': Decimal('4.50'),
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for key in payload.keys():
            self.assertEqual(getattr(recipe, key), payload[key])
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test that updating the recipe user results in an error."""
        other_user = create_user(email='theruser@example.com', password='other123')

        recipe = create_recipe(self.user)

        url = detail_url(recipe_id=recipe.id)
        payload = {"user": other_user.id}

        self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe successful"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        """Test deleting other user recipe results in error"""

        new_user = create_user(email='otheruser@example.com', password='test123')
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

            
    def test_create_recipe_with_new_tag(self):
        """Test creating a recipe with new tags."""

        payload = {
            "title": "Thai Prawn Curry",
            "time_minutes": 30,
            "price": Decimal('2.50'),
            "tags":[{"name":"Thai"}, {"name":"Dinner"}]
        }
        
        res = self.client.post(RECIPE_URL,payload, 'json')
        
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user= self.user)
        self.assertEqual(recipes.count(),1)
        recipes = recipes[0]
        self.assertEqual(recipes.tags.count(),2)
        for tag in payload["tags"]:
            exists= recipes.tags.filter(name=tag['name'], user=self.user)
            self.assertTrue(exists)
    
    
    def test_create_recipe_with_existing_tags(self):
        """Tests crating a recipe with existing tags"""

        tag_ecuador = Tag.objects.create(user=self.user, name='Ecuadorian')
        payload= {
            "title":"Encebollado",
            "time_minutes":120,
            "price":Decimal("5.60"),
            "tags": [{"name":"Ecuadorian"}, {"name":"SeaFood"}]
        }
        res = self.client.post(RECIPE_URL, payload,format="json")
        
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe= Recipe.objects.filter(user= self.user)
        self.assertEqual(recipe.count(),1)
        recipe= recipe[0]
        
        self.assertEqual(recipe.tags.count(),2)

        self.assertIn(tag_ecuador, recipe.tags.all())
        
        for tag in payload["tags"]:

            exists = recipe.tags.filter(
                name=tag["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)
            
    def test_create_tag_on_update(self):
        """Test creating a tag when updating a recipe"""
        recipe = create_recipe(user=self.user)

        payload = {"tags": [{"name": "Lunch"}]}
        
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        new_tag = Tag.objects.get(user=self.user, name="Lunch")
        self.assertIn(new_tag, recipe.tags.all())
        
    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe"""
        tag_breakfast = Tag.objects.create(user=self.user, name="Breakfast")

        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name="Lunch")

        payload = {"tags": [{"name": "Lunch"}]}
        
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())
        
    def test_update_recipes_with_tags_to_assign_tag(self):
        """Test updating a recipe with tags"""
        tag_breakfast = Tag.objects.create(user=self.user, name="Breakfast")
        tag_lunch = Tag.objects.create(user=self.user, name="Lunch")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)
        recipe.tags.add(tag_lunch)

        payload = {"tags": [{"name": "Dinner"}]}
        
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        tag_dinner = Tag.objects.get(user=self.user, name="Dinner")
        
    
        self.assertIn(tag_dinner, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())
        self.assertNotIn(tag_lunch, recipe.tags.all())
    
    
    def test_add_tags(self):
        """Test adding tags on update of recipe."""
        tag_breakfast = Tag.objects.create(user=self.user, name="Breakfast")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        payload = {"tags": [{"name": "Lunch"}], "append_tags": True}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag_lunch = Tag.objects.get(user=self.user, name="Lunch")
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertIn(tag_breakfast, recipe.tags.all())
    
    
    def test_add_tags_on_full_update(self):
        """Test adding tags on full update of recipe."""
        tag_breakfast = Tag.objects.create(user=self.user, name="Breakfast")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        payload = {
            "title": recipe.title,
            "time_minutes": recipe.time_minutes,
            "price": recipe.price,
            "tags": [{"name": "Lunch"}],
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag_lunch = Tag.objects.get(user=self.user, name="Lunch")
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())
    
    
    def test_clear_recipe_tags(self):
        """Test clearing a recipes tags."""
        tag = Tag.objects.create(user=self.user, name="Dessert")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {"tags": []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
        
        
    def test_create_ingredients_with_new_ingredient(self):
        """Test creating a new ingredients."""
        payload = {
            "title": "Arroz Marinero",
            "time_minutes": 60,
            "price": Decimal("4.30"),
            "ingredients": [{"name": "Rice"}, {"name":"Mariscos"}],
            
        }
        
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        recipes = Recipe.objects.filter(user=self.user)
        
        self.assertEqual(recipes.count(),1)
        
        recipe = recipes[0]

        self.assertEqual(recipe.ingredients.count(),2)
        
        for ingredient in payload["ingredients"]:
            exist = recipe.ingredients.filter(name = ingredient["name"], user= self.user).exists()
            
            self.assertTrue(exist)


    def test_create_recipe_with_existing_ingredient(self):
        """Test creating a new recipe with exisitng ingridients"""

        Ingredient.objects.create(user=self.user, name="Lemon")
        payload = {
            'title': 'Vietnamese Soup',
            'time_minutes': 30,
            'price':Decimal("2.33"),
            "ingredients":[{"name":"Lemon"}, {"name":"fisch sauce"}]
        }
        
        
        res = self.client.post(RECIPE_URL, payload, format= "json")
        
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        ingredients = Ingredient.objects.all().order_by("-name")

        
        self.assertEqual(ingredients.count(), 2)
        
        
    def test_create_ingredient_on_update(self):
        """Test creating and ingredient when updating a recipe"""
        
        recipe = create_recipe(user=self.user)
        
        payload = {
            "ingredients":[{"name":"Pescado"},{"name":"Pepino"}]
        }
        
        url = detail_url(recipe.id)
        
        res = self.client.patch(url, payload, format="json")
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_ingredients = [Ingredient.objects.get(user=self.user, name="Pescado") , Ingredient.objects.get(user=self.user, name="Pepino")]
        
        recipe.refresh_from_db()
        
        for new_ingredient in new_ingredients:
            self.assertIn(new_ingredient, recipe.ingredients.all())
            
    
    def test_update_recipe_assign_ingredient_not_append(self):
        
        ingredient1 = Ingredient.objects.create(user=self.user, name = "Pimienta")
        recipe = create_recipe(user= self.user)
        recipe.ingredients.add(ingredient1)
        
        # Ingredient 2
        ingredient2 =Ingredient.objects.create(user=self.user, name = "Cola")
        
        payload = {"ingredients": [{"name":"Cola"}]}
        url = detail_url(recipe.id)
        
        
        res = self.client.patch(url, payload, format="json")
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        recipe.refresh_from_db()

        self.assertNotIn(ingredient1 , recipe.ingredients.all())
        
        self.assertIn(ingredient2 , recipe.ingredients.all())
        
    
    def test_clear_recipe_ingredients(self):
        
        ingredient = Ingredient.objects.create(user=self.user, name= "Garlic")

        recipe = create_recipe(user=self.user)

        recipe.ingredients.add(ingredient)

        payload = {"ingredients":[]}
        
        url = detail_url(recipe.id)
        
        res =self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        self.assertEqual(recipe.ingredients.count(), 0)
        
    def test_filter_by_tags(self):
        """Test filtering recipes by tags"""
        r1 = create_recipe(user=self.user, title="Bolon")
        r2 = create_recipe(user=self.user, title="Sancocho")

        tag1 = Tag.objects.create(user=self.user, name= "Platano")
        tag2 = Tag.objects.create(user=self.user, name= "Soup")
    
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        
        r3 = create_recipe(user=self.user, title="Encebollado")


        params = {'tags': f'{tag1.id},{tag2.id}'}
        res = self.client.get(RECIPE_URL, params)
        
        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)
        

    def test_filter_by_ingredients(self):
        """Test filtering recipes by tags"""
        r1 = create_recipe(user=self.user, title="Bolon")
        r2 = create_recipe(user=self.user, title="Sancocho")

        in1 = Ingredient.objects.create(user=self.user, name= "Chicharron")
        in2 = Ingredient.objects.create(user=self.user, name= "Pescado")
        
        r3 = create_recipe(user=self.user, title="Encebollado")
        
        r1.ingredients.add(in1)
        r2.ingredients.add(in2)
        
        params = {'ingredients': f'{in1.id},{in2.id}'}
        res = self.client.get(RECIPE_URL, params)
        
        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)
        
        
                  
        
        
class ImageUploadTests(TestCase):
    """Tests for the image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@example.com",
            "password123"
        )
            
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user= self.user)
        
    def tearDown(self):
        
        self.recipe.image.delete()
        
    
    def test_upload_image(self):
        """Test Uploading an image to a recipe"""
        url = image_upload_url(self.recipe.id)
        
        # Create a temporarily image file 
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10,10))
            img.save(image_file , format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url,payload, format = "multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code , status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))
        
    def test_upload_image_bad_request(self):
        """Test uploading invalid image"""
        url = image_upload_url(self.recipe.id)
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)