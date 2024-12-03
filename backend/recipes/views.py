from django.shortcuts import get_object_or_404, render, redirect
from rest_framework import generics, viewsets

from recipes.models import Tags, Ingredients, Recipes
from api.serializers import (
    TagsSerializers,
    IngredientGetSerialzers,
    RecipesSerializers,
    RecipeCreateSerializers
)


class TagsViewSet(viewsets.ModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagsSerializers


class IngredientsViewSet(viewsets.ModelViewSet):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientGetSerialzers


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipes.objects.all()
    serializer_class = RecipesSerializers

    def get_permissions(self):
        if self.action == 'create':
            return RecipeCreateSerializers
        return super().get_permissions()


def short_link(link):
    recipe = get_object_or_404(
        Recipes,
        short_link=link
    )
    return redirect('recipes-detail', pk=recipe.id)
