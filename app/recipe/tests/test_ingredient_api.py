"""
Test for the ingredient API
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse('recipe:ingredient-list')

def ingredient_detail_url(ingredient_id):
    """
    Return the URL for a single ingredient detail.
    """

    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email='user@example.com', password='password'):
    """
    Create a new user.
    """
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsApiTests(TestCase):
    """
    Test public API access for ingredients.
    """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """
        Test that authentication is required to access the ingredients API.
        """

        response = self.client.get(INGREDIENT_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """
    Test private API access for ingredients.
    """

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """
        Test retrieving ingredients.
        """

        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Test Ingredient')

        response = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """
        Test retrieving ingredients for the authenticated user only.
        """

        user2 = create_user(email='test2@example.com', password='test123')
        Ingredient.objects.create(user=user2, name='Salt')
        ingredient = Ingredient.objects.create(user=self.user, name='Pepper')

        response = self.client.get(INGREDIENT_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], ingredient.name)
        self.assertEqual(response.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        """
        Test updating ingredients.
        """

        ingredient = Ingredient.objects.create(user=self.user, name='Test Ingredient')
        payload = {'name': 'Updated Test Ingredient'}

        response = self.client.patch(ingredient_detail_url(ingredient.id), payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """
        Test deleting ingredients.
        """

        ingredient = Ingredient.objects.create(user=self.user, name='Test Ingredient')

        response = self.client.delete(ingredient_detail_url(ingredient.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Test if the ingredient was deleted
        self.assertEqual(Ingredient.objects.filter(id=ingredient.id).exists(), False)

