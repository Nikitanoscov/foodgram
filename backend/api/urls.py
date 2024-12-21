from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    IngredientsViewSet,
    RecipeViewSet,
    TagsViewSet
)
from api.views import UserViewSet

router = DefaultRouter()

router.register(
    r'tags',
    TagsViewSet
)
router.register(
    r'ingredients',
    IngredientsViewSet
)
router.register(
    r'recipes',
    RecipeViewSet
)
router.register(
    r'users',
    UserViewSet
)


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls))
]
