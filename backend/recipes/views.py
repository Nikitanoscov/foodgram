from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404

from .models import Recipes


def recipe_redirect(request, link):
    recipe = get_object_or_404(Recipes, short_link=link)
    recipe_url = f'/recipes/{recipe.id}/'
    return HttpResponsePermanentRedirect(recipe_url)
