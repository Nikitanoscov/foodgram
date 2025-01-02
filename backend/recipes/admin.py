from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (
    Favourites,
    Ingredients,
    Recipes,
    RecipesIngredients,
    RecipesTags,
    ShoppingCard,
    Tags
)
from .forms import RecipeIngredientsInLineFormSet, RecipeTagsInLineFormSet


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
    autocomplete_fields = ['ingredient']
    formset = RecipeIngredientsInLineFormSet


class RecipesTagsInline(admin.TabularInline):
    model = RecipesTags
    extra = 1
    formset = RecipeTagsInLineFormSet


@admin.register(Recipes)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipesIngredientsInline, RecipesTagsInline]
    list_display = (
        'name',
        'get_author_username',
        'get_ingredients',
        'get_tags',
        'text',
        'image_tag'
    )
    fields = (
        'author',
        'name',
        'text',
        'image',
        'cooking_time'
    )
    search_fields = (
        'name',
        'author__username'
    )
    list_filter = ('tags',)

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
        if obj.image:
            return mark_safe(
                f'<img src={obj.image.url} width="80" height="60">'
            )
        return 'Изображения нет.'

    @admin.display(description='Автор')
    def get_author_username(self, obj):
        return obj.author.username


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
