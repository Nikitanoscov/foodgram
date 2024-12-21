from django.db.models import Exists, OuterRef
from django_filters import rest_framework as filters

from recipes.models import Favourites, Recipes, ShoppingCard


class RecipeFilter(filters.FilterSet):
    """Фильтр для запросов к рецептам."""
    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug',
        required=False
    )
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
            'tags',
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
