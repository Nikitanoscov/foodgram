from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
import djoser.views
from rest_framework import viewsets, status
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticatedOrReadOnly,
    IsAuthenticated
)
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from api.filters import RecipeFilter, IngredientFilter
from api.mixins import DisableHttpMethodsMixin
from api.paginations import CustomPageNumberPagination
from api.permissions import OnlyAuthorOrReadOnly
from api.renders import TextShoppingCartRenders
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientGetSerializer,
    RecipeSerializer,
    RecipeShortLinksSerializer,
    ShoppingCardSerializer,
    SubscribeSerializers,
    TagsSerializer,
    UserSerializer
)
from recipes.models import Favourites, Ingredients, Recipes, ShoppingCard, Tags
from users.models import CustomUsers, Subscribers


class UserViewSet(djoser.views.UserViewSet):
    """Viewset для запросов к пользователям."""
    queryset = CustomUsers.objects.all()
    serializer_class = UserSerializer
    permission_class = (AllowAny,)
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        if self.action == 'list':
            return CustomUsers.objects.all()
        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def update_avatar(self, request):
        """Обновление аватара."""
        try:
            user = request.user
            serializer = AvatarSerializer(
                data=request.data,
                instance=user
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    data=serializer.data,
                    status=status.HTTP_200_OK
                )
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка при обновлении аватара: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete_avatar(self, request):
        """Удаление автара."""
        try:
            user = request.user
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {"error": f"Ошибка при удалении аватара: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=['put', 'delete'],
        detail=False,
        url_path='me/avatar',
        permission_class=(OnlyAuthorOrReadOnly,)
    )
    def me_avatar(self, request):
        """Распределитель запросв к аватару пользователя."""
        if self.request.user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if request.method == 'PUT':
            return self.update_avatar(request=request)
        return self.delete_avatar(request=request)

    @action(["get"], detail=False)
    def me(self, request, *args, **kwargs):
        """Для запроса пользователя к совим данным."""
        self.get_object = self.get_instance
        if request.method == "GET" and not self.request.user.is_anonymous:
            return self.retrieve(request, *args, **kwargs)
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    def add_subscribe(self, request, id):
        """Добавление подписки."""
        try:
            request.data['author'] = get_object_or_404(
                CustomUsers,
                id=id
            ).id
            request.data['subscriber'] = request.user.id
            serializer = SubscribeSerializers(
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

    def delete_subscribe(self, request, id):
        """Удаление подписки"""
        try:
            if not CustomUsers.objects.filter(
                id=id
            ).exists():
                raise ValidationError(code=400)
            sub = get_object_or_404(
                Subscribers,
                author=id,
                subscriber=self.request.user.id
            )
            sub.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404:
            return Response(
                data={'error': 'Такой подписки не существует.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError:
            return Response(
                data={'error': 'Автора не существует.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions'
    )
    def get_list_subscriptions(self, request):
        """Список подписок пользователя."""
        queryset = Subscribers.objects.filter(
            subscriber=self.request.user.id
        )
        paginator = self.pagination_class()
        paginate_queryset = paginator.paginate_queryset(
            queryset, request
        )
        serializer = SubscribeSerializers(
            paginate_queryset,
            many=True,
            context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(
        methods=('post', 'delete'),
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='subscribe'
    )
    def subscribe(self, request, id):
        """Распределитель запросов к подпискам."""
        if request.method == 'POST':
            return self.add_subscribe(request, id)
        elif request.method == 'DELETE':
            return self.delete_subscribe(request, id)


class TagsViewSet(DisableHttpMethodsMixin, viewsets.ModelViewSet):
    """Viewset для запросов к тегам."""
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    pagination_class = None


class IngredientsViewSet(DisableHttpMethodsMixin, viewsets.ModelViewSet):
    """Viewset для запросов к ингредиентам."""
    queryset = Ingredients.objects.all()
    serializer_class = IngredientGetSerializer
    permission_classes = (AllowAny,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Viewset для рецептов"""
    queryset = Recipes.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, OnlyAuthorOrReadOnly)
    pagination_class = CustomPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params:
            return self.filter_queryset(queryset)
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == 'retrieve':
            context['request'] = self.request
        return context

    def create(self, request, *args, **kwargs):
        request.data['author'] = request.user.id
        serializer = self.get_serializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def partial_update(self, request, pk):
        instance = get_object_or_404(
            Recipes,
            id=pk
        )
        self.check_object_permissions(self.request, instance)
        serializer = self.get_serializer(
            data=request.data,
            instance=instance,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(
        methods=('get',),
        detail=True,
        url_path='get-link',
        permission_classes=(AllowAny,)
    )
    def get_short_link(self, request, pk):
        """Получение короткой ссылки на рецепт."""
        try:
            recipe = get_object_or_404(
                Recipes,
                id=pk
            )
            serializer = RecipeShortLinksSerializer(
                data=request.data, instance=recipe
            )
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(
        methods=('get',),
        detail=False
    )
    def short_link_redirect(self, request, link):
        """Редирект по короткой ссылке на рецепт."""
        full_link = f"s/{link}"
        recipe = get_object_or_404(
            Recipes,
            short_link=full_link
        )
        return redirect('recipes-detail', pk=recipe.id)

    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
        renderer_classes=(TextShoppingCartRenders,)
    )
    def get_shopping_card(self, request):
        """Получения файла со списком продуктов."""
        filename = f"Список рецептов для {request.user.first_name}"
        recipes = request.user.shopping_recipe.all()
        serializer = ShoppingCardSerializer(
            recipes,
            many=True,
            context={'request': request}
        )
        return Response(
            serializer.data,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
            status=status.HTTP_200_OK
        )

    def add_shopping_cart(self, request, pk):
        """Добавление рецепта в список покупок"""
        request.data['user'] = self.request.user.id
        request.data['recipe'] = get_object_or_404(
            Recipes,
            id=pk
        ).id
        serializer = ShoppingCardSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def del_shopping_cart(self, request, pk):
        """Удаление рецепта из списка покупок."""
        try:
            if not Recipes.objects.filter(
                id=pk
            ).exists():
                raise ValidationError(code=400)
            cart = get_object_or_404(
                ShoppingCard,
                user=self.request.user.id,
                recipe=pk
            )
            cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404:
            return Response(
                data={'error': 'Рецепта нет в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError:
            return Response(
                data={'error': 'Рецепта нет в списке покупок.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(
        methods=('post', 'delete'),
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart'
    )
    def shopping_cart(self, request, pk):
        """Распределитель запросов к списку покупок."""
        if self.request.method == 'POST':
            return self.add_shopping_cart(request, pk)
        return self.del_shopping_cart(request, pk)

    def favorite_add(self, request, pk):
        """Добавление в избранное."""
        recipe = get_object_or_404(
            Recipes,
            id=pk
        )
        request.data['user'] = self.request.user.id
        request.data['recipe'] = recipe.id
        serializer = FavoriteSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def favorite_del(self, request, pk):
        """Удаление из избранного."""
        try:
            if not Recipes.objects.filter(
                id=pk
            ).exists():
                raise ValidationError(code=400)
            instance = get_object_or_404(
                Favourites,
                recipe_id=pk,
                user=self.request.user.id
            )
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'error': 'Рецепта нет в "избранном"'}
            )
        except ValidationError:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={'error': 'Рецепта не существует.'}
            )

    @action(
        methods=('post', 'delete'),
        detail=True,
        url_path='favorite',
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        """Распределение запросов к избранному."""
        if self.request.method == 'POST':
            return self.favorite_add(request, pk)
        return self.favorite_del(request, pk)
