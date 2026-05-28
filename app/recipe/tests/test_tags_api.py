"""
Test for the tags API.
"""


from app_models.models import Tag
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import TagSerializer
from rest_framework import status
from rest_framework.test import APIClient

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

