import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from recipes.models import (
    Favourites,
    Ingredients,
    Recipes,
    RecipesIngredients,
    RecipesTags,
    ShoppingCard,
    Tags
)
from users.models import CustomUsers, Subscribers


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для обработки изображений."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(
                base64.b64decode(imgstr), name='user_avatar.' + ext
            )

        return super().to_internal_value(data)


class UsersCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создание пользователей."""
    class Meta:
        model = CustomUsers
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }
        read_only_fields = (
            'id',
        )

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUsers.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для запросов к пользователям."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField(
        'get_avatar'
    )

    class Meta:
        model = CustomUsers
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscribers.objects.filter(
                subscriber=request.user, author=obj
            ).exists()
        return False

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для изменения аватарки пользователя."""
    avatar = Base64ImageField(
        required=True,
        write_only=True
    )

    class Meta:
        model = CustomUsers
        fields = ('avatar',)

        extra_kwargs = {
            'avatar': {'read_only': True}
        }

    def to_representation(self, instance):
        result = {
            'avatar': instance.avatar.url
        }
        return result

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class TagsSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    class Meta:
        model = Tags
        fields = (
            'id',
            'name',
            'slug'
        )
        read_only_fields = (
            'name',
            'slug'
        )

    def to_internal_value(self, data):
        if isinstance(data, int):
            return self.get_tag_by_id(data)

        elif isinstance(data, list):
            if not all(isinstance(item, int) for item in data):
                raise serializers.ValidationError(
                    "Все элементы должны быть числами."
                )

            return [self.get_tag_by_id(item) for item in data]

        return super().to_internal_value(data)

    def get_tag_by_id(self, tag_id):
        try:
            tag = Tags.objects.get(id=tag_id)
            return tag.id
        except Tags.DoesNotExist:
            raise serializers.ValidationError(
                f"Tag with id={tag_id} does not exist."
            )


class IngredientForRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов для интеграции в другие сериализаторы."""
    id = serializers.IntegerField()
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )
    amount = serializers.IntegerField(
        write_only=True
    )

    class Meta:
        model = RecipesIngredients
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )

    def validate(self, attrs):
        if attrs.get('amount') < 1:
            raise serializers.ValidationError(
                'amount: Must be greater than 0.'
            )
        return super().validate(attrs)


class IngredientGetSerializer(serializers.ModelSerializer):
    """Сериализатор для получения ингредиентов."""
    class Meta:
        model = Ingredients
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""
    ingredients = IngredientForRecipesSerializer(
        many=True,
        required=True
    )
    tags = TagsSerializer(
        many=True,
        required=True
    )
    image = Base64ImageField(
        required=True
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited'
    )

    class Meta:
        model = Recipes
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        extra_kwargs = {
            'author': {'required': False}
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        required_fields = ['name', 'image', 'cooking_time']
        missing_fields = [
            field for field in required_fields
            if field not in attrs or attrs[field] is None
        ]
        ingredients = attrs.get('ingredients', '')
        tags = attrs.get('tags', '')
        text = attrs.get('text', '')
        ingr_ids = [ingredients['id'] for ingredients in ingredients]
        if missing_fields:
            raise serializers.ValidationError(
                {field: f"{field} is required." for field in missing_fields}
            )
        if not text:
            raise serializers.ValidationError(
                'text: text is required.'
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
        if len(ingr_ids) > len(set(ingr_ids)):
            raise serializers.ValidationError(
                'ingredients: ingredients must be unique'
            )
        ingrs = Ingredients.objects.filter(
            id__in=ingr_ids
        )
        if len(ingrs) < len(ingr_ids):
            raise serializers.ValidationError(
                'ingredients: ingredient not found'
            )
        return attrs

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipes.objects.create(**validated_data)
        if ingredients and tags:
            for ingredient in ingredients:
                current_ingredient = get_object_or_404(
                    Ingredients,
                    id=ingredient['id']
                )
                RecipesIngredients.objects.create(
                    recipe=recipe,
                    ingredient=current_ingredient,
                    amount=ingredient.pop('amount')
                )
            for tag in tags:
                current_tag = get_object_or_404(
                    Tags,
                    id=tag
                )
                RecipesTags.objects.create(
                    recipe=recipe,
                    tag=current_tag,
                )
            return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text')
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            tags_lst = []
            for tag in tags:
                current_tag = get_object_or_404(
                    Tags,
                    id=tag
                )
                tags_lst.append(current_tag)
            instance.tags.set(tags_lst)
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            for ingredient in ingredients:
                current_ingredients = get_object_or_404(
                    Ingredients,
                    id=ingredient['id']
                )
                RecipesIngredients.objects.update_or_create(
                    recipe=instance,
                    ingredient=current_ingredients,
                    defaults={'amount': ingredient['amount']}
                )
        instance.save()
        return instance

    def to_representation(self, instance):
        """
        Метод для отображения данных после создания рецепта.
        """
        representation = super().to_representation(instance)
        ingredients = RecipesIngredients.objects.filter(
            recipe=instance
        )
        author = CustomUsers.objects.get(
            id=representation['author']
        )
        representation['author'] = UserSerializer(
            author
        ).data
        representation['ingredients'] = IngredientForRecipesSerializer(
            ingredients,
            many=True
        ).data
        for ingredient, amount_ingredients in zip(
            representation['ingredients'], ingredients
        ):
            ingredient['amount'] = amount_ingredients.amount
        representation['tags'] = TagsSerializer(
            instance.tags.all(),
            many=True
        ).data
        return representation

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_is_in_shopping_cart(self, obj):
        if ShoppingCard.objects.filter(
            user=obj.author,
            recipe=obj.id
        ).exists():
            return True
        return False

    def get_is_favorited(self, obj):
        if Favourites.objects.filter(
            user=obj.author,
            recipe=obj.id
        ).exists():
            return True
        return False


class RecipeShortLinksSerializer(serializers.ModelSerializer):
    """Сериализатор для получения короткой ссылки на рецепт."""
    short_link = serializers.CharField(read_only=True)

    class Meta:
        model = Recipes
        fields = (
            'short_link',
        )

    def to_representation(self, instance):
        data = {
            'short-link': instance.get_full_short_link()
        }
        return data


class RecipesForSubscribeSerializer(serializers.ModelSerializer):
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


class SubscribeSerializers(serializers.ModelSerializer):
    """Сериализатор подписок."""
    email = serializers.EmailField(
        source='author.email',
        read_only=True
    )
    id = serializers.IntegerField(
        source='author.id',
        read_only=True
    )
    username = serializers.CharField(
        source='author.username',
        read_only=True
    )
    first_name = serializers.CharField(
        source='author.first_name',
        read_only=True
    )
    last_name = serializers.CharField(
        source='author.last_name',
        read_only=True
    )
    recipes = RecipesForSubscribeSerializer(
        source='author.recipes',
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
        source='author.avatar',
        read_only=True
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
            'avatar',
            'author',
            'subscriber'
        )
        extra_kwargs = {
            'author': {'write_only': True},
            'subscriber': {'write_only': True}
        }
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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit and data.get('recipes'):
                limit = int(recipes_limit)
                data['recipes'] = data['recipes'][:limit]
        return data

    def validate(self, attrs):
        author = attrs.get('author')
        subscriber = attrs.get('subscriber')
        if author == subscriber:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        return super().validate(attrs)

    def get_is_subscribed(self, obj):
        if Subscribers.objects.filter(
            author=obj.author,
            subscriber=obj.subscriber
        ).exists():
            return True
        return False

    def get_recipes_count(self, obj):
        return Recipes.objects.filter(
            author=obj.author
        ).count()


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избарнного."""
    id = serializers.IntegerField(
        source='recipe.id',
        read_only=True
    )
    name = serializers.CharField(
        source='recipe.name',
        read_only=True
    )
    image = serializers.ImageField(
        source='recipe.image',
        read_only=True
    )
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True
    )

    class Meta:
        model = Favourites
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
            'recipe',
            'user'
        )
        extra_kwargs = {
            'recipe': {'write_only': True},
            'user': {'write_only': True}
        }
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Favourites.objects.all(),
                fields=('recipe', 'user'),
                message='Данный рецепт уже добавлен в избранное.'
            )
        ]


class ShoppingCardSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок"""
    id = serializers.IntegerField(
        source='recipe.id',
        required=False
    )
    name = serializers.CharField(
        source='recipe.name',
        required=False
    )
    image = serializers.ImageField(
        source='recipe.image',
        required=False
    )
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        required=False
    )

    class Meta:
        model = ShoppingCard
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
            'user',
            'recipe'
        )
        read_only_fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        extra_kwargs = {
            'recipe': {'write_only': True},
            'user': {'write_only': True}
        }
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingCard.objects.all(),
                fields=(
                    'user',
                    'recipe'
                ),
                message='Данный рецепт уже добавлин в список покупок.'
            ),
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        if request:
            data = {}
            recipe = instance.recipe
            ingredients = RecipesIngredients.objects.filter(
                recipe=recipe
            )
            for ingredient in ingredients:
                data[ingredient.ingredient.name] = ingredient.amount
            return data
        return super().to_representation(instance)
