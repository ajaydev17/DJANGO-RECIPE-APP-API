"""
Serializers for the recipe API view
"""

from rest_framework import serializers
from core import models


class IngredientSerializer(serializers.ModelSerializer):
    """
    Serializer for the ingredient object.
    """

    class Meta:
        model = models.Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for the tag object.
    """

    class Meta:
        model = models.Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    """
    Serializer for the recipe object.
    """
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = models.Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags', 'ingredients']
        read_only_fields = ['id']

    def _get_or_create_tags(self, instance, tags):
        """
        Helper method to get or create tags for a recipe.
        """

        authenticated_user = self.context['request'].user

        for tag in tags:
            tag_obj, _ = models.Tag.objects.get_or_create(user=authenticated_user, **tag)
            instance.tags.add(tag_obj)

    def _get_or_create_ingredients(self, instance, ingredients):
        """
        Helper method to get or create ingredients for a recipe.
        """
        authenticated_user = self.context['request'].user

        for ingredient in ingredients:
            ingredient_obj, _ = models.Ingredient.objects.get_or_create(user=authenticated_user, **ingredient)
            instance.ingredients.add(ingredient_obj)

    def create(self, validated_data):
        """
        Create and return a new recipe instance, given the validated data.
        """

        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = models.Recipe.objects.create(**validated_data)
        self._get_or_create_tags(recipe, tags)
        self._get_or_create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """
        Update and return the recipe instance, given the validated data.
        """

        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(instance, tags)

        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(instance, ingredients)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """
    Serializer for the detailed recipe object.
    """

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description', 'image']


class RecipeImageSerializer(serializers.ModelSerializer):
    """
    Serializer for uploaded recipe images.
    """

    class Meta:
        model = models.Recipe
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': True}}