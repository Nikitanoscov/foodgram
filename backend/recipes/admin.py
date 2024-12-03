from django.contrib import admin

from .models import Recipes, Ingredients, Tags


@admin.register(Recipes)
class RecipeAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'author',
        'get_ingredients',
        'get_tags',
        'text',
        'image'
    )

    def get_ingredients(self, obj):
        return ', '.join(
            [ingredient.name for ingredient in obj.ingredient.all()]
        )

    def get_tags(self, obj):
        return ', '.join(
            [tag.name for tag in obj.tag.all()]
        )


admin.site.register(Tags)
admin.site.register(Ingredients)
