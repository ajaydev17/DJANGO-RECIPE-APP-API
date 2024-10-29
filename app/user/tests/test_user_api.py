"""
Tests for the user API
"""

from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')

def create_user(**params):
    """
    Create a new user.
    """

    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """
    Test the public user API
    """

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """
        Test creating a new user with valid payload.
        """

        payload = {
            'email': 'test@example.com',
            'password': 'test123',
            'name': 'Test User'
        }

        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**response.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', response.data)

    def test_user_with_email_exists(self):
        """
        Test creating a new user with an existing email.
        """

        create_user(email='test@example.com', password='test123', name='Test User')

        payload = {
            'email': 'test@example.com',
            'password': 'test456',
            'name': 'Test User 2'
        }

        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_with_short_password(self):
        """
        Test creating a new user with a short password.
        """

        payload = {
            'email': 'test@example.com',
            'password': 'pw',
            'name': 'Test User'
        }

        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(email=payload['email']).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """
        Test generates a token for a user for a valid credentials.
        """

        user_details = {
            'email': 'test@example.com',
            'password': 'test123',
            'name': 'Test User'
        }

        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password']
        }

        response = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """
        Test generates a token for a user with invalid credentials.
        """

        create_user(email='test@example.com', password='test123', name='Test User')

        payload = {
            'email': 'test@example.com',
            'password': 'wrong_password'
        }

        response = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """
        Test posting a blank password for a user.
        """

        payload = {
            'email': 'test@example.com',
            'password': '',
        }

        response = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """
        Test authentication required for retrieving user details.
        """

        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """
    Test the private user API
    """

    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='test123',
            name='Test User'
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_user_details_success(self):
        """
        Test retrieving user details authenticated user.
        """

        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['name'], self.user.name)

    def test_post_me_not_allowed(self):
        """
        Test POST method not allowed on the user detail endpoint.
        """

        response = self.client.post(ME_URL, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_details_success(self):
        """
        Test updating user details authenticated user.
        """

        payload = {
            'name': 'Updated Test User',
            'password': 'new_password'
        }

        response = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))