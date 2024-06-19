from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (FavoriteViewSet, FollowListViewSet, FollowViewSet,
                    IngredientViewSet, RecipeViewSet, ShoppingCartViewSet,
                    TagsViewSet, UsersViewSet)

router = DefaultRouter()
router.register(r'users', UsersViewSet, basename='users')
router.register('tags',
                TagsViewSet,
                basename='tags')

router.register('recipes',
                RecipeViewSet,
                basename='recipes')

router.register(r'recipes/(?P<title_id>\d+)/favorite',
                FavoriteViewSet,
                basename='favorite-detail')

router.register(r'users/(?P<title_id>\d+)/subscribe',
                FollowViewSet,
                basename='follow-detail')

router.register(r'recipes/(?P<title_id>\d+)/shopping_cart',
                ShoppingCartViewSet,
                basename='shopping_cart')

router.register('users/subscriptions',
                FollowListViewSet,
                basename='follow-list')

router.register('ingredients',
                IngredientViewSet,
                basename='Ingredient')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls),),
    path('', include('djoser.urls')),
]
