"""
Test for the Django admin modification
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminUserTestCase(TestCase):
    """
    Test the Django admin modification
    """

    # def __init__(self):
    #     self.user = None
    #     self.admin_user = None
    #     self.client = None

    def setUp(self):
        """
        Create user and client for testing
        """

        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            password='password123'
        )
        self.client.force_login(self.admin_user)

        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            password='password456',
            name='John Doe'
        )

    def test_users_list(self):
        """
        Test the users list page
        """

        url = reverse('admin:core_user_changelist')
        response = self.client.get(url)

        self.assertContains(response, self.user.name)
        self.assertContains(response, self.user.email)

    def test_edit_user_page(self):
        """
        Test the edit user page
        """

        url = reverse('admin:core_user_change', args=[self.user.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_create_user_page(self):
        """
        Test the create user page
        """

        url = reverse('admin:core_user_add')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)