from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (FollowViewSet, IngredientViewSet, RecipeViewSet,
                    TagsViewSet, UsersViewSet)

router = DefaultRouter()
router.register(r'users', UsersViewSet, basename='users')
router.register('tags',
                TagsViewSet,
                basename='tags')

router.register('recipes',
                RecipeViewSet,
                basename='recipes')

router.register(r'users/(?P<user_id>\d+)/subscribe',
                FollowViewSet,
                basename='follow-detail')

router.register('ingredients',
                IngredientViewSet,
                basename='Ingredient')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls),),
]
