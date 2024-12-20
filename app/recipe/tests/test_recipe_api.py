"""
Tests for recipe API
"""

from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def recipe_detail_url(recipe_id):
    """
    Return the URL for a single recipe detail.
    """

    return reverse('recipe:recipe-detail', args=[recipe_id])

def image_upload_url(recipe_id):
    """
    Return the URL for uploading an image for a recipe.
    """

    return reverse('recipe:recipe-upload-image', args=[recipe_id])



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

    def test_create_recipe_with_new_ingredient(self):
        """
        Test creating a new recipe with a new ingredient.
        """

        payload = {
            'title': 'New Recipe with Ingredient',
            'time_minutes': 90,
            'price': Decimal('20.00'),
            'description': 'This is a new recipe with a new ingredient.',
            'link': 'https://example.com/new_recipe.pdf',
            'ingredients': [{'name': 'Sample Ingredient1'}, {'name': 'Sample Ingredient2'}]
        }

        response = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)

        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(name=ingredient['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """
        Test creating a new recipe with an existing ingredient.
        """

        existing_ingredient = Ingredient.objects.create(name='Sample Ingredient', user=self.user)

        payload = {
            'title': 'New Recipe with Existing Ingredient',
            'time_minutes': 90,
            'price': Decimal('20.00'),
            'description': 'This is a new recipe with an existing ingredient.',
            'link': 'https://example.com/new_recipe.pdf',
            'ingredients': [{'name': 'Sample Ingredient'}, {'name': 'Sample Ingredient2'}]
        }

        response = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(existing_ingredient, recipe.ingredients.all())

        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(name=ingredient['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update_recipe(self):
        """
        Test creating a new ingredient on updating a recipe.
        """

        recipe = create_recipe(self.user)

        payload = {
            'ingredients': [{'name': 'Sample Ingredient3'}]
        }
        url = recipe_detail_url(recipe.id)

        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.ingredients.count(), 1)

        new_ingredient = Ingredient.objects.get(name='Sample Ingredient3', user=self.user)
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """
        Test updating a recipe to assign a new ingredient.
        """

        ingredient_kale = Ingredient.objects.create(name='Kale', user=self.user)
        recipe = create_recipe(self.user)
        recipe.ingredients.add(ingredient_kale)

        ingredient_tomato = Ingredient.objects.create(name='Tomato', user=self.user)
        payload = {
            'ingredients': [{'name': 'Tomato'}]
        }
        url = recipe_detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.ingredients.count(), 1)
        self.assertIn(ingredient_tomato, recipe.ingredients.all())
        self.assertNotIn(ingredient_kale, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """
        Test updating a recipe to clear all ingredients.
        """

        ingredient_kale = Ingredient.objects.create(name='Kale', user=self.user)
        recipe = create_recipe(self.user)
        recipe.ingredients.add(ingredient_kale)

        payload = {
            'ingredients': []
        }
        url = recipe_detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_recipes_by_tag(self):
        """
        Test filtering recipes by tag.
        """

        tag_vegan = Tag.objects.create(name='Vegan', user=self.user)
        tag_dessert = Tag.objects.create(name='Dessert', user=self.user)

        recipe1 = create_recipe(self.user, title="Thai vegetable Curry")
        recipe1.tags.add(tag_vegan)

        recipe2 = create_recipe(self.user, title="Chocolate Lava Cake")
        recipe2.tags.add(tag_dessert)

        recipe3 = create_recipe(self.user, title="Fish and chips")

        params = {'tags': f'{tag_vegan.id},{tag_dessert.id}'}
        response = self.client.get(RECIPE_URL, params)

        s1 = RecipeSerializer(recipe1)
        s2 = RecipeSerializer(recipe2)
        s3 = RecipeSerializer(recipe3)

        self.assertIn(s1.data, response.data)
        self.assertIn(s2.data, response.data)
        self.assertNotIn(s3.data, response.data)

    def test_filter_recipes_by_ingredient(self):
        """
        Test filtering recipes by ingredient.
        """

        ingredient_carrot = Ingredient.objects.create(name='Carrot', user=self.user)
        ingredient_potato = Ingredient.objects.create(name='Potato', user=self.user)

        recipe1 = create_recipe(self.user, title="Carrot Stuffed Bell Peppers")
        recipe1.ingredients.add(ingredient_carrot)

        recipe2 = create_recipe(self.user, title="Potato Salad")
        recipe2.ingredients.add(ingredient_potato)

        recipe3 = create_recipe(self.user, title="Grilled Chicken and Vegetables")

        params = {'ingredients': f'{ingredient_carrot.id},{ingredient_potato.id}'}
        response = self.client.get(RECIPE_URL, params)

        s1 = RecipeSerializer(recipe1)
        s2 = RecipeSerializer(recipe2)
        s3 = RecipeSerializer(recipe3)

        self.assertIn(s1.data, response.data)
        self.assertIn(s2.data, response.data)
        self.assertNotIn(s3.data, response.data)


class ImageUploadTest(TestCase):
    """
    Test the image upload functionality
    """

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='test123'
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """
        Test uploading an image to a recipe
        """

        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (100, 100))
            img.save(image_file, format='JPEG')
            image_file.seek(0)

            payload = {
                'image': image_file,
            }

            response = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('image', response.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_invalid_image(self):
        """
        Test uploading an invalid image (non-JPEG format) to a recipe
        """

        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix='.txt') as image_file:
            image_file.write(b'Not a JPEG file')
            image_file.seek(0)

            payload = {
                'image': image_file,
            }

            response = self.client.post(url, payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)