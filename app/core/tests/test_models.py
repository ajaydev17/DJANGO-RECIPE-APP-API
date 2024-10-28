"""
Tests for models.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model


class UserModelTest(TestCase):
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