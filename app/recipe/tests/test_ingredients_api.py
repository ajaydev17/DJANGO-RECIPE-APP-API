"""
Test for the ingredient API
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
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

    def test_filter_ingredients_assigned_to_recipe(self):
        """
        Test filtering ingredients assigned to a recipe.
        """

        ingredient1 = Ingredient.objects.create(user=self.user, name='Apples')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Turkey')

        recipe = Recipe.objects.create(user=self.user, title='Test Recipe', time_minutes=10, price=Decimal('10.00'))
        recipe.ingredients.add(ingredient1)

        response = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        s1 = IngredientSerializer(ingredient1)
        s2 = IngredientSerializer(ingredient2)

        self.assertIn(s1.data, response.data)
        self.assertNotIn(s2.data, response.data)

    def test_filter_ingredients_unique(self):
        """
        Test that only unique ingredients are returned when assigned_only=True.
        """

        ingredient1 = Ingredient.objects.create(user=self.user, name='Apples')
        Ingredient.objects.create(user=self.user, name='Apples')

        recipe1 = Recipe.objects.create(user=self.user, title='Test Recipe', time_minutes=10, price=Decimal('10.00'))
        recipe2 = Recipe.objects.create(user=self.user, title='Test Recipe 2', time_minutes=10, price=Decimal('10.00'))

        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient1)

        response = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        self.assertEqual(len(response.data), 1)

