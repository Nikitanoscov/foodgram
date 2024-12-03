from django.urls import include, path
from rest_framework.routers import DefaultRouter

from recipes.views import (
    TagsViewSet,
    RecipeViewSet,
    IngredientsViewSet,
    short_link
)
from users.views import UserViewSet

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
    path('s/<str:link>', short_link),
    # path(
    #     'users/me/avatar/',
    #     UserAvatarApi.as_view(),
    #     name='update_avatar'
    # ),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls))
]
