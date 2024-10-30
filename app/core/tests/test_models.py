"""
Tests for models.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models
from decimal import Decimal


def create_user(email='user@example.com', password='password123'):
    """
    Create a new user.
    """

    return get_user_model().objects.create_user(
        email=email,
        password=password
    )


class ModelTest(TestCase):
    """
    Test the User model
    """

    def test_create_user_with_email_successful(self):
        """
        Test creating a new user with an email.
        """

        email = 'test@example.com'
        password = 'password123'

        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_user_with_email_normalized(self):
        """
        Test the email is normalized for new users.
        """

        sample_emails = [
            ['test1@EXAMPLE.COM', 'test1@example.com'],
            ['Test2@EXAMPLE.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.com', 'test4@example.com'],
        ]

        for email, expected_email in sample_emails:
            user = get_user_model().objects.create_user(email=email, password='sample123')
            self.assertEqual(user.email, expected_email)

    def test_create_user_without_email(self):
        """
        Test creating a new user without an email.
        """

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'password123')

    def test_create_superuser_successful(self):
        """
        Test creating a new superuser.
        """

        user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            password='password123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """
        Test creating a new recipe.
        """

        user = get_user_model().objects.create_user(
            email='test@example.com',
            password='password123',
            name='Test User'
        )

        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample Recipe',
            time_minutes=30,
            price=Decimal('5.50'),
            description='Sample recipe description'
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """
        Test creating a new tag.
        """

        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Sample Tag')

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """
        Test creating a new ingredient.
        """

        user = create_user()
        ingredient = models.Ingredient.objects.create(user=user, name='Sample Ingredient')

        self.assertEqual(str(ingredient), ingredient.name)