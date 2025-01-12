from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse

from .models import Recipes


def recipe_redirect(request, link):
    recipe = get_object_or_404(Recipes, short_link=link)
    recipe_url = reverse('recipe-detail', kwargs={'pk': recipe.id})

    return HttpResponsePermanentRedirect(recipe_url)
