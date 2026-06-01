"""
Test for the tags API.
"""


from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from app_models.models import Recipe, Tag
from recipe.serializers import TagSerializer

TAG_URL = reverse("recipe:tag-list")


def detail_url(tag_id):
    """Create and return a tag detail URL"""
    return reverse("recipe:tag-detail", args=[tag_id])


def create_user(email="user@example.com", password="testpass123"):
    """Create and return a user"""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsApiTests(TestCase):
    """Tests unauthenticated"""

    def setUp(self):
        self.client = APIClient()

    def test_auht_required(self):
        """Test for not authorized cases"""

        res = self.client.get(TAG_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags"""

        Tag.objects.create(user=self.user, name="Spicy")
        Tag.objects.create(user=self.user, name="Dessert")

        res = self.client.get(TAG_URL)

        tags = Tag.objects.all().order_by("-name")

        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test that tags returned are for the authenticated user."""

        user2 = create_user(email="user2@example.com")
        tag = Tag.objects.create(user=self.user, name="Sour")
        Tag.objects.create(user=user2, name="Sweet")

        # tags = Tag.objects.filter(user=self.user).order_by('name')
        # serializer = TagSerializer(tags, many=True)

        res = self.client.get(TAG_URL)

        self.assertEqual(len(res.data), 1)

        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)

    def test_update_tag(self):
        """Test updating a tag"""

        tag = Tag.objects.create(user=self.user, name="After Dinner")

        payload = {"name": "Dessert"}

        url = detail_url(tag.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        tag.refresh_from_db()

        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag(self):
        """Test deleting a tag"""

        tag = Tag.objects.create(user=self.user, name="Breakfast")

        url = detail_url(tag.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        tags = Tag.objects.filter(user=self.user)

        self.assertFalse(tags.exists())

    def test_delete_other_user_tag_error(self):
        """Test trying to delete another user's tag gives error"""

        user2 = create_user(email="otheruser@example.com")
        tag = Tag.objects.create(user=user2, name="Lunch")
        url = detail_url(tag.id)

        res = self.client.delete(url)
        
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        tag.refresh_from_db()
        self.assertTrue(Tag.objects.filter(id=tag.id).exists())

    def test_filter_tags_assigned_to_recipes(self):
        """Test listing recipes based on ingredients only on assigned status"""
        
        tag1 = Tag.objects.create(user=self.user, name="Brakfast")
        tag2 = Tag.objects.create(user=self.user, name="Fruit")
        
        recipe = Recipe.objects.create(
            title = "Encebollado",
            time_minutes = 5,
            price = Decimal('4.20'),  # noqa: F821
            user = self.user
        )
        
        recipe.tags.add(tag1)
        
        res = self.client.get(TAG_URL, {"assigned_only": 1})
        
        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)
        
        
    def test_filter_tags_unique(self):
        """Test filetered tags returns a unique list"""
        tag1 = Tag.objects.create(user=self.user, name="Breakfast")
        Tag.objects.create(user=self.user, name="Lunch")

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
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag1)

        res = self.client.get(TAG_URL, {'assigned_only':1})
        
        self.assertEqual(len(res.data),1)