from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .forms import RecipeIngredientsInLineFormSet
from .models import (
    Favourites,
    Ingredients,
    Recipes,
    RecipesIngredients,
    ShoppingCard,
    Tags
)


@admin.register(Ingredients)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    search_fields = ('name',)


class RecipesIngredientsInline(admin.TabularInline):
    model = RecipesIngredients
    extra = 1
    min_num = 1
    validate_min = True
    autocomplete_fields = ('ingredient',)
    formset = RecipeIngredientsInLineFormSet


@admin.register(Recipes)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipesIngredientsInline,)
    list_display = (
        'name',
        'get_author_username',
        'get_ingredients',
        'get_tags',
        'text',
        'image_tag',
        'get_count_favorites'
    )
    fields = (
        'author',
        'name',
        'text',
        'image',
        'cooking_time',
        'tags'
    )
    search_fields = (
        'name',
        'author__username'
    )
    list_filter = ('tags',)
    filter_horizontal = ('tags',)

    def save_formset(self, request, form, formset, change):
        return super().save_formset(request, form, formset, change)

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        return ', '.join(
            [ingredient.name for ingredient in obj.ingredients.all()]
        )

    @admin.display(description='Теги')
    def get_tags(self, obj):
        return ', '.join(
            [tag.name for tag in obj.tags.all()]
        )

    @admin.display(description='Изображение')
    def image_tag(self, obj):
        return mark_safe(
            f'<img src={obj.image.url} width="80" height="60">'
        )

    @admin.display(description='Автор')
    def get_author_username(self, obj):
        link = reverse('admin:users_users_change', args=[obj.author.id])
        return format_html('<a href="{}">{}</a>', link, obj.author.username)

    @admin.display(description='В избранном')
    def get_count_favorites(self, obj):
        return obj.favourites_set.all().count()


@admin.register(Tags)
class TagAdmin(admin.ModelAdmin):
    search_fields = ('slug',)


@admin.register(Favourites)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe'
    )
    list_filter = ('user',)
    search_fields = ('user',)


@admin.register(ShoppingCard)
class ShoppingCardAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe'
    )
    list_filter = ('user',)
    search_fields = ('user',)
