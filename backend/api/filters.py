from django.db.models import Exists, OuterRef, Q, Case, When, IntegerField
from django_filters import rest_framework as filters

from recipes.models import Favourites, Ingredients, Recipes, ShoppingCard


class IngredientFilter(filters.FilterSet):
    """Фильтр для получения ингредиентов по названию с двойной фильтрацией."""

    name = filters.CharFilter(method='filter_name')

    class Meta:
        model = Ingredients
        fields = ('name',)

    def filter_name(self, queryset, name, value):
        """
        Фильтрует ингредиенты:
        сначала по началу названия, затем по вхождению.
        """
        return queryset.filter(
            Q(name__istartswith=value) | Q(name__icontains=value)
        ).annotate(
            priority=Case(
                When(name__istartswith=value, then=0),
                default=1,
                output_field=IntegerField(),
            )
        ).order_by('priority', 'name')


class RecipeFilter(filters.FilterSet):
    """Фильтр для запросов к рецептам."""
    author = filters.NumberFilter(
        field_name='author__id'
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipes
        fields = (
            'author',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset
        if value:
            return queryset.filter(
                Exists(Favourites.objects.filter(
                    user=self.request.user.id,
                    recipe=OuterRef('pk')
                ))
            )
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset
        if value:
            return queryset.filter(
                Exists(
                    ShoppingCard.objects.filter(
                        user=self.request.user.id,
                        recipe=OuterRef('pk')
                    )
                )
            )
        return queryset
