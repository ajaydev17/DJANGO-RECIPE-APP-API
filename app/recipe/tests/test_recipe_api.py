"""
Tests for recipe API
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe
from recipe.serializers import RecipeSerializer

RECIPE_LIST_URL = reverse('recipe:recipe-list')


def create_recipe(user, **kwargs):
    """
    Create a new recipe for the given user.
    """

    defaults = {
        'title': 'Sample Recipe',
        'time_minutes': 60,
        'price': Decimal('15.00'),
        'description': 'This is a sample recipe.',
        'link': 'https://example.com/recipe.pdf'
    }

    defaults.update(kwargs)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


class PublicRecipeApiTests(TestCase):
    """
    Test the public recipe API
    """

    def setUp(self):
        self.client = APIClient()

    def test_authentication_required(self):
        """
        Test that authentication is required to call the API.
        """

        response = self.client.get(RECIPE_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """
    Test the private recipe API
    """

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='test123',
            name='Test User'
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes_list(self):
        """
        Test retrieving a list of recipes.
        """

        create_recipe(self.user)
        create_recipe(self.user, title='Another Recipe')

        response = self.client.get(RECIPE_LIST_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """
        Test retrieving recipes for the authenticated user only.
        """

        user2 = get_user_model().objects.create_user(
            email='test2@example.com',
            password='test123',
            name='Test User 2'
        )

        create_recipe(user2)
        create_recipe(self.user)

        response = self.client.get(RECIPE_LIST_URL)
        recipes = Recipe.objects.filter(user=self.user).order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], recipes[0].title)