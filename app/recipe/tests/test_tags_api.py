"""
Test for the tags API
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def tag_detail_url(tag_id):
    """
    Return the URL for a single tag detail.
    """

    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='test@example.com', password='test123'):
    """
    Create a new user.
    """
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsApiTests(TestCase):
    """
    Test public API access for tags.
    """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """
        Test that authentication is required to access the tags API.
        """

        response = self.client.get(TAGS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """
    Test private API access for tags.
    """

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """
        Test retrieving tags.
        """

        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        response = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_tags_limited_to_user(self):
        """
        Test retrieving tags for the authenticated user only.
        """

        user2 = create_user(email='test2@example.com', password='test456')
        Tag.objects.create(user=user2, name='Gluten-Free')

        tag = Tag.objects.create(user=self.user, name='Vegetarian')

        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], tag.name)
        self.assertEqual(response.data[0]['id'], tag.id)

    def test_update_tags(self):
        """
        Test updating tags.
        """

        tag = Tag.objects.create(user=self.user, name='Vegan')

        payload = {'name': 'Updated Vegan'}
        url = tag_detail_url(tag.id)

        response = self.client.put(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tags(self):
        """
        Test deleting tags.
        """

        tag = Tag.objects.create(user=self.user, name='Vegan')

        url = tag_detail_url(tag.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Tag.objects.filter(id=tag.id).exists())

    def test_filter_tags_assigned_to_recipe(self):
        """
        Test filtering tags assigned to a recipe.
        """

        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Dessert')

        recipe = Recipe.objects.create(user=self.user, title='Test Recipe', time_minutes=60, price=Decimal('10.00'))
        recipe.tags.add(tag1)

        response = self.client.get(TAGS_URL, {'assigned_only': True})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, response.data)
        self.assertIn(serializer2.data, response.data)

    def test_filter_tags_unique(self):
        """
        Test filtering tags unique to a recipe.
        """

        tag = Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        recipe1 = Recipe.objects.create(user=self.user, title='Test Recipe', time_minutes=60, price=Decimal('10.00'))
        recipe2 = Recipe.objects.create(user=self.user, title='Test Recipe 2', time_minutes=90, price=Decimal('15.00'))
        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        response = self.client.get(TAGS_URL, {'assigned_only': True})
        print(response.data)

        self.assertEqual(len(response.data), 1)