"""
Tests for recipe API
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def recipe_detail_url(recipe_id):
    """
    Return the URL for a single recipe detail.
    """

    return reverse('recipe:recipe-detail', args=[recipe_id])



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

def create_user(**kwargs):
    """
    Create a new user.
    """

    return get_user_model().objects.create_user(**kwargs)


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

        response = self.client.get(RECIPE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """
    Test the private recipe API
    """

    def setUp(self):
        self.user = create_user(
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

        response = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """
        Test retrieving recipes for the authenticated user only.
        """

        user2 = create_user(
            email='test2@example.com',
            password='test123',
            name='Test User 2'
        )

        create_recipe(user2)
        create_recipe(self.user)

        response = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.filter(user=self.user).order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], recipes[0].title)

    def test_get_recipe_detail(self):
        """
        Test retrieving a single recipe detail.
        """

        recipe = create_recipe(self.user)
        url = recipe_detail_url(recipe.id)

        response = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_recipe_successful(self):
        """
        Test creating a new recipe.
        """

        payload = {
            'title': 'New Recipe',
            'time_minutes': 90,
            'price': Decimal('20.00'),
            'description': 'This is a new recipe.',
            'link': 'https://example.com/new_recipe.pdf'
        }

        response = self.client.post(RECIPE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=response.data['id'])

        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        """
        Test updating a recipe partially.
        """

        original_link = 'https://example.com/original_recipe.pdf'

        recipe = create_recipe(self.user, title='Sample recipe title', link=original_link)

        payload = {
            'title': 'Updated Recipe'
        }
        url = recipe_detail_url(recipe.id)

        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)  # Original link should not be updated.
        self.assertEqual(recipe.user, self.user)  # User should not be updated.

    def test_full_update_recipe(self):
        """
        Test updating a recipe completely.
        """

        recipe = create_recipe(self.user, title='Sample recipe title', link='https://example.com/original_recipe.pdf', description='This is a sample recipe.')

        payload = {
            'title': 'Updated Recipe',
            'time_minutes': 90,
            'price': Decimal('20.00'),
            'description': 'This is an updated recipe.',
            'link': 'https://example.com/updated_recipe.pdf'
        }
        url = recipe_detail_url(recipe.id)

        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)  # User should not be updated.

    def test_update_user_returns_error(self):
        """
        Test updating user details returns an error.
        """

        new_user = create_user(email='test3@example.com', password='test123', name='Test User 3')
        recipe = create_recipe(user=new_user)

        payload = {
            'user': new_user.id,
        }
        url = recipe_detail_url(recipe.id)

        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, new_user)  # User should not be updated.

    def test_delete_recipe(self):
        """
        Test deleting a recipe.
        """

        recipe = create_recipe(self.user)
        url = recipe_detail_url(recipe.id)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_user_recipe_returns_error(self):
        """
        Test deleting a recipe that belongs to another user returns an error.
        """

        new_user = create_user(email='test4@example.com', password='test123', name='Test User 4')
        recipe = create_recipe(user=new_user)

        url = recipe_detail_url(recipe.id)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())  # Recipe should still exist.

    def test_create_recipe_with_tag(self):
        """
        Test creating a new recipe with a tag.
        """

        payload = {
            'title': 'New Recipe with Tag',
            'time_minutes': 90,
            'price': Decimal('20.00'),
            'description': 'This is a new recipe with a tag.',
            'link': 'https://example.com/new_recipe.pdf',
            'tags': [{'name': 'Sample Tag1'}, {'name': 'Sample Tag2'}]
        }

        response = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        for tag in payload['tags']:
            exists = recipe.tags.filter(name=tag['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tag(self):
        """
        Test creating a new recipe with an existing tag.
        """

        existing_tag = Tag.objects.create(name='Sample Tag', user=self.user)

        payload = {
            'title': 'New Recipe with Existing Tag',
            'time_minutes': 90,
            'price': Decimal('20.00'),
            'description': 'This is a new recipe with an existing tag.',
            'link': 'https://example.com/new_recipe.pdf',
            'tags': [{'name': 'Sample Tag'}, {'name': 'Sample Tag2'}]
        }

        response = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(existing_tag, recipe.tags.all())

        for tag in payload['tags']:
            exists = recipe.tags.filter(name=tag['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update_recipe(self):
        """
        Test creating a new tag on updating a recipe.
        """

        recipe = create_recipe(self.user)

        payload = {
            'tags': [{'name': 'Sample Tag3'}]
        }
        url = recipe_detail_url(recipe.id)

        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.tags.count(), 1)

        new_tag = Tag.objects.get(name='Sample Tag3', user=self.user)
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """
        Test updating a recipe to assign a new tag.
        """

        tag_breakfast = Tag.objects.create(name='Breakfast', user=self.user)
        recipe = create_recipe(self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(name='Lunch', user=self.user)
        payload = {
            'tags': [{'name': 'Lunch'}]
        }
        url = recipe_detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.tags.count(), 1)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """
        Test updating a recipe to clear all tags.
        """

        tag_breakfast = Tag.objects.create(name='Breakfast', user=self.user)
        recipe = create_recipe(self.user)
        recipe.tags.add(tag_breakfast)

        payload = {
            'tags': []
        }
        url = recipe_detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.tags.count(), 0)

