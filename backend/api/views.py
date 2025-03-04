from io import BytesIO

from django.db.models import Count, F, Sum
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
import djoser.views
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.paginations import RecipesPageNumberPagination
from api.permissions import OnlyAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientGetSerializer,
    RecipesWriteSerializer,
    ShoppingCardSerializer,
    SubscriberReadSerializer,
    SubscriberWriteSerializer,
    TagsSerializer,
    UserSerializer
)
from recipes.models import (
    Favourites,
    Ingredients,
    Recipes,
    RecipesIngredients,
    ShoppingCard,
    Tags
)
from users.models import Users


class UserViewSet(djoser.views.UserViewSet):
    """Viewset для запросов к пользователям."""

    queryset = Users.objects.all()
    serializer_class = UserSerializer
    permission_class = (AllowAny,)
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        if self.action == 'list':
            return self.queryset
        return super().get_queryset()

    @action(
        methods=('put',),
        detail=False,
        url_path='me/avatar',
        permission_classes=(IsAuthenticated, OnlyAuthorOrReadOnly)
    )
    def me_avatar(self, request):
        """Распределитель запросов к аватару пользователя."""
        serializer = AvatarSerializer(
            data=request.data,
            instance=request.user,
            context={'request': self.request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @me_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление автара."""
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        ('get',),
        detail=False,
        permission_classes=(IsAuthenticated, OnlyAuthorOrReadOnly)
    )
    def me(self, request, *args, **kwargs):
        """Для запроса пользователя к своим данным."""
        serializer = UserSerializer(
            instance=request.user,
            context={'request': self.request}
        )
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions'
    )
    def get_list_subscriptions(self, request):
        """Список подписок пользователя."""
        queryset = Users.objects.filter(
            subscriptions_to_author__subscriber=self.request.user
        ).annotate(
            recipes_count=Count('recipes')
        ).order_by('username')
        paginator = self.pagination_class()
        paginate_queryset = paginator.paginate_queryset(
            queryset, request
        )
        serializer = SubscriberReadSerializer(
            paginate_queryset,
            many=True,
            context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(
        methods=('post',),
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='subscribe'
    )
    def subscribe(self, request, id):
        author = get_object_or_404(
            Users,
            id=id
        ).id
        subscriber = request.user.id
        data = {
            'author': author,
            'subscriber': subscriber
        }
        serializer = SubscriberWriteSerializer(
            data=data,
            context={'request': self.request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        """Удаление подписки."""
        author = get_object_or_404(
            Users,
            pk=id
        )
        deleted, _ = author.subscriptions_to_author.filter(
            subscriber=request.user
        ).delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
            if deleted
            else status.HTTP_400_BAD_REQUEST
        )


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    """Viewset для запросов к тегам."""

    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    pagination_class = None


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """Viewset для запросов к ингредиентам."""

    queryset = Ingredients.objects.all()
    serializer_class = IngredientGetSerializer
    permission_classes = (AllowAny,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Viewset для рецептов."""

    queryset = Recipes.objects.select_related(
        'author'
    ).prefetch_related('tags', 'ingredients')
    serializer_class = RecipesWriteSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, OnlyAuthorOrReadOnly)
    pagination_class = RecipesPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=('get',),
        detail=True,
        url_path='get-link',
        permission_classes=(AllowAny,)
    )
    def get_short_link(self, request, pk):
        """Получение короткой ссылки на рецепт."""
        recipe = get_object_or_404(
            Recipes,
            id=pk
        )
        short_link_path = reverse(
            'recipe_redirect', kwargs={'link': recipe.short_link}
        )
        full_short_link = request.build_absolute_uri(short_link_path)
        return JsonResponse(
            {'short-link': full_short_link}, status=status.HTTP_200_OK
        )

    @staticmethod
    def render_shopping_cart(ingredients):
        lines = []
        for ingredient in ingredients:
            name = ingredient['name']
            unit = ingredient['measurement_unit']
            amount = ingredient['total_amount']
            lines.append(f'- {name} ({amount} {unit})')
        return '\n'.join(lines)

    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart'
    )
    def get_shopping_card(self, request):
        """Получения файла со списком продуктов."""
        ingredients = RecipesIngredients.objects.filter(
            recipe__shoppingcard_set__user=request.user
        ).values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('name')

        shopping_cart = self.render_shopping_cart(ingredients)
        filename = f'Список покупок для {request.user.first_name}.txt'
        buffer = BytesIO()
        buffer.write(shopping_cart.encode('utf-8'))
        buffer.seek(0)

        return FileResponse(
            buffer,
            content_type='text/plain',
            as_attachment=True,
            filename=filename
        )

    @staticmethod
    def create_object(request, serializer_class, pk):
        recipe = get_object_or_404(
            Recipes,
            pk=pk
        )
        data = {
            'user': request.user.id,
            'recipe': recipe.id
        }
        serializer = serializer_class(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @staticmethod
    def delete_object(request, model_class, pk):
        deleted, _ = model_class.objects.filter(
            user=request.user, recipe__id=pk
        ).delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
            if deleted
            else status.HTTP_404_NOT_FOUND
        )

    @action(
        methods=('post',),
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart'
    )
    def add_in_shopping_cart(self, request, pk):
        """Распределитель запросов к списку покупок."""
        return self.create_object(request, ShoppingCardSerializer, pk)

    @add_in_shopping_cart.mapping.delete
    def delete_object_in_shopping_cart(self, request, pk):
        return self.delete_object(request, ShoppingCard, pk)

    @action(
        methods=('post',),
        detail=True,
        url_path='favorite',
        permission_classes=(IsAuthenticated,)
    )
    def favorite_add(self, request, pk):
        """Распределение запросов к избранному."""
        return self.create_object(request, FavoriteSerializer, pk)

    @favorite_add.mapping.delete
    def favorite_del(self, request, pk):
        return self.delete_object(request, Favourites, pk)
