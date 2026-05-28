from app_models.models import Ingredient, Recipe, Tag
from rest_framework import serializers

# Create your views here.


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for the ingredients objects"""

    class Meta:
        model = Ingredient
        fields = ["id", "name"]
        read_only_fields = ["id"]


class TagSerializer(serializers.ModelSerializer):
    """Serializer for the tag objects."""

    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe objects."""

    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    append_tags = serializers.BooleanField(default=False, write_only=True)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "time_minutes",
            "price",
            "link",
            "tags",
            "ingredients",
            "append_tags",
        ]
        read_only_fields = ["id"]

    def _get_or_create_tags(self, tags, recipe):
        """Handle getting or creating tags as needed."""
        auth_user = self.context["request"].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(user=auth_user, **tag)
            recipe.tags.add(tag_obj)

    def _get_or_create_ingredients(self, ingredients, recipe):
        """Handle getting or creating ingredient as needed"""
        auth_user = self.context["request"].user
        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(
                user=auth_user, **ingredient
            )
            recipe.ingredients.add(ingredient_obj)

    def create(self, validated_data):
        """reate a recipe"""
        validated_data.pop("append_tags", False)
        tags = validated_data.pop("tags", [])
        ingredients = validated_data.pop("ingredients", [])

        recipe = Recipe.objects.create(**validated_data)

        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Update a recipe"""
        tags_data = validated_data.pop("tags", None)
        ingredients_data = validated_data.pop("ingredients", None)
        append_mode = validated_data.pop("append_tags", False)
        
        

        if tags_data is not None:
            if append_mode:
                self._get_or_create_tags(tags_data, instance)
            else:
                instance.tags.clear()
                self._get_or_create_tags(tags_data, instance)

        if ingredients_data is not None:
            if append_mode:
                self._get_or_create_ingredients(ingredients_data, instance)
            else:
                instance.ingredients.clear()
                self._get_or_create_ingredients(ingredients_data, instance)



        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ["description"]
