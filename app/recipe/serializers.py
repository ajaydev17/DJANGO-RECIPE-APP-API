"""
Serializers for the recipe API view
"""

from rest_framework import serializers
from core import models


class RecipeSerializer(serializers.ModelSerializer):
    """
    Serializer for the recipe object.
    """

    class Meta:
        model = models.Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link']
        read_only_fields = ['id']