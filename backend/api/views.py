from io import BytesIO

from django.db.models import Count, F, Sum
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
import djoser.views
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticatedOrReadOnly,
    IsAuthenticated
)
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from api.filters import RecipeFilter, IngredientFilter
from api.paginations import RecipesPageNumberPagination
from api.permissions import OnlyAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientGetSerializer,
    RecipesWriteSerializer,
    SubscriberReadSerializer,
    SubscriberWriteSerializer,
    ShoppingCardSerializer,
    TagsSerializer,
    UserSerializer
)
from recipes.models import (
    Favourites,
    Ingredients,
    Recipes,
    ShoppingCard,
    Tags,
    RecipesIngredients
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
        """Распределитель запросв к аватару пользователя."""
        serializer = AvatarSerializer(
            data=request.data,
            instance=request.user
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
        request.user.avatar = None
        request.user.save()
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
            user_subscriptions__subscriber=self.request.user
        ).annotate(
            recipes_count=Count('recipes')
        )
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
        try:
            request.data['author'] = get_object_or_404(
                Users,
                id=id
            ).id
            request.data['subscriber'] = request.user.id
            serializer = SubscriberWriteSerializer(
                data=request.data,
                context={'request': self.request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Http404:
            return Response(
                data={'error': 'Такого автора не существует.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        """Удаление подписки"""
        if not Users.objects.filter(
            id=id
        ).exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        user = self.request.user
        if user.user_subscriptions.filter(
            author=id
        ).exists():
            user.user_subscriptions.filter(
                author=id
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            data={'error': 'Такой подписки не существует.'},
            status=status.HTTP_400_BAD_REQUEST
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
    """Viewset для рецептов"""
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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == 'retrieve':
            context['request'] = self.request
        return context

    @action(
        methods=('get',),
        detail=True,
        url_path='get-link',
        permission_classes=(AllowAny,)
    )
    def get_short_link(self, request, pk):
        """Получение короткой ссылки на рецепт."""
        try:
            print(pk)
            recipe = get_object_or_404(
                Recipes,
                id=pk
            )
            short_link_path = reverse(
                'recipe_redirect', kwargs={'link': recipe.short_link}
            )
            full_short_link = request.build_absolute_uri(short_link_path)
            print(full_short_link)
            return JsonResponse(
                {'short-link': full_short_link}, status=status.HTTP_200_OK
            )
        except Exception as err:
            print(err)
            return Response(status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def render_shopping_cart(ingredients):
        lines = []
        for ingredient in ingredients:
            name = ingredient['name']
            unit = ingredient['measurement_unit']
            amount = ingredient['total_amount']
            lines.append(f"- {name} ({amount} {unit})")
        return "\n".join(lines)

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
        if Recipes.objects.filter(pk=pk).exists():
            data = {
                'user': request.user.id,
                'recipe': pk
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
        return Response(
            status=status.HTTP_404_NOT_FOUND
        )

    @staticmethod
    def delete_object(request, model_class, pk):
        deleted, _ = model_class.objects.filter(
            user=request.user, recipe__id=pk
        ).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            data={'error': 'Рецепта нет в списке покупок.'},
            status=status.HTTP_404_NOT_FOUND
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
