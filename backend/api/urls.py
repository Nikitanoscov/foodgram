from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    IngredientsViewSet,
    RecipeViewSet,
    TagsViewSet,
    UserViewSet
)


router = DefaultRouter()

router.register(
    r'tags',
    TagsViewSet,
    basename='tag'
)
router.register(
    r'ingredients',
    IngredientsViewSet,
    basename='ingredient'
)
router.register(
    r'recipes',
    RecipeViewSet,
    basename='recipe'
)
router.register(
    r'users',
    UserViewSet,
    basename='user'
)


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls))
]
