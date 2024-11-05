"""
Tests for the health check API.
"""

from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient


HEALTH_CHECK_URL = reverse('health-check')


class HealthCheckTests(TestCase):
    """Tests for the health check API."""

    def test_health_check(self):
        """Test that the health check API returns status code 200."""
        client = APIClient()
        response = client.get(HEALTH_CHECK_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)