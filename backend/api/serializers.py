import base64

from django.shortcuts import get_object_or_404

from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import (
    Favourites,
    RecipesIngredients,
    Ingredients,
    Recipes,
    Tags,
    ShoppingCard,
    RecipesTags
)
from users.models import Subscribers
from users.serializers import UserSerializer


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagsSerializers(serializers.ModelSerializer):

    class Meta:
        model = Tags
        fields = ('id', 'name', 'slug')


class IngredientForRecipesSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        source='ingredient.id',
        read_only=True
    )
    name = serializers.CharField(
        source='ingredient.name'
    )
    unit_of_measurment = serializers.CharField(
        source='ingredient.unit_of_measurement',
        read_only=True
    )

    class Meta:
        model = RecipesIngredients
        fields = ('id', 'name', 'unit_of_measurement', 'amount')


class IngredientGetSerialzers(serializers.ModelSerializer):

    class Meta:
        model = Ingredients
        fields = (
            'id',
            'name',
            'unit_of_measurement'
        )


class RecipeCreateSerializers(serializers.ModelSerializer):

    ingredients = IngredientForRecipesSerializer(
        many=True,
        required=True
    )
    tags = IngredientForRecipesSerializer(
        many=True,
        required=True
    )
    image = Base64ImageField(
        required=True
    )

    class Meta:
        model = Recipes
        fields = (
            'ingredients',
            'tags',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipes.objects.create(**validated_data)
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredients,
                id=ingredient.pop('id')
            )
            RecipesIngredients.objects.create(
                recipe=recipe,
                ingredient=current_ingredient,
                amount=ingredient.pop('amount')
            )
        for tag in tags:
            current_tag = get_object_or_404(
                Tags,
                id=tag.pop('id')
            )
            RecipesTags.objects.create(
                recipe=recipe,
                tag=current_tag,
            )
        return recipe


class RecipesSerializers(serializers.ModelSerializer):
    tags = TagsSerializers(
        many=True
    )
    ingredients = IngredientForRecipesSerializer(
        many=True,
        read_only=True
    )
    author = UserSerializer()
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited'
    )
    is_in_shopping_card = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_card'
    )
    image = serializers.SerializerMethodField(
        method_name='get_image'
    )

    class Meta:
        model = Recipes
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_card',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return Favourites.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_card(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return ShoppingCard.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None


class RecipesForSubscribeSerializers(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        models = Recipes
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscribeSerializers(serializers.ModelSerializer):
    email = serializers.EmailField(
        source='author.email'
    )
    id = serializers.IntegerField(
        source='author.id'
    )
    username = serializers.CharField(
        source='author.username'
    )
    first_name = serializers.CharField(
        source='author.first_name'
    )
    last_name = serializers.CharField(
        source='author.last_name'
    )
    recipes = RecipesForSubscribeSerializers(
        many=True,
        read_only=True
    )
    recipes_count = serializers.SerializerMethodField(
        method_name='get_recipes_count'
    )
    is_subscribed = serializers.SerializerMethodField(
        method_name='get_is_subscribed'
    )
    avatar = serializers.ImageField(
        source='author.avatar'
    )

    class Meta:
        model = Subscribers
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )


    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscribers.objects.filter(
                subscriber=request.user, author=obj
            ).exists()
        return False
    
    def get_recipes_count(self, obj):
        return Recipes.objects.filter(
            author=obj
        ).count()
    

class FavoriteSerializers(serializers.ModelSerializer):
    id = serializers.IntegerField(
        source='recipe.id'
    )
    name = serializers.CharField(
        source='recipe.name'
    )
    image = serializers.ImageField(
        source='recipe.image'
    )
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time'
    )

    class Meta:
        model = Favourites
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class ShoppingCardSerializers(serializers.ModelSerializer):
    id = serializers.IntegerField(
        source='recipe.id'
    )
    name = serializers.CharField(
        source='recipe.name'
    )
    image = serializers.ImageField(
        source='recipe.image'
    )
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time'
    )

    class Meta:
        model = ShoppingCard
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )