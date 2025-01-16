from django.db import transaction
from django.db.models import Count
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from .constaints import MIN_INTEGER_VALUE
from recipes.models import (
    Favourites,
    Ingredients,
    Recipes,
    RecipesIngredients,
    ShoppingCard,
    Tags
)
from users.models import Subscribers, Users


class UserSerializer(DjoserUserSerializer):
    """Сериализатор для запросов к пользователям."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + (
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and obj.subscriptions_to_author.filter(
                subscriber=request.user
            ).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для изменения аватарки пользователя."""

    avatar = Base64ImageField(
        required=True
    )

    class Meta:
        model = Users
        fields = (
            'avatar',
        )


class TagsSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tags
        fields = (
            'id',
            'name',
            'slug'
        )


class IngredientForWriteRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для записи ингредиентов.
    Для интеграции в другие сериализатры.
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredients.objects.all()
    )
    amount = serializers.IntegerField(
        min_value=MIN_INTEGER_VALUE
    )

    class Meta:
        model = Ingredients
        fields = (
            'id',
            'amount'
        )


class IngredientForReadRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения ингредиентов.
    Для интеграции в другие сериализаторы.
    """
    id = serializers.IntegerField(
        read_only=True,
        source='ingredient.id'
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipesIngredients
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class IngredientGetSerializer(serializers.ModelSerializer):
    """Сериализатор для получения ингредиентов."""

    class Meta:
        model = Ingredients
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class RecipesReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов."""

    ingredients = IngredientForReadRecipeSerializer(
        many=True,
        source='ingredients_for_recipe'
    )
    tags = TagsSerializer(
        many=True
    )
    author = UserSerializer()
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipes
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_in_shopping_cart',
            'is_favorited',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and obj.shoppingcard_set.filter(
                user=request.user
            ).exists()
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and obj.favourites_set.filter(
                user=request.user
            ).exists()
        )


class RecipesWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи рецептов."""

    ingredients = IngredientForWriteRecipeSerializer(
        many=True,
        required=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tags.objects.all()
    )
    image = Base64ImageField(
        required=False
    )
    cooking_time = serializers.IntegerField(
        min_value=MIN_INTEGER_VALUE,
        required=True
    )

    class Meta:
        model = Recipes
        fields = (
            'author',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

        extra_kwargs = {
            'author': {'required': False}
        }

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                'Изображение обЪязательное.'
            )
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        ingredients = attrs.get('ingredients', '')
        tags = attrs.get('tags', '')
        unique_ingredients = set(
            ingredient['id'] for ingredient in ingredients
        )
        if not tags:
            raise serializers.ValidationError(
                'tags: tags is required.'
            )
        if len(tags) > len(set(tags)):
            raise serializers.ValidationError(
                'tags: Tags must be unique'
            )
        if not ingredients:
            raise serializers.ValidationError(
                'ingredients: ingredients is required.'
            )
        if len(ingredients) > len(unique_ingredients):
            raise serializers.ValidationError(
                'ingredients: Ingredients must be unique'
            )
        return attrs

    @staticmethod
    def _ingredients_create(recipe, ingredients):
        RecipesIngredients.objects.bulk_create(
            RecipesIngredients(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        )

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipes.objects.create(**validated_data)
        self._ingredients_create(recipe, ingredients)
        recipe.tags.set(tags)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.set(tags)
        instance.ingredients.clear()
        self._ingredients_create(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """
        Метод для отображения данных после создания рецепта.
        """
        return RecipesReadSerializer(
            instance,
            context=self.context
        ).data


class RecipesShortSerializer(serializers.ModelSerializer):
    """Сериализато рецептов для интеграции в другие сереализаторы."""

    image = Base64ImageField()

    class Meta:
        model = Recipes
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscriberReadSerializer(UserSerializer):
    """Сериализатор для чтения подписок."""

    recipes = serializers.SerializerMethodField(
        method_name='get_recipes'
    )
    recipes_count = serializers.IntegerField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        queryset = obj.recipes.all()
        request = self.context.get('request')
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit:
                try:
                    limit = int(recipes_limit)
                    queryset = queryset[:limit]
                except (ValueError, TypeError):
                    pass
        return RecipesShortSerializer(
            queryset,
            many=True,
            context=self.context
        ).data


class SubscriberWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи подписок."""

    class Meta:
        model = Subscribers
        fields = (
            'author',
            'subscriber'
        )
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Subscribers.objects.all(),
                fields=(
                    'author',
                    'subscriber'
                ),
                message='Вы уже подписаны на данного пользователя.',
            )
        ]

    def validate(self, attrs):
        author = attrs.get('author')
        subscriber = attrs.get('subscriber')
        if author == subscriber:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        return super().validate(attrs)

    def to_representation(self, instance):
        instance = Users.objects.annotate(
            recipes_count=Count('recipes')
        ).get(
            pk=instance.author.pk
        )
        return SubscriberReadSerializer(
            instance,
            context=self.context
        ).data


class BaseRecipesRelatedSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        return RecipesShortSerializer(
            instance.recipe,
            context=self.context
        ).data

    def validate(self, attrs):
        model = self.Meta.model
        user = self.context['request'].user
        recipe = attrs.get('recipe')

        if model.objects.filter(user=user, recipe=recipe).exists():
            verbose_name = model._meta.verbose_name
            raise serializers.ValidationError(
                f'Данный рецепт уже добавлен в {verbose_name}.'
            )
        return attrs


class FavoriteSerializer(BaseRecipesRelatedSerializer):
    """Сериализатор для избранного."""

    class Meta:
        model = Favourites
        fields = (
            'recipe',
            'user'
        )
        extra_kwargs = {
            'recipe': {'write_only': True},
            'user': {'write_only': True}
        }


class ShoppingCardSerializer(BaseRecipesRelatedSerializer):
    """Сериализатор для списка покупок"""

    class Meta:
        model = ShoppingCard
        fields = (
            'user',
            'recipe'
        )
        extra_kwargs = {
            'recipe': {'write_only': True},
            'user': {'write_only': True}
        }
